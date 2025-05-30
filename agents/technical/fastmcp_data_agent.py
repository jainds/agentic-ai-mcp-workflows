"""
FastMCP Data Agent - A2A-compatible technical agent using official FastMCP Client to connect to insurance services.
Handles MCP tool calls and data analysis for domain agents via Google A2A protocol and official FastMCP Client.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import structlog

# FastMCP Client imports (official FastMCP 2.0)
from fastmcp import Client

# Official Google A2A Library imports (a2a-sdk) - conditional import
try:
    from a2a import A2AServer, run_server
    from a2a.models import AgentCard, TaskRequest, TaskResponse
    A2A_AVAILABLE = True
except ImportError:
    # Mock classes for testing/development environments
    class TaskRequest:
        def __init__(self, taskId: str, user: Dict[str, Any]):
            self.taskId = taskId
            self.user = user
    
    class TaskResponse:
        def __init__(self, taskId: str, status: str, parts: List[Dict[str, Any]], metadata: Dict[str, Any]):
            self.taskId = taskId
            self.status = status
            self.parts = parts
            self.metadata = metadata
    
    A2A_AVAILABLE = False

try:
    from agents.shared.a2a_base import A2AAgent
    A2A_BASE_AVAILABLE = True
except ImportError:
    # Mock base class for testing/development environments
    class A2AAgent:
        def __init__(self, name: str, description: str, port: int, capabilities: Dict[str, Any], version: str):
            self.name = name
            self.description = description
            self.port = port
            self.capabilities = capabilities
            self.version = version
    
    A2A_BASE_AVAILABLE = False

logger = structlog.get_logger(__name__)


class FastMCPDataAgent(A2AAgent):
    """A2A-compatible technical agent that connects to FastMCP services using official MCP Client"""
    
    def __init__(self, port: int = 8002):
        capabilities = {
            "streaming": False,
            "pushNotifications": False,
            "fileUpload": False,
            "messageHistory": True,
            "dataAccess": True,
            "mcpIntegration": True,
            "google_a2a_compatible": True,
            "fastmcp_client": True
        }
        
        # Initialize A2A agent with official library
        super().__init__(
            name="FastMCPDataAgent",
            description="Technical agent providing data access via FastMCP services using official FastMCP Client and Google A2A protocol",
            port=port,
            capabilities=capabilities,
            version="2.1.0"
        )
        
        # FastMCP service URLs for official Client connections
        self.service_urls = {
            "user": os.getenv("USER_SERVICE_URL", "http://localhost:8000/mcp"),
            "claims": os.getenv("CLAIMS_SERVICE_URL", "http://localhost:8001/mcp"),
            "policy": os.getenv("POLICY_SERVICE_URL", "http://localhost:8002/mcp"),
            "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8003/mcp")
        }
        
        # FastMCP clients (will be initialized per request)
        self.mcp_clients: Dict[str, Client] = {}
        
        # Available tools cache
        self.available_tools = {}
        
        logger.info("FastMCP Data Agent initialized with official FastMCP Client", 
                   services=list(self.service_urls.keys()), 
                   port=port,
                   fastmcp_version="2.0+")
    
    def handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle incoming A2A tasks for data operations using FastMCP Client"""
        user_data = task.user
        action = user_data.get("action", "unknown")
        
        logger.info("Processing data request via FastMCP", 
                   task_id=task.taskId, 
                   action=action)
        
        try:
            # Route to appropriate handler based on action
            if action == "get_customer":
                result = asyncio.run(self._handle_get_customer(user_data))
            elif action == "get_claims":
                result = asyncio.run(self._handle_get_claims(user_data))
            elif action == "get_policies":
                result = asyncio.run(self._handle_get_policies(user_data))
            elif action == "create_claim":
                result = asyncio.run(self._handle_create_claim(user_data))
            elif action == "update_claim":
                result = asyncio.run(self._handle_update_claim(user_data))
            elif action == "fraud_analysis":
                result = asyncio.run(self._handle_fraud_analysis(user_data))
            elif action == "get_customer_data":
                result = asyncio.run(self._handle_get_customer_data(user_data))
            else:
                result = {"error": f"Unknown action: {action}"}
            
            # Return successful TaskResponse
            return TaskResponse(
                taskId=task.taskId,
                status="completed",
                parts=[{
                    "text": json.dumps({
                        "action": action,
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent": "FastMCPDataAgent",
                        "protocol": "FastMCP_2.0"
                    }),
                    "type": "data_response"
                }],
                metadata={
                    "agent": "FastMCPDataAgent",
                    "action": action,
                    "result_type": type(result).__name__,
                    "protocol": "FastMCP_Client_2.0"
                }
            )
            
        except Exception as e:
            logger.error("Data operation failed", 
                        task_id=task.taskId, 
                        action=action, 
                        error=str(e))
            
            # Return error TaskResponse
            return TaskResponse(
                taskId=task.taskId,
                status="failed",
                parts=[{
                    "text": json.dumps({
                        "action": action,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent": "FastMCPDataAgent"
                    }),
                    "type": "error"
                }],
                metadata={
                    "agent": "FastMCPDataAgent",
                    "action": action,
                    "error": str(e)
                }
            )
    
    async def initialize(self):
        """Initialize the agent by discovering available tools from FastMCP services"""
        try:
            logger.info("Initializing FastMCP Data Agent...")
            
            # Initialize MCP clients for each service
            for service_name, service_url in self.service_urls.items():
                try:
                    # Create FastMCP client for the service
                    client = Client(service_url)
                    self.mcp_clients[service_name] = client
                    
                    # Test connection and discover tools
                    await self._discover_service_tools(service_name, client)
                    
                    logger.info(f"FastMCP client initialized for {service_name}", 
                              url=service_url)
                    
                except Exception as e:
                    logger.warning(f"Failed to initialize client for {service_name}", 
                                  error=str(e))
                    self.available_tools[service_name] = []
            
            total_tools = sum(len(tools) for tools in self.available_tools.values())
            logger.info("FastMCP Agent initialization complete", 
                       services=len(self.mcp_clients),
                       total_tools=total_tools)
                       
        except Exception as e:
            logger.error("Failed to initialize FastMCP agent", error=str(e))
            raise
    
    async def _discover_service_tools(self, service_name: str, client: Client):
        """Discover available MCP tools from a service using FastMCP Client"""
        try:
            # Use FastMCP Client to discover tools
            async with client:
                # List available tools
                tools = await client.list_tools()
                
                # Convert to our internal format
                tool_list = []
                for tool in tools:
                    tool_info = {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                    }
                    tool_list.append(tool_info)
                
                self.available_tools[service_name] = tool_list
                
                logger.info(f"Discovered FastMCP tools for {service_name}", 
                           count=len(tool_list), 
                           tools=[tool["name"] for tool in tool_list])
                           
        except Exception as e:
            logger.error(f"Error discovering FastMCP tools for {service_name}", 
                        error=str(e))
            self.available_tools[service_name] = []
    
    async def call_tool(self, service_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool on a service using FastMCP Client"""
        try:
            client = self.mcp_clients.get(service_name)
            if not client:
                return {
                    "success": False, 
                    "error": f"No FastMCP client available for service: {service_name}"
                }
            
            logger.debug(f"Calling FastMCP tool", 
                        service=service_name, 
                        tool=tool_name,
                        arguments=arguments)
            
            # Use FastMCP Client to call the tool
            async with client:
                result = await client.call_tool(tool_name, arguments)
                
                # Process the result
                if result and len(result) > 0:
                    # Get the first content item (usually TextContent)
                    content = result[0]
                    
                    if hasattr(content, 'text'):
                        try:
                            # Try to parse as JSON
                            tool_result = json.loads(content.text)
                        except json.JSONDecodeError:
                            # If not JSON, return as text
                            tool_result = {
                                "success": True,
                                "result": content.text,
                                "type": "text"
                            }
                    else:
                        tool_result = {
                            "success": True,
                            "result": str(content),
                            "type": "content"
                        }
                    
                    logger.debug(f"FastMCP tool call successful", 
                               service=service_name, 
                               tool=tool_name,
                               success=tool_result.get("success", True))
                    
                    return tool_result
                else:
                    return {
                        "success": False, 
                        "error": "Empty result from FastMCP tool"
                    }
                
        except Exception as e:
            logger.error(f"Error calling FastMCP tool", 
                        service=service_name, 
                        tool=tool_name, 
                        error=str(e))
            return {
                "success": False, 
                "error": f"FastMCP tool call failed: {str(e)}"
            }
    
    # Customer data operations using FastMCP
    async def _handle_get_customer_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_customer_data action using FastMCP"""
        customer_id = user_data.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID required"}
        
        try:
            # Get customer basic info via FastMCP
            customer_result = await self.call_tool("user", "get_user", {"user_id": customer_id})
            
            # Get customer policies via FastMCP
            policies_result = await self.call_tool("policy", "list_policies", {"customer_id": customer_id})
            
            # Get customer claims via FastMCP
            claims_result = await self.call_tool("claims", "list_claims", {"customer_id": customer_id})
            
            return {
                "success": True,
                "customer_id": customer_id,
                "customer_info": customer_result,
                "policies": policies_result.get("policies", []) if policies_result.get("success") else [],
                "claims": claims_result.get("claims", []) if claims_result.get("success") else [],
                "timestamp": datetime.utcnow().isoformat(),
                "protocol": "FastMCP_2.0"
            }
            
        except Exception as e:
            logger.error("Error getting customer data via FastMCP", 
                        customer_id=customer_id, 
                        error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            }
    
    async def _handle_get_customer(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_customer action using FastMCP"""
        customer_id = user_data.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID required"}
        
        return await self.call_tool("user", "get_user", {"user_id": customer_id})
    
    async def _handle_get_claims(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_claims action using FastMCP"""
        customer_id = user_data.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID required"}
        
        return await self.call_tool("claims", "list_claims", {"customer_id": customer_id})
    
    async def _handle_get_policies(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_policies action using FastMCP"""
        customer_id = user_data.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID required"}
        
        return await self.call_tool("policy", "list_policies", {"customer_id": customer_id})
    
    async def _handle_create_claim(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_claim action using FastMCP"""
        required_fields = ["customer_id", "policy_number", "incident_date", "description", "amount", "claim_type"]
        
        for field in required_fields:
            if field not in user_data:
                return {"success": False, "error": f"{field} is required"}
        
        arguments = {
            "customer_id": user_data["customer_id"],
            "policy_number": user_data["policy_number"],
            "incident_date": user_data["incident_date"],
            "description": user_data["description"],
            "amount": user_data["amount"],
            "claim_type": user_data["claim_type"]
        }
        
        return await self.call_tool("claims", "create_claim", arguments)
    
    async def _handle_update_claim(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update_claim action using FastMCP"""
        required_fields = ["claim_id", "customer_id", "new_status"]
        
        for field in required_fields:
            if field not in user_data:
                return {"success": False, "error": f"{field} is required"}
        
        arguments = {
            "claim_id": user_data["claim_id"],
            "customer_id": user_data["customer_id"],
            "new_status": user_data["new_status"],
            "notes": user_data.get("notes")
        }
        
        return await self.call_tool("claims", "update_claim_status", arguments)
    
    async def _handle_fraud_analysis(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fraud_analysis action using FastMCP"""
        claim_id = user_data.get("claim_id")
        customer_id = user_data.get("customer_id")
        
        if not claim_id or not customer_id:
            return {"success": False, "error": "Both claim_id and customer_id required"}
        
        arguments = {
            "claim_id": claim_id,
            "customer_id": customer_id,
            "analysis_type": "fraud_detection"
        }
        
        return await self.call_tool("analytics", "analyze_claim", arguments)
    
    async def get_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available FastMCP tools across all services"""
        return self.available_tools.copy()
    
    async def close(self):
        """Clean up FastMCP clients and resources"""
        try:
            # Close all MCP clients
            for service_name, client in self.mcp_clients.items():
                try:
                    if hasattr(client, 'close'):
                        await client.close()
                except Exception as e:
                    logger.warning(f"Error closing FastMCP client for {service_name}", 
                                  error=str(e))
            
            self.mcp_clients.clear()
            logger.info("FastMCP Data Agent closed")
            
        except Exception as e:
            logger.error("Error during FastMCP agent cleanup", error=str(e))

# Create a global instance for use by domain agents
fastmcp_data_agent = FastMCPDataAgent()

# FastAPI Server for the agent
if __name__ == "__main__":
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    
    # Create FastAPI app
    app = FastAPI(
        title="FastMCP Data Agent",
        description="Technical agent for accessing FastMCP-enabled insurance services using official FastMCP Client",
        version="2.1.0"
    )
    
    # Request/Response models
    class CustomerDataRequest(BaseModel):
        customer_id: str
    
    class ClaimRequest(BaseModel):
        customer_id: str
        policy_number: str
        incident_date: str
        description: str
        amount: float
        claim_type: str
    
    class UpdateClaimRequest(BaseModel):
        claim_id: str
        customer_id: str
        new_status: str
        notes: Optional[str] = None
    
    class QuoteRequest(BaseModel):
        customer_id: str
        policy_type: str
        coverage_amount: float
        risk_factors: Optional[Dict[str, Any]] = None
    
    @app.on_event("startup")
    async def startup_event():
        await fastmcp_data_agent.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await fastmcp_data_agent.close()
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy", 
            "service": "fastmcp-data-agent",
            "version": "2.1.0",
            "protocol": "FastMCP_Client_2.0",
            "capabilities": {
                "mcpIntegration": True,
                "google_a2a_compatible": True,
                "fastmcp_client": True
            }
        }
    
    @app.get("/ready")
    async def readiness_check():
        return {
            "status": "ready", 
            "service": "fastmcp-data-agent",
            "clients": len(fastmcp_data_agent.mcp_clients),
            "services": list(fastmcp_data_agent.service_urls.keys())
        }
    
    @app.get("/tools")
    async def get_available_tools():
        tools = await fastmcp_data_agent.get_available_tools()
        return {
            "tools": tools,
            "protocol": "FastMCP_2.0",
            "total_services": len(tools),
            "total_tools": sum(len(service_tools) for service_tools in tools.values())
        }
    
    @app.post("/customer/data")
    async def get_customer_data(request: CustomerDataRequest):
        user_data = {"action": "get_customer_data", "customer_id": request.customer_id}
        task = TaskRequest(taskId=f"api_customer_data_{request.customer_id}", user=user_data)
        
        response = fastmcp_data_agent.handle_task(task)
        
        if response.status == "failed":
            raise HTTPException(status_code=400, detail=response.parts[0]["text"])
        
        return json.loads(response.parts[0]["text"])
    
    @app.post("/claims/create")
    async def create_claim(request: ClaimRequest):
        user_data = {
            "action": "create_claim",
            "customer_id": request.customer_id,
            "policy_number": request.policy_number,
            "incident_date": request.incident_date,
            "description": request.description,
            "amount": request.amount,
            "claim_type": request.claim_type
        }
        task = TaskRequest(taskId=f"api_create_claim_{request.customer_id}", user=user_data)
        
        response = fastmcp_data_agent.handle_task(task)
        
        if response.status == "failed":
            raise HTTPException(status_code=400, detail=response.parts[0]["text"])
        
        return json.loads(response.parts[0]["text"])
    
    @app.post("/claims/update")
    async def update_claim(request: UpdateClaimRequest):
        user_data = {
            "action": "update_claim",
            "claim_id": request.claim_id,
            "customer_id": request.customer_id,
            "new_status": request.new_status,
            "notes": request.notes
        }
        task = TaskRequest(taskId=f"api_update_claim_{request.claim_id}", user=user_data)
        
        response = fastmcp_data_agent.handle_task(task)
        
        if response.status == "failed":
            raise HTTPException(status_code=400, detail=response.parts[0]["text"])
        
        return json.loads(response.parts[0]["text"])
    
    # Get server configuration
    host = os.getenv("FASTMCP_DATA_AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("FASTMCP_DATA_AGENT_PORT", 8004))
    
    logger.info(f"Starting FastMCP Data Agent server with official FastMCP Client on {host}:{port}")
    uvicorn.run(app, host=host, port=port) 