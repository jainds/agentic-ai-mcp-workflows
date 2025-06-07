"""
FastAPI Server with Google ADK Integration
Provides external API interfaces for the ADK-based insurance agent system
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our ADK orchestrator
from agents.orchestrator import create_adk_orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class CustomerInquiryRequest(BaseModel):
    message: str = Field(..., description="Customer message")
    session_id: Optional[str] = Field(None, description="Session ID")
    customer_id: Optional[str] = Field(None, description="Customer ID")

class TechnicalRequest(BaseModel):
    customer_id: str = Field(..., description="Customer ID")
    operation: str = Field(default="get_customer_policies", description="Operation type")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional parameters")

class SessionRequest(BaseModel):
    customer_id: Optional[str] = Field(None, description="Customer ID for authentication")

# Initialize FastAPI app
app = FastAPI(
    title="Insurance AI ADK System",
    description="FastAPI server with Google ADK integration for insurance agents",
    version="2.0.0-adk"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize ADK orchestrator on startup"""
    global orchestrator
    try:
        logger.info("🚀 Starting Insurance AI ADK System...")
        orchestrator = create_adk_orchestrator()
        logger.info("✅ ADK Orchestrator initialized successfully")
        
        # Test health check
        health_result = await orchestrator.route_request("health_check")
        if health_result.get("success"):
            logger.info("✅ System health check passed")
        else:
            logger.warning("⚠️ System health check failed")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize ADK orchestrator: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    global orchestrator
    if orchestrator:
        try:
            await orchestrator.close()
            logger.info("✅ ADK Orchestrator closed successfully")
        except Exception as e:
            logger.error(f"❌ Error closing orchestrator: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Insurance AI ADK System",
        "version": "2.0.0-adk",
        "framework": "Google ADK v1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        
        health_result = await orchestrator.route_request("health_check")
        
        if health_result.get("success"):
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "details": health_result.get("status", {}),
                "framework": "Google ADK"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": health_result.get("error", "Health check failed"),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions")
async def create_session(request: SessionRequest):
    """Create a new customer session"""
    try:
        session_id = str(uuid.uuid4())
        
        # If customer_id provided, authenticate immediately
        if request.customer_id:
            # Use domain agent for authentication through orchestrator
            auth_result = await orchestrator.domain_agent.check_authentication(
                session_id=session_id,
                customer_id=request.customer_id
            )
            
            return {
                "session_id": session_id,
                "customer_id": request.customer_id,
                "authenticated": auth_result.get("authenticated", False),
                "created_at": datetime.now().isoformat()
            }
        else:
            return {
                "session_id": session_id,
                "authenticated": False,
                "created_at": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/customer/inquiry")
async def handle_customer_inquiry(request: CustomerInquiryRequest):
    """Handle customer inquiry using ADK orchestration"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not ready")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Process inquiry through ADK orchestrator
        result = await orchestrator.route_request(
            request_type="customer_inquiry",
            message=request.message,
            session_id=session_id,
            customer_id=request.customer_id
        )
        
        if result.get("success"):
            return {
                "response": result.get("response", ""),
                "session_id": session_id,
                "customer_id": request.customer_id,
                "processed_by": "adk_orchestrator",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "error": result.get("error", "Processing failed"),
                    "response": result.get("response", "I apologize, but I couldn't process your request."),
                    "session_id": session_id
                }
            )
            
    except Exception as e:
        logger.error(f"Customer inquiry error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/technical/data")
async def handle_technical_request(request: TechnicalRequest):
    """Handle technical data request using ADK orchestration"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not ready")
        
        # Prepare technical request
        tech_request = {
            "customer_id": request.customer_id,
            "operation": request.operation,
            "parameters": request.parameters
        }
        
        # Process through ADK orchestrator
        result = await orchestrator.route_request(
            request_type="technical_request",
            request=tech_request
        )
        
        if result.get("success"):
            return {
                "data": result.get("data", {}),
                "customer_id": request.customer_id,
                "operation": request.operation,
                "processed_by": "adk_orchestrator",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "error": result.get("error", "Technical processing failed"),
                    "customer_id": request.customer_id,
                    "operation": request.operation
                }
            )
            
    except Exception as e:
        logger.error(f"Technical request error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows")
async def get_available_workflows():
    """Get list of available ADK workflows"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not ready")
        
        workflows = await orchestrator.get_available_workflows()
        
        return {
            "workflows": workflows,
            "framework": "Google ADK",
            "total_count": len(workflows)
        }
        
    except Exception as e:
        logger.error(f"Workflows list error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not ready")
        
        return {
            "domain_agent": {
                "name": orchestrator.domain_agent.name,
                "description": orchestrator.domain_agent.description,
                "status": "active"
            },
            "technical_agent": {
                "name": orchestrator.technical_agent.name,
                "description": orchestrator.technical_agent.description,
                "status": "active"
            },
            "orchestrator": {
                "status": "active",
                "workflows": list(orchestrator.workflows.keys())
            },
            "framework": "Google ADK v1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Agent status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# A2A compatibility endpoint (legacy support)
@app.post("/a2a/handle_task")
async def handle_a2a_task(request: Request):
    """A2A compatibility endpoint for legacy systems"""
    try:
        if not orchestrator:
            raise HTTPException(status_code=503, detail="System not ready")
        
        # Parse A2A request
        body = await request.json()
        
        # Convert to technical request format
        tech_request = {
            "customer_id": body.get("customer_id", ""),
            "operation": body.get("operation", "get_customer_policies"),
            "parameters": body.get("parameters", {})
        }
        
        # Process through orchestrator
        result = await orchestrator.route_request(
            request_type="technical_request",
            request=tech_request
        )
        
        # Return in A2A format
        if result.get("success"):
            return {
                "status": "success",
                "data": result.get("data", {}),
                "agent": "adk_technical_agent",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "error": result.get("error", "A2A processing failed"),
                    "agent": "adk_technical_agent"
                }
            )
            
    except Exception as e:
        logger.error(f"A2A task error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Load configuration
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    debug = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Insurance AI ADK Server on {host}:{port}")
    logger.info(f"🤖 Using Google ADK v1.0.0")
    logger.info(f"🔧 Debug mode: {debug}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    ) 