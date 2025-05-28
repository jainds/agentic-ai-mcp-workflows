import asyncio
import os
from typing import Dict, Any, Optional, List
from ..base import TechnicalAgent, skill


class ClaimsDataAgent(TechnicalAgent):
    """Technical agent for claims data operations"""
    
    def __init__(self, port: int = 8012):
        service_url = os.getenv("CLAIMS_SERVICE_URL", "http://claims-service:8002")
        super().__init__("ClaimsDataAgent", service_url, port)

    @skill("GetClaimInfo", "Retrieve claim information by ID")
    async def get_claim_info(self, claim_id: int) -> Dict[str, Any]:
        """Get claim information by ID"""
        try:
            result = await self.make_service_request("GET", f"/claim/{claim_id}")
            return {
                "success": True,
                "claim": result
            }
        except Exception as e:
            self.logger.error(f"Error getting claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetClaimStatus", "Get claim status information")
    async def get_claim_status(self, claim_id: int) -> Dict[str, Any]:
        """Get claim status information"""
        try:
            result = await self.make_service_request("GET", f"/claim/{claim_id}/status")
            return {
                "success": True,
                "status": result
            }
        except Exception as e:
            self.logger.error(f"Error getting claim status {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetClaimSummary", "Get claim summary information")
    async def get_claim_summary(self, claim_id: int) -> Dict[str, Any]:
        """Get claim summary information"""
        try:
            result = await self.make_service_request("GET", f"/claim/{claim_id}/summary")
            return {
                "success": True,
                "summary": result
            }
        except Exception as e:
            self.logger.error(f"Error getting claim summary {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("CreateClaim", "Create a new claim")
    async def create_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new claim"""
        try:
            result = await self.make_service_request("POST", "/claim", json=claim_data)
            return {
                "success": True,
                "claim": result
            }
        except Exception as e:
            self.logger.error(f"Error creating claim: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("UpdateClaimStatus", "Update claim status")
    async def update_claim_status(self, claim_id: int, new_status: str, reason: str, updated_by: str = "System") -> Dict[str, Any]:
        """Update claim status with tracking"""
        try:
            result = await self.make_service_request(
                "POST", 
                f"/claim/{claim_id}/status",
                params={
                    "new_status": new_status,
                    "reason": reason,
                    "updated_by": updated_by
                }
            )
            return {
                "success": True,
                "status_update": result
            }
        except Exception as e:
            self.logger.error(f"Error updating claim status {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetCustomerClaims", "Get all claims for a customer")
    async def get_customer_claims(self, customer_id: int) -> Dict[str, Any]:
        """Get all claims for a specific customer"""
        try:
            result = await self.make_service_request("GET", f"/customer/{customer_id}/claims")
            return {
                "success": True,
                "claims": result
            }
        except Exception as e:
            self.logger.error(f"Error getting claims for customer {customer_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetPolicyClaims", "Get all claims for a policy")
    async def get_policy_claims(self, policy_id: int) -> Dict[str, Any]:
        """Get all claims for a specific policy"""
        try:
            result = await self.make_service_request("GET", f"/policy/{policy_id}/claims")
            return {
                "success": True,
                "claims": result
            }
        except Exception as e:
            self.logger.error(f"Error getting claims for policy {policy_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("SearchClaims", "Search claims by claim number or IDs")
    async def search_claims(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search claims by claim number, customer ID, or policy ID"""
        try:
            result = await self.make_service_request(
                "GET", 
                "/search/claims", 
                params={"q": query, "limit": limit}
            )
            return {
                "success": True,
                "claims": result
            }
        except Exception as e:
            self.logger.error(f"Error searching claims with query '{query}': {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("AddClaimDocument", "Add a document to a claim")
    async def add_claim_document(self, claim_id: int, document_type: str, filename: str, description: str = "") -> Dict[str, Any]:
        """Add a document to a claim"""
        try:
            result = await self.make_service_request(
                "POST", 
                f"/claim/{claim_id}/documents",
                params={
                    "document_type": document_type,
                    "filename": filename,
                    "description": description
                }
            )
            return {
                "success": True,
                "document": result
            }
        except Exception as e:
            self.logger.error(f"Error adding document to claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetClaimDocuments", "Get documents for a claim")
    async def get_claim_documents(self, claim_id: int) -> Dict[str, Any]:
        """Get documents for a claim"""
        try:
            result = await self.make_service_request("GET", f"/claim/{claim_id}/documents")
            return {
                "success": True,
                "documents": result
            }
        except Exception as e:
            self.logger.error(f"Error getting documents for claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("AddClaimNote", "Add a note to a claim")
    async def add_claim_note(self, claim_id: int, content: str, author: str, is_internal: bool = False) -> Dict[str, Any]:
        """Add a note to a claim"""
        try:
            result = await self.make_service_request(
                "POST", 
                f"/claim/{claim_id}/notes",
                params={
                    "content": content,
                    "author": author,
                    "is_internal": is_internal
                }
            )
            return {
                "success": True,
                "note": result
            }
        except Exception as e:
            self.logger.error(f"Error adding note to claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetClaimNotes", "Get notes for a claim")
    async def get_claim_notes(self, claim_id: int, include_internal: bool = False) -> Dict[str, Any]:
        """Get notes for a claim"""
        try:
            result = await self.make_service_request(
                "GET", 
                f"/claim/{claim_id}/notes",
                params={"include_internal": include_internal}
            )
            return {
                "success": True,
                "notes": result
            }
        except Exception as e:
            self.logger.error(f"Error getting notes for claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("ApproveClaim", "Approve a claim for payment")
    async def approve_claim(self, claim_id: int, approved_amount: float, approver: str) -> Dict[str, Any]:
        """Approve a claim for payment"""
        try:
            result = await self.make_service_request(
                "POST", 
                f"/claim/{claim_id}/approve",
                params={
                    "approved_amount": approved_amount,
                    "approver": approver
                }
            )
            return {
                "success": True,
                "approval": result
            }
        except Exception as e:
            self.logger.error(f"Error approving claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("DenyClaim", "Deny a claim")
    async def deny_claim(self, claim_id: int, reason: str, reviewer: str) -> Dict[str, Any]:
        """Deny a claim"""
        try:
            result = await self.make_service_request(
                "POST", 
                f"/claim/{claim_id}/deny",
                params={
                    "reason": reason,
                    "reviewer": reviewer
                }
            )
            return {
                "success": True,
                "denial": result
            }
        except Exception as e:
            self.logger.error(f"Error denying claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("ProcessClaimPayment", "Process payment for an approved claim")
    async def process_claim_payment(self, claim_id: int, payment_amount: float, payment_method: str = "check") -> Dict[str, Any]:
        """Process payment for an approved claim"""
        try:
            result = await self.make_service_request(
                "POST", 
                f"/claim/{claim_id}/payment",
                params={
                    "payment_amount": payment_amount,
                    "payment_method": payment_method
                }
            )
            return {
                "success": True,
                "payment": result
            }
        except Exception as e:
            self.logger.error(f"Error processing payment for claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetClaimsStatistics", "Get claims statistics")
    async def get_claims_statistics(self) -> Dict[str, Any]:
        """Get claims statistics"""
        try:
            result = await self.make_service_request("GET", "/claims/statistics")
            return {
                "success": True,
                "statistics": result
            }
        except Exception as e:
            self.logger.error(f"Error getting claims statistics: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("ValidateClaim", "Validate claim exists and basic information")
    async def validate_claim(self, claim_id: int) -> Dict[str, Any]:
        """Validate claim exists and get basic information"""
        try:
            status_result = await self.get_claim_status(claim_id)
            
            if not status_result["success"]:
                return {
                    "success": False,
                    "valid": False,
                    "reason": "Claim not found"
                }
            
            status_info = status_result["status"]
            
            return {
                "success": True,
                "valid": True,
                "claim_id": claim_id,
                "claim_number": status_info.get("claim_number"),
                "status": status_info.get("status"),
                "priority": status_info.get("priority"),
                "claimed_amount": status_info.get("claimed_amount"),
                "approved_amount": status_info.get("approved_amount")
            }
            
        except Exception as e:
            self.logger.error(f"Error validating claim {claim_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """Run the ClaimsDataAgent as a standalone service"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    # Create FastAPI app
    app = FastAPI(
        title="Claims Data Agent",
        description="Technical agent for claims data operations",
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
    agent = ClaimsDataAgent()
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
    port = int(os.getenv("AGENT_PORT", 8012))
    return app, port
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        metrics_data = await agent_server.handle_metrics_request()
        from fastapi import Response
        return Response(content=metrics_data, media_type="text/plain")


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