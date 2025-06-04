#!/usr/bin/env python3
"""
Configuration and Feature Toggles for Insurance AI UI
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
    
    # Agent endpoints - Updated for current Kubernetes deployment
    DOMAIN_AGENT_ENDPOINTS = [
        os.getenv("DOMAIN_AGENT_URL", "http://insurance-ai-poc-domain-agent:8003"),  # Current Kubernetes service
        "http://localhost:8003",             # Port forwarded current agent
        "http://127.0.0.1:8003"              # Fallback
    ]
    
    # Demo customer data
    DEMO_CUSTOMERS = {
        "CUST-001": {"name": "John Smith", "status": "Active", "type": "Premium"},
        "CUST-002": {"name": "Jane Doe", "status": "Active", "type": "Standard"},
        "CUST-003": {"name": "Bob Johnson", "status": "Active", "type": "Basic"},
        "user_001": {"name": "Test User 1", "status": "Active", "type": "Demo"},
        "user_002": {"name": "Test User 2", "status": "Active", "type": "Demo"},
        "user_003": {"name": "Test User 3", "status": "Active", "type": "Demo"}
    }
    
    # Service endpoints for monitoring - Updated for current deployment
    MONITORED_SERVICES = {
        "Domain Agent": os.getenv("DOMAIN_AGENT_URL", "http://insurance-ai-poc-domain-agent:8003") + "/agent.json",
        "Technical Agent": os.getenv("TECHNICAL_AGENT_URL", "http://insurance-ai-poc-technical-agent:8002") + "/agent.json",
        "Policy Server": os.getenv("POLICY_SERVER_URL", "http://insurance-ai-poc-policy-server:8001") + "/mcp",
        "Streamlit UI": "http://insurance-ai-poc-streamlit-ui:80/healthz"
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