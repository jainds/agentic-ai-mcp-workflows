#!/usr/bin/env python3
"""
Domain Agent - Simple and Readable
Conversational insurance agent that helps customers and communicates with Technical Agent
"""

import sys
import re
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

import structlog
import openai
import yaml
from dotenv import load_dotenv
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState, A2AClient

from prompt_loader import PromptLoader

# Load environment variables
load_dotenv()

# Setup logging
structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@agent(
    name="Insurance Domain Agent",
    description="Conversational insurance agent that helps customers with policy inquiries and claims",
    version="2.0.0"
)
class DomainAgent(A2AServer):
    """Simple Domain Agent that talks to customers and Technical Agent"""
    
    def __init__(self):
        super().__init__()
        
        # Load prompts from YAML
        self.prompts = PromptLoader()
        
        # Technical Agent setup
        self.technical_agent_url = os.getenv("TECHNICAL_AGENT_URL", "http://localhost:8002")
        self.technical_client = None
        
        # OpenAI setup
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("OpenAI client initialized")
        else:
            logger.warning("No OpenAI API key - using rule-based responses only")
        
        logger.info("Domain Agent initialized")
        logger.info(f"Will connect to Technical Agent at: {self.technical_agent_url}")
    
    def get_technical_client(self):
        """Get Technical Agent client (create if needed)"""
        if self.technical_client is None:
            self.technical_client = A2AClient(self.technical_agent_url)
        return self.technical_client
    
    def analyze_customer_intent(self, customer_message: str) -> Dict[str, Any]:
        """Figure out what the customer wants"""
        
        # Try LLM first if available
        if self.openai_client:
            try:
                return self._analyze_with_llm(customer_message)
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}, using rules")
        
        # Fallback to rule-based analysis
        return self._analyze_with_rules(customer_message)
    
    def _analyze_with_llm(self, customer_message: str) -> Dict[str, Any]:
        """Use LLM to understand customer intent"""
        prompt = self.prompts.get_intent_analysis_prompt(customer_message)
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300
        )
        
        result_text = response.choices[0].message.content.strip()
        logger.info(f"LLM analysis: {result_text}")
        
        try:
            # Try to parse JSON response
            result = json.loads(result_text)
            result["method"] = "llm"
            
            # Clean up null values
            if result.get("customer_id") in ["null", "none", ""]:
                result["customer_id"] = None
                
            return result
            
        except json.JSONDecodeError:
            # Try to extract JSON from wrapped response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group(0))
                    result["method"] = "llm"
                    if result.get("customer_id") in ["null", "none", ""]:
                        result["customer_id"] = None
                    return result
                except json.JSONDecodeError:
                    pass
            
            logger.warning("Could not parse LLM response, using rules")
            return self._analyze_with_rules(customer_message)
    
    def _analyze_with_rules(self, customer_message: str) -> Dict[str, Any]:
        """Use simple rules to understand customer intent"""
        text_lower = customer_message.lower()
        
        # Look for customer ID patterns
        customer_id = None
        original_mention = None
        
        patterns = [
            r'user_\w+',                                    # user_003
            r'CUST-\d+',                                    # CUST-001
            r'cust-\d+',                                    # cust-001
            r'customer[_\s-]+([A-Za-z0-9_-]+)',            # customer CUST-001
            r'user[_\s]+([A-Za-z0-9_-]+)',                 # user 003
            r'client[_\s]+([A-Za-z0-9_-]+)',               # client 001
        ]
        
        for pattern in patterns:
            match = re.search(pattern, customer_message, re.IGNORECASE)
            if match:
                if '(' in pattern:  # pattern with group
                    customer_id = match.group(1)
                else:
                    customer_id = match.group(0)
                original_mention = match.group(0)
                break
        
        # Determine intent
        intent = "general_inquiry"
        
        if any(word in text_lower for word in ["policy", "policies", "coverage", "premium"]):
            intent = "policy_inquiry"
        elif any(word in text_lower for word in ["claim", "claims", "status", "file"]):
            intent = "claim_status"
        elif customer_id and any(word in text_lower for word in ["tell", "show", "get", "my"]):
            intent = "policy_inquiry"
        
        confidence = 0.7 if customer_id else 0.5
        
        return {
            "primary_intent": intent,
            "customer_id": customer_id,
            "original_customer_mention": original_mention,
            "confidence": confidence,
            "reasoning": f"Rule-based analysis found: {original_mention}" if original_mention else "Rule-based analysis",
            "method": "rules"
        }
    
    def plan_response(self, customer_message: str, intent_analysis: Dict[str, Any], 
                     session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Figure out how to respond to the customer"""
        
        intent = intent_analysis.get("primary_intent")
        customer_id = intent_analysis.get("customer_id")
        
        # Check session for customer info (priority over parsing)
        session_customer_id = session_data.get("customer_id")
        if session_customer_id:
            customer_id = session_customer_id
            intent_analysis["customer_id"] = session_customer_id
            intent_analysis["method"] = "session"
            intent_analysis["confidence"] = 1.0
        
        plan = {
            "action": "ask_technical_agent",
            "customer_id": customer_id,
            "intent": intent,
            "technical_request": None,
            "response_strategy": intent
        }
        
        # Plan what to ask Technical Agent
        if intent == "policy_inquiry" and customer_id:
            plan["technical_request"] = f"Get policies for customer {customer_id}"
        elif intent == "claim_status" and customer_id:
            plan["technical_request"] = f"Get claim status for customer {customer_id}"
        elif intent == "policy_inquiry" and not customer_id:
            plan["action"] = "request_customer_id"
        elif intent == "claim_status" and not customer_id:
            plan["action"] = "request_customer_id"
        else:
            plan["action"] = "general_help"
            plan["technical_request"] = "General insurance help"
        
        return plan
    
    def format_customer_response(self, intent: str, technical_response: str, 
                               customer_id: Optional[str] = None, **context) -> str:
        """Format a nice response for the customer"""
        
        # Get base template from YAML
        template = self.prompts.get_response_template(intent)
        
        if template:
            # Use template from YAML
            response = template.format(technical_response=technical_response)
        else:
            # Fallback response
            response = f"Thank you for your inquiry.\n\n{technical_response}\n\nHow else can I help you?"
        
        # Add context notes if needed
        if context.get("method") == "session" and context.get("customer_name"):
            session_note = self.prompts.get_context_message("session_context_note")
            if session_note:
                response += "\n\n" + session_note.format(customer_name=context["customer_name"])
        
        return response
    
    def handle_customer_conversation(self, customer_message: str, session_data: Dict[str, Any] = None) -> str:
        """Main conversation handler - simple and clear"""
        
        if session_data is None:
            session_data = {}
        
        try:
            # Step 1: Understand what customer wants
            intent_analysis = self.analyze_customer_intent(customer_message)
            logger.info(f"Customer intent: {intent_analysis}")
            
            # Step 2: Plan response strategy
            response_plan = self.plan_response(customer_message, intent_analysis, session_data)
            logger.info(f"Response plan: {response_plan}")
            
            # Step 3: Get information from Technical Agent if needed
            technical_response = ""
            if response_plan["action"] == "ask_technical_agent" and response_plan["technical_request"]:
                try:
                    technical_client = self.get_technical_client()
                    technical_response = technical_client.ask(response_plan["technical_request"])
                    logger.info(f"Technical Agent response: {technical_response}")
                except Exception as e:
                    logger.error(f"Technical Agent error: {e}")
                    technical_response = "I'm having trouble accessing your account information right now."
            
            elif response_plan["action"] == "request_customer_id":
                technical_response = self.prompts.get_error_response("missing_customer_id").format(
                    additional_context="To provide specific information, I need your customer ID."
                )
            
            elif response_plan["action"] == "general_help":
                technical_response = "I'm here to help with your insurance questions."
            
            # Step 4: Format nice response for customer
            customer_context = {
                "method": intent_analysis.get("method"),
                "customer_name": session_data.get("customer_data", {}).get("name")
            }
            
            final_response = self.format_customer_response(
                response_plan["response_strategy"],
                technical_response,
                response_plan["customer_id"],
                **customer_context
            )
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error in conversation: {e}")
            error_response = self.prompts.get_error_response("parsing_error")
            return error_response.format(error_message=str(e))
    
    @skill(
        name="Customer Conversation",
        description="Handle customer conversations about insurance",
        tags=["conversation", "customer", "insurance"]
    )
    def customer_conversation_skill(self, customer_message: str) -> str:
        """A2A skill for customer conversations"""
        return self.handle_customer_conversation(customer_message)
    
    def handle_task(self, task):
        """Handle A2A tasks from UI"""
        logger.info(f"Received task: {task}")
        
        try:
            # Extract message
            message_data = task.message or {}
            content = message_data.get("content", {})
            
            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)
            
            # Extract session data
            session_data = getattr(task, 'session', {}) or {}
            
            # Handle conversation
            response = self.handle_customer_conversation(text, session_data)
            
            # Set response
            task.artifacts = [{
                "parts": [{"type": "text", "text": response}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            logger.error(f"Task error: {e}")
            error_response = self.prompts.get_error_response("parsing_error")
            task.artifacts = [{
                "parts": [{"type": "text", "text": error_response.format(error_message=str(e))}]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task


if __name__ == "__main__":
    port = 8003
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    logger.info(f"Starting Simple Domain Agent on port {port}")
    
    agent = DomainAgent()
    run_server(agent, port=port) 