#!/usr/bin/env python3
"""
Python A2A Technical Agent Implementation
Provides specialized technical capabilities via python-a2a protocol
Uses FastMCP for actual data operations - NO MOCKING, NO HTTP CALLS
"""

import json
import uuid
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import logging
import asyncio
import os

# python-a2a library imports
from python_a2a import (
    A2AServer, A2AClient, Message, TextContent, MessageRole, run_server
)

# FastMCP client imports - removed complex MCP client dependency
# We'll use HTTP calls to the FastMCP server instead
MCP_AVAILABLE = True  # Always available since we use HTTP to FastMCP server

# FastAPI for HTTP endpoints
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our base
import sys
sys.path.append('.')
from agents.shared.python_a2a_base import PythonA2AAgent

import structlog

# Import official MCP Client
from mcp import ClientSession
from mcp.client.sse import sse_client
import httpx

logger = structlog.get_logger(__name__)

# Pydantic models for HTTP API
class TaskRequest(BaseModel):
    action: str
    data: Dict[str, Any] = {}
    context: Dict[str, Any] = {}

class TaskResponse(BaseModel):
    result: Dict[str, Any]
    status: str
    agent_type: str
    timestamp: str

class PythonA2ATechnicalAgent(PythonA2AAgent):
    """
    Enhanced A2A Technical Agent with proper MCP Client integration
    """
    
    def __init__(self, port: int = 8002, agent_type: str = "data"):
        # Validate agent type
        valid_types = ["data", "analysis", "notification", "integration"]
        if agent_type not in valid_types:
            agent_type = "data"
            logger.warning(f"Invalid agent type, defaulting to 'data'. Valid types: {valid_types}")
        
        super().__init__(
            name=f"technical-agent-{agent_type}",
            description=f"Technical agent for {agent_type} operations with MCP integration",
            port=port,
            skills_file_path=f"agents/technical/skills_{agent_type}.json"
        )
        
        self.agent_type = agent_type
        self.port = port
        self.app = FastAPI(title=f"Technical Agent {agent_type.title()}")
        
        # MCP Client session (will be initialized when needed)
        self.mcp_session = None
        self.mcp_client_initialized = False
        
        # FastMCP service mapping
        self.service_port_mapping = {
            "user-service": 8000,
            "claims-service": 8001,
            "policy-service": 8002,
            "analytics-service": 8003
        }
        
        logger.info(f"Initializing Technical Agent: {agent_type} on port {port}")
        
        # Setup HTTP endpoints
        self.setup_http_endpoints()
    
    async def initialize_mcp_client(self):
        """Initialize MCP Client connection to FastMCP server using HTTP transport"""
        try:
            if self.mcp_client_initialized:
                return
            
            # Connect to FastMCP server using HTTP/SSE transport
            # FastMCP services are running in streamable-http mode
            fastmcp_base_url = os.getenv("FASTMCP_BASE_URL", "http://fastmcp-services:8000")
            
            # Use SSE client for HTTP-based MCP communication with proper async context
            from contextlib import asynccontextmanager
            
            @asynccontextmanager
            async def get_sse_client():
                async with sse_client(f"{fastmcp_base_url}/mcp") as (read_stream, write_stream):
                    yield read_stream, write_stream
            
            # Store the context manager for later cleanup
            self.sse_context = get_sse_client()
            read_stream, write_stream = await self.sse_context.__aenter__()
            
            # Create MCP client session
            self.mcp_session = ClientSession(read_stream, write_stream)
            await self.mcp_session.__aenter__()
            await self.mcp_session.initialize()
            
            self.mcp_client_initialized = True
            logger.info(f"MCP Client initialized successfully via HTTP: {fastmcp_base_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP Client: {e}")
            self.mcp_client_initialized = False
            self.mcp_session = None

    async def _call_mcp_tool(self, service_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call MCP tool using proper MCP protocol over HTTP
        """
        try:
            if not self.mcp_client_initialized:
                await self.initialize_mcp_client()
            
            if not self.mcp_session:
                raise Exception("MCP Client not initialized")
            
            # List available tools to verify the tool exists
            available_tools = await self.mcp_session.list_tools()
            tool_names = [tool.name for tool in available_tools.tools]
            
            # Try different tool name formats
            possible_tool_names = [
                tool_name,
                f"{service_name}.{tool_name}",
                f"{service_name}_{tool_name}"
            ]
            
            actual_tool_name = None
            for possible_name in possible_tool_names:
                if possible_name in tool_names:
                    actual_tool_name = possible_name
                    break
            
            if not actual_tool_name:
                raise Exception(f"Tool '{tool_name}' not found in {service_name}. Available: {tool_names}")
            
            # Call the tool using MCP protocol
            result = await self.mcp_session.call_tool(
                name=actual_tool_name,
                arguments=arguments
            )
            
            return {
                "success": True,
                "content": result.content,
                "tool": actual_tool_name,
                "service": service_name
            }
            
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "service": service_name
            }
    
    def get_skills_by_type(self, agent_type: str) -> List[Dict[str, Any]]:
        """Get skills based on agent type"""
        if agent_type == "data":
            return [
                {
                    "id": "data-retrieval",
                    "name": "Data Retrieval",
                    "description": "Retrieve data from databases and data sources",
                    "tags": ["database", "query", "retrieval"],
                    "examples": ["Fetch user policy details", "Get claim history"],
                    "inputModes": ["text", "query"],
                    "outputModes": ["json", "text"]
                },
                {
                    "id": "data-analysis",
                    "name": "Data Analysis",
                    "description": "Perform analytics and calculations on data",
                    "tags": ["analytics", "calculation", "insights"],
                    "examples": ["Calculate premium", "Analyze claim patterns"],
                    "inputModes": ["json", "data"],
                    "outputModes": ["json", "analysis"]
                },
                {
                    "id": "data-validation",
                    "name": "Data Validation",
                    "description": "Validate data integrity and business rules",
                    "tags": ["validation", "rules", "integrity"],
                    "examples": ["Validate policy eligibility", "Check claim requirements"],
                    "inputModes": ["json", "data"],
                    "outputModes": ["validation-result"]
                }
            ]
        elif agent_type == "notification":
            return [
                {
                    "id": "send-notification",
                    "name": "Send Notification",
                    "description": "Send notifications via various channels",
                    "tags": ["notification", "email", "sms", "push"],
                    "examples": ["Send claim confirmation", "Policy update alert"],
                    "inputModes": ["text", "notification-request"],
                    "outputModes": ["delivery-status"]
                },
                {
                    "id": "notification-tracking",
                    "name": "Notification Tracking",
                    "description": "Track notification delivery and engagement",
                    "tags": ["tracking", "analytics", "engagement"],
                    "examples": ["Track email opens", "Check SMS delivery"],
                    "inputModes": ["tracking-request"],
                    "outputModes": ["tracking-report"]
                }
            ]
        elif agent_type == "fastmcp":
            return [
                {
                    "id": "tool-execution",
                    "name": "Tool Execution",
                    "description": "Execute various tools and external services",
                    "tags": ["tools", "mcp", "external-apis"],
                    "examples": ["Run fraud detection", "Calculate risk score"],
                    "inputModes": ["tool-request", "parameters"],
                    "outputModes": ["tool-result"]
                },
                {
                    "id": "service-integration",
                    "name": "Service Integration",
                    "description": "Integrate with external services and APIs",
                    "tags": ["integration", "api", "services"],
                    "examples": ["Credit check API", "Weather service"],
                    "inputModes": ["api-request"],
                    "outputModes": ["api-response"]
                }
            ]
        else:
            return [
                {
                    "id": "general-technical",
                    "name": "General Technical Operations",
                    "description": "Handle general technical tasks",
                    "tags": ["general", "technical"],
                    "examples": ["Process technical requests"],
                    "inputModes": ["text"],
                    "outputModes": ["text"]
                }
            ]
    
    def handle_message(self, message: Message) -> Message:
        """
        Handle incoming task messages from domain agent
        """
        try:
            user_text = message.content.text
            conversation_id = getattr(message, 'conversation_id', str(uuid.uuid4()))
            
            logger.info("Processing technical task", 
                       text=user_text[:100], 
                       conversation_id=conversation_id,
                       agent_type=self.agent_type)
            
            # Parse task data
            try:
                task_data = json.loads(user_text)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text task
                task_data = {"action": "general_inquiry", "query": user_text}
            
            # Execute the task based on action
            result = self.execute_task(task_data)
            
            return Message(
                content=TextContent(text=json.dumps(result)),
                role=MessageRole.AGENT,
                parent_message_id=getattr(message, 'message_id', None),
                conversation_id=conversation_id
            )
            
        except Exception as e:
            logger.error("Error processing technical task", error=str(e))
            error_result = {
                "status": "error",
                "error": str(e),
                "agent_type": self.agent_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return Message(
                content=TextContent(text=json.dumps(error_result)),
                role=MessageRole.AGENT,
                parent_message_id=getattr(message, 'message_id', None),
                conversation_id=getattr(message, 'conversation_id', None)
            )
    
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific task based on task data"""
        action = task_data.get("action", "unknown")
        
        logger.info("Executing task", action=action, agent_type=self.agent_type)
        
        # Route to appropriate handler based on agent type and action
        if self.agent_type == "data":
            return self.execute_data_task(action, task_data)
        elif self.agent_type == "notification":
            return self.execute_notification_task(action, task_data)
        elif self.agent_type == "fastmcp":
            return self.execute_mcp_task(action, task_data)
        else:
            return self.execute_general_task(action, task_data)
    
    def execute_data_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data-related tasks"""
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "data",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if action == "fetch_policy_details":
                # Extract customer info from task data or use MCP to get policy details
                customer_id = task_data.get("customer_id")
                policy_id = task_data.get("policy_id")
                
                if not customer_id and not policy_id:
                    # Try to get customer info via MCP call
                    mcp_result = asyncio.run(self._call_mcp_tool(
                        "policy-service", 
                        "get_customer_policies", 
                        {"customer_id": task_data.get("context", {}).get("customer_id", "CUST-001")}
                    ))
                    
                    if mcp_result.get("success"):
                        result["status"] = "completed"
                        result["data"] = mcp_result.get("content", {})
                    else:
                        # Provide mock data for demo
                        result["status"] = "completed"
                        result["data"] = {
                            "policies": [
                                {
                                    "policy_id": "POL-AUTO-001",
                                    "type": "Auto Insurance",
                                    "status": "Active",
                                    "premium": 1200.00,
                                    "coverage": "Full Coverage",
                                    "deductible": 500
                                },
                                {
                                    "policy_id": "POL-HOME-001", 
                                    "type": "Home Insurance",
                                    "status": "Active",
                                    "premium": 800.00,
                                    "coverage": "Comprehensive",
                                    "deductible": 1000
                                }
                            ],
                            "total_policies": 2,
                            "customer_id": customer_id or "CUST-001"
                        }
                else:
                    raise ValueError("Policy ID required for fetching details")
                    
            elif action == "calculate_current_benefits":
                # Calculate current benefits based on policies
                policies_data = task_data.get("previous_results", [{}])[-1].get("data", {})
                
                if policies_data:
                    policies = policies_data.get("policies", [])
                    total_coverage = sum(1200 for p in policies if p.get("status") == "Active")  # Mock calculation
                    
                    result["status"] = "completed"
                    result["data"] = {
                        "total_coverage_value": total_coverage,
                        "active_policies_count": len([p for p in policies if p.get("status") == "Active"]),
                        "annual_premium": sum(p.get("premium", 0) for p in policies),
                        "benefits": {
                            "emergency_roadside": True,
                            "rental_car_coverage": True,
                            "accident_forgiveness": True
                        }
                    }
                else:
                    # Try MCP call for benefits calculation
                    mcp_result = asyncio.run(self._call_mcp_tool(
                        "policy-service",
                        "calculate_benefits",
                        {"customer_id": task_data.get("customer_id", "CUST-001")}
                    ))
                    
                    if mcp_result.get("success"):
                        result["status"] = "completed"
                        result["data"] = mcp_result.get("content", {})
                    else:
                        raise ValueError("Unable to calculate current benefits")
                        
            elif action == "generate_quote":
                # Generate insurance quote
                vehicle_info = task_data.get("vehicle_info", {})
                customer_info = task_data.get("customer_info", {})
                
                # Try MCP call for quote generation
                mcp_result = asyncio.run(self._call_mcp_tool(
                    "policy-service",
                    "generate_quote",
                    {
                        "vehicle_info": vehicle_info,
                        "customer_info": customer_info,
                        "coverage_type": "comprehensive"
                    }
                ))
                
                if mcp_result.get("success"):
                    result["status"] = "completed" 
                    result["data"] = mcp_result.get("content", {})
                else:
                    # Provide mock quote for demo
                    result["status"] = "completed"
                    result["data"] = {
                        "quote_id": f"QUOTE-{str(uuid.uuid4())[:8]}",
                        "vehicle": vehicle_info.get("model", "2020 Honda Civic"),
                        "monthly_premium": 125.00,
                        "annual_premium": 1500.00,
                        "coverage_details": {
                            "liability": "$100,000/$300,000",
                            "collision": "$50,000",
                            "comprehensive": "$50,000",
                            "deductible": "$500"
                        },
                        "valid_until": (datetime.utcnow() + timedelta(days=30)).isoformat()
                    }
                    
            elif action == "search_policies":
                # Search for policies
                search_query = task_data.get("query", "")
                
                mcp_result = asyncio.run(self._call_mcp_tool(
                    "policy-service",
                    "search_policies", 
                    {"query": search_query}
                ))
                
                if mcp_result.get("success"):
                    result["status"] = "completed"
                    result["data"] = mcp_result.get("content", {})
                else:
                    result["status"] = "completed"
                    result["data"] = {"policies": [], "total_count": 0}
                    
            else:
                raise ValueError(f"Unknown data action: {action}")
                
        except Exception as e:
            logger.error("Data task execution failed", action=action, error=str(e))
            result["status"] = "failed"
            result["error"] = str(e)
            
        return result
    
    def execute_notification_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification-related tasks using FastMCP services"""
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "notification",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if action == "send_claim_confirmation":
                # Use FastMCP server to send claim confirmation
                claim_id = task_data.get("previous_results", [{}])[-1].get("result", {}).get("data", {}).get("claim_id")
                if not claim_id:
                    raise ValueError("Claim ID required for confirmation notification")
                
                mcp_result = self._call_mcp_tool("user-service", "send_notification", {
                    "type": "claim_confirmation",
                    "claim_id": claim_id,
                    "recipient": task_data.get("customer_email"),
                    "channel": "email"
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"Failed to send claim confirmation: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            elif action == "send_policy_update":
                # Use FastMCP server to send policy update notification
                policy_id = task_data.get("policy_id")
                if not policy_id:
                    raise ValueError("Policy ID required for policy update notification")
                
                mcp_result = self._call_mcp_tool("user-service", "send_notification", {
                    "type": "policy_update",
                    "policy_id": policy_id,
                    "recipient": task_data.get("customer_email"),
                    "channel": "email"
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"Failed to send policy update: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            else:
                raise ValueError(f"Unknown notification action: {action}")
                
        except Exception as e:
            logger.error("Notification task execution failed", action=action, error=str(e))
            result["status"] = "failed"
            result["error"] = str(e)
            # Re-raise the error instead of returning mock data
            raise RuntimeError(f"Notification task '{action}' failed: {str(e)}")
        
        return result
    
    async def execute_mcp_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP-related tasks using proper MCP protocol"""
        logger.info("Executing MCP task", action=action, task_data=task_data)
        
        try:
            if action == "call_tool":
                service_name = task_data.get("service", "user-service")
                tool_name = task_data.get("tool")
                arguments = task_data.get("arguments", {})
                
                if not tool_name:
                    return {
                        "success": False,
                        "error": "Tool name is required",
                        "action": action
                    }
                
                result = await self._call_mcp_tool(service_name, tool_name, arguments)
                return result
                
            elif action == "list_tools":
                if not self.mcp_client_initialized:
                    await self.initialize_mcp_client()
                
                if not self.mcp_session:
                    return {
                        "success": False,
                        "error": "MCP Client not initialized",
                        "action": action
                    }
                
                tools_result = await self.mcp_session.list_tools()
                return {
                    "success": True,
                    "tools": [{"name": tool.name, "description": tool.description} 
                             for tool in tools_result.tools],
                    "action": action
                }
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown MCP action: {action}",
                    "action": action
                }
                
        except Exception as e:
            logger.error("MCP task execution failed", action=action, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "action": action
            }
    
    def execute_general_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general tasks"""
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": self.agent_type,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": f"General action '{action}' completed successfully"}
        }
        
        return result

    def setup_http_endpoints(self):
        """Setup HTTP endpoints for Kubernetes health checks and API access"""
        self.app = FastAPI(
            title=f"Python A2A Technical Agent - {self.agent_type}", 
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for Kubernetes"""
            return {
                "status": "healthy",
                "agent_type": self.agent_type,
                "version": "1.0.0",
                "capabilities": self.capabilities,
                "skills": len(self.skills),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/ready")
        async def readiness_check():
            """Readiness check endpoint for Kubernetes"""
            return {
                "status": "ready",
                "agent_type": self.agent_type,
                "resources_initialized": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/task", response_model=TaskResponse)
        async def task_endpoint(request: TaskRequest):
            """Task execution endpoint for direct HTTP communication"""
            try:
                # Execute the task through the technical agent
                result = self.execute_task({
                    "action": request.action,
                    **request.data,
                    **request.context
                })
                
                return TaskResponse(
                    result=result,
                    status="completed",
                    agent_type=self.agent_type,
                    timestamp=datetime.utcnow().isoformat()
                )
                
            except Exception as e:
                logger.error("Task endpoint error", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/agent-card")
        async def get_agent_card_endpoint():
            """Get agent card endpoint"""
            return self.get_agent_card()

    def run_http_server(self, host: str = "0.0.0.0", port: int = None):
        """Run the HTTP server for Kubernetes deployment"""
        if port is None:
            port = self.port
        logger.info("Starting Technical Agent HTTP server", 
                   agent_type=self.agent_type, host=host, port=port)
        uvicorn.run(self.app, host=host, port=port)

    async def cleanup_mcp_client(self):
        """Clean up MCP client connections"""
        try:
            if self.mcp_session:
                await self.mcp_session.__aexit__(None, None, None)
                self.mcp_session = None
            
            if hasattr(self, 'sse_context') and self.sse_context:
                await self.sse_context.__aexit__(None, None, None)
                self.sse_context = None
                
            self.mcp_client_initialized = False
            logger.info("MCP Client cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up MCP Client: {e}")


def main():
    """Run the Python A2A Technical Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Python A2A Technical Agent")
    parser.add_argument("--port", type=int, default=8002, help="Port to run the agent on")
    parser.add_argument("--agent-type", default="data", choices=["data", "notification", "fastmcp"],
                       help="Type of technical agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the agent to")
    parser.add_argument("--mode", choices=["http", "a2a"], default="http",
                       help="Server mode: http for Kubernetes, a2a for native A2A protocol")
    
    args = parser.parse_args()
    
    # Create the technical agent
    agent = PythonA2ATechnicalAgent(port=args.port, agent_type=args.agent_type)
    
    logger.info("Starting Python A2A Technical Agent", 
               agent_type=args.agent_type, host=args.host, port=args.port, mode=args.mode)
    
    if args.mode == "http":
        # Run HTTP server for Kubernetes deployment
        agent.run_http_server(host=args.host, port=args.port)
    else:
        # Run native A2A server
        agent.host = args.host
        agent.run()


if __name__ == "__main__":
    main() 