"""
FastMCP Data Agent - A2A-compatible technical agent using FastMCP to connect to insurance services.
Handles database queries, API calls, and data analysis for domain agents via official Google A2A protocol.
"""

import os
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import structlog

# Official Google A2A Library imports (a2a-sdk)
from a2a import A2AServer, run_server
from a2a.models import AgentCard, TaskRequest, TaskResponse

from agents.shared.a2a_base import A2AAgent

logger = structlog.get_logger(__name__)


class FastMCPDataAgent(A2AAgent):
    """A2A-compatible technical agent that connects to FastMCP-enabled services"""
    
    def __init__(self, port: int = 8002):
        capabilities = {
            "streaming": False,
            "pushNotifications": False,
            "fileUpload": False,
            "messageHistory": True,
            "dataAccess": True,
            "mcpIntegration": True,
            "google_a2a_compatible": True
        }
        
        # Initialize A2A agent with official library
        super().__init__(
            name="FastMCPDataAgent",
            description="Technical agent providing data access via FastMCP services using official Google A2A protocol",
            port=port,
            capabilities=capabilities,
            version="2.0.0"
        )
        
        # Service endpoints with FastMCP integration
        self.service_urls = {
            "user": os.getenv("USER_SERVICE_URL", "http://localhost:8000"),
            "claims": os.getenv("CLAIMS_SERVICE_URL", "http://localhost:8004"),
            "policy": os.getenv("POLICY_SERVICE_URL", "http://localhost:8002"),
            "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8003")
        }
        
        # HTTP client for making requests
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Available tools cache
        self.available_tools = {}
        
        logger.info("FastMCP Data Agent initialized with A2A support", 
                   services=list(self.service_urls.keys()), port=port)
    
    def handle_task(self, task: TaskRequest) -> TaskResponse:
        """Handle incoming A2A tasks for data operations"""
        user_data = task.user
        action = user_data.get("action", "unknown")
        
        logger.info("Processing data request", task_id=task.taskId, action=action)
        
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
            else:
                result = {"error": f"Unknown action: {action}"}
            
            # Return successful TaskResponse
            return TaskResponse(
                taskId=task.taskId,
                status="completed",
                parts=[{
                    "text": f"Data operation '{action}' completed successfully",
                    "type": "data_response",
                    "data": result
                }],
                metadata={
                    "agent": "FastMCPDataAgent",
                    "action": action,
                    "result_type": type(result).__name__
                }
            )
            
        except Exception as e:
            logger.error("Data operation failed", task_id=task.taskId, action=action, error=str(e))
            
            # Return error TaskResponse
            return TaskResponse(
                taskId=task.taskId,
                status="failed",
                parts=[{
                    "text": f"Data operation failed: {str(e)}",
                    "type": "error"
                }],
                metadata={
                    "agent": "FastMCPDataAgent",
                    "action": action,
                    "error": str(e)
                }
            )
    
    async def initialize(self):
        """Initialize the agent by discovering available tools from services"""
        try:
            for service_name, base_url in self.service_urls.items():
                await self._discover_service_tools(service_name, base_url)
            
            logger.info("Agent initialization complete", 
                       total_tools=sum(len(tools) for tools in self.available_tools.values()))
        except Exception as e:
            logger.error("Failed to initialize agent", error=str(e))
            raise
    
    async def _discover_service_tools(self, service_name: str, base_url: str):
        """Discover available MCP tools from a service"""
        try:
            response = await self.client.post(f"{base_url}/mcp/tools/list")
            if response.status_code == 200:
                tools_data = response.json()
                tools = tools_data.get("tools", [])
                self.available_tools[service_name] = tools
                logger.info(f"Discovered tools for {service_name}", 
                           count=len(tools), 
                           tools=[tool['name'] for tool in tools])
            else:
                logger.warning(f"Failed to discover tools for {service_name}", 
                              status=response.status_code)
                self.available_tools[service_name] = []
        except Exception as e:
            logger.error(f"Error discovering tools for {service_name}", error=str(e))
            self.available_tools[service_name] = []
    
    async def call_tool(self, service_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool on a service"""
        try:
            base_url = self.service_urls.get(service_name)
            if not base_url:
                return {"success": False, "error": f"Unknown service: {service_name}"}
            
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = await self.client.post(f"{base_url}/mcp/call", json=payload)
            
            if response.status_code == 200:
                result_data = response.json()
                result = result_data.get("result", {})
                content = result.get("content", [])
                
                if content and len(content) > 0:
                    tool_result = json.loads(content[0].get("text", "{}"))
                    logger.debug(f"Tool call successful", 
                               service=service_name, 
                               tool=tool_name,
                               success=tool_result.get("success", False))
                    return tool_result
                else:
                    return {"success": False, "error": "Empty result from tool"}
            else:
                logger.error(f"Tool call failed", 
                           service=service_name, 
                           tool=tool_name,
                           status=response.status_code)
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error calling tool", 
                        service=service_name, 
                        tool=tool_name, 
                        error=str(e))
            return {"success": False, "error": str(e)}
    
    # Customer data operations
    async def get_customer_data(self, customer_id: str) -> Dict[str, Any]:
        """Get comprehensive customer data"""
        try:
            # Get customer basic info
            customer_result = await self.call_tool("user", "get_user", {"user_id": customer_id})
            
            # Get customer policies
            policies_result = await self.call_tool("policy", "list_policies", {"customer_id": customer_id})
            
            # Get customer claims
            claims_result = await self.call_tool("claims", "list_claims", {"customer_id": customer_id})
            
            return {
                "success": True,
                "customer_id": customer_id,
                "customer_info": customer_result,
                "policies": policies_result.get("policies", []) if policies_result.get("success") else [],
                "claims": claims_result.get("claims", []) if claims_result.get("success") else [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error getting customer data", customer_id=customer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            }
    
    # Claims operations
    async def get_customer_claims(self, customer_id: str) -> Dict[str, Any]:
        """Get all claims for a customer"""
        return await self.call_tool("claims", "list_claims", {"customer_id": customer_id})
    
    async def get_claim_details(self, claim_id: str, customer_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific claim"""
        return await self.call_tool("claims", "get_claim_details", {
            "claim_id": claim_id,
            "customer_id": customer_id
        })
    
    async def create_claim(self, customer_id: str, policy_number: str, incident_date: str, 
                          description: str, amount: float, claim_type: str) -> Dict[str, Any]:
        """Create a new insurance claim"""
        return await self.call_tool("claims", "create_claim", {
            "customer_id": customer_id,
            "policy_number": policy_number,
            "incident_date": incident_date,
            "description": description,
            "amount": amount,
            "claim_type": claim_type
        })
    
    async def update_claim_status(self, claim_id: str, customer_id: str, 
                                 new_status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Update the status of an existing claim"""
        return await self.call_tool("claims", "update_claim_status", {
            "claim_id": claim_id,
            "customer_id": customer_id,
            "new_status": new_status,
            "notes": notes
        })
    
    # Policy operations
    async def get_customer_policies(self, customer_id: str) -> Dict[str, Any]:
        """Get all policies for a customer"""
        return await self.call_tool("policy", "list_policies", {"customer_id": customer_id})
    
    async def get_policy_details(self, policy_id: str, customer_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific policy"""
        return await self.call_tool("policy", "get_policy_details", {
            "policy_id": policy_id,
            "customer_id": customer_id
        })
    
    async def get_coverage_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get coverage summary for all customer policies"""
        return await self.call_tool("policy", "get_coverage_summary", {"customer_id": customer_id})
    
    async def calculate_quote(self, customer_id: str, policy_type: str, coverage_amount: float,
                             risk_factors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate insurance quote for a customer"""
        return await self.call_tool("policy", "calculate_quote", {
            "customer_id": customer_id,
            "policy_type": policy_type,
            "coverage_amount": coverage_amount,
            "risk_factors": risk_factors or {}
        })
    
    # Analytics and reporting
    async def generate_customer_summary(self, customer_id: str) -> Dict[str, Any]:
        """Generate a comprehensive customer summary"""
        try:
            # Get all customer data
            customer_data = await self.get_customer_data(customer_id)
            
            if not customer_data.get("success"):
                return customer_data
            
            # Generate summary
            policies = customer_data.get("policies", [])
            claims = customer_data.get("claims", [])
            
            total_coverage = sum(policy.get("coverage_amount", 0) for policy in policies)
            total_premium = sum(policy.get("premium", 0) for policy in policies)
            total_claims_amount = sum(claim.get("amount", 0) for claim in claims)
            
            active_policies = [p for p in policies if p.get("status") == "active"]
            recent_claims = [c for c in claims if c.get("status") in ["processing", "under_review"]]
            
            return {
                "success": True,
                "customer_id": customer_id,
                "summary": {
                    "total_policies": len(policies),
                    "active_policies": len(active_policies),
                    "total_coverage": total_coverage,
                    "annual_premium": total_premium,
                    "total_claims": len(claims),
                    "recent_claims": len(recent_claims),
                    "total_claims_amount": total_claims_amount,
                    "claim_to_premium_ratio": total_claims_amount / total_premium if total_premium > 0 else 0
                },
                "policies": policies,
                "claims": claims,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error generating customer summary", customer_id=customer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            }
    
    async def get_available_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available tools across all services"""
        return self.available_tools.copy()
    
    async def close(self):
        """Clean up resources"""
        await self.client.aclose()
        logger.info("FastMCP Data Agent closed")

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
        description="Technical agent for accessing FastMCP-enabled insurance services",
        version="1.0.0"
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
        return {"status": "healthy", "service": "fastmcp-data-agent"}
    
    @app.get("/ready")
    async def readiness_check():
        return {"status": "ready", "service": "fastmcp-data-agent"}
    
    @app.get("/tools")
    async def get_available_tools():
        return await fastmcp_data_agent.get_available_tools()
    
    @app.post("/customer/data")
    async def get_customer_data(request: CustomerDataRequest):
        result = await fastmcp_data_agent.get_customer_data(request.customer_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    
    @app.post("/customer/summary")
    async def generate_customer_summary(request: CustomerDataRequest):
        result = await fastmcp_data_agent.generate_customer_summary(request.customer_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    
    @app.post("/claims/list")
    async def get_customer_claims(request: CustomerDataRequest):
        result = await fastmcp_data_agent.get_customer_claims(request.customer_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    
    @app.post("/claims/create")
    async def create_claim(request: ClaimRequest):
        result = await fastmcp_data_agent.create_claim(
            request.customer_id,
            request.policy_number,
            request.incident_date,
            request.description,
            request.amount,
            request.claim_type
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    
    @app.post("/policies/list")
    async def get_customer_policies(request: CustomerDataRequest):
        result = await fastmcp_data_agent.get_customer_policies(request.customer_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    
    @app.post("/policies/quote")
    async def calculate_quote(request: QuoteRequest):
        result = await fastmcp_data_agent.calculate_quote(
            request.customer_id,
            request.policy_type,
            request.coverage_amount,
            request.risk_factors
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        return result
    
    # Run the server
    port = int(os.getenv("FASTMCP_DATA_AGENT_PORT", 8004))
    host = os.getenv("FASTMCP_DATA_AGENT_HOST", "0.0.0.0")
    
    logger.info(f"Starting FastMCP Data Agent server on {host}:{port}")
    uvicorn.run(app, host=host, port=port) 