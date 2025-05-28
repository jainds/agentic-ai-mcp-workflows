import asyncio
import os
from typing import Dict, Any, Optional, List
from ..base import TechnicalAgent, skill


class PolicyDataAgent(TechnicalAgent):
    """Technical agent for policy data operations"""
    
    def __init__(self, port: int = 8011):
        service_url = os.getenv("POLICY_SERVICE_URL", "http://policy-service:8001")
        super().__init__("PolicyDataAgent", service_url, port)

    @skill("GetPolicyInfo", "Retrieve policy information by ID")
    async def get_policy_info(self, policy_id: int) -> Dict[str, Any]:
        """Get policy information by ID"""
        try:
            result = await self.make_service_request("GET", f"/policy/{policy_id}")
            return {
                "success": True,
                "policy": result
            }
        except Exception as e:
            self.logger.error(f"Error getting policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetPolicyStatus", "Get policy status information")
    async def get_policy_status(self, policy_id: int) -> Dict[str, Any]:
        """Get policy status information"""
        try:
            result = await self.make_service_request("GET", f"/policy/{policy_id}/status")
            return {
                "success": True,
                "status": result
            }
        except Exception as e:
            self.logger.error(f"Error getting policy status {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetPolicySummary", "Get policy summary information")
    async def get_policy_summary(self, policy_id: int) -> Dict[str, Any]:
        """Get policy summary information"""
        try:
            result = await self.make_service_request("GET", f"/policy/{policy_id}/summary")
            return {
                "success": True,
                "summary": result
            }
        except Exception as e:
            self.logger.error(f"Error getting policy summary {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetCustomerPolicies", "Get all policies for a customer")
    async def get_customer_policies(self, customer_id: int) -> Dict[str, Any]:
        """Get all policies for a specific customer"""
        try:
            result = await self.make_service_request("GET", f"/customer/{customer_id}/policies")
            return {
                "success": True,
                "policies": result
            }
        except Exception as e:
            self.logger.error(f"Error getting policies for customer {customer_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetPolicyCoverages", "Get coverage details for a policy")
    async def get_policy_coverages(self, policy_id: int) -> Dict[str, Any]:
        """Get coverage details for a policy"""
        try:
            result = await self.make_service_request("GET", f"/policy/{policy_id}/coverages")
            return {
                "success": True,
                "coverages": result
            }
        except Exception as e:
            self.logger.error(f"Error getting coverages for policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("SearchPolicies", "Search policies by policy number or customer ID")
    async def search_policies(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search policies by policy number or customer details"""
        try:
            result = await self.make_service_request(
                "GET", 
                "/search/policies", 
                params={"q": query, "limit": limit}
            )
            return {
                "success": True,
                "policies": result
            }
        except Exception as e:
            self.logger.error(f"Error searching policies with query '{query}': {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetExpiringPolicies", "Get policies expiring within specified days")
    async def get_expiring_policies(self, days: int = 30) -> Dict[str, Any]:
        """Get policies expiring within specified days"""
        try:
            result = await self.make_service_request(
                "GET", 
                "/policies/expiring", 
                params={"days": days}
            )
            return {
                "success": True,
                "expiring_policies": result
            }
        except Exception as e:
            self.logger.error(f"Error getting expiring policies: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("ValidatePolicy", "Validate policy exists and is active")
    async def validate_policy(self, policy_id: int) -> Dict[str, Any]:
        """Validate policy exists and is active"""
        try:
            status_result = await self.get_policy_status(policy_id)
            
            if not status_result["success"]:
                return {
                    "success": False,
                    "valid": False,
                    "reason": "Policy not found"
                }
            
            status_info = status_result["status"]
            is_active = status_info.get("is_active", False)
            
            return {
                "success": True,
                "valid": is_active,
                "policy_id": policy_id,
                "policy_number": status_info.get("policy_number"),
                "status": status_info.get("status"),
                "expiration_date": status_info.get("expiration_date"),
                "days_until_expiry": status_info.get("days_until_expiry", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("CreatePolicyQuote", "Generate a quote for a new policy")
    async def create_policy_quote(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a quote for a new policy"""
        try:
            result = await self.make_service_request("POST", "/quote", json=quote_data)
            return {
                "success": True,
                "quote": result
            }
        except Exception as e:
            self.logger.error(f"Error creating policy quote: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("UpdatePolicy", "Update existing policy")
    async def update_policy(self, policy_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing policy"""
        try:
            result = await self.make_service_request(
                "PUT", 
                f"/policy/{policy_id}", 
                json=update_data
            )
            return {
                "success": True,
                "policy": result
            }
        except Exception as e:
            self.logger.error(f"Error updating policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("CancelPolicy", "Cancel a policy")
    async def cancel_policy(self, policy_id: int, reason: str = "Customer request") -> Dict[str, Any]:
        """Cancel a policy"""
        try:
            result = await self.make_service_request(
                "POST", 
                f"/policy/{policy_id}/cancel",
                json={"cancellation_reason": reason}
            )
            return {
                "success": True,
                "cancellation": result
            }
        except Exception as e:
            self.logger.error(f"Error cancelling policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("RenewPolicy", "Renew an existing policy")
    async def renew_policy(self, policy_id: int, renewal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Renew an existing policy"""
        try:
            result = await self.make_service_request(
                "POST", 
                f"/policy/{policy_id}/renew", 
                json=renewal_data
            )
            return {
                "success": True,
                "renewed_policy": result
            }
        except Exception as e:
            self.logger.error(f"Error renewing policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """Run the PolicyDataAgent as a standalone service"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    # Create FastAPI app
    app = FastAPI(
        title="Policy Data Agent",
        description="Technical agent for policy data operations",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create agent
    agent = PolicyDataAgent()
    from ..base import AgentServer
    agent_server = AgentServer(agent)
    
    @app.post("/execute")
    async def execute_skill(request: Dict[str, Any]):
        """Execute an agent skill"""
        try:
            return await agent_server.handle_execute_request(request)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return await agent_server.handle_health_check()
    
    @app.get("/skills")
    async def get_skills():
        """Get available skills"""
        return await agent_server.handle_skills_request()
    
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint"""
        metrics_data = await agent_server.handle_metrics_request()
        from fastapi import Response
        return Response(content=metrics_data, media_type="text/plain")
    
    # Start server
    port = int(os.getenv("AGENT_PORT", 8011))
    return app, port


def run_server():
    """Run the server"""
    import uvicorn
    import asyncio
    
    # Get the app and port
    app, port = asyncio.run(main())
    
    # Start server
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_server()