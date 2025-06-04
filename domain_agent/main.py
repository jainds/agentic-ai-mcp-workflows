#!/usr/bin/env python3
"""
Domain Agent - Simple and Readable
Conversational insurance agent that helps customers and communicates with Technical Agent
"""

import sys
import os
import json
import re
import logging
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
import uuid

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

import structlog
import openai
import yaml
from dotenv import load_dotenv
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState, A2AClient, Task
from openai import OpenAI

from prompt_loader import PromptLoader
from intent_analyzer import IntentAnalyzer
from response_formatter import ResponseFormatter

# Import monitoring and session management
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from monitoring.setup.monitoring_setup import get_monitoring_manager
    monitoring = get_monitoring_manager()
    MONITORING_ENABLED = monitoring.is_monitoring_enabled()
    if MONITORING_ENABLED:
        print("✅ Domain Agent: Monitoring enabled")
    else:
        print("⚠️  Domain Agent: Monitoring disabled (providers not available)")
except Exception as e:
    print(f"⚠️  Domain Agent: Monitoring not available: {e}")
    monitoring = None
    MONITORING_ENABLED = False

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

# Thread-local storage for session data
_thread_local = threading.local()

def set_current_session_data(session_data: Dict[str, Any]):
    """Set session data for current thread/request"""
    _thread_local.session_data = session_data
    logger.info(f"🔥 DOMAIN AGENT: Set thread-local session data: {session_data}")

def get_current_session_data() -> Dict[str, Any]:
    """Get session data for current thread/request"""
    session_data = getattr(_thread_local, 'session_data', {})
    logger.info(f"🔥 DOMAIN AGENT: Retrieved thread-local session data: {session_data}")
    return session_data

def clear_current_session_data():
    """Clear session data for current thread/request"""
    if hasattr(_thread_local, 'session_data'):
        delattr(_thread_local, 'session_data')

# Monkey-patch the handle_task method to extract session data from the request
def extract_session_from_raw_request():
    """
    Extract session data from the raw HTTP request context.
    This is a fallback method when middleware isn't available.
    """
    try:
        # Try to access the current request from different possible contexts
        import inspect
        
        # Walk up the call stack to find any request-like objects
        frame = inspect.currentframe()
        while frame:
            for var_name, var_value in frame.f_locals.items():
                # Look for request-like objects
                if hasattr(var_value, 'json') and callable(getattr(var_value, 'json')):
                    try:
                        payload = var_value.json()
                        if isinstance(payload, dict) and 'session' in payload:
                            logger.info(f"🔥 DOMAIN AGENT: Found session data in request object: {payload['session']}")
                            return payload['session']
                    except:
                        pass
                
                # Look for direct payload data
                if isinstance(var_value, dict) and 'session' in var_value:
                    logger.info(f"🔥 DOMAIN AGENT: Found session data in payload: {var_value['session']}")
                    return var_value['session']
            
            frame = frame.f_back
    
    except Exception as e:
        logger.warning(f"🔥 DOMAIN AGENT: Could not extract session from request: {e}")
    
    return {}

@agent(
    name="Domain Agent", 
    description="Conversational insurance agent that helps customers and communicates with Technical Agent",
    version="2.0.0"
)
class DomainAgent(A2AServer):
    """Simple Domain Agent that talks to customers and Technical Agent"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize prompt loader
        self.prompts = PromptLoader()
        
        # Set up OpenAI client for LLM features - required for LLM-only mode
        self.openai_client = None
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                self.openai_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key
                )
                logger.info("🔥 DOMAIN AGENT: OpenAI client initialized for LLM-based analysis")
            else:
                raise ValueError("OPENROUTER_API_KEY environment variable is required for LLM-based operation")
        except Exception as e:
            logger.error(f"🔥 DOMAIN AGENT: Failed to initialize OpenAI: {e}")
            raise RuntimeError(f"Domain Agent requires OpenAI client for LLM-based operation: {e}")
        
        # Initialize modular components
        try:
            self.intent_analyzer = IntentAnalyzer(self.openai_client)
            self.response_formatter = ResponseFormatter(self.openai_client)
        except Exception as e:
            logger.error(f"🔥 DOMAIN AGENT: Failed to initialize components: {e}")
            raise RuntimeError(f"Failed to initialize LLM-based components: {e}")
        
        # Technical Agent setup with direct A2A communication
        self.technical_agent_url = os.getenv("TECHNICAL_AGENT_URL", "http://insurance-ai-poc-technical-agent:8002")
        self.technical_client = None
        
        logger.info("🔥 DOMAIN AGENT: Initialized with modular components")
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
        """Analyze customer intent using LLM-based IntentAnalyzer"""
        start_time = time.time()
        
        try:
            # Use the IntentAnalyzer for LLM-based intent analysis
            result = self.intent_analyzer.analyze_customer_intent(user_text)
            
            # Record intent analysis metrics
            if MONITORING_ENABLED and monitoring:
                duration = time.time() - start_time
                monitoring.record_intent_analysis(
                    intent=result.get("primary_intents", ["unknown"])[0],
                    confidence=result.get("confidence", 0.0),
                    method=result.get("method", "unknown"),
                    success=True,
                    duration_seconds=duration
                )
            
            return result
            
        except Exception as e:
            # Record failed intent analysis
            if MONITORING_ENABLED and monitoring:
                duration = time.time() - start_time
                monitoring.record_intent_analysis(
                    intent="error",
                    confidence=0.0,
                    method="llm_failed",
                    success=False,
                    duration_seconds=duration
                )
            
            logger.error(f"🔥 DOMAIN AGENT: Intent analysis failed: {e}")
            # Re-raise the error - no fallback
            raise RuntimeError(f"Intent analysis failed: {e}")
    
    def format_comprehensive_response(self, intent: str, customer_id: str, technical_response: str, user_question: str) -> str:
        """Format comprehensive response using modular formatter"""
        return self.response_formatter.format_comprehensive_response(intent, customer_id, technical_response, user_question)
    
    def plan_response(self, user_text: str, intent_analysis: Dict[str, Any], session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Plan what to do based on customer intents and session data"""
        
        intents = intent_analysis.get("primary_intents", [])
        if not isinstance(intents, list):
            # Handle backward compatibility if single intent is returned
            single_intent = intent_analysis.get("primary_intent")
            intents = [single_intent] if single_intent else ["general_inquiry"]
        
        customer_id = session_data.get("customer_id")  # Only from session data
        
        plan = {
            "action": "general_help",
            "customer_id": customer_id,
            "technical_request": None,
            "response_template": "general_help",
            "intents": intents
        }
        
        # Plan what to ask Technical Agent - only if we have customer ID from session
        if customer_id and any(intent in ["policy_inquiry", "coverage_inquiry", "payment_inquiry", "deductible_inquiry", "agent_contact"] for intent in intents):
            plan["action"] = "ask_technical_agent"
            
            # Create comprehensive request based on all intents
            if len(intents) > 1:
                plan["technical_request"] = f"Get comprehensive information for customer {customer_id} covering: {', '.join(intents)}"
                plan["response_template"] = "comprehensive_multi_intent"
            elif "policy_inquiry" in intents:
                plan["technical_request"] = f"Get policies for customer {customer_id}"
                plan["response_template"] = "policy_inquiry"
            elif "coverage_inquiry" in intents:
                plan["technical_request"] = f"Get coverage information for customer {customer_id}"
                plan["response_template"] = "coverage_inquiry"
            elif "payment_inquiry" in intents:
                plan["technical_request"] = f"Get payment information for customer {customer_id}"
                plan["response_template"] = "payment_inquiry"
            elif "deductible_inquiry" in intents:
                plan["technical_request"] = f"Get deductible information for customer {customer_id}"
                plan["response_template"] = "deductible_inquiry"
            elif "agent_contact" in intents:
                plan["technical_request"] = f"Get agent contact information for customer {customer_id}"
                plan["response_template"] = "agent_contact"
        elif "claim_status" in intents:
            plan["action"] = "claims_not_available"
            plan["response_template"] = "claims_not_available"
        
        return plan
    
    @skill(
        name="ask",
        description="Handle customer conversations about insurance policies and claims",
        tags=["conversation", "customer", "insurance"]
    )
    def ask(self, task):
        """Handle customer conversation requests"""
        request_start_time = time.time()
        logger.info(f"🔥 DOMAIN AGENT: Received task: {task}")
        
        try:
            # Extract customer message
            message_data = task.message or {}
            content = message_data.get("content", {})
            user_text = content.get("text", "") if isinstance(content, dict) else str(content)
            
            logger.info(f"🔥 DOMAIN AGENT: Processing message: {user_text}")
            
            # Extract metadata - this is where we can get session data in A2A protocol
            metadata = getattr(task, 'metadata', {}) or {}
            ui_mode = metadata.get('ui_mode', 'unknown')
            
            # Check if session data is embedded in metadata
            session_data = {}
            session_customer_id = None
            authenticated = False
            customer_data = {}
            
            # Try multiple approaches to extract session data
            # Approach 1: Check if session data is in metadata
            if 'session' in metadata:
                session_data = metadata['session']
                session_customer_id = session_data.get('customer_id')
                authenticated = session_data.get('authenticated', False)
                customer_data = session_data.get('customer_data', {})
                logger.info(f"🔥 DOMAIN AGENT: Found session data in metadata: {session_data}")
            
            # Approach 2: Try the thread-local storage
            elif get_current_session_data():
                session_data = get_current_session_data()
                session_customer_id = session_data.get('customer_id')
                authenticated = session_data.get('authenticated', False)
                customer_data = session_data.get('customer_data', {})
                logger.info(f"🔥 DOMAIN AGENT: Found session data in thread-local: {session_data}")
            
            # Approach 3: Try the raw request extraction
            else:
                extracted_session = extract_session_from_raw_request()
                if extracted_session:
                    session_data = extracted_session
                    session_customer_id = session_data.get('customer_id')
                    authenticated = session_data.get('authenticated', False)
                    customer_data = session_data.get('customer_data', {})
                    logger.info(f"🔥 DOMAIN AGENT: Found session data via extraction: {session_data}")
            
            # Approach 4: Check if customer ID is embedded in message content
            if not session_customer_id:
                # Look for customer ID patterns in the message
                import re
                customer_pattern = r'\b(CUST-\w+)\b'
                match = re.search(customer_pattern, user_text)
                if match:
                    session_customer_id = match.group(1)
                    session_data = {'customer_id': session_customer_id, 'authenticated': True}
                    logger.info(f"🔥 DOMAIN AGENT: Extracted customer ID from message: {session_customer_id}")
            
            logger.info(f"🔥 DOMAIN AGENT: Session-based identification - Customer ID: {session_customer_id}, Authenticated: {authenticated}, UI Mode: {ui_mode}")
            logger.info(f"🔥 DOMAIN AGENT: Final session data: {session_data}")
            
            # Only proceed if we have a customer ID from session - NO FALLBACKS
            if not session_customer_id:
                logger.warning("🔥 DOMAIN AGENT: No customer ID found in any source. Session-only mode requires authenticated session.")
                final_response = "I need you to be logged in with a valid session to access your policy information. Please log in and try again."
                
                task.artifacts = [{
                    "parts": [{"type": "text", "text": final_response}]
                }]
                task.status = TaskStatus(state=TaskState.INPUT_REQUIRED)
                return task
            
            # Step 1: Analyze customer intent (simplified, no customer ID extraction)
            intent_analysis = self.analyze_customer_intent(user_text)
            logger.info(f"🔥 DOMAIN AGENT: Intent: {intent_analysis}")
            
            # Step 2: Plan response
            response_plan = self.plan_response(user_text, intent_analysis, session_data)
            logger.info(f"🔥 DOMAIN AGENT: Plan: {response_plan}")
            
            # Step 3: Get information from Technical Agent if needed
            if response_plan["action"] == "ask_technical_agent":
                try:
                    logger.info(f"🔥 DOMAIN AGENT: Sending request to technical agent: {response_plan['technical_request']}")
                    
                    # Use A2A client with session data
                    client = self.get_technical_client()
                    if client:
                        # Create enhanced technical request with explicit customer ID for A2A transmission
                        customer_id = session_data.get('customer_id', 'unknown')
                        enhanced_request = f"{response_plan['technical_request']} (session_customer_id: {customer_id})"
                        
                        logger.info(f"🔥 DOMAIN AGENT: Sending A2A request with session data embedded in text: {enhanced_request}")
                        
                        # Send task via A2A client with customer ID embedded in text
                        technical_response_data = client.ask(enhanced_request)
                        
                        # Extract response text from A2A response format
                        if isinstance(technical_response_data, dict):
                            artifacts = technical_response_data.get("artifacts", [])
                            if artifacts and len(artifacts) > 0:
                                parts = artifacts[0].get("parts", [])
                                if parts and len(parts) > 0:
                                    technical_response = parts[0].get("text", "No response")
                                else:
                                    technical_response = "No response parts found"
                            else:
                                technical_response = "No response artifacts found"
                        else:
                            technical_response = str(technical_response_data)
                        
                        logger.info(f"🔥 DOMAIN AGENT: Technical response received")
                        logger.info(f"🔥 DOMAIN AGENT: Raw technical response: {technical_response}")
                        
                        # Check if technical response contains actual policy data or just help message
                        if self._is_valid_policy_response(technical_response):
                            # Use LLM to format comprehensive response with templates
                            try:
                                # Get the primary intent from the intents array
                                primary_intent = intent_analysis.get("primary_intents", ["general_inquiry"])[0]
                                final_response = self.format_comprehensive_response(
                                    primary_intent,
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
                            # Technical response is just a help message or error - don't format with LLM
                            logger.warning(f"🔥 DOMAIN AGENT: Technical response appears to be help message, not policy data: {technical_response[:100]}")
                            final_response = "I'm having trouble retrieving your policy information. Please try again."
                    else:
                        final_response = "I'm having trouble connecting to our policy system. Please try again."
                
                except Exception as e:
                    logger.error(f"🔥 DOMAIN AGENT: Technical Agent error: {e}")
                    final_response = "I'm having trouble retrieving your policy information. Please try again."
            
            elif response_plan["action"] == "claims_not_available":
                final_response = "Claims information is currently being updated. Please contact your agent for claim status."
            
            else:
                # General help response - no customer ID available
                if authenticated:
                    final_response = "I can help you with your insurance needs. However, I need your customer ID in the session to retrieve your specific policy information. Please log in again or provide your customer ID."
                else:
                    final_response = "I can help you with policy information, coverage details, payment schedules, and agent contact information. Please log in or provide your customer ID to get specific policy details."
            
            logger.info(f"🔥 DOMAIN AGENT: Sending response: {final_response[:100]}...")
            
            # Record successful request metrics
            if MONITORING_ENABLED and monitoring:
                request_duration = time.time() - request_start_time
                customer_id = session_data.get("customer_id", "unknown")
                
                # Record overall request success
                monitoring.increment_counter(
                    "domain_agent_requests_total",
                    labels={
                        "status": "success",
                        "intent": intent_analysis.get("primary_intents", ["unknown"])[0],
                        "action": response_plan.get("action", "unknown")
                    }
                )
                
                # Record request duration
                monitoring.record_duration(
                    "domain_agent_request_duration",
                    request_duration,
                    labels={
                        "intent": intent_analysis.get("primary_intents", ["unknown"])[0],
                        "action": response_plan.get("action", "unknown")
                    }
                )
            
            # Return response
            task.artifacts = [{
                "parts": [{"type": "text", "text": final_response}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
        except Exception as e:
            logger.error(f"🔥 DOMAIN AGENT: Error: {e}")
            
            # Record failed request metrics
            if MONITORING_ENABLED and monitoring:
                request_duration = time.time() - request_start_time
                
                monitoring.increment_counter(
                    "domain_agent_requests_total",
                    labels={
                        "status": "error",
                        "intent": "error",
                        "action": "error"
                    }
                )
                
                monitoring.record_duration(
                    "domain_agent_request_duration",
                    request_duration,
                    labels={
                        "intent": "error",
                        "action": "error"
                    }
                )
            
            error_response = f"I apologize, but I encountered an error processing your request. Please try again."
            task.artifacts = [{
                "parts": [{"type": "text", "text": error_response}]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task
    
    def handle_task(self, task):
        """Handle incoming A2A tasks - main entry point"""
        logger.info(f"🔥🔥🔥 DOMAIN AGENT HANDLE_TASK CALLED: {task}")
        
        # Extract session data from the request
        session_data = extract_session_from_raw_request()
        if session_data:
            set_current_session_data(session_data)
        
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

    def _is_valid_policy_response(self, response: str) -> bool:
        """Check if the technical response contains actual policy data"""
        if not response or not isinstance(response, str):
            return False
        
        # Remove any identification prefix from the response for analysis
        cleaned_response = response
        if response.startswith("(identified from:"):
            # Find the end of the identification prefix and extract the actual response
            closing_paren_idx = response.find(")")
            if closing_paren_idx != -1:
                cleaned_response = response[closing_paren_idx + 1:].strip()
        
        response_lower = cleaned_response.lower()
        
        # Check for help/error indicators that suggest no real data
        help_indicators = [
            "i can help with",
            "i'm here to help",
            "how can i assist",
            "please provide",
            "customer id from session",
            "error:",
            "failed to",
            "unable to",
            "no data found",
            "customer not found",
            "not available",
            "try again"
        ]
        
        # If response contains help indicators, it's not policy data
        for indicator in help_indicators:
            if indicator in response_lower:
                return False
        
        # Check for policy data indicators
        policy_data_indicators = [
            "policy_id",
            "coverage_amount",
            "premium",
            "deductible",
            "start_date",
            "end_date",
            "vehicle",
            "beneficiary",
            "agent_name",
            '"policies"',
            '"customer_policies"',
            "POL-",  # Policy ID pattern
            "$",     # Money amounts
            "coverage",
            "liability",
            "collision",
            "your payment information:",
            "your deductible",
            "due on"
        ]
        
        # Check if response contains actual policy data indicators
        policy_data_count = sum(1 for indicator in policy_data_indicators if indicator in response_lower)
        
        # Also check for JSON structure that might contain policy data
        try:
            import json
            # Try to parse as JSON
            if cleaned_response.strip().startswith('[') or cleaned_response.strip().startswith('{'):
                parsed = json.loads(cleaned_response)
                if isinstance(parsed, list) and len(parsed) > 0:
                    # Check if it's a list of policies
                    first_item = parsed[0]
                    if isinstance(first_item, dict) and any(key in first_item for key in ['policy_id', 'id', 'type', 'premium']):
                        return True
                elif isinstance(parsed, dict) and any(key in parsed for key in ['policies', 'customer_policies', 'policy_data']):
                    return True
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
        
        # Return True if we found multiple policy data indicators
        return policy_data_count >= 2

if __name__ == "__main__":
    import logging
    
    # Create and run the domain agent
    domain_agent = DomainAgent()
    
    # Start the A2A server
    logger.info("Starting Domain Agent on port 8003")
    logger.info("Domain Agent provides conversational interface for insurance customers")
    run_server(domain_agent, host="0.0.0.0", port=8003) 