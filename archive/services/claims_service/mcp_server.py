"""
FastMCP Server for Claims Service
Integrates with the existing FastAPI claims service to provide MCP tools
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
import structlog

logger = structlog.get_logger(__name__)

class ClaimsMCPServer:
    """FastMCP server for claims operations"""
    
    def __init__(self, fastapi_app: FastAPI, claims_db: Dict[str, Any]):
        self.app = fastapi_app
        self.claims_db = claims_db
        
        # Initialize FastMCP server
        self.mcp = FastMCP(
            name="claims-service",
            dependencies=["fastapi", "structlog", "pydantic"]
        )
        
        self._setup_tools()
        self._setup_resources()
        self._integrate_with_fastapi()
    
    def _setup_tools(self):
        """Setup MCP tools for claims operations"""
        
        # Tool: List claims for a customer
        @self.mcp.tool()
        def list_claims(customer_id: str) -> Dict[str, Any]:
            """List all claims for a specific customer"""
            try:
                customer_claims = [
                    claim.dict() for claim in self.claims_db.values()
                    if claim.customer_id == customer_id
                ]
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "claims": customer_claims,
                    "total_claims": len(customer_claims)
                }
            except Exception as e:
                logger.error("Error listing claims", customer_id=customer_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "customer_id": customer_id
                }
        
        # Tool: Get specific claim details
        @self.mcp.tool()
        def get_claim_details(claim_id: str, customer_id: str) -> Dict[str, Any]:
            """Get detailed information about a specific claim"""
            try:
                if claim_id not in self.claims_db:
                    return {
                        "success": False,
                        "error": f"Claim {claim_id} not found",
                        "claim_id": claim_id
                    }
                
                claim = self.claims_db[claim_id]
                
                # Verify customer ownership
                if claim.customer_id != customer_id:
                    return {
                        "success": False,
                        "error": "Unauthorized access to claim",
                        "claim_id": claim_id
                    }
                
                return {
                    "success": True,
                    "claim": claim.dict()
                }
            except Exception as e:
                logger.error("Error getting claim details", claim_id=claim_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "claim_id": claim_id
                }
        
        # Tool: Create new claim
        @self.mcp.tool()
        def create_claim(
            customer_id: str,
            policy_number: str,
            incident_date: str,
            description: str,
            amount: float,
            claim_type: str
        ) -> Dict[str, Any]:
            """Create a new insurance claim"""
            try:
                from datetime import datetime
                import uuid
                
                # Generate new claim ID
                claim_id = f"CLM-{customer_id}-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
                
                # Create claim object (using the Claim model from main.py)
                new_claim_data = {
                    "claim_id": claim_id,
                    "policy_number": policy_number,
                    "customer_id": customer_id,
                    "incident_date": incident_date,
                    "description": description,
                    "amount": amount,
                    "claim_type": claim_type,
                    "status": "submitted"
                }
                
                # Import Claim model dynamically to avoid circular imports
                from main import Claim
                new_claim = Claim(**new_claim_data)
                
                # Store in database
                self.claims_db[claim_id] = new_claim
                
                logger.info("New claim created", claim_id=claim_id, customer_id=customer_id)
                
                return {
                    "success": True,
                    "claim_id": claim_id,
                    "claim": new_claim.dict(),
                    "message": "Claim successfully created"
                }
                
            except Exception as e:
                logger.error("Error creating claim", customer_id=customer_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "customer_id": customer_id
                }
        
        # Tool: Update claim status
        @self.mcp.tool()
        def update_claim_status(
            claim_id: str,
            customer_id: str,
            new_status: str,
            notes: Optional[str] = None
        ) -> Dict[str, Any]:
            """Update the status of an existing claim"""
            try:
                if claim_id not in self.claims_db:
                    return {
                        "success": False,
                        "error": f"Claim {claim_id} not found",
                        "claim_id": claim_id
                    }
                
                claim = self.claims_db[claim_id]
                
                # Verify customer ownership
                if claim.customer_id != customer_id:
                    return {
                        "success": False,
                        "error": "Unauthorized access to claim",
                        "claim_id": claim_id
                    }
                
                # Update claim status
                old_status = claim.status
                claim.status = new_status
                from datetime import datetime
                claim.updated_at = datetime.utcnow().isoformat()
                
                logger.info(
                    "Claim status updated",
                    claim_id=claim_id,
                    old_status=old_status,
                    new_status=new_status
                )
                
                return {
                    "success": True,
                    "claim_id": claim_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "notes": notes,
                    "updated_at": claim.updated_at
                }
                
            except Exception as e:
                logger.error("Error updating claim status", claim_id=claim_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "claim_id": claim_id
                }
    
    def _setup_resources(self):
        """Setup MCP resources for claims data"""
        
        # Resource: Get customer claims
        @self.mcp.resource("claims://customer/{customer_id}")
        def get_customer_claims_resource(customer_id: str) -> Dict[str, Any]:
            """Provides all claims for a specific customer as a resource"""
            try:
                customer_claims = [
                    claim.dict() for claim in self.claims_db.values()
                    if claim.customer_id == customer_id
                ]
                return {
                    "customer_id": customer_id,
                    "claims": customer_claims,
                    "total_claims": len(customer_claims)
                }
            except Exception as e:
                logger.error("Error getting customer claims resource", customer_id=customer_id, error=str(e))
                return {"error": str(e), "customer_id": customer_id}
        
        # Resource: Get specific claim
        @self.mcp.resource("claims://claim/{claim_id}")
        def get_claim_resource(claim_id: str) -> Dict[str, Any]:
            """Provides detailed information about a specific claim as a resource"""
            try:
                if claim_id not in self.claims_db:
                    return {"error": f"Claim {claim_id} not found", "claim_id": claim_id}
                
                claim = self.claims_db[claim_id]
                return claim.dict()
            except Exception as e:
                logger.error("Error getting claim resource", claim_id=claim_id, error=str(e))
                return {"error": str(e), "claim_id": claim_id}
    
    def _integrate_with_fastapi(self):
        """Integrate FastMCP with FastAPI by adding endpoints"""
        
        # Add FastMCP endpoints to the existing FastAPI app
        @self.app.get("/mcp/tools")
        async def mcp_list_tools():
            """List available MCP tools"""
            try:
                # Use the proper FastMCP API to get tool information
                tools = []
                # In FastMCP 2.x, we can use the server to get tool schemas
                tool_schemas = self.mcp.get_tool_schemas() if hasattr(self.mcp, 'get_tool_schemas') else {}
                
                # If the method doesn't exist, we'll manually track tools
                for tool_name in ['list_claims', 'get_claim_details', 'create_claim', 'update_claim_status']:
                    tools.append({
                        "name": tool_name,
                        "description": f"MCP tool: {tool_name}",
                        "inputSchema": {"type": "object", "properties": {}}
                    })
                
                return {"tools": tools}
            except Exception as e:
                logger.error("Error listing MCP tools", error=str(e))
                return {"error": str(e), "tools": []}
        
        @self.app.post("/mcp/call")
        async def mcp_call_tool(request: Dict[str, Any]):
            """Call an MCP tool"""
            try:
                method = request.get("method", "")
                params = request.get("params", {})
                
                if method != "tools/call":
                    return {"error": f"Unsupported method: {method}"}
                
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Route to the appropriate tool function
                if tool_name == "list_claims":
                    result = self._tool_list_claims(**arguments)
                elif tool_name == "get_claim_details":
                    result = self._tool_get_claim_details(**arguments)
                elif tool_name == "create_claim":
                    result = self._tool_create_claim(**arguments)
                elif tool_name == "update_claim_status":
                    result = self._tool_update_claim_status(**arguments)
                else:
                    return {"error": f"Tool '{tool_name}' not found"}
                
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result)
                            }
                        ]
                    }
                }
            except Exception as e:
                logger.error("Error calling MCP tool", error=str(e))
                return {"error": str(e)}
        
        @self.app.get("/mcp/resources")
        async def mcp_list_resources():
            """List available MCP resources"""
            try:
                resources = [
                    {
                        "uri": "claims://customer/{customer_id}",
                        "name": "customer_claims",
                        "description": "Get all claims for a specific customer"
                    },
                    {
                        "uri": "claims://claim/{claim_id}",
                        "name": "claim_details", 
                        "description": "Get details for a specific claim"
                    }
                ]
                
                return {"resources": resources}
            except Exception as e:
                logger.error("Error listing MCP resources", error=str(e))
                return {"error": str(e), "resources": []}
    
    # Helper methods for tool calls (to avoid relying on FastMCP internals)
    def _tool_list_claims(self, customer_id: str) -> Dict[str, Any]:
        """Internal method for list_claims tool"""
        try:
            customer_claims = [
                claim.dict() for claim in self.claims_db.values()
                if claim.customer_id == customer_id
            ]
            
            return {
                "success": True,
                "customer_id": customer_id,
                "claims": customer_claims,
                "total_claims": len(customer_claims)
            }
        except Exception as e:
            logger.error("Error listing claims", customer_id=customer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            }
    
    def _tool_get_claim_details(self, claim_id: str, customer_id: str) -> Dict[str, Any]:
        """Internal method for get_claim_details tool"""
        try:
            if claim_id not in self.claims_db:
                return {
                    "success": False,
                    "error": f"Claim {claim_id} not found",
                    "claim_id": claim_id
                }
            
            claim = self.claims_db[claim_id]
            
            # Verify customer ownership
            if claim.customer_id != customer_id:
                return {
                    "success": False,
                    "error": "Unauthorized access to claim",
                    "claim_id": claim_id
                }
            
            return {
                "success": True,
                "claim": claim.dict()
            }
        except Exception as e:
            logger.error("Error getting claim details", claim_id=claim_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "claim_id": claim_id
            }
    
    def _tool_create_claim(self, customer_id: str, policy_number: str, incident_date: str, 
                          description: str, amount: float, claim_type: str) -> Dict[str, Any]:
        """Internal method for create_claim tool"""
        try:
            from datetime import datetime
            import uuid
            
            # Generate new claim ID
            claim_id = f"CLM-{customer_id}-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
            
            # Create claim object (using the Claim model from main.py)
            new_claim_data = {
                "claim_id": claim_id,
                "policy_number": policy_number,
                "customer_id": customer_id,
                "incident_date": incident_date,
                "description": description,
                "amount": amount,
                "claim_type": claim_type,
                "status": "submitted"
            }
            
            # Import Claim model dynamically to avoid circular imports
            from main import Claim
            new_claim = Claim(**new_claim_data)
            
            # Store in database
            self.claims_db[claim_id] = new_claim
            
            logger.info("New claim created", claim_id=claim_id, customer_id=customer_id)
            
            return {
                "success": True,
                "claim_id": claim_id,
                "claim": new_claim.dict(),
                "message": "Claim successfully created"
            }
            
        except Exception as e:
            logger.error("Error creating claim", customer_id=customer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            }
    
    def _tool_update_claim_status(self, claim_id: str, customer_id: str, new_status: str, 
                                 notes: Optional[str] = None) -> Dict[str, Any]:
        """Internal method for update_claim_status tool"""
        try:
            if claim_id not in self.claims_db:
                return {
                    "success": False,
                    "error": f"Claim {claim_id} not found",
                    "claim_id": claim_id
                }
            
            claim = self.claims_db[claim_id]
            
            # Verify customer ownership
            if claim.customer_id != customer_id:
                return {
                    "success": False,
                    "error": "Unauthorized access to claim",
                    "claim_id": claim_id
                }
            
            # Update claim status
            old_status = claim.status
            claim.status = new_status
            from datetime import datetime
            claim.updated_at = datetime.utcnow().isoformat()
            
            logger.info(
                "Claim status updated",
                claim_id=claim_id,
                old_status=old_status,
                new_status=new_status
            )
            
            return {
                "success": True,
                "claim_id": claim_id,
                "old_status": old_status,
                "new_status": new_status,
                "notes": notes,
                "updated_at": claim.updated_at
            }
            
        except Exception as e:
            logger.error("Error updating claim status", claim_id=claim_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "claim_id": claim_id
            } 