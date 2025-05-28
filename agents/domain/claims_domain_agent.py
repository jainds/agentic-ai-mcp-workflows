import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from ..base import DomainAgent, skill
from ..llm_client import LLMSkillMixin, LLMTemplates


class ClaimsDomainAgent(DomainAgent, LLMSkillMixin):
    """Domain agent for claims workflow management"""
    
    def __init__(self, port: int = 8007):
        DomainAgent.__init__(self, "ClaimsDomainAgent", port)
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
            os.getenv("CLAIMS_DATA_AGENT_URL", "http://claims-data-agent:8012")
        )

    @skill("HandleClaimInquiry", "Process claims-related inquiries and route to appropriate workflow")
    async def handle_claim_inquiry(self, user_message: str, customer_id: Optional[int] = None, claim_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle general claims inquiries with intent detection and routing"""
        try:
            self.logger.info(f"Processing claim inquiry: {user_message[:100]}...")
            
            # Extract intent from user message
            intent_result = await self.extract_intent(user_message)
            intent = intent_result["intent"]
            
            self.logger.info(f"Detected intent: {intent}")
            
            # Extract claim ID from message if not provided
            if not claim_id:
                extracted_claim_id = await self.extract_claim_id(user_message)
                if extracted_claim_id:
                    claim_id = extracted_claim_id
                    self.logger.info(f"Extracted claim ID from message: {claim_id}")
                else:
                    # Fallback: regex extraction for claim IDs
                    import re
                    claim_matches = re.findall(r'claimid\s+is\s+(\d+)|claim\s*#?\s*(\d+)', user_message.lower())
                    if claim_matches:
                        for match in claim_matches:
                            claim_id = int(match[0] or match[1])
                            self.logger.info(f"Extracted claim ID via regex fallback: {claim_id}")
                            break
            
            # Extract customer ID from message if not provided
            if not customer_id:
                extracted_customer_id = await self.extract_customer_id(user_message)
                if extracted_customer_id:
                    customer_id = extracted_customer_id
                    self.logger.info(f"Extracted customer ID from message: {customer_id}")
                else:
                    # Fallback: regex extraction for customer IDs
                    import re
                    customer_matches = re.findall(r'customer\s+id\s+is\s+(\d+)|customer\s*#?\s*(\d+)', user_message.lower())
                    if customer_matches:
                        for match in customer_matches:
                            customer_id = int(match[0] or match[1])
                            self.logger.info(f"Extracted customer ID via regex fallback: {customer_id}")
                            break
            
            # Route based on intent
            if intent == "claim_filing":
                return await self.handle_claim_filing(user_message, customer_id)
            elif intent == "claim_status":
                return await self.handle_claim_status_check(user_message, customer_id, claim_id)
            else:
                # Extract claim details to see if this is a claim-related request
                claim_details = await self.extract_claim_details(user_message)
                
                if claim_details:
                    # If we found claim details, treat as claim filing
                    return await self.handle_claim_filing(user_message, customer_id, claim_details)
                else:
                    # General claims support
                    return await self.handle_general_claims_support(user_message, customer_id)
                
        except Exception as e:
            self.logger.error(f"Error handling claim inquiry: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties processing your claim request. Please try again or contact our claims department directly."
            }

    @skill("HandleClaimFiling", "Handle new claim filing workflow")
    async def handle_claim_filing(self, user_message: str, customer_id: Optional[int] = None, extracted_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle new claim filing workflow"""
        try:
            self.logger.info(f"Processing claim filing for customer {customer_id}")
            
            if not customer_id:
                return {
                    "success": False,
                    "response": "I need your customer ID to file a claim. Can you please provide it?",
                    "workflow": "claim_filing",
                    "next_action": "collect_customer_id"
                }
            
            # Validate customer and get their policies
            customer_validation = await self.call_technical_agent(
                "CustomerDataAgent", 
                "ValidateCustomer", 
                {"customer_id": customer_id}
            )
            
            if not customer_validation.get("result", {}).get("valid"):
                return {
                    "success": False,
                    "response": "I couldn't find an active customer account with that ID. Please verify your customer ID.",
                    "workflow": "claim_filing"
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
                    "response": "I'm having trouble accessing your policy information. Please try again later.",
                    "workflow": "claim_filing"
                }
            
            policies = policies_result["result"]["policies"]
            
            if not policies:
                return {
                    "success": False,
                    "response": "I don't see any active policies for your account. You need an active policy to file a claim.",
                    "workflow": "claim_filing"
                }
            
            # Extract or prompt for claim details
            if not extracted_details:
                extracted_details = await self.extract_claim_details(user_message)
            
            # Check if we have enough information to file the claim
            required_fields = ["incident_date", "incident_type", "location", "description"]
            missing_fields = [field for field in required_fields if not extracted_details.get(field)]
            
            if missing_fields:
                # Generate questions for missing information
                questions = await self.generate_claim_questions(missing_fields, extracted_details, policies)
                return {
                    "success": True,
                    "response": questions,
                    "workflow": "claim_filing",
                    "next_action": "collect_claim_details",
                    "missing_fields": missing_fields,
                    "collected_details": extracted_details,
                    "customer_policies": policies
                }
            
            # Determine appropriate policy for claim
            policy_id = await self.determine_claim_policy(extracted_details, policies)
            
            if not policy_id:
                return {
                    "success": False,
                    "response": "I couldn't determine which of your policies covers this type of incident. Please contact our claims department for assistance.",
                    "workflow": "claim_filing",
                    "collected_details": extracted_details
                }
            
            # Create the claim
            claim_data = {
                "customer_id": customer_id,
                "policy_id": policy_id,
                "claim_type": extracted_details.get("incident_type", "other"),
                "incident_details": {
                    "incident_date": extracted_details.get("incident_date"),
                    "incident_time": extracted_details.get("incident_time"),
                    "location": extracted_details.get("location"),
                    "description": extracted_details.get("description"),
                    "police_report_number": extracted_details.get("police_report"),
                    "weather_conditions": extracted_details.get("weather_conditions"),
                    "witnesses": extracted_details.get("witnesses", [])
                },
                "claimed_amount": float(extracted_details.get("estimated_damage", 0)),
                "priority": "medium"
            }
            
            claim_result = await self.call_technical_agent(
                "ClaimsDataAgent",
                "CreateClaim",
                {"claim_data": claim_data}
            )
            
            if not claim_result.get("result", {}).get("success"):
                return {
                    "success": False,
                    "response": "I encountered an error while filing your claim. Please try again or contact our claims department.",
                    "workflow": "claim_filing",
                    "error": claim_result.get("result", {}).get("error")
                }
            
            claim = claim_result["result"]["claim"]
            
            # Generate confirmation response
            response = await self.generate_response(
                user_message,
                context="Claim successfully filed",
                information={
                    "claim": claim,
                    "customer": customer_validation["result"],
                    "next_steps": [
                        "Save your claim number for reference",
                        "An adjuster will be assigned within 24 hours",
                        "You may be contacted for additional information",
                        "Upload any photos or documents through our portal"
                    ]
                }
            )
            
            return {
                "success": True,
                "response": response,
                "workflow": "claim_filing",
                "data": {
                    "claim": claim,
                    "claim_number": claim["claim_number"],
                    "claim_id": claim["claim_id"],
                    "status": claim["status"]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error handling claim filing: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm having trouble processing your claim filing. Please contact our claims department for assistance."
            }

    @skill("HandleClaimStatusCheck", "Handle claim status check requests")
    async def handle_claim_status_check(self, user_message: str, customer_id: Optional[int] = None, claim_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle claim status check requests"""
        try:
            self.logger.info(f"Processing claim status check for customer {customer_id}, claim {claim_id}")
            
            if not customer_id and not claim_id:
                return {
                    "success": False,
                    "response": "I need either your customer ID or claim number to check claim status. Can you please provide one?",
                    "workflow": "claim_status",
                    "next_action": "collect_identifier"
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
                
                # Get claim notes for additional context
                notes_result = await self.call_technical_agent(
                    "ClaimsDataAgent",
                    "GetClaimNotes",
                    {"claim_id": claim_id, "include_internal": False}
                )
                
                notes = notes_result.get("result", {}).get("notes", []) if notes_result.get("result", {}).get("success") else []
                
                response = await self.generate_response(
                    user_message,
                    context="Claim status inquiry for specific claim",
                    information={
                        "claim": claim_status,
                        "recent_notes": notes[-3:] if notes else []  # Last 3 public notes
                    }
                )
                
                return {
                    "success": True,
                    "response": response,
                    "workflow": "claim_status",
                    "data": {
                        "claim": claim_status,
                        "notes": notes[-3:]
                    }
                }
            
            # Otherwise, get all customer claims
            if not customer_id:
                return {
                    "success": False,
                    "response": "I need your customer ID to look up your claims. Can you please provide it?",
                    "workflow": "claim_status"
                }
            
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
            self.logger.error(f"Error handling claim status check: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm having trouble processing your claim status request. Please contact our claims department for assistance."
            }

    @skill("HandleGeneralClaimsSupport", "Handle general claims support questions")
    async def handle_general_claims_support(self, user_message: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """Handle general claims support questions"""
        try:
            context = "General claims support - provide helpful information about claims process and requirements"
            
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
                    context = f"General claims support for customer {customer_info.get('name', '')}"
            
            response = await self.generate_response(
                user_message,
                context=context,
                information={
                    "customer": customer_info,
                    "claims_info": {
                        "filing_requirements": [
                            "Valid policy number",
                            "Date and time of incident",
                            "Location where incident occurred",
                            "Description of what happened",
                            "Contact information for witnesses (if any)",
                            "Police report number (if applicable)"
                        ],
                        "claim_process": [
                            "File claim within 24-48 hours of incident",
                            "Adjuster assignment within 1 business day",
                            "Initial contact from adjuster within 2 business days",
                            "Investigation and assessment",
                            "Settlement offer or denial",
                            "Payment processing (if approved)"
                        ]
                    }
                }
            )
            
            return {
                "success": True,
                "response": response,
                "workflow": "general_claims_support",
                "data": customer_info
            }
            
        except Exception as e:
            self.logger.error(f"Error handling general claims support: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I'm here to help with your claims questions! Could you please be more specific about what you'd like to know?"
            }

    async def generate_claim_questions(self, missing_fields: List[str], existing_details: Dict[str, Any], policies: List[Dict[str, Any]]) -> str:
        """Generate questions to collect missing claim information"""
        try:
            questions_map = {
                "incident_date": "When did the incident occur? Please provide the date and approximate time.",
                "incident_type": "What type of incident happened? (e.g., auto accident, theft, fire, water damage, etc.)",
                "location": "Where did the incident take place? Please provide the address or location details.",
                "description": "Can you describe what happened in detail?",
                "estimated_damage": "Do you have an estimate of the damage amount?",
                "police_report": "Was a police report filed? If so, what is the report number?",
                "witnesses": "Were there any witnesses? If so, can you provide their contact information?"
            }
            
            questions = []
            for field in missing_fields:
                if field in questions_map:
                    questions.append(questions_map[field])
            
            context = f"Collecting claim information. Already have: {', '.join(existing_details.keys())}"
            
            prompt = f"""I'm helping file a claim and need some additional information. 
            
Existing details: {existing_details}
Available policies: {[p.get('policy_type', 'Unknown') for p in policies]}

Please ask for the following information in a helpful, empathetic way:
{chr(10).join(f'- {q}' for q in questions)}

Be conversational and supportive, as this may be a stressful time for the customer."""
            
            return await self.llm_chat([
                {"role": "user", "content": prompt}
            ], system_prompt=LLMTemplates.SYSTEM_PROMPTS["claims_processor"])
            
        except Exception as e:
            self.logger.error(f"Error generating claim questions: {str(e)}")
            return "I need some additional information to file your claim. " + " ".join([
                questions_map.get(field, f"Please provide {field}.") for field in missing_fields
            ])

    async def determine_claim_policy(self, claim_details: Dict[str, Any], policies: List[Dict[str, Any]]) -> Optional[int]:
        """Determine which policy should be used for the claim"""
        try:
            incident_type = claim_details.get("incident_type", "").lower()
            
            # Simple mapping logic (in reality this would be more sophisticated)
            type_mappings = {
                "auto": ["auto_accident", "auto_theft", "auto_vandalism", "car", "vehicle", "accident"],
                "home": ["home_fire", "home_theft", "home_water_damage", "home_storm", "fire", "theft", "water", "storm", "house"],
                "health": ["health_medical", "health_emergency", "medical", "injury", "hospital"],
                "life": ["life_death", "death"],
                "business": ["business", "commercial"]
            }
            
            for policy in policies:
                policy_type = policy.get("policy_type", "").lower()
                
                if policy_type in type_mappings:
                    if any(keyword in incident_type for keyword in type_mappings[policy_type]):
                        return policy.get("policy_id")
            
            # If no specific match, return the first active policy
            for policy in policies:
                if policy.get("status") == "active":
                    return policy.get("policy_id")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error determining claim policy: {str(e)}")
            return None

    @skill("CreateClaim", "Create a new claim with provided details")
    async def create_claim(self, customer_id: int, policy_id: int, claim_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new claim with provided details"""
        try:
            claim_data = {
                "customer_id": customer_id,
                "policy_id": policy_id,
                "claim_type": claim_details.get("incident_type", "other"),
                "incident_details": claim_details.get("incident_details", {}),
                "claimed_amount": float(claim_details.get("claimed_amount", 0)),
                "priority": claim_details.get("priority", "medium")
            }
            
            result = await self.call_technical_agent(
                "ClaimsDataAgent",
                "CreateClaim",
                {"claim_data": claim_data}
            )
            
            if result.get("result", {}).get("success"):
                return {
                    "success": True,
                    "claim": result["result"]["claim"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("result", {}).get("error", "Unknown error")
                }
                
        except Exception as e:
            self.logger.error(f"Error creating claim: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @skill("GetClaimStatus", "Get status for a specific claim")
    async def get_claim_status(self, claim_id: int) -> Dict[str, Any]:
        """Get status for a specific claim"""
        try:
            result = await self.call_technical_agent(
                "ClaimsDataAgent",
                "GetClaimStatus",
                {"claim_id": claim_id}
            )
            
            if result.get("result", {}).get("success"):
                return {
                    "success": True,
                    "status": result["result"]["status"]
                }
            else:
                return {
                    "success": False,
                    "error": "Claim not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting claim status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


async def main():
    """Run the ClaimsDomainAgent as a standalone service"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    # Create FastAPI app
    app = FastAPI(
        title="Claims Domain Agent",
        description="Domain agent for claims workflow management",
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
    agent = ClaimsDomainAgent()
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
        """Chat interface for claims inquiries"""
        try:
            message = request.get("message", "")
            customer_id = request.get("customer_id")
            claim_id = request.get("claim_id")
            
            result = await agent.handle_claim_inquiry(message, customer_id, claim_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/file-claim")
    async def file_claim(request: Dict[str, Any]):
        """Direct claim filing endpoint"""
        try:
            customer_id = request.get("customer_id")
            message = request.get("message", "")
            claim_details = request.get("claim_details")
            
            result = await agent.handle_claim_filing(message, customer_id, claim_details)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/claim/{claim_id}/status")
    async def check_claim_status(claim_id: int):
        """Check status of specific claim"""
        try:
            result = await agent.get_claim_status(claim_id)
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
    
    # Cleanup on shutdown
    @app.on_event("shutdown")
    async def shutdown_event():
        await agent.close_llm_client()
    
    # Start server
    port = int(os.getenv("CLAIMS_DOMAIN_AGENT_PORT", 8007))
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