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
    name="Domain Agent", 
    description="Conversational insurance agent that helps customers and communicates with Technical Agent",
    version="2.0.0"
)
class DomainAgent(A2AServer):
    """Simple Domain Agent that talks to customers and Technical Agent"""
    
    def __init__(self):
        super().__init__()
        
        # Load prompts
        self.prompts = PromptLoader()
        
        # Technical Agent setup
        self.technical_agent_url = os.getenv("TECHNICAL_AGENT_URL", "http://insurance-ai-poc-technical-agent:8002")
        self.technical_client = None
        
        # OpenAI setup (configured for OpenRouter)
        self.openai_client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                # Use OpenRouter if the key starts with sk-or-
                if api_key.startswith("sk-or-"):
                    self.openai_client = openai.OpenAI(
                        api_key=api_key,
                        base_url="https://openrouter.ai/api/v1"
                    )
                    logger.info("OpenRouter client initialized")
                else:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"LLM client initialization failed: {e}")
        else:
            logger.warning("No OpenAI API key found - using rule-based responses only")
        
        logger.info("Domain Agent initialized")
        logger.info(f"Will connect to Technical Agent at: {self.technical_agent_url}")
    
    def get_technical_client(self):
        """Get Technical Agent client (create if needed)"""
        if not self.technical_client:
            try:
                self.technical_client = A2AClient(self.technical_agent_url)
                logger.info("Technical Agent client created")
            except Exception as e:
                logger.error(f"Failed to create Technical Agent client: {e}")
                self.technical_client = None
        return self.technical_client
    
    def analyze_customer_intent(self, user_text: str) -> Dict[str, Any]:
        """Analyze customer intent and extract information"""
        
        # Try LLM analysis first if available
        if self.openai_client:
            return self._analyze_with_llm(user_text)
        else:
            return self._analyze_with_rules(user_text)
    
    def _analyze_with_llm(self, user_text: str) -> Dict[str, Any]:
        """Use LLM to understand customer intent"""
        try:
            prompt = self.prompts.get_intent_analysis_prompt(user_text)
            
            response = self.openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"🔥 DOMAIN AGENT: LLM raw response: {result_text}")
            
            # Try to parse JSON, handling common formatting issues
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if result_text.startswith("```json") and result_text.endswith("```"):
                    json_content = result_text[7:-3].strip()
                    result = json.loads(json_content)
                elif result_text.startswith("```") and result_text.endswith("```"):
                    json_content = result_text[3:-3].strip()
                    result = json.loads(json_content)
                else:
                    # Try to find JSON in the response
                    import re
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(0)
                        result = json.loads(json_content)
                    else:
                        raise ValueError(f"No valid JSON found in LLM response: {result_text}")
            
            logger.info(f"LLM intent analysis: {result}")
            return result
            
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}, falling back to rules")
            return self._analyze_with_rules(user_text)
    
    def _analyze_with_rules(self, user_text: str) -> Dict[str, Any]:
        """Use simple rules to understand customer intent"""
        text_lower = user_text.lower()
        
        # Extract customer ID
        customer_id = None
        patterns = [
            r'cust-\d+',
            r'user_\d+', 
            r'customer\s+([a-zA-Z0-9_-]+)',
            r'for\s+customer\s+([a-zA-Z0-9_-]+)',
            r'customer\s+id\s+([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                if match.groups():
                    customer_id = match.group(1)
                else:
                    customer_id = match.group(0)
                break
        
        # Determine intent based on keywords
        intent = "general_inquiry"  # default
        
        # Coverage/total amount queries
        if any(word in text_lower for word in ["total coverage", "coverage amount", "total amount", "how much coverage"]):
            intent = "coverage_inquiry"
        # Payment queries (including premium and billing)
        elif any(word in text_lower for word in ["payment", "due", "billing", "pay", "premium", "premiums", "deductible", "deductibles"]):
            intent = "payment_inquiry"
        # Agent contact queries
        elif any(word in text_lower for word in ["agent", "contact", "who is my", "representative"]):
            intent = "agent_contact"
        # Policy type queries  
        elif any(word in text_lower for word in ["types of policies", "what policies", "policy types"]):
            intent = "policy_inquiry"
        # General policy queries
        elif any(word in text_lower for word in ["policy", "policies", "coverage"]):
            intent = "policy_inquiry"
        # Claims queries
        elif any(word in text_lower for word in ["claim", "claims"]):
            intent = "claim_status"
        
        result = {
            "primary_intent": intent,
            "customer_id": customer_id,
            "confidence": 0.7 if customer_id else 0.5
        }
        
        logger.info(f"Rule-based intent analysis: {result}")
        return result
    
    def plan_response(self, user_text: str, intent_analysis: Dict[str, Any], session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan what to do based on customer intent"""
        
        intent = intent_analysis.get("primary_intent", "general_inquiry")
        customer_id = intent_analysis.get("customer_id")
        
        # Use session customer ID if available
        if not customer_id and session_data.get("customer_id"):
            customer_id = session_data["customer_id"]
        
        plan = {
            "action": "general_help",
            "customer_id": customer_id,
            "technical_request": None,
            "response_template": "general_help"
        }
        
        # Plan what to ask Technical Agent
        if intent in ["policy_inquiry", "coverage_inquiry", "payment_inquiry", "agent_contact"] and customer_id:
            plan["action"] = "ask_technical_agent"
            plan["technical_request"] = f"Get comprehensive policies for customer {customer_id}"
            plan["response_template"] = intent
        elif intent == "claim_status":
            plan["action"] = "claims_not_available"
            plan["response_template"] = "claims_not_available"
        
        return plan
    
    def format_comprehensive_response(self, intent: str, customer_id: str, technical_response: str, user_question: str) -> str:
        """Format response using LLM with intent-specific templates - LLM required"""
        
        if not technical_response:
            return "I couldn't retrieve your policy information. Please try again or contact your agent."
        
        # Require LLM for formatting - no fallback
        if not self.openai_client:
            raise ValueError("OpenAI API key is required for response formatting. Please configure OPENAI_API_KEY environment variable.")
        
        return self._format_with_llm(intent, customer_id, technical_response, user_question)
    
    def _format_with_llm(self, intent: str, customer_id: str, technical_response: str, user_question: str) -> str:
        """Use LLM to intelligently extract and format information using intent-specific templates"""
        try:
            # Select appropriate template based on intent
            template_key = self._get_template_key_for_intent(intent)
            response_template = self.prompts.prompts.get("response_formatting", {}).get(template_key, "")
            
            # Enhanced prompt that combines template structure with LLM intelligence
            enhanced_prompt = f"""You are an expert insurance customer service representative. Format a comprehensive response using the provided template structure and policy data.

CUSTOMER QUESTION: "{user_question}"
CUSTOMER ID: {customer_id}
INTENT: {intent}

COMPREHENSIVE POLICY DATA:
{technical_response}

RESPONSE TEMPLATE STRUCTURE:
{response_template}

INSTRUCTIONS:
1. Use the template structure above as your formatting guide
2. Extract relevant data from the comprehensive policy JSON to populate the template
3. Calculate totals, dates, and summaries as needed
4. For payment_inquiry: Focus on payment dates, amounts, billing cycles
5. For coverage_inquiry: Calculate total coverage amounts across policies
6. For policy_types: List all policy types and their key details
7. For agent_contact: Extract agent information from the policy data
8. Format monetary amounts clearly (e.g., $325,000.00)
9. Format dates in readable format (e.g., September 1, 2024)
10. Be conversational, professional, and helpful
11. If data is missing for template sections, adapt gracefully, but don't make up data
12. Restrict response to only relevant to actual customer question based on template. End with offer to help further


IMPORTANT: Extract and calculate actual values from the JSON data - don't use placeholder or mock or fake values."""

            response = self.openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            formatted_response = response.choices[0].message.content.strip()
            logger.info(f"🔥 DOMAIN AGENT: LLM formatted response using template: {template_key}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"🔥 DOMAIN AGENT: LLM formatting failed: {e}")
            raise ValueError(f"Failed to format response with LLM: {e}")

    def _get_template_key_for_intent(self, intent: str) -> str:
        """Map intent to appropriate response template key"""
        template_mapping = {
            "payment_inquiry": "payment_due_template",
            "coverage_inquiry": "coverage_total_template", 
            "agent_contact": "agent_contact_template",
            "policy_inquiry": "policy_response_template",
            "policy_types": "policy_types_template"
        }
        
        return template_mapping.get(intent, "policy_response_template")
    
    @skill(
        name="ask",
        description="Handle customer conversations about insurance policies and claims",
        tags=["conversation", "customer", "insurance"]
    )
    def ask(self, task):
        """Handle customer conversation requests"""
        logger.info(f"🔥 DOMAIN AGENT: Received task: {task}")
        
        try:
            # Extract customer message
            message_data = task.message or {}
            content = message_data.get("content", {})
            user_text = content.get("text", "") if isinstance(content, dict) else str(content)
            
            logger.info(f"🔥 DOMAIN AGENT: Processing message: {user_text}")
            
            # Extract session data - try multiple approaches
            session_data = {}
            
            # Approach 1: From task.session attribute
            if hasattr(task, 'session') and task.session:
                session_data = task.session
                logger.info(f"🔥 DOMAIN AGENT: Session data from task.session: {session_data}")
            
            # Approach 2: From getattr
            elif getattr(task, 'session', None):
                session_data = getattr(task, 'session', {})
                logger.info(f"🔥 DOMAIN AGENT: Session data from getattr: {session_data}")
            
            # Approach 3: Check if session data is in metadata
            elif hasattr(task, 'metadata') and task.metadata and 'session' in task.metadata:
                session_data = task.metadata.get('session', {})
                logger.info(f"🔥 DOMAIN AGENT: Session data from metadata: {session_data}")
            
            # Approach 4: Check if there's a request context (for direct HTTP calls)
            else:
                try:
                    from flask import request
                    if request and request.is_json:
                        request_data = request.get_json()
                        if request_data and 'session' in request_data:
                            session_data = request_data['session']
                            logger.info(f"🔥 DOMAIN AGENT: Session data from Flask request: {session_data}")
                except:
                    pass
            
            logger.info(f"🔥 DOMAIN AGENT: Final session data: {session_data}")
            
            # Step 1: Analyze customer intent
            intent_analysis = self.analyze_customer_intent(user_text)
            logger.info(f"🔥 DOMAIN AGENT: Intent: {intent_analysis}")
            
            # Step 2: Plan response
            response_plan = self.plan_response(user_text, intent_analysis, session_data)
            logger.info(f"🔥 DOMAIN AGENT: Plan: {response_plan}")
            
            # Step 3: Get information from Technical Agent if needed
            if response_plan["action"] == "ask_technical_agent":
                try:
                    client = self.get_technical_client()
                    if client:
                        technical_response = client.ask(response_plan["technical_request"])
                        logger.info(f"🔥 DOMAIN AGENT: Technical response received")
                        logger.info(f"🔥 DOMAIN AGENT: Raw technical response: {technical_response}")
                        
                        # Use LLM to format comprehensive response with templates
                        try:
                            final_response = self.format_comprehensive_response(
                                intent_analysis["primary_intent"],
                                response_plan["customer_id"], 
                                technical_response,
                                user_text
                            )
                        except ValueError as e:
                            # Handle LLM formatting errors gracefully
                            if "OpenAI API key" in str(e):
                                final_response = "I need OpenAI configuration to provide formatted responses. Please contact support to enable AI formatting capabilities."
                            else:
                                final_response = f"I retrieved your policy information but encountered a formatting issue. Please contact support or try again. Raw data: {technical_response[:200]}..."
                            logger.error(f"🔥 DOMAIN AGENT: Formatting error: {e}")
                    else:
                        final_response = "I'm having trouble connecting to our policy system. Please try again."
                except Exception as e:
                    logger.error(f"🔥 DOMAIN AGENT: Technical Agent error: {e}")
                    final_response = "I'm having trouble retrieving your policy information. Please try again."
            
            elif response_plan["action"] == "claims_not_available":
                final_response = "Claims information is currently being updated. Please contact your agent for claim status."
            
            else:
                # General help response
                final_response = "I can help you with policy information, coverage details, payment schedules, and agent contact information. Please provide your customer ID and let me know what you need."
            
            logger.info(f"🔥 DOMAIN AGENT: Sending response: {final_response[:100]}...")
            
            # Return response
            task.artifacts = [{
                "parts": [{"type": "text", "text": final_response}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            logger.error(f"🔥 DOMAIN AGENT: Error: {e}")
            error_response = f"I apologize, but I encountered an error processing your request. Please try again."
            task.artifacts = [{
                "parts": [{"type": "text", "text": error_response}]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task
    
    def handle_task(self, task):
        """Handle incoming A2A tasks - main entry point"""
        logger.info(f"🔥🔥🔥 DOMAIN AGENT HANDLE_TASK CALLED: {task}")
        return self.ask(task)
    
    def process_task(self, task):
        """Alternative task processing method"""
        logger.info(f"🔥🔥🔥 DOMAIN AGENT PROCESS_TASK CALLED: {task}")
        return self.ask(task)
    
    def handle_message(self, message):
        """Handle message-based requests"""
        logger.info(f"🔥🔥🔥 DOMAIN AGENT HANDLE_MESSAGE CALLED: {message}")
        # Convert message to task format if needed
        task = type('Task', (), {
            'message': message,
            'artifacts': [],
            'status': None
        })()
        return self.ask(task)
    
    def _parse_technical_response(self, response: str) -> list:
        """Parse technical agent response to extract policy data"""
        try:
            # Try to find JSON data in the response
            lines = response.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('[') or line.startswith('{'):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            
            # If no JSON found, return empty list
            logger.warning("No JSON policy data found in technical response")
            return []
            
        except Exception as e:
            logger.error(f"Failed to parse technical response: {e}")
            return []


if __name__ == "__main__":
    # Check command line arguments for port
    port = 8003
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    logger.info(f"Starting Domain Agent on port {port}")
    logger.info("Domain Agent provides conversational interface for insurance customers")
    
    # Create and run the agent
    agent = DomainAgent()
    run_server(agent, port=port) 