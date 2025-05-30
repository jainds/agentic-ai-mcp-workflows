"""
Domain Agent Core Module
Main orchestration class that coordinates all domain agent functionality
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from openai import OpenAI

# python-a2a library imports
from python_a2a import (
    Message, TextContent, MessageRole, AgentNetwork, AIAgentRouter
)

from agents.shared.python_a2a_base import PythonA2AAgent
from agents.shared.auth import service_auth

# Import our specialized modules
from .intent_analyzer import IntentAnalyzer
from .execution_planner import ExecutionPlanner
from .response_generator import ResponseGenerator
from .http_endpoints import HTTPEndpointManager

logger = structlog.get_logger(__name__)


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
        
        # Setup LLM client first
        self.setup_llm_client()
        
        # Initialize specialized modules
        self.intent_analyzer = IntentAnalyzer(self.llm_client, self.model_name)
        
        # Initialize agent network and technical agents
        self.setup_technical_agents()
        
        # Initialize execution planner with agent registry
        self.execution_planner = ExecutionPlanner(self.agent_registry, self.call_agent)
        
        # Initialize response generator
        self.template_enhancement_enabled = True
        self.response_generator = ResponseGenerator(self.template_enhancement_enabled)
        
        # Setup AI-powered router
        self.setup_ai_router()
        
        # Setup HTTP endpoints manager
        self.http_manager = HTTPEndpointManager(self)
        self.app = self.http_manager.setup_http_endpoints()
        
        logger.info("Enhanced Python A2A Domain Agent initialized with modular architecture")

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
        
        # Register technical agents with proper A2A URLs
        self.register_agent("data_agent", os.getenv('DATA_AGENT_URL', 'http://python-a2a-data-agent:8002'))
        # Temporarily disabled crashing agents for core functionality testing
        # self.register_agent("notification_agent", os.getenv('NOTIFICATION_AGENT_URL', 'http://python-a2a-notification-agent:8003'))
        # self.register_agent("fastmcp_agent", os.getenv('FASTMCP_AGENT_URL', 'http://python-a2a-fastmcp-agent:8004'))
        
        # Add to agent network using correct method
        if self.agent_network:
            self.agent_network.add("data_agent", os.getenv('DATA_AGENT_URL', 'http://python-a2a-data-agent:8002'))
        
        logger.info("Technical agents registered for A2A communication", 
                   registered_agents=list(self.agent_registry.keys()))

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
        Main message handler implementing the three-role functionality:
        1. Intent understanding and planning
        2. Task routing and coordination
        3. Response preparation
        """
        try:
            user_text = message.content.text
            conversation_id = getattr(message, 'conversation_id', str(uuid.uuid4()))
            
            logger.info("Processing user request", 
                       text=user_text[:100], 
                       conversation_id=conversation_id)
            
            # Role 1: Intent Understanding & Planning
            intent_analysis = self.intent_analyzer.understand_intent(user_text)
            execution_plan = self.execution_planner.create_execution_plan(intent_analysis, user_text)
            
            # Role 2: Task Routing & Execution
            execution_results = self.execution_planner.execute_plan(execution_plan, conversation_id)
            
            # Role 3: Response Preparation
            final_response = self.response_generator.prepare_response(intent_analysis, execution_results, user_text)
            
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

    async def process_user_message(self, message: str, customer_id: str = "default-customer") -> Dict[str, Any]:
        """Process user message through the enhanced domain agent workflow"""
        # Role 1: Intent Understanding & Planning - NO ERROR HANDLING, LET ERRORS PROPAGATE
        intent_analysis = self.intent_analyzer.understand_intent(message)
        
        # Role 2: Create and execute plan - NO ERROR HANDLING, LET ERRORS PROPAGATE  
        execution_plan = self.execution_planner.create_execution_plan(intent_analysis, message, customer_id)
        execution_results = self.execution_planner.execute_plan(execution_plan, customer_id)
        
        # Role 3: Prepare professional response - NO ERROR HANDLING, LET ERRORS PROPAGATE
        response = self.response_generator.prepare_response(intent_analysis, execution_results, message)
        
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
        self.http_manager.run_http_server(host=host, port=port)


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