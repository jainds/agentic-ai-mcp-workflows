#!/usr/bin/env python3
"""
LLM-Powered Claims Domain Agent - Pure A2A Architecture
Domain Agent: LLM planning + A2A messaging ONLY
Technical Agent: A2A receiving + FastMCP tools
Communication: ONLY via Google's A2A SDK
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# Google A2A SDK for agent-to-agent communication
logger = structlog.get_logger(__name__)

try:
    from a2a import A2AClient
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False
    logger.error("Google A2A SDK not available - this is required for the architecture")

class LLMClaimsAgent:
    """
    Domain Agent: LLM reasoning + A2A orchestration ONLY
    No FastMCP tools, no HTTP fallbacks, pure A2A messaging
    """
    
    def __init__(self, port: int = 8000):
        if not A2A_AVAILABLE:
            raise RuntimeError("Google A2A SDK is required but not available. Install with: pip install a2a")
        
        self.port = port
        self.app = FastAPI(title="LLM Claims Domain Agent", version="1.0.0")
        self._setup_cors()
        self._setup_llm_client()
        self._setup_prompts()
        self._setup_a2a_clients()
        self._setup_endpoints()
        
        self.template = self._load_template()
        logger.info("LLM Claims Domain Agent initialized with pure A2A architecture")

    def _setup_cors(self):
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_llm_client(self):
        """Setup LLM client with API keys"""
        self.use_mock_llm = True
        
        # Try OpenRouter first
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            self.llm_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key
            )
            self.model_name = "anthropic/claude-3.5-sonnet"
            self.use_mock_llm = False
            logger.info("Using OpenRouter API for LLM reasoning")
        else:
            # Try OpenAI
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.llm_client = OpenAI(api_key=openai_key)
                self.model_name = "gpt-4"
                self.use_mock_llm = False
                logger.info("Using OpenAI API for LLM reasoning")
        
        if self.use_mock_llm:
            logger.warning("No valid LLM API keys found, using mock LLM responses")

    def _setup_a2a_clients(self):
        """Setup A2A SDK clients for technical agent communication"""
        self.technical_agent_endpoint = "http://localhost:8001"  # Single technical agent
        
        try:
            self.a2a_client = A2AClient(
                agent_id="domain_agent",
                target_agent_id="technical_agent",
                endpoint=self.technical_agent_endpoint
            )
            logger.info(f"A2A client configured for technical agent at {self.technical_agent_endpoint}")
        except Exception as e:
            raise RuntimeError(f"Failed to setup A2A client: {e}")

    def _load_template(self) -> str:
        """Load response template from file"""
        try:
            template_path = Path("Template")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read().strip()
                logger.info("Response template loaded successfully")
                return template
        except Exception as e:
            logger.warning(f"Could not load template: {e}")
        
        return "Professional insurance response template"

    def _setup_prompts(self):
        """Setup LLM prompts for domain agent reasoning"""
        
        self.system_prompt = """You are an expert insurance claims domain agent with advanced reasoning capabilities.

ROLE & RESPONSIBILITIES:
- You are the orchestrating intelligence layer that coordinates with technical agents
- You use insurance domain expertise and reasoning to understand customer intent and plan actions
- You communicate with technical agents via A2A protocol to gather real data
- You synthesize responses using structured templates for professional communication

ARCHITECTURE UNDERSTANDING:
- YOU are the Insurance Domain Agent (LLM reasoning layer)
- Technical Agents provide specialized data access via FastMCP tools
- You orchestrate via A2A protocol - you send plans, they execute tools
- You never use mock data or fake data - always call technical agents for real information

AVAILABLE TECHNICAL AGENT CAPABILITIES:
- User data: Customer authentication, profile data, account management
- Claims data: Claims filing, status checking, claims history
- Policy data: Policy information, coverage details, renewals
- Analytics data: Risk assessment, fraud detection, recommendations

INTENT DETECTION CAPABILITIES:
- policy_inquiry: Customer asking about policies, coverage, renewals
- claims_status: Customer checking existing claim status
- file_claim: Customer wants to file a new claim
- account_inquiry: Customer asking about account details
- general_help: General questions about insurance

ORCHESTRATION PLANNING:
For each customer request, you must:
1. Analyze the customer's intent using LLM reasoning
2. Plan which data types to request from technical agent
3. Send structured A2A message with data requirements
4. Synthesize the returned data into a professional response

You are the brain - you think, plan, and orchestrate. Technical agent is the hands - they execute."""

        self.intent_analysis_prompt = """Analyze this customer message and create an orchestration plan:

Customer Message: "{user_message}"
Customer ID: "{customer_id}"

Provide a JSON response with:
1. Intent classification (policy_inquiry, claims_status, file_claim, account_inquiry, general_help)
2. Confidence score (0.0-1.0)
3. Data requirements for technical agent
4. Reasoning for your analysis

Format:
{
    "intent": "policy_inquiry",
    "confidence": 0.9,
    "reasoning": "Customer is asking about...",
    "data_requirements": ["user_profile", "policy_data", "claims_history"],
    "urgent": false
}"""

        self.response_synthesis_prompt = """Synthesize a professional insurance response using this data:

Customer Message: "{user_message}"
Intent: "{intent}"
Technical Agent Data: {technical_data}
Template Guidelines: {template}

Create a professional, helpful response that:
1. Addresses the customer's specific question
2. Uses the real data from technical agent
3. Follows the template style
4. Provides clear next steps if applicable

Response:"""

    def _setup_endpoints(self):
        """Setup HTTP endpoints"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "agent_type": "domain_agent", 
                "version": "1.0.0",
                "llm_enabled": not self.use_mock_llm,
                "a2a_configured": True,
                "technical_agent": self.technical_agent_endpoint,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.post("/chat")
        async def chat_endpoint(request_data: dict):
            """Main chat endpoint - handles customer interactions"""
            message = request_data.get("message", "")
            customer_id = request_data.get("customer_id", "default-customer")
            
            if not message:
                return {"error": "Message is required"}
            
            try:
                result = await self.process_with_llm_reasoning(message, customer_id)
                return result
            except Exception as e:
                logger.error(f"Chat processing failed: {e}")
                return {"error": str(e)}

    async def process_with_llm_reasoning(self, message: str, customer_id: str) -> Dict[str, Any]:
        """Process customer message using LLM reasoning and A2A orchestration"""
        
        thinking_steps = []
        orchestration_events = []
        a2a_calls = []
        
        try:
            thinking_steps.append("🧠 Starting LLM-powered domain agent processing")
            
            # Step 1: LLM-powered intent analysis and planning
            intent_analysis = await self._llm_intent_analysis(message, customer_id, thinking_steps)
            
            # Step 2: A2A orchestration with technical agent
            technical_data = await self._a2a_orchestration(intent_analysis, customer_id, 
                                                          thinking_steps, orchestration_events, a2a_calls)
            
            # Step 3: LLM response synthesis
            response = await self._llm_response_synthesis(message, intent_analysis, technical_data, thinking_steps)
            
            thinking_steps.append("✅ Domain agent processing completed successfully")
            
            return {
                "response": response,
                "intent": intent_analysis.get("intent"),
                "confidence": intent_analysis.get("confidence"),
                "thinking_steps": thinking_steps,
                "orchestration_events": orchestration_events,
                "a2a_calls": a2a_calls,
                "technical_data_received": bool(technical_data),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Domain agent processing failed: {str(e)}"
            thinking_steps.append(f"❌ {error_msg}")
            logger.error(error_msg)
            
            return {
                "error": error_msg,
                "thinking_steps": thinking_steps,
                "orchestration_events": orchestration_events,
                "a2a_calls": a2a_calls,
                "timestamp": datetime.now().isoformat()
            }

    async def _llm_intent_analysis(self, message: str, customer_id: str, thinking_steps: List[str]) -> Dict[str, Any]:
        """Use LLM to analyze customer intent and plan orchestration"""
        
        thinking_steps.append("🎯 Analyzing customer intent with LLM")
        
        if self.use_mock_llm:
            thinking_steps.append("⚠️  Using mock LLM for intent analysis")
            return self._mock_intent_analysis(message)
        
        try:
            prompt = self.intent_analysis_prompt.format(
                user_message=message,
                customer_id=customer_id
            )
            
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            intent_analysis = json.loads(result_text)
            
            thinking_steps.append(f"✅ LLM intent analysis: {intent_analysis.get('intent')} (confidence: {intent_analysis.get('confidence')})")
            return intent_analysis
            
        except Exception as e:
            thinking_steps.append(f"❌ LLM intent analysis failed: {str(e)}")
            return self._mock_intent_analysis(message)

    def _mock_intent_analysis(self, message: str) -> Dict[str, Any]:
        """Mock intent analysis when LLM is not available"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["policies", "policy", "coverage", "insurance"]):
            return {
                "intent": "policy_inquiry",
                "confidence": 0.9,
                "reasoning": "Customer asking about policies/coverage",
                "data_requirements": ["user_profile", "policy_data"],
                "urgent": False
            }
        elif any(keyword in message_lower for keyword in ["claim", "status", "file"]):
            return {
                "intent": "claims_status",
                "confidence": 0.9,
                "reasoning": "Customer asking about claims",
                "data_requirements": ["user_profile", "claims_data"],
                "urgent": False
            }
        else:
            return {
                "intent": "general_help",
                "confidence": 0.7,
                "reasoning": "General inquiry",
                "data_requirements": ["user_profile"],
                "urgent": False
            }

    async def _a2a_orchestration(self, intent_analysis: Dict[str, Any], customer_id: str, 
                               thinking_steps: List[str], orchestration_events: List[Dict], 
                               a2a_calls: List[Dict]) -> Dict[str, Any]:
        """Orchestrate with technical agent via A2A protocol"""
        
        thinking_steps.append("🔗 Starting A2A orchestration with technical agent")
        
        # Create A2A message for technical agent
        a2a_message = {
            "request_type": "data_request",
            "customer_id": customer_id,
            "intent": intent_analysis.get("intent"),
            "data_requirements": intent_analysis.get("data_requirements", []),
            "urgent": intent_analysis.get("urgent", False),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Record orchestration event
            orchestration_events.append({
                "step": 1,
                "action": "a2a_data_request",
                "message": a2a_message,
                "timestamp": datetime.now().isoformat(),
                "status": "executing"
            })
            
            thinking_steps.append(f"📤 Sending A2A message: {a2a_message['request_type']}")
            
            # Send A2A message to technical agent
            response = await self.a2a_client.send_message(a2a_message)
            
            # Record successful A2A call
            a2a_calls.append({
                "direction": "outbound",
                "message_type": "data_request",
                "success": True,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update orchestration event
            orchestration_events[-1]["status"] = "completed"
            orchestration_events[-1]["response_received"] = True
            
            thinking_steps.append("✅ A2A message sent successfully, data received")
            
            return response.get("data", {})
            
        except Exception as e:
            error_msg = f"A2A orchestration failed: {str(e)}"
            thinking_steps.append(f"❌ {error_msg}")
            logger.error(error_msg)
            
            # Record failed A2A call
            a2a_calls.append({
                "direction": "outbound", 
                "message_type": "data_request",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            # Update orchestration event
            orchestration_events[-1]["status"] = "failed"
            orchestration_events[-1]["error"] = str(e)
            
            # NO FALLBACK - if A2A fails, we fail
            raise RuntimeError(f"A2A communication failed and no fallback allowed: {e}")

    async def _llm_response_synthesis(self, message: str, intent_analysis: Dict[str, Any], 
                                    technical_data: Dict[str, Any], thinking_steps: List[str]) -> str:
        """Use LLM to synthesize response from technical agent data"""
        
        thinking_steps.append("✍️  Synthesizing response with LLM")
        
        if self.use_mock_llm:
            thinking_steps.append("⚠️  Using mock LLM for response synthesis")
            return self._mock_response_synthesis(message, intent_analysis, technical_data)
        
        try:
            prompt = self.response_synthesis_prompt.format(
                user_message=message,
                intent=intent_analysis.get("intent"),
                technical_data=json.dumps(technical_data, indent=2),
                template=self.template[:300] + "..." if len(self.template) > 300 else self.template
            )
            
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            result = response.choices[0].message.content
            thinking_steps.append("✅ LLM response synthesis completed")
            return result
            
        except Exception as e:
            thinking_steps.append(f"❌ LLM response synthesis failed: {str(e)}")
            return self._mock_response_synthesis(message, intent_analysis, technical_data)

    def _mock_response_synthesis(self, message: str, intent_analysis: Dict[str, Any], technical_data: Dict[str, Any]) -> str:
        """Mock response synthesis when LLM is not available"""
        
        intent = intent_analysis.get("intent", "general_help")
        
        if intent == "policy_inquiry":
            return f"""Thank you for your policy inquiry. Based on the information retrieved from our systems:

**Your Account Information:**
{json.dumps(technical_data.get('user_profile', {}), indent=2)}

**Policy Details:**
{json.dumps(technical_data.get('policy_data', {}), indent=2)}

Is there anything specific about your policies you'd like me to explain further?"""
        
        elif intent == "claims_status":
            return f"""Here's your current claims information:

**Claims Status:**
{json.dumps(technical_data.get('claims_data', {}), indent=2)}

**Account Information:**
{json.dumps(technical_data.get('user_profile', {}), indent=2)}

Would you like more details about any specific claim?"""
        
        else:
            return f"""I'm here to help with your insurance needs. Based on your account:

**Your Information:**
{json.dumps(technical_data.get('user_profile', {}), indent=2)}

How can I assist you today? I can help with:
- Policy information and coverage details
- Claims status and filing
- Account management
- General insurance questions"""

async def main():
    """Run the LLM-powered domain agent"""
    try:
        agent = LLMClaimsAgent(port=8000)
        
        print("🧠 LLM Domain Agent starting on http://localhost:8000")
        print("   Health check: http://localhost:8000/health")
        print("   Features: LLM reasoning, A2A orchestration, Template responses")
        print("   Architecture: Domain Agent (LLM + A2A) ↔ Technical Agent (A2A + FastMCP)")
        print("   A2A Required: No fallbacks allowed")
        
        config = uvicorn.Config(agent.app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        print(f"❌ Failed to start domain agent: {e}")
        print("   Make sure Google A2A SDK is installed: pip install a2a")

if __name__ == "__main__":
    asyncio.run(main()) 