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
    
    # Agent endpoints - Updated for Google ADK + A2A architecture
    DOMAIN_AGENT_ENDPOINTS = [
        "http://insurance-ai-poc-domain-agent:8003",    # Domain Agent (Kubernetes service)
        "http://localhost:8003",                        # Port forwarded domain agent  
        "http://127.0.0.1:8003"                        # Local domain agent
    ]
    
    # Demo customer data
    DEMO_CUSTOMERS = {
        "CUST-001": {"name": "John Smith", "status": "Active", "type": "Premium"},
        "CUST-002": {"name": "Jane Doe", "status": "Active", "type": "Standard"},
        "CUST-003": {"name": "Bob Johnson", "status": "Active", "type": "Basic"},
        "TEST-CUSTOMER": {"name": "Test User", "status": "Active", "type": "Demo"}
    }
    
    # Service endpoints for monitoring - Updated for current architecture
    MONITORED_SERVICES = {
        "Domain Agent (Google ADK)": "http://localhost:8003/health",
        "Technical Agent (A2A)": "http://localhost:8002/health", 
        "Policy Server (MCP)": "http://localhost:8001/mcp",
        "A2A Communication": "http://localhost:8002/a2a/agent.json",
        "ADK Orchestrator": "http://localhost:8000/health"
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