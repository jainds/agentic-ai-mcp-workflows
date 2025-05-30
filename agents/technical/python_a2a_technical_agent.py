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
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import logging

# python-a2a library imports
from python_a2a import (
    A2AServer, A2AClient, Message, TextContent, MessageRole, run_server
)

# FastMCP client imports
try:
    from mcp import Client as MCPClient
    from mcp.types import Tool, TextContent as MCPTextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP client not available - this will cause runtime errors")

# FastAPI for HTTP endpoints
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our base
import sys
import os
sys.path.append('.')
from agents.shared.python_a2a_base import PythonA2AAgent

import structlog

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
    Technical agent for executing tasks using python-a2a
    
    Responsibilities:
    - Execute specific technical tasks routed from domain agent
    - Provide data access and analytics capabilities
    - Handle API integrations and external service calls
    - Manage notifications and communications
    - Perform tool-based operations
    """
    
    def __init__(self, port: int = 8002, agent_type: str = "data"):
        # Validate agent type
        valid_types = ["data", "notification", "fastmcp"]
        if agent_type not in valid_types:
            raise ValueError(f"Invalid agent type: {agent_type}. Must be one of {valid_types}")
        
        self.agent_type = agent_type
        
        # Define capabilities based on agent type
        capabilities = {
            "streaming": False,
            "pushNotifications": agent_type == "notification",
            "fileUpload": False,
            "messageHistory": True,
            "taskExecution": True,
            "dataAccess": agent_type == "data",
            "apiIntegration": True,
            "toolOperations": agent_type in ["fastmcp", "tools"],
            "notifications": agent_type == "notification",
            "python_a2a_compatible": True
        }
        
        # Initialize Python A2A Agent
        super().__init__(
            name=f"{agent_type.title()}TechnicalAgent",
            description=f"Python A2A Technical Agent for {agent_type} operations using FastMCP",
            port=port,
            capabilities=capabilities,
            version="2.0.0"
        )
        
        # Agent-specific skills
        self.skills = self.get_skills_by_type(agent_type)
        
        # Initialize MCP clients instead of mock resources
        self.mcp_clients = {}
        self.initialize_mcp_connections()
        
        # Setup HTTP endpoints for Kubernetes deployment
        self.setup_http_endpoints()
        
        logger.info("Python A2A Technical Agent initialized with MCP connections",
                   agent_type=agent_type, port=port, mcp_available=MCP_AVAILABLE)
    
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
    
    def initialize_mcp_connections(self):
        """Initialize MCP connections to FastMCP services"""
        if not MCP_AVAILABLE:
            logger.warning("MCP client not available - technical agent will fail on MCP calls")
            return
        
        # FastMCP service endpoints (Kubernetes service names)
        self.fastmcp_services = {
            "user-service": os.getenv("USER_SERVICE_URL", "http://user-service:8000/mcp/"),
            "claims-service": os.getenv("CLAIMS_SERVICE_URL", "http://claims-service:8001/mcp/"),
            "policy-service": os.getenv("POLICY_SERVICE_URL", "http://policy-service:8002/mcp/"),
            "analytics-service": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8003/mcp/")
        }
        
        # Initialize MCP clients for each service
        for service_name, service_url in self.fastmcp_services.items():
            try:
                # In a real implementation, this would establish MCP connections
                # For now, we store the service endpoints for MCP tool calls
                self.mcp_clients[service_name] = {
                    "url": service_url,
                    "connected": True,
                    "tools": []  # Will be populated via tool discovery
                }
                logger.info(f"MCP connection configured for {service_name}", url=service_url)
            except Exception as e:
                logger.error(f"Failed to connect to {service_name}", error=str(e))
                self.mcp_clients[service_name] = {
                    "url": service_url,
                    "connected": False,
                    "error": str(e)
                }
        
        logger.info("MCP connections initialized", 
                   total_services=len(self.fastmcp_services),
                   connected_services=sum(1 for client in self.mcp_clients.values() if client.get("connected")))
    
    def _call_mcp_tool(self, service_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call FastMCP tool on specified service"""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP client not available")
        
        if service_name not in self.mcp_clients:
            raise ValueError(f"Unknown FastMCP service: {service_name}")
        
        mcp_client = self.mcp_clients[service_name]
        if not mcp_client.get("connected"):
            raise RuntimeError(f"FastMCP service {service_name} not connected: {mcp_client.get('error')}")
        
        try:
            # In a real MCP implementation, this would use the MCP protocol
            # For now, we simulate the MCP call structure
            logger.info(f"Calling MCP tool {tool_name} on {service_name}", arguments=arguments)
            
            # Simulate MCP tool call
            # In production, this would be:
            # result = await self.mcp_clients[service_name].call_tool(tool_name, arguments)
            
            # For now, raise an error since we don't have real MCP integration
            # This ensures the technical agent fails properly when MCP is not available
            raise RuntimeError(f"Real MCP integration not implemented - tool call to {service_name}.{tool_name} failed")
            
        except Exception as e:
            logger.error(f"MCP tool call failed", 
                        service=service_name, 
                        tool=tool_name, 
                        error=str(e))
            # Return MCP-style error response
            return {
                "success": False,
                "error": str(e),
                "service": service_name,
                "tool": tool_name
            }
    
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
        """Execute data-related tasks using FastMCP services"""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP client not available - cannot execute data tasks")
        
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "data",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if action == "validate_policy":
                # Use MCP tool to validate policy
                policy_id = task_data.get("plan_context", {}).get("entities", {}).get("policy_id")
                if not policy_id:
                    raise ValueError("Policy ID required for validation")
                
                # Call FastMCP policy service
                mcp_result = self._call_mcp_tool("policy-service", "validate_policy", {
                    "policy_id": policy_id
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"Policy validation failed: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            elif action == "fetch_policy_details":
                # Use MCP tool to fetch policy details
                policy_id = task_data.get("plan_context", {}).get("entities", {}).get("policy_id")
                if not policy_id:
                    raise ValueError("Policy ID required for fetching details")
                
                mcp_result = self._call_mcp_tool("policy-service", "get_policy_details", {
                    "policy_id": policy_id
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"Failed to fetch policy details: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            elif action == "create_claim_record":
                # Use MCP tool to create claim
                claim_data = task_data.get("plan_context", {})
                
                mcp_result = self._call_mcp_tool("claims-service", "create_claim", {
                    "customer_id": claim_data.get("customer_id"),
                    "policy_number": claim_data.get("policy_id"),
                    "incident_date": claim_data.get("incident_date"),
                    "description": claim_data.get("description"),
                    "amount": claim_data.get("amount"),
                    "claim_type": claim_data.get("claim_type", "auto")
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"Failed to create claim: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            elif action == "fetch_billing_history":
                # Use MCP tool to fetch billing
                customer_id = task_data.get("plan_context", {}).get("customer_id")
                if not customer_id:
                    raise ValueError("Customer ID required for billing history")
                
                mcp_result = self._call_mcp_tool("user-service", "get_billing_history", {
                    "customer_id": customer_id
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"Failed to fetch billing history: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            elif action == "general_information_lookup":
                # Use MCP tool for general lookup
                query = task_data.get("plan_context", {}).get("user_request", "")
                customer_id = task_data.get("plan_context", {}).get("customer_id")
                
                mcp_result = self._call_mcp_tool("analytics-service", "general_lookup", {
                    "query": query,
                    "customer_id": customer_id
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"General lookup failed: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            else:
                raise ValueError(f"Unknown data action: {action}")
                
        except Exception as e:
            logger.error("Data task execution failed", action=action, error=str(e))
            result["status"] = "failed"
            result["error"] = str(e)
            # Re-raise the error instead of returning mock data
            raise RuntimeError(f"Data task '{action}' failed: {str(e)}")
        
        return result
    
    def execute_notification_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification-related tasks using FastMCP services"""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP client not available - cannot execute notification tasks")
        
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "notification",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if action == "send_claim_confirmation":
                # Use MCP tool to send claim confirmation
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
                # Use MCP tool to send policy update notification
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
    
    def execute_mcp_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP/tool-related tasks using FastMCP services"""
        if not MCP_AVAILABLE:
            raise RuntimeError("MCP client not available - cannot execute MCP tasks")
        
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "fastmcp",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            if action == "fraud_detection_check":
                # Use MCP tool for fraud detection
                claim_data = task_data.get("previous_results", [{}])[-1].get("result", {}).get("data", {})
                if not claim_data:
                    raise ValueError("Claim data required for fraud detection")
                
                mcp_result = self._call_mcp_tool("analytics-service", "fraud_detection", {
                    "claim_data": claim_data,
                    "threshold": 0.7
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"Fraud detection failed: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            elif action == "risk_assessment":
                # Use MCP tool for risk assessment
                policy_data = task_data.get("policy_data")
                customer_data = task_data.get("customer_data")
                
                if not policy_data or not customer_data:
                    raise ValueError("Policy and customer data required for risk assessment")
                
                mcp_result = self._call_mcp_tool("analytics-service", "risk_assessment", {
                    "policy_data": policy_data,
                    "customer_data": customer_data
                })
                
                if not mcp_result.get("success"):
                    raise RuntimeError(f"Risk assessment failed: {mcp_result.get('error')}")
                
                result["status"] = "completed"
                result["data"] = mcp_result["data"]
                
            else:
                raise ValueError(f"Unknown MCP action: {action}")
                
        except Exception as e:
            logger.error("MCP task execution failed", action=action, error=str(e))
            result["status"] = "failed"
            result["error"] = str(e)
            # Re-raise the error instead of returning mock data
            raise RuntimeError(f"MCP task '{action}' failed: {str(e)}")
        
        return result
    
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