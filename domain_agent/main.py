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
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

import structlog
import openai
import yaml
from dotenv import load_dotenv
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState, A2AClient
from openai import OpenAI

from prompt_loader import PromptLoader
from intent_analyzer import IntentAnalyzer
from response_formatter import ResponseFormatter

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
        
        # Initialize prompt loader
        self.prompts = PromptLoader()
        
        # Set up OpenAI client for LLM features
        self.openai_client = None
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                self.openai_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key
                )
                logger.info("🔥 DOMAIN AGENT: OpenAI client initialized")
            else:
                logger.warning("🔥 DOMAIN AGENT: No OpenAI API key found - using rule-based analysis only")
        except Exception as e:
            logger.warning(f"🔥 DOMAIN AGENT: Failed to initialize OpenAI: {e}")
        
        # Initialize modular components
        self.intent_analyzer = IntentAnalyzer(self.openai_client)
        self.response_formatter = ResponseFormatter(self.openai_client)
        
        # Technical Agent setup
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
        """Analyze customer intent and extract information using modular analyzer"""
        return self.intent_analyzer.analyze_customer_intent(user_text)
    
    def format_comprehensive_response(self, intent: str, customer_id: str, technical_response: str, user_question: str) -> str:
        """Format comprehensive response using modular formatter"""
        return self.response_formatter.format_comprehensive_response(intent, customer_id, technical_response, user_question)
    
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