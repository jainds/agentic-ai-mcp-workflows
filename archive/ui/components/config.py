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
    
    # Agent endpoints
    DOMAIN_AGENT_ENDPOINTS = [
        "http://enhanced-domain-agent:8000",  # Enhanced Python A2A Domain Agent (Kubernetes service)
        "http://claims-agent:8000",          # Legacy agent (fallback)
        "http://localhost:8080",             # Port forwarded enhanced agent
        "http://localhost:8000",             # Local testing
        "http://127.0.0.1:8000"              # Fallback
    ]
    
    # Demo customer data
    DEMO_CUSTOMERS = {
        "CUST-001": {"name": "John Smith", "status": "Active", "type": "Premium"},
        "CUST-002": {"name": "Jane Doe", "status": "Active", "type": "Standard"},
        "CUST-003": {"name": "Bob Johnson", "status": "Active", "type": "Basic"},
        "TEST-CUSTOMER": {"name": "Test User", "status": "Active", "type": "Demo"}
    }
    
    # Service endpoints for monitoring
    MONITORED_SERVICES = {
        "Enhanced Domain Agent (Python A2A)": "http://enhanced-domain-agent:8000/health",
        "Python A2A Data Agent": "http://python-a2a-data-agent:8002/health",
        "Python A2A Notification Agent": "http://python-a2a-notification-agent:8003/health",
        "Python A2A FastMCP Agent": "http://python-a2a-fastmcp-agent:8004/health",
        "Claims Agent (Legacy)": "http://claims-agent:8000/health",
        "User Service (FastMCP)": "http://user-service:8000/mcp/",
        "Claims Service (FastMCP)": "http://claims-service:8001/mcp/", 
        "Policy Service (FastMCP)": "http://policy-service:8002/mcp/",
        "Analytics Service (FastMCP)": "http://analytics-service:8003/mcp/",
        "FastMCP Data Agent": "http://fastmcp-data-agent:8004/health"
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