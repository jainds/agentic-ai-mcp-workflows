import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..base import DomainAgent, skill
from ..llm_client import LLMSkillMixin, LLMTemplates


class SupportDomainAgent(DomainAgent, LLMSkillMixin):
    """Domain agent for customer support workflows"""
    
    def __init__(self, port: int = 8005):
        DomainAgent.__init__(self, "SupportDomainAgent", port)
        LLMSkillMixin.__init__(self)
        
        # Register technical agents
        self.register_technical_agent(
            "CustomerDataAgent", 
            os.getenv("CUSTOMER_AGENT_URL", "http://customer-agent:8010")
        )
        self.register_technical_agent(
            "PolicyDataAgent", 
            os.getenv("POLICY_AGENT_URL", "http://policy-agent:8011")
        )
        self.register_technical_agent(
            "ClaimsDataAgent", 
            os.getenv("CLAIMS_DATA_AGENT_URL", "http://claims-agent:8012")
        )

    @skill("HandleCustomerInquiry", "Process general customer inquiries and route to appropriate workflow")
    async def handle_customer_inquiry(self, user_message: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle general customer inquiries with intent detection and routing"""
        try:
            self.logger.info(f"Processing customer inquiry: {user_message[:100]}...")
            
            # Extract intent from user message
            intent_result = await self.extract_intent(user_message)
            intent = intent_result["intent"]
            
            self.logger.info(f"Detected intent: {intent}")
            
            # Route based on intent
            if intent == "policy_inquiry":
                return await self.handle_policy_inquiry(user_message, customer_id)
            elif intent == "claim_status":
                return await self.handle_claim_status_inquiry(user_message, customer_id)
            elif intent == "billing_inquiry":
                return await self.handle_billing_inquiry(user_message, customer_id)
            elif intent == "general_support":
                return await self.handle_general_support(user_message, customer_id)
            else:
                # Default handling
                response = await self.generate_response(
                    user_message,
                    context="General customer support",
                    information={"intent": intent}
                )
                return {
                    "success": True,
                    "response": response,
                    "intent": intent,
                    "workflow": "general_support"
                }
                
        except Exception as e:
            self.logger.error(f"Error handling customer inquiry: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact customer service directly."
            }

    @skill("HandlePolicyInquiry", "Handle policy status and information requests")
    async def handle_policy_inquiry(self, user_message: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle policy-related inquiries"""
        try:
            self.logger.info(f"Processing policy inquiry for customer {customer_id}")
            
            if not customer_id:
                return {
                    "success": False,
                    "response": "I need your customer ID to look up your policy information. Can you please provide it?",
                    "workflow": "policy_inquiry",
                    "next_action": "collect_customer_id"
                }
            
            # Validate customer
            customer_validation = await self.call_technical_agent(
                "CustomerDataAgent", 
                "ValidateCustomer", 
                {"customer_id": customer_id}
            )
            
            if not customer_validation.get("result", {}).get("valid"):
                return {
                    "success": False,
                    "response": "I couldn't find an active customer account with that ID. Please verify your customer ID.",
                    "workflow": "policy_inquiry"
                }
            
            # Get customer policies
            policies_result = await self.call_technical_agent(
                "PolicyDataAgent", 
                "GetCustomerPolicies", 
                {"customer_id": customer_id}
            )
            
            if not policies_result.get("result", {}).get("success"):
                return {
                    "success": False,
                    "response": "I'm having trouble accessing your policy information right now. Please try again later.",
                    "workflow": "policy_inquiry"
                }
            
            policies = policies_result["result"]["policies"]
            
            if not policies:
                return {
                    "success": True,
                    "response": "I don't see any active policies for your account. Would you like me to help you get a quote for new coverage?",
                    "workflow": "policy_inquiry",
                    "data": {"policies": []}
                }
            
            # Get detailed policy information
            policy_details = []
            for policy_summary in policies:
                policy_id = policy_summary["policy_id"]
                policy_status = await self.call_technical_agent(
                    "PolicyDataAgent",
                    "GetPolicyStatus",
                    {"policy_id": policy_id}
                )
                
                if policy_status.get("result", {}).get("success"):
                    policy_details.append(policy_status["result"]["status"])
            
            # Generate comprehensive response
            customer_name = customer_validation["result"]["name"]
            response = await self.generate_response(
                user_message,
                context=f"Policy inquiry for customer {customer_name}",
                information={
                    "customer": customer_validation["result"],
                    "policies": policy_details
                }
            )
            
            return {
                "success": True,
                "response": response,
                "workflow": "policy_inquiry",
                "data": {
                    "customer": customer_validation["result"],
                    "policies": policy_details
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error handling policy inquiry: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm having trouble processing your policy inquiry. Please contact customer service for assistance."
            }

    @skill("HandleClaimStatusInquiry", "Handle claim status check requests")
    async def handle_claim_status_inquiry(self, user_message: str, customer_id: Optional[int] = None, claim_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle claim status inquiries"""
        try:
            self.logger.info(f"Processing claim status inquiry for customer {customer_id}, claim {claim_id}")
            
            if not customer_id:
                return {
                    "success": False,
                    "response": "I need your customer ID to look up your claims. Can you please provide it?",
                    "workflow": "claim_status",
                    "next_action": "collect_customer_id"
                }
            
            # If specific claim ID provided, get that claim
            if claim_id:
                claim_result = await self.call_technical_agent(
                    "ClaimsDataAgent",
                    "GetClaimStatus",
                    {"claim_id": claim_id}
                )
                
                if not claim_result.get("result", {}).get("success"):
                    return {
                        "success": False,
                        "response": f"I couldn't find claim #{claim_id}. Please verify the claim number.",
                        "workflow": "claim_status"
                    }
                
                claim_status = claim_result["result"]["status"]
                
                response = await self.generate_response(
                    user_message,
                    context="Claim status inquiry",
                    information={"claim": claim_status}
                )
                
                return {
                    "success": True,
                    "response": response,
                    "workflow": "claim_status",
                    "data": {"claim": claim_status}
                }
            
            # Otherwise, get all customer claims
            claims_result = await self.call_technical_agent(
                "ClaimsDataAgent",
                "GetCustomerClaims",
                {"customer_id": customer_id}
            )
            
            if not claims_result.get("result", {}).get("success"):
                return {
                    "success": False,
                    "response": "I'm having trouble accessing your claims information right now. Please try again later.",
                    "workflow": "claim_status"
                }
            
            claims = claims_result["result"]["claims"]
            
            if not claims:
                return {
                    "success": True,
                    "response": "I don't see any claims filed under your account. If you need to file a new claim, I can help you with that.",
                    "workflow": "claim_status",
                    "data": {"claims": []}
                }
            
            # Get detailed status for recent claims
            detailed_claims = []
            for claim_summary in claims[:5]:  # Limit to 5 most recent
                claim_status = await self.call_technical_agent(
                    "ClaimsDataAgent",
                    "GetClaimStatus",
                    {"claim_id": claim_summary["claim_id"]}
                )
                
                if claim_status.get("result", {}).get("success"):
                    detailed_claims.append(claim_status["result"]["status"])
            
            response = await self.generate_response(
                user_message,
                context="Claims status inquiry for customer",
                information={"claims": detailed_claims}
            )
            
            return {
                "success": True,
                "response": response,
                "workflow": "claim_status",
                "data": {"claims": detailed_claims}
            }
            
        except Exception as e:
            self.logger.error(f"Error handling claim status inquiry: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm having trouble processing your claim status inquiry. Please contact customer service for assistance."
            }

    @skill("HandleBillingInquiry", "Handle billing and payment related questions")
    async def handle_billing_inquiry(self, user_message: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle billing and payment inquiries"""
        try:
            if not customer_id:
                return {
                    "success": False,
                    "response": "I need your customer ID to access your billing information. Can you please provide it?",
                    "workflow": "billing_inquiry",
                    "next_action": "collect_customer_id"
                }
            
            # Get customer and policy information for billing context
            customer_validation = await self.call_technical_agent(
                "CustomerDataAgent",
                "ValidateCustomer",
                {"customer_id": customer_id}
            )
            
            if not customer_validation.get("result", {}).get("valid"):
                return {
                    "success": False,
                    "response": "I couldn't find an active customer account with that ID.",
                    "workflow": "billing_inquiry"
                }
            
            policies_result = await self.call_technical_agent(
                "PolicyDataAgent",
                "GetCustomerPolicies",
                {"customer_id": customer_id}
            )
            
            billing_info = {
                "customer": customer_validation["result"],
                "policies": policies_result.get("result", {}).get("policies", [])
            }
            
            response = await self.generate_response(
                user_message,
                context="Billing inquiry - provide general billing information and direct to billing department for specific account details",
                information=billing_info
            )
            
            return {
                "success": True,
                "response": response,
                "workflow": "billing_inquiry",
                "data": billing_info
            }
            
        except Exception as e:
            self.logger.error(f"Error handling billing inquiry: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm having trouble accessing billing information. Please contact our billing department directly."
            }

    @skill("HandleGeneralSupport", "Handle general support questions")
    async def handle_general_support(self, user_message: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle general support questions"""
        try:
            context = "General customer support - provide helpful information about insurance topics"
            
            # If customer ID provided, get basic customer info for personalization
            customer_info = {}
            if customer_id:
                customer_validation = await self.call_technical_agent(
                    "CustomerDataAgent",
                    "ValidateCustomer",
                    {"customer_id": customer_id}
                )
                
                if customer_validation.get("result", {}).get("valid"):
                    customer_info = customer_validation["result"]
                    context = f"General support for customer {customer_info.get('name', '')}"
            
            response = await self.generate_response(
                user_message,
                context=context,
                information=customer_info
            )
            
            return {
                "success": True,
                "response": response,
                "workflow": "general_support",
                "data": customer_info
            }
            
        except Exception as e:
            self.logger.error(f"Error handling general support: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm here to help! Could you please rephrase your question or contact customer service for assistance?"
            }

    @skill("CheckPolicyStatus", "Quick policy status check for specific policy")
    async def check_policy_status(self, policy_id: int, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Quick policy status check"""
        try:
            # Validate policy exists
            policy_validation = await self.call_technical_agent(
                "PolicyDataAgent",
                "ValidatePolicy",
                {"policy_id": policy_id}
            )
            
            if not policy_validation.get("result", {}).get("valid"):
                return {
                    "success": False,
                    "message": f"Policy {policy_id} not found or inactive",
                    "valid": False
                }
            
            policy_info = policy_validation["result"]
            
            return {
                "success": True,
                "policy_id": policy_id,
                "status": policy_info["status"],
                "policy_number": policy_info["policy_number"],
                "expiration_date": policy_info["expiration_date"],
                "days_until_expiry": policy_info["days_until_expiry"],
                "valid": True
            }
            
        except Exception as e:
            self.logger.error(f"Error checking policy status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """Run the SupportDomainAgent as a standalone service"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    # Create FastAPI app
    app = FastAPI(
        title="Support Domain Agent",
        description="Domain agent for customer support workflows",
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
    agent = SupportDomainAgent()
    from ..base import AgentServer
    agent_server = AgentServer(agent)
    
    @app.post("/execute")
    async def execute_skill(request: Dict[str, Any]):
        """Execute an agent skill"""
        try:
            return await agent_server.handle_execute_request(request)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/chat")
    async def chat(request: Dict[str, Any]):
        """Chat interface for customer inquiries"""
        try:
            message = request.get("message", "")
            customer_id = request.get("customer_id")
            
            result = await agent.handle_customer_inquiry(message, customer_id)
            return result
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
    async def metrics():
        """Prometheus metrics endpoint"""
        metrics_data = await agent_server.handle_metrics_request()
        from fastapi import Response
        return Response(content=metrics_data, media_type="text/plain")
    
    # Cleanup on shutdown
    @app.on_event("shutdown")
    async def shutdown_event():
        await agent.close_llm_client()
    
    # Start server
    port = int(os.getenv("SUPPORT_AGENT_PORT", 8005))
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