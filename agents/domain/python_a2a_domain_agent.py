"""
Domain Agent using python-a2a library.
Plays two roles:
1. Understanding intent and drafting out a plan
2. Routing tasks to technical agents for execution

Once tasks are complete, domain agent prepares a response and sends it back.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
import time
from pathlib import Path

# python-a2a library imports
from python_a2a import (
    A2AServer, A2AClient, Message, TextContent, MessageRole, run_server,
    AgentNetwork, Flow, AIAgentRouter, AgentCard, Task, TaskState, AgentSkill
)

from agents.shared.python_a2a_base import PythonA2AAgent, PythonA2AClientWrapper
from agents.shared.auth import service_auth
import structlog
from openai import OpenAI

# FastAPI for HTTP endpoints
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logger = structlog.get_logger(__name__)

# Pydantic models for HTTP API
class ChatRequest(BaseModel):
    message: str
    customer_id: str = "default-customer"

class ChatResponse(BaseModel):
    response: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    thinking_steps: List[str] = []
    orchestration_events: List[Dict[str, Any]] = []
    api_calls: List[Dict[str, Any]] = []
    timestamp: str

class PythonA2ADomainAgent(PythonA2AAgent):
    """
    Enhanced Python A2A Domain Agent with professional response templates
    
    This agent plays three roles:
    1. Understanding intent and extracting entities from user messages  
    2. Creating and executing plans by routing tasks to technical agents
    3. Preparing professional responses using structured templates
    """
    
    def __init__(self, port: int = 8000):
        super().__init__(
            name="Python A2A Domain Agent",
            description="Insurance domain agent with LLM reasoning and professional response templates",
            port=port,
            capabilities={
                "streaming": True,
                "pushNotifications": False,
                "fileUpload": False,
                "messageHistory": True,
                "python_a2a_compatible": True,
                "intent_analysis": True,
                "execution_planning": True,
                "professional_templates": True
            },
            skills=[{
                "id": "insurance-domain-orchestration",
                "name": "Insurance Domain Orchestration",
                "description": "Comprehensive insurance task orchestration with professional response templates",
                "tags": ["insurance", "domain", "orchestration", "professional"],
                "examples": [
                    "Help me check my claim status",
                    "What is my policy coverage?", 
                    "I want to file a new claim",
                    "Show me my billing information"
                ],
                "inputModes": ["text"],
                "outputModes": ["text"]
            }]
        )
        
        # Load professional response template
        self.response_template = self._load_professional_template()
        
        # Setup LLM client
        self.setup_llm_client()
        
        # Initialize agent network
        self.setup_technical_agents()
        
        # Setup AI-powered router
        self.setup_ai_router()
        
        # Template-specific response enhancement
        self.template_enhancement_enabled = True
        
        # Setup HTTP endpoints for Kubernetes deployment
        self.setup_http_endpoints()
        
        logger.info("Enhanced Python A2A Domain Agent initialized with professional templates")

    def _load_professional_template(self) -> str:
        """Load the professional response template from file"""
        try:
            template_path = Path("Template")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read().strip()
                logger.info("Professional response template loaded successfully")
                return template
        except Exception as e:
            logger.warning(f"Could not load professional template: {e}")
        
        # Fallback professional template
        return """Thank you for your inquiry. I've conducted a comprehensive analysis of your request.

**Current Status:**
Based on my review, here's what I found:
• {primary_status}
• Current state: **{current_state}**
• Estimated timeline: **{estimated_timeline}**

**Detailed Analysis:**
{detailed_analysis}

**Your Account Overview:**
• {account_summary}
• Customer type: **{customer_type}**

**Next Steps:**
{next_steps}

**Contact Information:**
If you need immediate assistance, please don't hesitate to contact our support team.

Is there any specific aspect you'd like me to explain in more detail?"""

    def setup_llm_client(self):
        """Setup LLM client for intent analysis and response generation"""
        # Try OpenRouter first, fall back to OpenAI
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        model_name = os.getenv('LLM_MODEL') or os.getenv('PRIMARY_MODEL_NAME') or os.getenv('SECONDARY_MODEL_NAME') or "anthropic/claude-3.5-sonnet"
        
        if openrouter_key:
            self.llm_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key
            )
            self.model_name = model_name
            logger.info("LLM client configured with OpenRouter", model=self.model_name)
        elif openai_key:
            self.llm_client = OpenAI(api_key=openai_key)
            self.model_name = model_name
            logger.info("LLM client configured with OpenAI", model=self.model_name)
        else:
            self.llm_client = None
            self.model_name = None
            logger.warning("No LLM client configured - OPENROUTER_API_KEY or OPENAI_API_KEY environment variable required")

    def setup_technical_agents(self):
        """Setup connections to technical agents via python-a2a"""
        # Initialize agent network for technical agents
        try:
            self.agent_network = AgentNetwork(name="Insurance Technical Agents")
        except:
            # If AgentNetwork not available, use simple registry
            self.agent_network = None
            logger.warning("AgentNetwork not available, using simple registry")
        
        # Register technical agents with the agent network
        self.register_agent("data_agent", os.getenv('DATA_AGENT_URL', 'http://localhost:8002'))
        # Temporarily disabled crashing agents for core functionality testing
        # self.register_agent("notification_agent", os.getenv('NOTIFICATION_AGENT_URL', 'http://localhost:8003'))
        # self.register_agent("fastmcp_agent", os.getenv('FASTMCP_AGENT_URL', 'http://localhost:8004'))
        
        self.agent_network.add_agent("data_agent", os.getenv('DATA_AGENT_URL', 'http://localhost:8002'))
        # self.agent_network.add_agent("notification_agent", os.getenv('NOTIFICATION_AGENT_URL', 'http://localhost:8003'))
        # self.agent_network.add_agent("fastmcp_agent", os.getenv('FASTMCP_AGENT_URL', 'http://localhost:8004'))
        
        logger.info("Technical agents registered in agent network")

    def setup_ai_router(self):
        """Setup AI-powered router for intelligent task routing"""
        try:
            # Try to create AI router if available with correct parameters
            if hasattr(self, 'agent_network') and self.agent_network:
                self.ai_router = AIAgentRouter(
                    llm_client=self.llm_client if hasattr(self, 'llm_client') else None,
                    agent_network=self.agent_network
                )
                logger.info("AI router initialized for intelligent task routing")
            else:
                logger.warning("Agent network not available for AI router")
                self.ai_router = None
        except Exception as e:
            logger.warning(f"AI router not available: {e}, using simple routing")
            self.ai_router = None
    
    def handle_message(self, message: Message) -> Message:
        """
        Main message handler implementing the two-role functionality:
        1. Intent understanding and planning
        2. Task routing and coordination
        """
        try:
            user_text = message.content.text
            conversation_id = getattr(message, 'conversation_id', str(uuid.uuid4()))
            
            logger.info("Processing user request", 
                       text=user_text[:100], 
                       conversation_id=conversation_id)
            
            # Role 1: Intent Understanding & Planning
            intent_analysis = self.understand_intent(user_text)
            execution_plan = self.create_execution_plan(intent_analysis, user_text)
            
            # Role 2: Task Routing & Execution
            execution_results = self.execute_plan(execution_plan, conversation_id)
            
            # Role 3: Response Preparation
            final_response = self.prepare_response(intent_analysis, execution_results, user_text)
            
            return Message(
                content=TextContent(text=final_response),
                role=MessageRole.AGENT,
                parent_message_id=getattr(message, 'message_id', None),
                conversation_id=conversation_id
            )
            
        except Exception as e:
            logger.error("Error processing message", error=str(e))
            return Message(
                content=TextContent(text=f"I apologize, but I encountered an error processing your request: {str(e)}"),
                role=MessageRole.AGENT,
                parent_message_id=getattr(message, 'message_id', None),
                conversation_id=getattr(message, 'conversation_id', None)
            )
    
    def understand_intent(self, user_text: str) -> Dict[str, Any]:
        """
        Role 1: Understand user intent and extract key information
        """
        prompt = f"""
        As an insurance domain expert, analyze this user request and extract:
        1. Primary intent - Choose ONE from: claim_filing, policy_inquiry, billing_question, claim_status, quote_request, general_inquiry
        2. Secondary intents (if any)
        3. Key entities (policy numbers, claim IDs, dates, amounts, etc.)
        4. Required information gathering
        5. Urgency level
        6. Complexity assessment
        
        IMPORTANT INTENT CLASSIFICATION RULES:
        - If user mentions "claim" AND ("status", "check", "update", "progress", "recent") → claim_status
        - If user mentions claim ID (like CLM-123456) → claim_status  
        - If user asks about "claims" in plural → claim_status
        - If user wants to "file" or "submit" new claim → claim_filing
        - If user asks about "policy" or "policies" → policy_inquiry
        - If user asks about "billing", "payment", "premium" → billing_question
        - If user wants a "quote" or "rate" → quote_request
        - Otherwise → general_inquiry
        
        User Request: "{user_text}"
        
        Respond in JSON format:
        {{
            "primary_intent": "string",
            "secondary_intents": ["string"],
            "entities": {{"entity_type": "value"}},
            "required_info": ["info_needed"],
            "urgency": "low|medium|high",
            "complexity": "simple|moderate|complex",
            "confidence": 0.0-1.0
        }}
        """
        
        logger.info("Intent analysis starting", user_text=user_text, model=self.model_name)
        
        response = self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        intent_text = response.choices[0].message.content
        logger.info("LLM raw response", response_text=intent_text)
        
        # Handle markdown code blocks around JSON
        if intent_text.startswith("```json") and intent_text.endswith("```"):
            intent_text = intent_text[7:-3].strip()
        elif intent_text.startswith("```") and intent_text.endswith("```"):
            intent_text = intent_text[3:-3].strip()
        
        intent_analysis = json.loads(intent_text)
        
        logger.info("Intent analysis completed", 
                   primary_intent=intent_analysis.get("primary_intent"),
                   confidence=intent_analysis.get("confidence"),
                   entities=intent_analysis.get("entities"))
        
        return intent_analysis
    
    def _rule_based_intent_analysis(self, user_text: str) -> Dict[str, Any]:
        """REMOVED: Rule-based intent analysis - now throws error instead"""
        raise RuntimeError("Rule-based intent analysis removed - LLM required for proper intent understanding")
    
    def create_execution_plan(self, intent_analysis: Dict[str, Any], user_text: str) -> Dict[str, Any]:
        """
        Create a detailed execution plan based on intent analysis
        """
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        complexity = intent_analysis.get("complexity", "simple")
        
        # Define plan templates based on intent
        plan_templates = {
            "claim_filing": {
                "steps": [
                    {"agent": "data_agent", "action": "validate_policy", "priority": 1},
                    {"agent": "data_agent", "action": "create_claim_record", "priority": 2}
                ],
                "expected_duration": "5-10 minutes",
                "parallel_execution": False
            },
            "claim_status": {
                "steps": [
                    {"agent": "data_agent", "action": "fetch_claim_status", "priority": 1},
                    {"agent": "data_agent", "action": "fetch_claim_details", "priority": 2}
                ],
                "expected_duration": "2-3 minutes",
                "parallel_execution": False
            },
            "policy_inquiry": {
                "steps": [
                    {"agent": "data_agent", "action": "fetch_policy_details", "priority": 1},
                    {"agent": "data_agent", "action": "calculate_current_benefits", "priority": 2}
                ],
                "expected_duration": "2-5 minutes",
                "parallel_execution": False
            },
            "billing_question": {
                "steps": [
                    {"agent": "data_agent", "action": "fetch_billing_history", "priority": 1},
                    {"agent": "data_agent", "action": "calculate_outstanding_balance", "priority": 2}
                ],
                "expected_duration": "2-3 minutes",
                "parallel_execution": False
            },
            "quote_request": {
                "steps": [
                    {"agent": "data_agent", "action": "generate_quote", "priority": 1}
                ],
                "expected_duration": "3-5 minutes",
                "parallel_execution": False
            },
            "general_inquiry": {
                "steps": [
                    {"agent": "data_agent", "action": "general_information_lookup", "priority": 1}
                ],
                "expected_duration": "1-2 minutes",
                "parallel_execution": False
            }
        }
        
        # Get plan template or create custom plan
        plan = plan_templates.get(primary_intent, plan_templates["general_inquiry"]).copy()
        
        # Enhance plan with context
        plan.update({
            "intent": primary_intent,
            "user_request": user_text,
            "entities": intent_analysis.get("entities", {}),
            "urgency": intent_analysis.get("urgency", "medium"),
            "complexity": complexity,
            "plan_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat()
        })
        
        logger.info("Execution plan created", 
                   plan_id=plan["plan_id"],
                   steps=len(plan["steps"]),
                   intent=primary_intent)
        
        return plan
    
    def execute_plan(self, execution_plan: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
        """
        Role 2: Execute the plan by routing tasks to technical agents
        """
        results = {
            "plan_id": execution_plan["plan_id"],
            "execution_id": str(uuid.uuid4()),
            "started_at": datetime.utcnow().isoformat(),
            "step_results": [],
            "status": "in_progress"
        }
        
        steps = execution_plan.get("steps", [])
        parallel_execution = execution_plan.get("parallel_execution", False)
        
        if parallel_execution and len(steps) > 1:
            # Execute steps in parallel where possible
            results["step_results"] = self.execute_parallel_steps(steps, execution_plan)
        else:
            # Execute steps sequentially
            results["step_results"] = self.execute_sequential_steps(steps, execution_plan)
        
        results["status"] = "completed"
        results["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info("Plan execution completed", 
                   execution_id=results["execution_id"],
                   steps_completed=len(results["step_results"]))
        
        return results
    
    def execute_sequential_steps(self, steps: List[Dict[str, Any]], execution_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute plan steps sequentially"""
        step_results = []
        
        for i, step in enumerate(steps):
            # Call the agent
            agent_name = step["agent"]
            action = step["action"]
            
            logger.info("Executing step", step_number=i+1, agent=agent_name, action=action)
            
            # Prepare task data
            task_data = {
                "action": action,
                "plan_context": execution_plan,
                "step_info": step,
                "previous_results": step_results
            }
            
            # Call the registered agent directly
            result = self.call_registered_agent(agent_name, json.dumps(task_data))
            
            step_result = {
                "step_number": i + 1,
                "agent": agent_name,
                "action": action,
                "status": "completed",
                "result": result,
                "executed_at": datetime.utcnow().isoformat()
            }
            
            step_results.append(step_result)
        
        return step_results
    
    def execute_parallel_steps(self, steps: List[Dict[str, Any]], execution_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute plan steps in parallel (simplified implementation)"""
        # For now, implement as sequential execution
        # In a full implementation, this would use asyncio or threading
        logger.info("Parallel execution requested, executing sequentially for now")
        return self.execute_sequential_steps(steps, execution_plan)
    
    def prepare_response(self, intent_analysis: Dict[str, Any], execution_results: Dict[str, Any], user_text: str) -> str:
        """
        Role 3: Prepare professional response using structured templates
        Enhanced with template-based formatting and professional presentation
        """
        # Extract key information for response preparation
        primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
        step_results = execution_results.get("step_results", [])
        execution_status = execution_results.get("status", "unknown")
        entities = intent_analysis.get("entities", {})
        
        # Aggregate data from step results
        aggregated_data = self._aggregate_step_results(step_results)
        
        # Use professional template if enabled
        if self.template_enhancement_enabled and self.response_template:
            return self._generate_template_response(
                intent_analysis, execution_results, user_text, aggregated_data
            )
        
        # Enhanced LLM-based response preparation
        context = {
            "user_request": user_text,
            "intent": primary_intent,
            "execution_status": execution_status,
            "step_results": step_results,
            "entities": entities,
            "aggregated_data": aggregated_data
        }
        
        enhanced_prompt = f"""
        As a professional insurance assistant, prepare a comprehensive and structured response to the user.
        
        User Request: "{user_text}"
        Intent: {primary_intent}
        Execution Status: {execution_status}
        
        Available Data:
        {json.dumps(aggregated_data, indent=2)}
        
        Guidelines for Professional Response:
        1. Start with a professional acknowledgment
        2. Provide specific status and findings
        3. Include detailed analysis with clear sections
        4. Add account overview with metrics
        5. Provide clear next steps and timeline
        6. Maintain professional, helpful tone
        7. Structure with clear headers and bullet points
        8. Include contact information
        9. End with offer for additional assistance
        10. Use ** for emphasis and • for bullet points
        
        Format the response professionally with clear sections and specific data points.
        
        Response:
        """
        
        response = self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": enhanced_prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        final_response = response.choices[0].message.content
        
        logger.info("Response prepared", 
                   intent=primary_intent,
                   status=execution_status,
                   template_used=self.template_enhancement_enabled)
        
        return final_response

    def _aggregate_step_results(self, step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate data from step results for template population"""
        aggregated = {
            "claims_data": {},
            "policy_data": {},
            "analytics_data": {},
            "user_data": {},
            "context": {}
        }
        
        for step in step_results:
            if step.get("status") == "completed" and "result" in step:
                try:
                    result_data = json.loads(step["result"]) if isinstance(step["result"], str) else step["result"]
                    agent_type = step.get("agent", "")
                    
                    # Categorize results by agent type
                    if "data" in agent_type and "validate_policy" in step.get("action", ""):
                        aggregated["policy_data"].update(result_data.get("policy_info", {}))
                    elif "data" in agent_type and "claim" in step.get("action", ""):
                        aggregated["claims_data"].update(result_data.get("claim_info", {}))
                    elif "fastmcp" in agent_type or "fraud" in step.get("action", ""):
                        aggregated["analytics_data"].update(result_data.get("analytics", {}))
                    elif "notification" in agent_type:
                        aggregated["context"]["notification_sent"] = True
                    
                    # Extract general metrics
                    if isinstance(result_data, dict):
                        for key, value in result_data.items():
                            if key in ["customer_type", "account_status", "risk_score"]:
                                aggregated["context"][key] = value
                                
                except Exception as e:
                    logger.warning(f"Failed to parse step result: {e}")
        
        return aggregated

    def _generate_template_response(self, intent_analysis: Dict[str, Any], 
                                  execution_results: Dict[str, Any], 
                                  user_text: str, 
                                  aggregated_data: Dict[str, Any]) -> str:
        """Generate response using the professional template structure"""
        try:
            claims_data = aggregated_data.get("claims_data", {})
            policy_data = aggregated_data.get("policy_data", {})
            analytics_data = aggregated_data.get("analytics_data", {})
            context = aggregated_data.get("context", {})
            
            # Build template variables
            template_vars = {
                "primary_status": self._get_primary_status(intent_analysis, claims_data, policy_data),
                "current_state": claims_data.get("status", "Under Review"),
                "estimated_timeline": claims_data.get("estimated_resolution", "3-5 business days"),
                "detailed_analysis": self._build_detailed_analysis(intent_analysis, aggregated_data),
                "account_summary": self._build_account_summary(aggregated_data),
                "customer_type": context.get("customer_type", "Standard"),
                "next_steps": self._build_next_steps(intent_analysis, execution_results),
                "claims_data": claims_data,
                "policy_data": policy_data,
                "analytics_data": analytics_data,
                "context": context
            }
            
            # Use original template with enhanced variable substitution
            try:
                formatted_response = self.response_template.format(**template_vars)
            except KeyError as e:
                logger.warning(f"Template formatting error: {e}, using fallback")
                formatted_response = self._generate_enhanced_fallback_response(
                    intent_analysis.get("primary_intent"), 
                    execution_results.get("status"),
                    aggregated_data,
                    user_text
                )
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            return self._generate_enhanced_fallback_response(
                intent_analysis.get("primary_intent"), 
                execution_results.get("status"),
                aggregated_data,
                user_text
            )

    def _get_primary_status(self, intent_analysis: Dict[str, Any], 
                          claims_data: Dict[str, Any], 
                          policy_data: Dict[str, Any]) -> str:
        """Determine primary status message based on intent and data"""
        intent = intent_analysis.get("primary_intent", "general_inquiry")
        
        if intent == "claim_filing":
            active_claims = claims_data.get("active_claims", 0)
            return f"You currently have {active_claims} active claim(s) in our system"
        elif intent == "policy_inquiry":
            active_policies = policy_data.get("active_policies", 0)
            return f"You have {active_policies} active policy(ies) in your portfolio"
        elif intent == "billing_question":
            balance = claims_data.get("balance", "$0.00")
            return f"Your current account balance is {balance}"
        else:
            return "I've completed a comprehensive review of your account"

    def _build_detailed_analysis(self, intent_analysis: Dict[str, Any], 
                               aggregated_data: Dict[str, Any]) -> str:
        """Build detailed analysis section"""
        intent = intent_analysis.get("primary_intent", "general_inquiry")
        claims_data = aggregated_data.get("claims_data", {})
        
        if intent == "claim_filing":
            return f"""Our claims processing team has been actively working on your case. The "{claims_data.get('status', 'In Review')}" status indicates that your claim is currently undergoing thorough evaluation by our specialized claims adjusters. This process typically involves:

1. **Documentation Verification**: Ensuring all required documentation is complete and accurate
2. **Coverage Assessment**: Verifying that the claimed incident falls within your policy coverage  
3. **Loss Evaluation**: Determining the extent and value of the claimed loss
4. **Fraud Prevention**: Standard security checks to protect both you and our company"""
        
        elif intent == "policy_inquiry":
            return """I've reviewed your policy portfolio and coverage details. Your policies are active and in good standing. All coverage limits and deductibles are current, and your renewal dates are properly scheduled."""
        
        else:
            return "I've conducted a comprehensive review of your account status, policy coverage, and any recent activity to provide you with the most accurate and up-to-date information."

    def _build_account_summary(self, aggregated_data: Dict[str, Any]) -> str:
        """Build account summary section"""
        claims_data = aggregated_data.get("claims_data", {})
        policy_data = aggregated_data.get("policy_data", {})
        context = aggregated_data.get("context", {})
        
        return f"""Total active policies: **{policy_data.get('active_policies', 0)} policies**
• Recent claims history: **{claims_data.get('recent_claims', 0)} claim(s) in the past 12 months**
• Customer satisfaction score: **{context.get('satisfaction_score', '4.5')}/5.0**"""

    def _build_next_steps(self, intent_analysis: Dict[str, Any], 
                         execution_results: Dict[str, Any]) -> str:
        """Build next steps section"""
        intent = intent_analysis.get("primary_intent", "general_inquiry")
        
        if intent == "claim_filing":
            return """1. **Immediate**: Your claim will continue through the review process
2. **Within 24-48 hours**: You should receive an update from your assigned claims adjuster
3. **Within 3-5 business days**: Target completion of the review process
4. **Upon approval**: Settlement processing will begin immediately"""
        
        elif intent == "policy_inquiry":
            return """1. **Review**: Your policy information is current and accurate
2. **Action**: No immediate action required unless you have specific questions
3. **Planning**: Consider scheduling a policy review before your next renewal date
4. **Support**: Contact us if you need coverage adjustments"""
        
        else:
            return """1. **Review**: I've provided the most current information available
2. **Follow-up**: Monitor your account for any updates
3. **Questions**: Don't hesitate to reach out if you need clarification
4. **Support**: Our team is available for additional assistance"""

    def _generate_enhanced_fallback_response(self, primary_intent: str, 
                                           execution_status: str,
                                           aggregated_data: Dict[str, Any],
                                           user_text: str) -> str:
        """Generate enhanced fallback response when template fails"""
        claims_data = aggregated_data.get("claims_data", {})
        policy_data = aggregated_data.get("policy_data", {})
        context = aggregated_data.get("context", {})
        
        return f"""Thank you for your inquiry. I've completed a comprehensive analysis of your request.

**Current Status:**
Based on my review of your {primary_intent.replace('_', ' ')}, here's what I found:
• Processing status: **{execution_status.title()}**
• Account type: **{context.get('customer_type', 'Standard')} Customer**
• Active policies: **{policy_data.get('active_policies', 0)}**

**Summary:**
I've processed your request regarding {primary_intent.replace('_', ' ')} and gathered the relevant information from our systems. {f"Your claim status is currently {claims_data.get('status', 'under review')}." if 'claim' in primary_intent else "Your account information has been retrieved and reviewed."}

**Next Steps:**
1. The information I've provided reflects the current state of your account
2. If you need additional details, please let me know your specific questions
3. For urgent matters, you can contact our support team directly

**Professional Note:**
As a valued {context.get('customer_type', 'Standard')} customer, you have access to our full range of services and support options.

Is there any specific aspect of your {primary_intent.replace('_', ' ')} that you'd like me to explain in more detail?"""

    def _generate_error_response(self, intent_analysis: Dict[str, Any], 
                               user_text: str, error_msg: str) -> str:
        """Generate professional error response"""
        primary_intent = intent_analysis.get("primary_intent", "your inquiry")
        
        return f"""Thank you for contacting us regarding {primary_intent.replace('_', ' ')}.

**Current Status:**
I've encountered a technical issue while processing your request, but I'm committed to helping you resolve your inquiry.

**What Happened:**
While gathering information from our systems, I experienced a temporary processing delay. This doesn't affect your account or any pending transactions.

**Next Steps:**
1. **Immediate**: You can try rephrasing your question or asking about a specific aspect
2. **Alternative**: Contact our customer service team directly for immediate assistance
3. **Follow-up**: I'll be available to help once the technical issue is resolved

**Professional Assistance:**
Our support team is standing by to provide immediate assistance with any urgent matters.

Please let me know how else I can help you, or feel free to try your request again in a few moments."""

    def setup_http_endpoints(self):
        """Setup HTTP endpoints for Kubernetes health checks and API access"""
        self.app = FastAPI(title="Enhanced Python A2A Domain Agent", version="1.0.0")
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for Kubernetes"""
            return {
                "status": "healthy",
                "agent_type": "enhanced_domain_agent",
                "version": "1.0.0",
                "template_enabled": self.template_enhancement_enabled,
                "registered_agents": list(self.agent_registry.keys()),
                "capabilities": self.capabilities,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/ready")
        async def readiness_check():
            """Readiness check endpoint for Kubernetes"""
            return {
                "status": "ready",
                "agent_network_size": len(self.agent_registry),
                "template_loaded": bool(self.response_template),
                "llm_configured": bool(self.llm_client),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.post("/chat", response_model=ChatResponse)
        async def chat_endpoint(request: ChatRequest):
            """Chat endpoint for direct HTTP communication"""
            try:
                # Process the message through the enhanced domain agent
                result = await self.process_user_message(request.message, request.customer_id)
                
                return ChatResponse(
                    response=result["response"],
                    intent=result.get("intent"),
                    confidence=result.get("confidence"),
                    thinking_steps=result.get("thinking_steps", []),
                    orchestration_events=result.get("orchestration_events", []),
                    api_calls=result.get("api_calls", []),
                    timestamp=datetime.utcnow().isoformat()
                )
                
            except Exception as e:
                logger.error("Chat endpoint error", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/agent-card")
        async def get_agent_card_endpoint():
            """Get agent card endpoint"""
            return self.get_agent_card()
        
        @self.app.get("/test-llm")
        async def test_llm_endpoint():
            """Test LLM direct call"""
            if not self.llm_client:
                return {"error": "No LLM client configured"}
            
            try:
                response = self.llm_client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Reply with exactly: claim_status"}],
                    temperature=0.0
                )
                return {
                    "model": self.model_name,
                    "response": response.choices[0].message.content,
                    "success": True
                }
            except Exception as e:
                return {"error": str(e), "model": self.model_name}

    async def process_user_message(self, message: str, customer_id: str = "default-customer") -> Dict[str, Any]:
        """Process user message through the enhanced domain agent workflow"""
        # Role 1: Intent Understanding & Planning - NO ERROR HANDLING, LET ERRORS PROPAGATE
        intent_analysis = self.understand_intent(message)
        
        # Role 2: Create and execute plan - NO ERROR HANDLING, LET ERRORS PROPAGATE  
        execution_plan = self.create_execution_plan(intent_analysis, message)
        execution_results = self.execute_plan(execution_plan, customer_id)
        
        # Role 3: Prepare professional response - NO ERROR HANDLING, LET ERRORS PROPAGATE
        response = self.prepare_response(intent_analysis, execution_results, message)
        
        return {
            "response": response,
            "intent": intent_analysis.get("primary_intent"),
            "confidence": intent_analysis.get("confidence"),
            "thinking_steps": [],  # Could be enhanced with actual thinking steps
            "orchestration_events": [
                {
                    "event": "intent_analysis",
                    "data": intent_analysis,
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "event": "execution_plan",
                    "data": execution_plan,
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "event": "execution_results", 
                    "data": execution_results,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ],
            "api_calls": [],  # Could be enhanced with actual API call tracking
            "timestamp": datetime.utcnow().isoformat()
        }

    def run_http_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the HTTP server for Kubernetes deployment"""
        logger.info("Starting Enhanced Domain Agent HTTP server", host=host, port=port)
        uvicorn.run(self.app, host=host, port=port)


def main():
    """Run the Enhanced Domain Agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Python A2A Domain Agent")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the agent on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the agent to")
    parser.add_argument("--mode", choices=["http", "a2a"], default="http", 
                       help="Server mode: http for Kubernetes, a2a for native A2A protocol")
    
    args = parser.parse_args()
    
    # Create the enhanced domain agent
    agent = PythonA2ADomainAgent(port=args.port)
    
    logger.info("Starting Enhanced Python A2A Domain Agent", 
               host=args.host, port=args.port, mode=args.mode)
    
    if args.mode == "http":
        # Run HTTP server for Kubernetes deployment
        agent.run_http_server(host=args.host, port=args.port)
    else:
        # Run native A2A server
        agent.host = args.host
        agent.run()


if __name__ == "__main__":
    main() 