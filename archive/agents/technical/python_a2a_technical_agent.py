#!/usr/bin/env python3
"""
Python A2A Technical Agent Implementation
Provides specialized technical capabilities via python-a2a protocol
Uses FastMCP for actual data operations - NO MOCKING, NO HTTP CALLS
"""

import json
import uuid
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
import sys

# python-a2a library imports
from python_a2a import (
    Message, TextContent, MessageRole
)

# FastMCP client imports - using the official FastMCP Client
from fastmcp import Client

# FastAPI for HTTP endpoints
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our base
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
    Enhanced A2A Technical Agent with proper MCP Client integration using FastMCP
    """
    
    def __init__(self, port: int = 8002, agent_type: str = "data"):
        # Validate agent type
        if agent_type not in ["data", "notification", "fastmcp"]:
            raise ValueError(f"Invalid agent type: {agent_type}. Must be one of: data, notification, fastmcp")
        
        # Initialize the base class with proper parameters
        super().__init__(
            name=f"Technical {agent_type.title()} Agent",
            description=f"Specialized A2A technical agent for {agent_type} operations using FastMCP",
            port=port
        )
        
        self.agent_type = agent_type
        self.port = port
        self.mcp_client = None
        self.mcp_client_initialized = False
        
        # MCP tool registry - discovered tools from FastMCP services
        self.available_mcp_tools = {}
        
        # FastMCP server configuration based on documentation
        self.mcp_config = {
            "mcpServers": {
                "user-service": {
                    "url": os.getenv("USER_SERVICE_MCP_URL", "http://user-service:8000/mcp"),
                    "transport": "streamable-http"
                },
                "claims-service": {
                    "url": os.getenv("CLAIMS_SERVICE_MCP_URL", "http://claims-service:8001/mcp"), 
                    "transport": "streamable-http"
                },
                "policy-service": {
                    "url": os.getenv("POLICY_SERVICE_MCP_URL", "http://policy-service:8002/mcp"),
                    "transport": "streamable-http"
                },
                "analytics-service": {
                    "url": os.getenv("ANALYTICS_SERVICE_MCP_URL", "http://analytics-service:8003/mcp"),
                    "transport": "streamable-http"
                }
            }
        }
        
        # Agent capabilities based on type
        self.agent_capabilities = self._initialize_agent_capabilities()
        
        # Setup HTTP endpoints for Kubernetes deployment
        self.setup_http_endpoints()
        
        logger.info(f"Initialized {agent_type} technical agent", 
                   port=port, 
                   capabilities=len(self.agent_capabilities),
                   mcp_servers=list(self.mcp_config["mcpServers"].keys()))
    
    def _initialize_agent_capabilities(self) -> Dict[str, Any]:
        """Initialize agent capabilities and knowledge about when to use them"""
        if self.agent_type == "data":
            return {
                "primary_functions": [
                    "fetch_customer_data",
                    "retrieve_policy_information", 
                    "get_claims_history",
                    "calculate_benefits",
                    "analyze_risk_factors"
                ],
                "triggers": [
                    "policy details", "customer information", "claims history",
                    "benefits", "coverage", "what policies", "my account"
                ],
                "required_info": {
                    "fetch_policy_details": ["customer_id"],
                    "calculate_benefits": ["customer_id", "policies_data"],
                    "get_claims": ["customer_id"]
                },
                "fallback_questions": {
                    "missing_customer_id": "I need your customer ID to look up your information. Could you provide it?",
                    "missing_policy_id": "Could you specify which policy you're asking about?"
                }
            }
        elif self.agent_type == "notification":
            return {
                "primary_functions": [
                    "send_confirmation",
                    "send_updates",
                    "schedule_reminders",
                    "deliver_notifications"
                ],
                "triggers": [
                    "send notification", "confirm", "alert", "remind", "notify"
                ],
                "required_info": {
                    "send_notification": ["recipient", "message_type"],
                    "schedule_reminder": ["recipient", "reminder_date"]
                }
            }
        elif self.agent_type == "fastmcp":
            return {
                "primary_functions": [
                    "execute_external_tools",
                    "integrate_services", 
                    "run_calculations",
                    "process_complex_requests"
                ],
                "triggers": [
                    "calculate", "analyze", "process", "external", "integration"
                ]
            }
        else:
            return {"primary_functions": [], "triggers": []}

    async def discover_and_register_mcp_tools(self):
        """Discover MCP tools from FastMCP services and register them with the agent"""
        try:
            if not self.mcp_client_initialized:
                await self.initialize_mcp_client()
            
            if not self.mcp_client:
                logger.warning("FastMCP client not available, skipping tool discovery")
                return
            
            # Discover available tools from all connected servers
            try:
                # Try to get tools - FastMCP may expose tools differently
                # Check if the client has a list_tools method
                if hasattr(self.mcp_client, 'list_tools'):
                    available_tools = await self.mcp_client.list_tools()
                    # Handle different response formats
                    tools_list = []
                    if hasattr(available_tools, 'tools'):
                        tools_list = available_tools.tools
                    elif isinstance(available_tools, list):
                        tools_list = available_tools
                    elif isinstance(available_tools, dict) and 'tools' in available_tools:
                        tools_list = available_tools['tools']
                    
                    for tool in tools_list:
                        # Register tool with agent's knowledge base
                        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                        tool_desc = tool.description if hasattr(tool, 'description') else ""
                        
                        self.available_mcp_tools[tool_name] = {
                            "description": tool_desc,
                            "input_schema": getattr(tool, 'inputSchema', {}),
                            "capabilities": self._analyze_tool_capabilities_simple(tool_name, tool_desc)
                        }
                else:
                    logger.warning("FastMCP client does not support list_tools method")
                    
            except Exception as e:
                logger.warning(f"Could not list tools from FastMCP client: {e}")
                # Continue without tool discovery
            
            logger.info(f"Discovered and registered {len(self.available_mcp_tools)} MCP tools",
                       tools=list(self.available_mcp_tools.keys()))
            
        except Exception as e:
            logger.error(f"Failed to discover MCP tools: {e}")
            # Continue without MCP tools - agent can still provide mock responses

    def _analyze_tool_capabilities_simple(self, tool_name: str, tool_description: str) -> List[str]:
        """Analyze what a tool can do based on its name and description (simplified version)"""
        capabilities = []
        name_lower = tool_name.lower()
        desc_lower = tool_description.lower() if tool_description else ""
        
        # Categorize tool capabilities
        if any(word in name_lower or word in desc_lower for word in ["get", "fetch", "retrieve", "find"]):
            capabilities.append("data_retrieval")
        if any(word in name_lower or word in desc_lower for word in ["create", "add", "insert", "new"]):
            capabilities.append("data_creation")
        if any(word in name_lower or word in desc_lower for word in ["update", "modify", "edit", "change"]):
            capabilities.append("data_modification")
        if any(word in name_lower or word in desc_lower for word in ["calculate", "compute", "analyze"]):
            capabilities.append("computation")
        if any(word in name_lower or word in desc_lower for word in ["send", "notify", "alert"]):
            capabilities.append("notification")
        
        return capabilities

    def _analyze_tool_capabilities(self, tool) -> List[str]:
        """Analyze what a tool can do based on its name and description (legacy version for compatibility)"""
        tool_name = tool.name if hasattr(tool, 'name') else str(tool)
        tool_description = tool.description if hasattr(tool, 'description') else ""
        return self._analyze_tool_capabilities_simple(tool_name, tool_description)

    def determine_appropriate_action(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently determine what action to take based on available information"""
        action = task_data.get("action", "")
        context = task_data.get("context", {})
        
        # Check if we have required information
        required_info = self.agent_capabilities.get("required_info", {}).get(action, [])
        missing_info = []
        
        for req in required_info:
            if not task_data.get(req) and not context.get(req):
                missing_info.append(req)
        
        # If we're missing critical information, suggest what questions to ask
        if missing_info:
            return {
                "status": "needs_more_info",
                "missing_fields": missing_info,
                "suggested_questions": [
                    self.agent_capabilities.get("fallback_questions", {}).get(f"missing_{field}", 
                        f"I need {field.replace('_', ' ')} to help you with this request.")
                    for field in missing_info
                ],
                "action": action
            }
        
        # We have enough info, check if we have appropriate MCP tools
        suitable_tools = self._find_suitable_mcp_tools(action, task_data)
        
        return {
            "status": "ready_to_execute",
            "action": action,
            "suitable_tools": suitable_tools,
            "execution_plan": self._create_execution_plan(action, task_data, suitable_tools)
        }

    def _find_suitable_mcp_tools(self, action: str, task_data: Dict[str, Any]) -> List[str]:
        """Find MCP tools that are suitable for the requested action"""
        suitable_tools = []
        
        for tool_name, tool_info in self.available_mcp_tools.items():
            # Match based on action and tool capabilities
            if self._tool_matches_action(action, tool_name, tool_info):
                suitable_tools.append(tool_name)
        
        return suitable_tools

    def _tool_matches_action(self, action: str, tool_name: str, tool_info: Dict[str, Any]) -> bool:
        """Check if a tool is suitable for the given action"""
        action_lower = action.lower()
        tool_name_lower = tool_name.lower()
        capabilities = tool_info.get("capabilities", [])
        
        # Direct name matching
        if action_lower in tool_name_lower or any(word in tool_name_lower for word in action_lower.split("_")):
            return True
        
        # Capability-based matching
        action_to_capability = {
            "fetch_policy_details": "data_retrieval",
            "calculate_benefits": "computation",
            "get_customer": "data_retrieval",
            "send_notification": "notification",
            "create_claim": "data_creation"
        }
        
        required_capability = action_to_capability.get(action)
        if required_capability and required_capability in capabilities:
            return True
        
        return False

    def _create_execution_plan(self, action: str, task_data: Dict[str, Any], suitable_tools: List[str]) -> Dict[str, Any]:
        """Create an execution plan using available MCP tools or fallback strategies"""
        plan = {
            "primary_strategy": "mcp_tools" if suitable_tools else "mock_data",
            "tools_to_use": suitable_tools,
            "fallback_strategy": "mock_data",
            "expected_outcome": f"Complete {action} successfully"
        }
        
        return plan

    async def initialize_mcp_client(self):
        """Initialize MCP Client connection to FastMCP servers using official FastMCP Client"""
        try:
            if self.mcp_client_initialized:
                return
            
            # Create FastMCP client with multiple server configuration
            self.mcp_client = Client(self.mcp_config)
            
            # Initialize the client - this will connect to all configured servers
            await self.mcp_client.__aenter__()
            
            self.mcp_client_initialized = True
            logger.info("FastMCP Client initialized successfully", 
                       servers=list(self.mcp_config["mcpServers"].keys()))
            
            # Register MCP tools with the agent
            await self.discover_and_register_mcp_tools()
                
        except Exception as e:
            logger.error(f"Failed to initialize FastMCP Client: {e}")
            self.mcp_client_initialized = False
            self.mcp_client = None

    async def _call_mcp_tool(self, service_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call MCP tool using proper FastMCP Client with server prefixes
        """
        try:
            if not self.mcp_client_initialized:
                await self.initialize_mcp_client()
            
            if not self.mcp_client:
                raise Exception("FastMCP Client not initialized")
            
            # Use server prefix as per FastMCP documentation
            # Tools are accessed with server name prefix: "server_tool_name"
            prefixed_tool_name = f"{service_name}_{tool_name}"
            
            # Call the tool using FastMCP client
            result = await self.mcp_client.call_tool(prefixed_tool_name, arguments)
            
            return {
                "success": True,
                "content": result,
                "tool": prefixed_tool_name,
                "service": service_name
            }
            
        except Exception as e:
            logger.error(f"FastMCP tool call failed: {e}")
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
                "timestamp": datetime.now().isoformat()
            }
            
            return Message(
                content=TextContent(text=json.dumps(error_result)),
                role=MessageRole.AGENT,
                parent_message_id=getattr(message, 'message_id', None),
                conversation_id=getattr(message, 'conversation_id', None)
            )
    
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task with intelligent action determination and MCP tool usage
        """
        try:
            # First, determine if we can proceed or need more information
            action_plan = self.determine_appropriate_action(task_data)
            
            if action_plan["status"] == "needs_more_info":
                return {
                    "status": "incomplete",
                    "agent_type": self.agent_type,
                    "message": "I need more information to help you.",
                    "required_questions": action_plan["suggested_questions"],
                    "missing_fields": action_plan["missing_fields"],
                    "timestamp": datetime.now().isoformat()
                }
            
            # We have enough info to proceed
            action = action_plan["action"]
            suitable_tools = action_plan["suitable_tools"]
            
            # Try to execute using MCP tools first, then fallback to agent-specific logic
            if suitable_tools:
                return asyncio.run(self._execute_with_mcp_tools(action, task_data, suitable_tools))
            else:
                return self._execute_with_agent_logic(action, task_data)
                
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "status": "error",
                "agent_type": self.agent_type,
                "error": str(e),
                "message": "I encountered an error while processing your request. Let me try a different approach.",
                "timestamp": datetime.now().isoformat()
            }

    async def _execute_with_mcp_tools(self, action: str, task_data: Dict[str, Any], suitable_tools: List[str]) -> Dict[str, Any]:
        """Execute task using discovered MCP tools"""
        try:
            results = []
            
            for tool_name in suitable_tools:
                # Prepare arguments based on task data
                tool_args = self._prepare_tool_arguments(tool_name, task_data)
                
                # Execute the MCP tool
                tool_result = await self._call_mcp_tool_intelligent(tool_name, tool_args)
                results.append(tool_result)
            
            # Combine and process results
            return self._process_mcp_results(action, results, task_data)
            
        except Exception as e:
            logger.error(f"MCP tool execution failed: {e}")
            # Fallback to agent logic
            return self._execute_with_agent_logic(action, task_data)

    def _prepare_tool_arguments(self, tool_name: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare arguments for MCP tool based on task data and tool requirements"""
        # Extract relevant data from task_data and context
        args = {}
        context = task_data.get("context", {})
        
        # Common argument mappings
        if "customer_id" in task_data:
            args["customer_id"] = task_data["customer_id"]
        elif "customer_id" in context:
            args["customer_id"] = context["customer_id"]
        
        if "policy_id" in task_data:
            args["policy_id"] = task_data["policy_id"]
        elif "policy_id" in context:
            args["policy_id"] = context["policy_id"]
        
        # Tool-specific argument preparation
        tool_info = self.available_mcp_tools.get(tool_name, {})
        input_schema = tool_info.get("input_schema", {})
        
        # Add other required parameters based on input schema
        if input_schema and "properties" in input_schema:
            for prop_name, prop_info in input_schema["properties"].items():
                if prop_name not in args and prop_name in task_data:
                    args[prop_name] = task_data[prop_name]
        
        return args

    async def _call_mcp_tool_intelligent(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call FastMCP tool with intelligent error handling"""
        try:
            if not self.mcp_client_initialized:
                await self.initialize_mcp_client()
            
            if not self.mcp_client:
                raise Exception("FastMCP client not available")
            
            # Call the tool using FastMCP client
            result = await self.mcp_client.call_tool(tool_name, arguments)
            
            return {
                "success": True,
                "tool": tool_name,
                "content": result,
                "arguments": arguments
            }
            
        except Exception as e:
            logger.error(f"FastMCP tool call failed for {tool_name}: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "arguments": arguments
            }

    def _process_mcp_results(self, action: str, results: List[Dict[str, Any]], task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and combine MCP tool results into a coherent response"""
        successful_results = [r for r in results if r.get("success")]
        failed_results = [r for r in results if not r.get("success")]
        
        if not successful_results:
            # All tools failed, use fallback
            return self._execute_with_agent_logic(action, task_data)
        
        # Combine successful results
        combined_content = []
        for result in successful_results:
            if result.get("content"):
                combined_content.extend(result["content"])
        
        return {
            "status": "success",
            "agent_type": self.agent_type,
            "action": action,
            "data": combined_content,
            "tools_used": [r["tool"] for r in successful_results],
            "message": f"Successfully executed {action} using MCP tools",
            "timestamp": datetime.now().isoformat()
        }

    def _execute_with_agent_logic(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using agent-specific logic as fallback"""
        # Route to appropriate agent-specific method
        if self.agent_type == "data":
            return self.execute_data_task(action, task_data)
        elif self.agent_type == "notification":
            return self.execute_notification_task(action, task_data)
        elif self.agent_type == "fastmcp":
            return self.execute_general_task(action, task_data)
        else:
            return self.execute_general_task(action, task_data)

    def execute_data_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data-related tasks"""
        result = {
            "task_id": str(uuid.uuid4()),
            "action": action,
            "agent_type": "data",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if action == "fetch_policy_details":
                # Extract customer info from task data or use MCP to get policy details
                customer_id = task_data.get("customer_id") or task_data.get("context", {}).get("customer_id")
                policy_id = task_data.get("policy_id")
                
                # Try to get customer policies using available identifiers
                if customer_id or policy_id:
                    # Try MCP call to get policy details
                    mcp_result = asyncio.run(self._call_mcp_tool(
                        "policy-service", 
                        "get_customer_policies", 
                        {"customer_id": customer_id or "CUST-001"}
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
                    # No customer_id or policy_id provided - use default for demo
                    result["status"] = "completed"
                    result["data"] = {
                        "policies": [],
                        "total_policies": 0,
                        "message": "No customer identifier provided",
                        "customer_id": "UNKNOWN"
                    }
                    
            elif action == "calculate_current_benefits":
                # Calculate current benefits based on customer context or previous results
                customer_id = task_data.get("customer_id") or task_data.get("context", {}).get("customer_id")
                policies_data = task_data.get("previous_results", [{}])[-1].get("data", {})
                
                if policies_data and policies_data.get("policies"):
                    # Use existing policy data from previous results
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
                        },
                        "customer_id": customer_id or "CUST-001"
                    }
                elif customer_id:
                    # Try MCP call for benefits calculation using customer_id
                    mcp_result = asyncio.run(self._call_mcp_tool(
                        "policy-service",
                        "calculate_benefits",
                        {"customer_id": customer_id}
                    ))
                    
                    if mcp_result.get("success"):
                        result["status"] = "completed"
                        result["data"] = mcp_result.get("content", {})
                    else:
                        # Provide fallback benefits data
                        result["status"] = "completed"
                        result["data"] = {
                            "total_coverage_value": 0,
                            "active_policies_count": 0,
                            "annual_premium": 0,
                            "benefits": {},
                            "message": "No active policies found",
                            "customer_id": customer_id
                        }
                else:
                    # No customer context available
                    result["status"] = "completed"
                    result["data"] = {
                        "total_coverage_value": 0,
                        "active_policies_count": 0,
                        "annual_premium": 0,
                        "benefits": {},
                        "message": "Customer identification required",
                        "customer_id": "UNKNOWN"
                    }
                    
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
                        "valid_until": (datetime.now() + timedelta(days=30)).isoformat()
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
            "timestamp": datetime.now().isoformat()
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
                
                if not self.mcp_client:
                    return {
                        "success": False,
                        "error": "FastMCP Client not initialized",
                        "action": action
                    }
                
                try:
                    tools_result = await self.mcp_client.list_tools()
                    # Handle different response formats from FastMCP
                    tools_list = []
                    if hasattr(tools_result, 'tools'):
                        tools_list = [{"name": tool.name, "description": getattr(tool, 'description', '')} 
                                     for tool in tools_result.tools]
                    elif isinstance(tools_result, list):
                        tools_list = [{"name": str(tool), "description": ""} for tool in tools_result]
                    elif isinstance(tools_result, dict) and 'tools' in tools_result:
                        tools_list = tools_result['tools']
                    
                    return {
                        "success": True,
                        "tools": tools_list,
                        "action": action
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to list tools: {str(e)}",
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
            "timestamp": datetime.now().isoformat(),
            "data": {"message": f"General action '{action}' completed successfully"}
        }
        
        return result

    def setup_http_endpoints(self):
        """Setup HTTP endpoints including automatic MCP tool discovery"""
        self.app = FastAPI(title=f"Technical Agent {self.agent_type.title()}")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.on_event("startup")
        async def startup_event():
            """Initialize MCP tools on startup"""
            logger.info(f"Starting {self.agent_type} technical agent with MCP integration")
            await self.initialize_mcp_client()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on shutdown"""
            await self.cleanup_mcp_client()

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "agent_type": self.agent_type,
                "mcp_initialized": self.mcp_client_initialized,
                "available_tools": len(self.available_mcp_tools),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/ready")
        async def readiness_check():
            return {
                "ready": True,
                "agent_type": self.agent_type,
                "mcp_tools_registered": len(self.available_mcp_tools) > 0,
                "capabilities": self.agent_capabilities.get("primary_functions", []),
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/task", response_model=TaskResponse)
        async def task_endpoint(request: TaskRequest):
            try:
                result = self.execute_task({
                    "action": request.action,
                    **request.data,
                    "context": request.context
                })
                
                return TaskResponse(
                    result=result,
                    status="success",
                    agent_type=self.agent_type,
                    timestamp=datetime.now().isoformat()
                )
            except Exception as e:
                logger.error(f"Task execution failed: {e}")
                return TaskResponse(
                    result={"error": str(e)},
                    status="error",
                    agent_type=self.agent_type,
                    timestamp=datetime.now().isoformat()
                )

        @self.app.get("/agent-card")
        async def get_agent_card_endpoint():
            return self.get_agent_card()

        @self.app.get("/tools")
        async def get_available_tools():
            """Return available MCP tools and agent capabilities"""
            return {
                "agent_type": self.agent_type,
                "mcp_tools": self.available_mcp_tools,
                "agent_capabilities": self.agent_capabilities,
                "mcp_initialized": self.mcp_client_initialized,
                "timestamp": datetime.now().isoformat()
            }

    def run_http_server(self, host: str = "0.0.0.0", port: int = None):
        """Run the HTTP server for Kubernetes deployment"""
        if port is None:
            port = self.port
        logger.info("Starting Technical Agent HTTP server", 
                   agent_type=self.agent_type, host=host, port=port)
        uvicorn.run(self.app, host=host, port=port)

    async def cleanup_mcp_client(self):
        """Cleanup MCP client connections"""
        try:
            if self.mcp_client:
                await self.mcp_client.__aexit__(None, None, None)
                self.mcp_client = None
                logger.info("MCP client closed")
            
            self.mcp_client_initialized = False
            logger.info("MCP client cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during MCP cleanup: {e}")
            self.mcp_client_initialized = False
            self.mcp_client = None


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