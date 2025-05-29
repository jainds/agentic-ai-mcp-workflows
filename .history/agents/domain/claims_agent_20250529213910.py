"""
Claims Agent - Domain agent for processing insurance claims using LLM.
Processes customer queries and orchestrates technical agent calls via A2A protocol.
"""

import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from agents.shared.a2a_base import A2AAgent, TaskRequest, TaskResponse
from agents.shared.mcp_base import MCPAgentMixin
from agents.shared.auth import service_auth
import structlog
import openai
from anthropic import Anthropic

logger = structlog.get_logger(__name__)


class ClaimsAgent(A2AAgent, MCPAgentMixin):
    """Domain agent for insurance claims processing with LLM intelligence"""
    
    def __init__(self, port: int = 8000):
        capabilities = {
            "streaming": False,
            "pushNotifications": True,
            "fileUpload": True,
            "messageHistory": True,
            "claimsProcessing": True,
            "documentAnalysis": True,
            "llmEnabled": True
        }
        
        # Initialize A2A agent
        A2AAgent.__init__(
            self,
            name="ClaimsAgent",
            description="LLM-powered agent for processing insurance claims with AI analysis and fraud detection",
            port=port,
            capabilities=capabilities
        )
        
        # Initialize MCP capabilities
        MCPAgentMixin.__init__(self)
        
        # Initialize LLM clients
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "demo-key")
        )
        self.anthropic_client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY", "demo-key")
        )
        
        # Setup MCP connections to technical agents
        self._setup_technical_agent_connections()
        
        # Claims processing state
        self.active_claims: Dict[str, Dict[str, Any]] = {}
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        
        logger.info("Claims Agent initialized with LLM capabilities", port=port)
    
    def _setup_technical_agent_connections(self):
        """Setup connections to technical agents"""
        # Connect to Data Agent for data access
        data_agent_url = os.getenv("DATA_AGENT_URL", "http://data-agent:8002")
        self.add_api_wrapper("data_agent", data_agent_url)
        
        # Connect to Notification Agent
        notification_agent_url = os.getenv("NOTIFICATION_AGENT_URL", "http://notification-agent:8003")
        self.add_api_wrapper("notification_agent", notification_agent_url)
        
        # Connect to mock APIs via enterprise wrappers
        claims_api_url = os.getenv("CLAIMS_API_URL", "http://claims-service:8000")
        self.add_api_wrapper("claims_api", claims_api_url)
        
        user_api_url = os.getenv("USER_API_URL", "http://user-service:8000")
        self.add_api_wrapper("user_api", user_api_url)
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process incoming A2A tasks using LLM intelligence"""
        user_data = task.user
        user_message = user_data.get("message", "")
        user_id = user_data.get("user_id", "anonymous")
        conversation_id = user_data.get("conversation_id", task.taskId)
        
        logger.info("Processing customer query", task_id=task.taskId, user_id=user_id, message=user_message[:100])
        
        try:
            # Add to conversation history
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            self.conversation_history[conversation_id].append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Use LLM to understand intent and plan actions
            intent_analysis = await self._analyze_user_intent(user_message, conversation_id)
            
            # Execute the planned actions
            response_content = await self._execute_plan(intent_analysis, user_data, task.taskId)
            
            # Add assistant response to history
            self.conversation_history[conversation_id].append({
                "role": "assistant", 
                "content": response_content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return TaskResponse(
                taskId=task.taskId,
                parts=[{"text": response_content, "type": "claims_response"}],
                status="completed",
                metadata={
                    "agent": "ClaimsAgent",
                    "intent": intent_analysis.get("intent"),
                    "actions_taken": intent_analysis.get("actions", [])
                }
            )
            
        except Exception as e:
            logger.error("Task processing failed", task_id=task.taskId, error=str(e))
            return TaskResponse(
                taskId=task.taskId,
                parts=[{"text": f"I apologize, but I encountered an error processing your request: {str(e)}", "type": "error"}],
                status="failed",
                metadata={"agent": "ClaimsAgent", "error": str(e)}
            )
    
    async def _analyze_user_intent(self, user_message: str, conversation_id: str) -> Dict[str, Any]:
        """Use LLM to analyze user intent and plan actions"""
        
        # Get conversation history for context
        history = self.conversation_history.get(conversation_id, [])
        history_context = "\n".join([f"{h['role']}: {h['content']}" for h in history[-5:]])  # Last 5 messages
        
        system_prompt = """
        You are an expert insurance claims agent AI. Analyze the user's message and determine:
        1. Primary intent (file_claim, check_status, fraud_inquiry, general_question, etc.)
        2. Required actions (what technical agents/APIs to call)
        3. Information needed from user
        4. Response strategy
        
        Available technical agents:
        - data_agent: Access policy data, customer information, claims history
        - notification_agent: Send notifications, alerts
        - claims_api: Create, update claims, process payments
        - user_api: User authentication, profile management
        
        Respond in JSON format with: {"intent": str, "confidence": float, "actions": [str], "info_needed": [str], "response_strategy": str}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Conversation history:\n{history_context}\n\nCurrent message: {user_message}"}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            import json
            intent_analysis = json.loads(response.choices[0].message.content)
            logger.info("Intent analyzed", intent=intent_analysis.get("intent"), confidence=intent_analysis.get("confidence"))
            return intent_analysis
            
        except Exception as e:
            logger.error("Intent analysis failed", error=str(e))
            return {
                "intent": "general_question",
                "confidence": 0.5,
                "actions": ["provide_general_help"],
                "info_needed": [],
                "response_strategy": "fallback"
            }
    
    async def _execute_plan(self, intent_analysis: Dict[str, Any], user_data: Dict[str, Any], task_id: str) -> str:
        """Execute the planned actions based on intent analysis"""
        
        intent = intent_analysis.get("intent", "unknown")
        actions = intent_analysis.get("actions", [])
        
        if intent == "file_claim":
            return await self._handle_claim_filing(user_data, actions, task_id)
        elif intent == "check_status":
            return await self._handle_status_check(user_data, actions, task_id)
        elif intent == "fraud_inquiry":
            return await self._handle_fraud_inquiry(user_data, actions, task_id)
        elif intent == "policy_question":
            return await self._handle_policy_question(user_data, actions, task_id)
        else:
            return await self._handle_general_question(user_data, intent_analysis, task_id)
    
    async def _handle_claim_filing(self, user_data: Dict[str, Any], actions: List[str], task_id: str) -> str:
        """Handle claim filing with orchestrated technical agent calls"""
        
        user_id = user_data.get("user_id", "unknown")
        message = user_data.get("message", "")
        
        try:
            # Step 1: Extract claim information using LLM
            claim_info = await self._extract_claim_information(message)
            
            # Step 2: Get customer data from Data Agent
            customer_data = await self.call_enterprise_api(
                "data_agent",
                "GET", 
                f"/customer/{user_id}"
            )
            
            # Step 3: Validate policy via Data Agent
            if claim_info.get("policy_number"):
                policy_data = await self.call_enterprise_api(
                    "data_agent",
                    "GET",
                    f"/policy/{claim_info['policy_number']}"
                )
            else:
                # Find policies for customer
                policy_data = await self.call_enterprise_api(
                    "data_agent",
                    "GET",
                    f"/policies?customer_id={user_id}"
                )
            
            # Step 4: Create claim via Claims API
            claim_data = {
                "policy_number": claim_info.get("policy_number", "AUTO-DETECT"),
                "customer_id": user_id,
                "incident_date": claim_info.get("incident_date", datetime.utcnow().isoformat()),
                "description": claim_info.get("description", message),
                "amount": claim_info.get("estimated_amount", 0),
                "claim_type": claim_info.get("claim_type", "general")
            }
            
            claim_result = await self.call_enterprise_api(
                "claims_api",
                "POST",
                "/claims",
                data=claim_data
            )
            
            # Step 5: Analyze for fraud using Data Agent
            fraud_analysis = await self.call_enterprise_api(
                "data_agent",
                "POST",
                "/analyze/fraud",
                data={"claim_data": claim_data, "customer_data": customer_data}
            )
            
            # Step 6: Send notifications if needed
            if fraud_analysis and fraud_analysis.get("risk_level") == "high":
                await self.call_enterprise_api(
                    "notification_agent",
                    "POST",
                    "/notifications",
                    data={
                        "type": "fraud_alert",
                        "claim_id": claim_result.get("claim_id"),
                        "priority": "high",
                        "message": f"High fraud risk detected for claim {claim_result.get('claim_id')}"
                    }
                )
            
            # Generate response using LLM
            return await self._generate_claim_response(claim_result, fraud_analysis, policy_data)
            
        except Exception as e:
            logger.error("Claim filing failed", task_id=task_id, error=str(e))
            return f"I apologize, but I encountered an issue while processing your claim. Please try again or contact support. Error: {str(e)}"
    
    async def _extract_claim_information(self, message: str) -> Dict[str, Any]:
        """Extract structured claim information from user message using LLM"""
        
        system_prompt = """
        Extract claim information from the user's message. Return JSON with:
        {
            "policy_number": "string or null",
            "incident_date": "ISO date or null", 
            "description": "string",
            "estimated_amount": "number or null",
            "claim_type": "auto|home|health|life|commercial",
            "location": "string or null",
            "parties_involved": "string or null"
        }
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error("Claim extraction failed", error=str(e))
            return {"description": message, "claim_type": "general"}
    
    async def _handle_status_check(self, user_data: Dict[str, Any], actions: List[str], task_id: str) -> str:
        """Handle claim status check"""
        
        user_id = user_data.get("user_id", "unknown")
        
        try:
            # Get claims for user from Data Agent
            claims = await self.call_enterprise_api(
                "data_agent",
                "GET",
                f"/claims?customer_id={user_id}"
            )
            
            if not claims:
                return "I couldn't find any claims associated with your account. Would you like to file a new claim?"
            
            # Generate status summary using LLM
            return await self._generate_status_response(claims)
            
        except Exception as e:
            logger.error("Status check failed", task_id=task_id, error=str(e))
            return "I'm having trouble accessing your claim information right now. Please try again later."
    
    async def _handle_fraud_inquiry(self, user_data: Dict[str, Any], actions: List[str], task_id: str) -> str:
        """Handle fraud-related inquiries"""
        return "I take fraud very seriously. If you suspect fraudulent activity, I'll flag this for immediate investigation by our fraud team. Can you provide more details about your concerns?"
    
    async def _handle_policy_question(self, user_data: Dict[str, Any], actions: List[str], task_id: str) -> str:
        """Handle policy-related questions"""
        
        user_id = user_data.get("user_id", "unknown")
        
        try:
            # Get policies for user
            policies = await self.call_enterprise_api(
                "data_agent",
                "GET",
                f"/policies?customer_id={user_id}"
            )
            
            return await self._generate_policy_response(policies, user_data.get("message", ""))
            
        except Exception as e:
            logger.error("Policy question failed", task_id=task_id, error=str(e))
            return "I'm having trouble accessing your policy information. Please contact customer service for detailed policy questions."
    
    async def _handle_general_question(self, user_data: Dict[str, Any], intent_analysis: Dict[str, Any], task_id: str) -> str:
        """Handle general questions using LLM"""
        
        system_prompt = """
        You are a helpful insurance claims agent. Provide accurate, helpful responses about:
        - Insurance claims processes
        - Policy information
        - General insurance questions
        - Next steps for customers
        
        Be professional, empathetic, and concise. If you can't answer something, direct them to appropriate resources.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_data.get("message", "")}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("General question handling failed", error=str(e))
            return "I'm here to help with your insurance needs. Could you please rephrase your question?"
    
    async def _generate_claim_response(self, claim_result: Dict[str, Any], fraud_analysis: Dict[str, Any], policy_data: Dict[str, Any]) -> str:
        """Generate a comprehensive claim response using LLM"""
        
        context = f"""
        Claim created: {claim_result}
        Fraud analysis: {fraud_analysis}
        Policy info: {policy_data}
        """
        
        system_prompt = """
        Generate a professional, empathetic response to a customer who just filed a claim. Include:
        - Acknowledgment of claim filing
        - Claim number/reference
        - Next steps
        - Timeline expectations
        - Contact information if needed
        
        Be reassuring but professional.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return f"Your claim has been successfully filed with reference number {claim_result.get('claim_id', 'N/A')}. We'll review it and get back to you within 2-3 business days."
    
    async def _generate_status_response(self, claims: List[Dict[str, Any]]) -> str:
        """Generate status response using LLM"""
        
        context = f"Customer claims: {claims}"
        
        system_prompt = """
        Provide a clear, organized summary of the customer's claims status. Include:
        - Number of claims
        - Status of each claim
        - Any pending actions
        - Next steps
        
        Be clear and helpful.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Status response generation failed", error=str(e))
            return f"You have {len(claims)} claim(s) on file. The most recent status updates are available in your account dashboard."
    
    async def _generate_policy_response(self, policies: List[Dict[str, Any]], question: str) -> str:
        """Generate policy response using LLM"""
        
        context = f"Customer policies: {policies}\nQuestion: {question}"
        
        system_prompt = """
        Answer the customer's policy question based on their policy information. Be accurate and helpful.
        If you can't find specific information, direct them to policy documents or customer service.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.2,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Policy response generation failed", error=str(e))
            return "I'd be happy to help with your policy question. For detailed policy information, please refer to your policy documents or contact customer service."


# Main execution
if __name__ == "__main__":
    port = int(os.getenv("CLAIMS_AGENT_PORT", "8000"))
    agent = ClaimsAgent(port=port)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("Claims Agent shutting down")
    finally:
        # Cleanup MCP connections
        asyncio.run(agent.cleanup_mcp_connections()) 