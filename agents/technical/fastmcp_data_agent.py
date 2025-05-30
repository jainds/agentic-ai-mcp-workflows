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
    # Minimal mock classes for testing/development environments
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

# A2A Base Agent (conditionally imported)
try:
    from agents.shared.a2a_base import A2AAgent
    A2A_BASE_AVAILABLE = True
except ImportError:
    # Simple base class for testing/development environments
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
        """Initialize the FastMCP Data Agent with real FastMCP Client connections"""
        
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
        
        # Initialize A2A agent
        super().__init__(
            name="FastMCPDataAgent",
            description="Technical agent providing data access via FastMCP services using official FastMCP Client and Google A2A protocol",
            port=port,
            capabilities=capabilities,
            version="2.1.0"
        )
        
        # Real FastMCP service URLs - NO MOCKING
        self.service_urls = {
            "user": os.getenv("USER_SERVICE_URL", "http://localhost:8000"),
            "claims": os.getenv("CLAIMS_SERVICE_URL", "http://localhost:8001"),
            "policy": os.getenv("POLICY_SERVICE_URL", "http://localhost:8002"),
            "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8003")
        }
        
        # Real FastMCP clients (will be initialized)
        self.mcp_clients: Dict[str, Client] = {}
        
        # Available tools cache from real services
        self.available_tools = {}
        
        # Initialization flag
        self.initialized = False
        
        logger.info("FastMCP Data Agent created with real FastMCP Client", 
                   services=list(self.service_urls.keys()), 
                   port=port,
                   fastmcp_version="2.0+")
    
    def handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle incoming A2A tasks for data operations using REAL FastMCP Client"""
        
        # Ensure initialization before handling tasks
        if not self.initialized:
            # Can't use asyncio.run() here - need to handle this differently
            logger.error("Agent not initialized when handling task")
            return TaskResponse(
                taskId=task.taskId,
                status="failed",
                parts=[{
                    "text": json.dumps({
                        "error": "Agent not initialized - call initialize() first",
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent": "FastMCPDataAgent"
                    }),
                    "type": "error"
                }],
                metadata={"agent": "FastMCPDataAgent", "error": "not_initialized"}
            )
        
        user_data = task.user
        action = user_data.get("action", "unknown")
        
        logger.info("Processing REAL data request via FastMCP", 
                   task_id=task.taskId, 
                   action=action)
        
        try:
            # Create an async wrapper to handle the async operations
            async def process_action():
                if action == "get_customer":
                    return await self._handle_get_customer(user_data)
                elif action == "get_claims":
                    return await self._handle_get_claims(user_data)
                elif action == "get_policies":
                    return await self._handle_get_policies(user_data)
                elif action == "create_claim":
                    return await self._handle_create_claim(user_data)
                elif action == "update_claim":
                    return await self._handle_update_claim(user_data)
                elif action == "fraud_analysis":
                    return await self._handle_fraud_analysis(user_data)
                elif action == "get_customer_data":
                    return await self._handle_get_customer_data(user_data)
                else:
                    return {"error": f"Unknown action: {action}"}
            
            # Try to get the current event loop, if available
            try:
                loop = asyncio.get_running_loop()
                # If we're in an event loop, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, process_action())
                    result = future.result()
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                result = asyncio.run(process_action())
            
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
                        "protocol": "REAL_FastMCP_2.0"
                    }),
                    "type": "data_response"
                }],
                metadata={
                    "agent": "FastMCPDataAgent",
                    "action": action,
                    "result_type": type(result).__name__,
                    "protocol": "REAL_FastMCP_Client_2.0"
                }
            )
            
        except Exception as e:
            logger.error("REAL data operation failed", 
                        task_id=task.taskId, 
                        action=action, 
                        error=str(e),
                        error_type=type(e).__name__)
            
            # Return error TaskResponse with full error details
            return TaskResponse(
                taskId=task.taskId,
                status="failed",
                parts=[{
                    "text": json.dumps({
                        "action": action,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent": "FastMCPDataAgent"
                    }),
                    "type": "error"
                }],
                metadata={
                    "agent": "FastMCPDataAgent",
                    "action": action,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def initialize(self):
        """Initialize the agent by discovering available tools from REAL FastMCP services"""
        try:
            logger.info("Initializing REAL FastMCP Data Agent connections...")
            
            # Initialize REAL MCP clients for each service
            for service_name, service_url in self.service_urls.items():
                try:
                    # Create REAL FastMCP client for the service
                    logger.info(f"Creating REAL FastMCP client for {service_name}", url=service_url)
                    
                    # Use the official FastMCP Client API
                    client = Client(f"{service_url}/mcp")
                    
                    # Test REAL connection
                    await self._test_client_connection(service_name, client)
                    
                    self.mcp_clients[service_name] = client
                    
                    # Discover REAL tools
                    await self._discover_service_tools(service_name, client)
                    
                    logger.info(f"REAL FastMCP client initialized for {service_name}", 
                              url=service_url,
                              tools_discovered=len(self.available_tools.get(service_name, [])))
                    
                except Exception as e:
                    logger.error(f"REAL FastMCP client initialization failed for {service_name}", 
                                error=str(e),
                                error_type=type(e).__name__,
                                url=service_url)
                    # Set empty tools but don't fail completely
                    self.available_tools[service_name] = []
            
            self.initialized = True
            total_tools = sum(len(tools) for tools in self.available_tools.values())
            logger.info("REAL FastMCP Data Agent initialization complete", 
                       services_connected=len(self.mcp_clients),
                       total_tools_discovered=total_tools)
            
        except Exception as e:
            logger.error("REAL FastMCP Data Agent initialization failed", 
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    async def _test_client_connection(self, service_name: str, client: Client):
        """Test REAL connection to FastMCP service"""
        try:
            # Try to list tools to test connection
            logger.info(f"Testing REAL connection to {service_name}")
            
            # Use the official FastMCP Client API with async context manager
            async with client as connected_client:
                tools_response = await connected_client.list_tools()
            
            logger.info(f"REAL connection test successful for {service_name}", 
                       response_type=type(tools_response).__name__)
            
        except Exception as e:
            logger.error(f"REAL connection test failed for {service_name}", 
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    async def _discover_service_tools(self, service_name: str, client: Client):
        """Discover REAL tools from FastMCP service"""
        try:
            logger.info(f"Discovering REAL tools for {service_name}")
            
            # Use the official FastMCP Client API to discover tools with async context manager
            async with client as connected_client:
                tools_response = await connected_client.list_tools()
            
            # Extract tools from response
            if hasattr(tools_response, 'tools') and tools_response.tools:
                self.available_tools[service_name] = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                    }
                    for tool in tools_response.tools
                ]
            else:
                # Fallback: try direct service query
                self.available_tools[service_name] = []
            
            logger.info(f"REAL tools discovered for {service_name}", 
                       tool_count=len(self.available_tools[service_name]),
                       tools=[tool["name"] for tool in self.available_tools[service_name]])
            
        except Exception as e:
            logger.error(f"REAL tool discovery failed for {service_name}", 
                        error=str(e),
                        error_type=type(e).__name__)
            self.available_tools[service_name] = []
    
    async def call_tool(self, service_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a REAL tool on a FastMCP service using official Client"""
        try:
            if service_name not in self.mcp_clients:
                raise ValueError(f"No REAL client available for service: {service_name}")
            
            client = self.mcp_clients[service_name]
            
            logger.info(f"Calling REAL tool on {service_name}", 
                       tool=tool_name, 
                       arguments=arguments)
            
            # Use the official FastMCP Client API to call tools with async context manager
            async with client as connected_client:
                result = await connected_client.call_tool(tool_name, arguments)
            
            # Extract result data
            if hasattr(result, 'content') and result.content:
                # Parse the content from the MCP response
                content = result.content[0]
                if hasattr(content, 'text'):
                    try:
                        parsed_result = json.loads(content.text)
                        logger.info(f"REAL tool call successful for {service_name}.{tool_name}", 
                                   result_type=type(parsed_result).__name__)
                        return parsed_result
                    except json.JSONDecodeError:
                        return {"text": content.text}
                else:
                    return {"content": str(content)}
            else:
                return {"result": str(result)}
            
        except Exception as e:
            logger.error(f"REAL tool call failed for {service_name}.{tool_name}", 
                        error=str(e),
                        error_type=type(e).__name__,
                        arguments=arguments)
            return {
                "success": False, 
                "error": str(e),
                "error_type": type(e).__name__,
                "service": service_name,
                "tool": tool_name
            }
    
    # REAL data handlers - NO MOCKING
    async def _handle_get_customer_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_customer_data action using REAL FastMCP"""
        customer_id = user_data.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID required"}
        
        logger.info("Handling REAL get_customer_data request", customer_id=customer_id)
        return await self.call_tool("user", "get_user", {"user_id": customer_id})

    async def _handle_get_customer(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_customer action using REAL FastMCP"""
        customer_id = user_data.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID required"}
        
        logger.info("Handling REAL get_customer request", customer_id=customer_id)
        return await self.call_tool("user", "get_user", {"user_id": customer_id})
    
    async def _handle_get_claims(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_claims action using REAL FastMCP"""
        customer_id = user_data.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID required"}
        
        logger.info("Handling REAL get_claims request", customer_id=customer_id)
        return await self.call_tool("claims", "list_claims", {"customer_id": customer_id})
    
    async def _handle_get_policies(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_policies action using REAL FastMCP"""
        customer_id = user_data.get("customer_id")
        if not customer_id:
            return {"success": False, "error": "Customer ID required"}
        
        logger.info("Handling REAL get_policies request", customer_id=customer_id)
        return await self.call_tool("policy", "list_policies", {"customer_id": customer_id})
    
    async def _handle_create_claim(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create_claim action using REAL FastMCP"""
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
        
        logger.info("Handling REAL create_claim request", arguments=arguments)
        return await self.call_tool("claims", "create_claim", arguments)
    
    async def _handle_update_claim(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update_claim action using REAL FastMCP"""
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
        
        logger.info("Handling REAL update_claim request", arguments=arguments)
        return await self.call_tool("claims", "update_claim_status", arguments)
    
    async def _handle_fraud_analysis(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fraud_analysis action using REAL FastMCP"""
        claim_id = user_data.get("claim_id")
        customer_id = user_data.get("customer_id")
        
        if not claim_id or not customer_id:
            return {"success": False, "error": "Both claim_id and customer_id required"}
        
        arguments = {
            "claim_id": claim_id,
            "customer_id": customer_id,
            "analysis_type": "fraud_detection"
        }
        
        logger.info("Handling REAL fraud_analysis request", arguments=arguments)
        return await self.call_tool("analytics", "analyze_fraud", arguments)
    
    async def get_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available REAL tools from FastMCP services"""
        return self.available_tools
    
    async def close(self):
        """Close all REAL FastMCP client connections"""
        logger.info("Closing REAL FastMCP client connections")
        for service_name, client in self.mcp_clients.items():
            try:
                if hasattr(client, 'close'):
                    await client.close()
                logger.info(f"REAL client closed for {service_name}")
            except Exception as e:
                logger.warning(f"Error closing REAL client for {service_name}", error=str(e))
        
        self.mcp_clients.clear()
        self.initialized = False


# REAL FastAPI application for HTTP endpoints (when running standalone)
if __name__ == "__main__":
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    
    app = FastAPI(
        title="FastMCP Data Agent",
        description="A2A-compatible technical agent using REAL FastMCP Client",
        version="2.1.0"
    )
    
    # Global agent instance
    agent = None
    
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
        """Initialize REAL FastMCP connections on startup"""
        global agent
        agent = FastMCPDataAgent()
        await agent.initialize()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Close REAL FastMCP connections on shutdown"""
        if agent:
            await agent.close()
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "agent": "FastMCPDataAgent",
            "version": "2.1.0",
            "initialized": agent.initialized if agent else False,
            "services": list(agent.service_urls.keys()) if agent else [],
            "protocol": "REAL_FastMCP_2.0"
        }
    
    @app.get("/ready")
    async def readiness_check():
        """Readiness check endpoint"""
        if not agent or not agent.initialized:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        return {
            "status": "ready",
            "connected_services": len(agent.mcp_clients),
            "total_tools": sum(len(tools) for tools in agent.available_tools.values())
        }
    
    @app.get("/tools")
    async def get_available_tools():
        """Get all available REAL tools"""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        return await agent.get_available_tools()
    
    @app.post("/customer/data")
    async def get_customer_data(request: CustomerDataRequest):
        """Get customer data via REAL FastMCP"""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            result = await agent._handle_get_customer_data({"customer_id": request.customer_id})
            return result
        except Exception as e:
            logger.error("Customer data request failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/claims/create")
    async def create_claim(request: ClaimRequest):
        """Create claim via REAL FastMCP"""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            result = await agent._handle_create_claim({
                "customer_id": request.customer_id,
                "policy_number": request.policy_number,
                "incident_date": request.incident_date,
                "description": request.description,
                "amount": request.amount,
                "claim_type": request.claim_type
            })
            return result
        except Exception as e:
            logger.error("Claim creation failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/claims/update")
    async def update_claim(request: UpdateClaimRequest):
        """Update claim via REAL FastMCP"""
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        try:
            result = await agent._handle_update_claim({
                "claim_id": request.claim_id,
                "customer_id": request.customer_id,
                "new_status": request.new_status,
                "notes": request.notes
            })
            return result
        except Exception as e:
            logger.error("Claim update failed", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))
    
    # Run the server
    host = os.getenv("FASTMCP_DATA_AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("FASTMCP_DATA_AGENT_PORT", 8004))
    
    logger.info("Starting REAL FastMCP Data Agent", host=host, port=port)
    uvicorn.run(app, host=host, port=port) 