#!/usr/bin/env python3
"""
Minimal Domain Agent
Conversational, intelligent chatbot that communicates with customers
and talks to Technical Agent via A2A for policy information
"""

import sys
import re
import json
from typing import Dict, Any, List
from datetime import datetime

import structlog
from python_a2a import A2AServer, AgentCard, skill, agent, run_server, TaskStatus, TaskState, A2AClient
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Setup logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

@agent(
    name="Insurance Domain Agent",
    description="Conversational insurance agent that helps customers with policy inquiries and claims",
    version="1.0.0"
)
class DomainAgent(A2AServer):
    
    def __init__(self):
        super().__init__()
        
        # Technical Agent configuration - use environment variable or fallback to localhost
        self.technical_agent_url = os.getenv("TECHNICAL_AGENT_URL", "http://localhost:8002")
        self.technical_client = None
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("OpenAI client initialized")
        else:
            logger.warning("No OpenAI API key found - using rule-based responses only")
        
        logger.info("Domain Agent initialized")
        logger.info(f"Will connect to Technical Agent at: {self.technical_agent_url}")
    
    def _get_technical_client(self):
        """Get or create A2A client for Technical Agent"""
        if self.technical_client is None:
            self.technical_client = A2AClient(self.technical_agent_url)
        return self.technical_client
    
    def _analyze_intent(self, user_text: str) -> Dict[str, Any]:
        """Analyze user intent using either LLM or rules"""
        
        # Try LLM-based analysis first if available
        if self.openai_client:
            try:
                return self._llm_intent_analysis(user_text)
            except Exception as e:
                logger.warning(f"LLM intent analysis failed, falling back to rules: {e}")
        
        # Fallback to rule-based analysis
        return self._rule_based_intent_analysis(user_text)
    
    def _llm_intent_analysis(self, user_text: str) -> Dict[str, Any]:
        """Use LLM to analyze user intent"""
        prompt = f"""
        As an insurance domain expert, analyze this user request and extract the primary intent.
        
        Choose ONE primary intent from: claim_status, policy_inquiry, general_inquiry
        
        RULES:
        - If user mentions "policy", "policies", "coverage" → policy_inquiry
        - If user mentions "claim", "status" → claim_status  
        - Otherwise → general_inquiry
        
        Also extract any customer ID mentioned in the request.
        
        User Request: "{user_text}"
        
        Respond in JSON format:
        {{
            "primary_intent": "string",
            "customer_id": "string or null",
            "confidence": 0.0-1.0
        }}
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content
        
        # Parse JSON response
        try:
            return json.loads(result_text.strip())
        except json.JSONDecodeError:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                raise ValueError("Could not parse LLM response")
    
    def _rule_based_intent_analysis(self, user_text: str) -> Dict[str, Any]:
        """Simple rule-based intent analysis"""
        text_lower = user_text.lower()
        
        # Extract customer ID - preserve original format
        customer_id = None
        
        # Look for various customer ID patterns
        patterns = [
            r'user_\w+',           # user_003, user_001
            r'CUST-\d+',           # CUST-001, CUST-002  
            r'cust-\d+',           # cust-001 (lowercase)
            r'customer\s*[-_]?\s*(\w+[-]\w+|\w+)',  # customer CUST-001, customer_001
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                if pattern.startswith(r'customer'):
                    # Extract the ID part after "customer"
                    customer_id = match.group(1)
                else:
                    customer_id = match.group(0)
                break
        
        # If no direct pattern match, look for "for customer X" pattern
        if not customer_id:
            customer_match = re.search(r'(?:for|customer)\s+([A-Za-z0-9_-]+)', user_text, re.IGNORECASE)
            if customer_match:
                customer_id = customer_match.group(1)
        
        # Determine intent
        if any(word in text_lower for word in ["policy", "policies", "coverage"]):
            primary_intent = "policy_inquiry"
        elif any(word in text_lower for word in ["claim", "status"]):
            primary_intent = "claim_status"
        else:
            primary_intent = "general_inquiry"
        
        return {
            "primary_intent": primary_intent,
            "customer_id": customer_id,
            "confidence": 0.8
        }
    
    def _format_professional_response(self, intent: str, technical_response: str, customer_id: str = None) -> str:
        """Format a professional customer-facing response"""
        
        if intent == "policy_inquiry":
            if "Found" in technical_response and "policies" in technical_response:
                return f"""Thank you for your inquiry about your insurance policies.

{technical_response}

**Account Summary:**
I've successfully retrieved your current policy information from our system. All policies shown above are currently active and in good standing.

**Need Additional Help?**
If you have questions about any specific policy details, coverage amounts, or would like to make changes to your policies, I'm here to help!

Is there anything specific about your policies you'd like me to explain in more detail?"""
            else:
                return f"""Thank you for your policy inquiry.

{technical_response}

If you have your customer ID or policy number available, I can provide more detailed information about your specific coverage and benefits.

How else can I assist you with your insurance needs today?"""
        
        elif intent == "claim_status":
            return f"""Thank you for checking on your claim status.

{technical_response}

**What This Means:**
I'm currently working on gathering your claim information. Our claims processing system is reviewing your case to provide you with the most up-to-date status.

**Next Steps:**
Once I have your complete claim details, I'll provide you with:
- Current claim status and processing stage
- Expected timeline for resolution
- Any required documentation or next steps

Is there anything specific about your claim you'd like me to help clarify?"""
        
        else:  # general_inquiry
            return f"""Thank you for contacting our insurance support team.

{technical_response}

**How I Can Help:**
I'm here to assist you with:
- Policy information and coverage details
- Claim status updates and filing assistance
- Billing and payment questions
- General insurance guidance

Please let me know what specific information you're looking for, and I'll be happy to help!"""
    
    @skill(
        name="Customer Conversation",
        description="Handle customer conversations about insurance policies and claims",
        tags=["conversation", "customer", "insurance"]
    )
    def handle_customer_conversation(self, customer_message: str) -> str:
        """Handle customer conversations intelligently"""
        try:
            # Analyze customer intent
            intent_analysis = self._analyze_intent(customer_message)
            logger.info(f"Intent analysis: {intent_analysis}")
            
            primary_intent = intent_analysis.get("primary_intent", "general_inquiry")
            customer_id = intent_analysis.get("customer_id")
            
            # Connect to Technical Agent for data
            technical_client = self._get_technical_client()
            
            if primary_intent == "policy_inquiry" and customer_id:
                # Ask Technical Agent for policies
                technical_response = technical_client.ask(f"Get policies for customer {customer_id}")
                return self._format_professional_response(primary_intent, technical_response, customer_id)
            
            elif primary_intent == "claim_status":
                # For now, provide helpful guidance
                technical_response = "I can help you check your claim status. Please provide your customer ID so I can look up your specific claims."
                return self._format_professional_response(primary_intent, technical_response, customer_id)
            
            else:
                # General inquiry or missing information
                if not customer_id and primary_intent != "general_inquiry":
                    technical_response = "To provide specific information about your account, I'll need your customer ID (such as user_003)."
                else:
                    technical_response = "I'm here to help with your insurance questions."
                
                return self._format_professional_response(primary_intent, technical_response, customer_id)
        
        except Exception as e:
            logger.error(f"Error in customer conversation: {e}")
            return f"""I apologize, but I encountered an issue while processing your request.

**Error Details:** {str(e)}

**What You Can Do:**
- Please try rephrasing your question
- Make sure to include your customer ID if asking about specific policies or claims
- Contact our support team directly if the issue persists

I'm here to help once we resolve this technical issue. Thank you for your patience!"""
    
    def handle_task(self, task):
        """Handle incoming A2A tasks (conversation requests)"""
        logger.info(f"Received conversation task: {task}")
        
        try:
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})
            
            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)
            
            logger.info(f"Processing customer message: {text}")
            
            # Handle the conversation
            response = self.handle_customer_conversation(text)
            
            # Format response
            task.artifacts = [{
                "parts": [{"type": "text", "text": response}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        
        except Exception as e:
            logger.error(f"Error handling conversation task: {e}")
            task.artifacts = [{
                "parts": [{"type": "text", "text": f"I apologize, but I encountered an error: {str(e)}"}]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task

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