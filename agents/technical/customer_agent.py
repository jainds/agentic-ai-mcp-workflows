import asyncio
import os
from typing import Dict, Any, Optional, List
from ..base import TechnicalAgent, skill


class CustomerDataAgent(TechnicalAgent):
    """Technical agent for customer data operations"""
    
    def __init__(self, port: int = 8010):
        service_url = os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8000")
        super().__init__("CustomerDataAgent", service_url, port)

    @skill("GetCustomerInfo", "Retrieve customer information by ID")
    async def get_customer_info(self, customer_id: int) -> Dict[str, Any]:
        """Get customer information by ID"""
        try:
            result = await self.make_service_request("GET", f"/customer/{customer_id}")
            return {
                "success": True,
                "customer": result
            }
        except Exception as e:
            self.logger.error(f"Error getting customer {customer_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetCustomerSummary", "Get customer summary information")
    async def get_customer_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get customer summary information"""
        try:
            result = await self.make_service_request("GET", f"/customer/{customer_id}/summary")
            return {
                "success": True,
                "summary": result
            }
        except Exception as e:
            self.logger.error(f"Error getting customer summary {customer_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("SearchCustomers", "Search customers by name or email")
    async def search_customers(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search customers by name or email"""
        try:
            result = await self.make_service_request(
                "GET", 
                "/search/customers", 
                params={"q": query, "limit": limit}
            )
            return {
                "success": True,
                "customers": result
            }
        except Exception as e:
            self.logger.error(f"Error searching customers with query '{query}': {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetCustomerPolicies", "Get policy IDs for a customer")
    async def get_customer_policies(self, customer_id: int) -> Dict[str, Any]:
        """Get list of policy IDs for a customer"""
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

    @skill("CreateCustomer", "Create a new customer")
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer"""
        try:
            result = await self.make_service_request("POST", "/customer", json=customer_data)
            return {
                "success": True,
                "customer": result
            }
        except Exception as e:
            self.logger.error(f"Error creating customer: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("UpdateCustomer", "Update existing customer")
    async def update_customer(self, customer_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing customer"""
        try:
            result = await self.make_service_request(
                "PUT", 
                f"/customer/{customer_id}", 
                json=update_data
            )
            return {
                "success": True,
                "customer": result
            }
        except Exception as e:
            self.logger.error(f"Error updating customer {customer_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("ValidateCustomer", "Validate customer exists and is active")
    async def validate_customer(self, customer_id: int) -> Dict[str, Any]:
        """Validate customer exists and is active"""
        try:
            customer_result = await self.get_customer_info(customer_id)
            
            if not customer_result["success"]:
                return {
                    "success": False,
                    "valid": False,
                    "reason": "Customer not found"
                }
            
            customer = customer_result["customer"]
            is_active = customer.get("status") == "active"
            
            return {
                "success": True,
                "valid": is_active,
                "customer_id": customer_id,
                "status": customer.get("status"),
                "name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
            }
            
        except Exception as e:
            self.logger.error(f"Error validating customer {customer_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """Run the CustomerDataAgent as a standalone service"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    # Create FastAPI app
    app = FastAPI(
        title="Customer Data Agent",
        description="Technical agent for customer data operations",
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
    agent = CustomerDataAgent()
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
    
    # Start server
    port = int(os.getenv("CUSTOMER_AGENT_PORT", 8010))
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