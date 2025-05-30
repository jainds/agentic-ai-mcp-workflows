"""
HTTP Endpoints Module for Domain Agent
Handles FastAPI endpoints, health checks, and API communication
"""

from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)


# Pydantic models for HTTP API
class ChatRequest(BaseModel):
    message: str
    customer_id: str = "default-customer"


class ChatResponse(BaseModel):
    response: str
    intent: str = None
    confidence: float = None
    thinking_steps: list = []
    orchestration_events: list = []
    api_calls: list = []
    timestamp: str


class HTTPEndpointManager:
    """
    Manages HTTP endpoints and FastAPI setup for the domain agent
    """
    
    def __init__(self, domain_agent):
        """
        Initialize the HTTP endpoint manager
        
        Args:
            domain_agent: Reference to the domain agent instance
        """
        self.domain_agent = domain_agent
        self.app = None
    
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
        
        # Register all endpoints
        self._register_health_endpoints()
        self._register_api_endpoints()
        self._register_utility_endpoints()
        
        return self.app
    
    def _register_health_endpoints(self):
        """Register health and readiness check endpoints"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for Kubernetes"""
            return {
                "status": "healthy",
                "agent_type": "enhanced_domain_agent",
                "version": "1.0.0",
                "template_enabled": self.domain_agent.template_enhancement_enabled,
                "registered_agents": list(self.domain_agent.agent_registry.keys()),
                "capabilities": self.domain_agent.capabilities,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/ready")
        async def readiness_check():
            """Readiness check endpoint for Kubernetes"""
            return {
                "status": "ready",
                "agent_network_size": len(self.domain_agent.agent_registry),
                "template_loaded": bool(self.domain_agent.response_generator.response_template),
                "llm_configured": bool(self.domain_agent.intent_analyzer.llm_client),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _register_api_endpoints(self):
        """Register main API endpoints"""
        
        @self.app.post("/chat", response_model=ChatResponse)
        async def chat_endpoint(request: ChatRequest):
            """Chat endpoint for direct HTTP communication"""
            try:
                # Process the message through the enhanced domain agent
                result = await self.domain_agent.process_user_message(request.message, request.customer_id)
                
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
    
    def _register_utility_endpoints(self):
        """Register utility and testing endpoints"""
        
        @self.app.get("/agent-card")
        async def get_agent_card_endpoint():
            """Get agent card endpoint"""
            return self.domain_agent.get_agent_card()
        
        @self.app.get("/test-llm")
        async def test_llm_endpoint():
            """Test LLM direct call"""
            if not self.domain_agent.intent_analyzer.llm_client:
                return {"error": "No LLM client configured"}
            
            try:
                response = self.domain_agent.intent_analyzer.llm_client.chat.completions.create(
                    model=self.domain_agent.intent_analyzer.model_name,
                    messages=[{"role": "user", "content": "Reply with exactly: claim_status"}],
                    temperature=0.0
                )
                return {
                    "model": self.domain_agent.intent_analyzer.model_name,
                    "response": response.choices[0].message.content,
                    "success": True
                }
            except Exception as e:
                return {"error": str(e), "model": self.domain_agent.intent_analyzer.model_name}
        
        @self.app.get("/agents")
        async def get_registered_agents():
            """Get list of registered technical agents"""
            return {
                "registered_agents": self.domain_agent.agent_registry,
                "agent_count": len(self.domain_agent.agent_registry),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/capabilities")
        async def get_capabilities():
            """Get agent capabilities and configuration"""
            return {
                "capabilities": self.domain_agent.capabilities,
                "skills": self.domain_agent.skills,
                "template_enabled": self.domain_agent.template_enhancement_enabled,
                "llm_model": getattr(self.domain_agent.intent_analyzer, 'model_name', None),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_http_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the HTTP server for Kubernetes deployment"""
        import uvicorn
        logger.info("Starting Enhanced Domain Agent HTTP server", host=host, port=port)
        uvicorn.run(self.app, host=host, port=port) 