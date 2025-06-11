#!/usr/bin/env python3
"""
Configuration and Feature Toggles for Insurance AI UI
Updated for Google ADK + LiteLLM + OpenRouter Integration
"""

import os
from typing import Dict, Any

class UIConfig:
    """Configuration for UI features and toggles"""
    
    # Feature toggles - can be controlled via environment variables
    ENABLE_ADVANCED_FEATURES = os.getenv("ENABLE_ADVANCED_FEATURES", "true").lower() == "true"
    ENABLE_SYSTEM_MONITORING = os.getenv("ENABLE_SYSTEM_MONITORING", "true").lower() == "true"
    ENABLE_API_MONITORING = os.getenv("ENABLE_API_MONITORING", "true").lower() == "true"
    ENABLE_THINKING_STEPS = os.getenv("ENABLE_THINKING_STEPS", "true").lower() == "true"
    ENABLE_ORCHESTRATION_VIEW = os.getenv("ENABLE_ORCHESTRATION_VIEW", "true").lower() == "true"
    
    # UI Mode: "simple" or "advanced"
    UI_MODE = os.getenv("UI_MODE", "advanced")  # Default to advanced mode
    
    # Google ADK Agent endpoints - Updated for LiteLLM + OpenRouter integration
    ADK_CUSTOMER_SERVICE_ENDPOINTS = [
        "http://adk-customer-service:8000",             # Kubernetes service
        "http://localhost:8000",                        # Port forwarded ADK web
        "http://127.0.0.1:8000"                        # Local ADK web
    ]
    
    ADK_TECHNICAL_AGENT_ENDPOINTS = [
        "http://adk-technical-agent:8002",              # Kubernetes service  
        "http://localhost:8002",                        # Port forwarded ADK API
        "http://127.0.0.1:8002"                        # Local ADK API
    ]
    
    ADK_ORCHESTRATOR_ENDPOINTS = [
        "http://adk-orchestrator:8003",                 # Kubernetes service
        "http://localhost:8003",                        # Port forwarded orchestrator
        "http://127.0.0.1:8003"                        # Local orchestrator
    ]
    
    # Legacy endpoints (for backwards compatibility)
    DOMAIN_AGENT_ENDPOINTS = [
        "http://insurance-ai-poc-domain-agent:8003",    # Legacy Kubernetes service
        "http://localhost:8003",                        # Legacy port forwarded  
        "http://127.0.0.1:8003"                        # Legacy local
    ]
    
    # Demo customer data
    DEMO_CUSTOMERS = {
        "CUST001": {"name": "John Smith", "status": "Active", "type": "Premium"},
        "CUST002": {"name": "Jane Doe", "status": "Active", "type": "Standard"},
        "CUST003": {"name": "Bob Johnson", "status": "Active", "type": "Basic"},
        "CUST004": {"name": "Alice Williams", "status": "Active", "type": "Standard"},
        "TEST-CUSTOMER": {"name": "Test User", "status": "Active", "type": "Demo"}
    }
    
    # Service endpoints for monitoring - Updated for Google ADK architecture
    MONITORED_SERVICES = {
        "ADK Customer Service": "http://localhost:8000/health",
        "ADK Technical Agent": "http://localhost:8002/health", 
        "ADK Orchestrator": "http://localhost:8003/health",
        "Policy Server (MCP)": "http://localhost:8001/mcp",
        "Google ADK Web UI": "http://localhost:8000/dev-ui/",
        "Streamlit UI": "http://localhost:8501"
    }
    
    # Google ADK specific configuration
    ADK_CONFIG = {
        "framework": "Google ADK v1.2.1",
        "model_provider": "OpenRouter",
        "integration": "LiteLLM",
        "default_model": "openai/gpt-4o-mini",
        "orchestrator_model": "anthropic/claude-3-5-sonnet",
        "technical_model": "openai/gpt-4o-mini"
    }
    
    # Agent communication patterns
    AGENT_PATTERNS = {
        "customer_service": {
            "type": "LlmAgent",
            "capabilities": ["chat", "inquiry_handling", "customer_support"],
            "endpoints": ADK_CUSTOMER_SERVICE_ENDPOINTS
        },
        "technical_agent": {
            "type": "LlmAgent", 
            "capabilities": ["policy_analysis", "mcp_integration", "data_processing"],
            "endpoints": ADK_TECHNICAL_AGENT_ENDPOINTS
        },
        "orchestrator": {
            "type": "LlmAgent",
            "capabilities": ["workflow_coordination", "multi_agent_communication", "response_synthesis"],
            "endpoints": ADK_ORCHESTRATOR_ENDPOINTS
        }
    }

    @classmethod
    def is_simple_mode(cls) -> bool:
        """Check if UI is in simple mode"""
        return cls.UI_MODE.lower() == "simple"
    
    @classmethod
    def is_advanced_mode(cls) -> bool:
        """Check if UI is in advanced mode"""
        return cls.UI_MODE.lower() == "advanced"
    
    @classmethod
    def get_enabled_features(cls) -> Dict[str, bool]:
        """Get all enabled features"""
        return {
            "advanced_features": cls.ENABLE_ADVANCED_FEATURES,
            "system_monitoring": cls.ENABLE_SYSTEM_MONITORING,
            "api_monitoring": cls.ENABLE_API_MONITORING,
            "thinking_steps": cls.ENABLE_THINKING_STEPS,
            "orchestration_view": cls.ENABLE_ORCHESTRATION_VIEW,
            "simple_mode": cls.is_simple_mode(),
            "advanced_mode": cls.is_advanced_mode()
        } 

# Backwards compatibility
class Config(UIConfig):
    """Legacy config class for backwards compatibility"""
    pass 