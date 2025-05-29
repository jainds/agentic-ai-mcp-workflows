"""
Dashboard Configuration Management
Centralized configuration for the Insurance AI PoC Dashboard
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """Configuration for external services"""
    name: str
    url: str
    health_endpoint: str
    timeout: int = 30


@dataclass
class DashboardConfig:
    """Main dashboard configuration"""
    host: str = "0.0.0.0"
    port: int = 8501
    debug_mode: bool = False
    auto_refresh: bool = False
    refresh_interval: int = 5
    max_conversation_history: int = 50
    enable_analytics: bool = True
    enable_health_monitoring: bool = True


class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        self.dashboard = DashboardConfig(
            host=os.getenv("DASHBOARD_HOST", "0.0.0.0"),
            port=int(os.getenv("DASHBOARD_PORT", "8501")),
            debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
            auto_refresh=os.getenv("ENABLE_AUTO_REFRESH", "false").lower() == "true",
            refresh_interval=int(os.getenv("REFRESH_INTERVAL", "5")),
            max_conversation_history=int(os.getenv("MAX_CONVERSATION_HISTORY", "50")),
            enable_analytics=os.getenv("ENABLE_ANALYTICS", "true").lower() == "true",
            enable_health_monitoring=os.getenv("ENABLE_HEALTH_MONITORING", "true").lower() == "true"
        )
        
        self.services = {
            "claims_agent": ServiceConfig(
                name="Claims Agent",
                url=os.getenv("CLAIMS_AGENT_URL", "http://claims-agent:8000"),
                health_endpoint="/health"
            ),
            "data_agent": ServiceConfig(
                name="Data Agent", 
                url=os.getenv("DATA_AGENT_URL", "http://data-agent:8002"),
                health_endpoint="/health"
            ),
            "notification_agent": ServiceConfig(
                name="Notification Agent",
                url=os.getenv("NOTIFICATION_AGENT_URL", "http://notification-agent:8003"),
                health_endpoint="/health"
            ),
            "claims_service": ServiceConfig(
                name="Claims Service",
                url=os.getenv("CLAIMS_SERVICE_URL", "http://claims-service:8000"),
                health_endpoint="/health"
            ),
            "user_service": ServiceConfig(
                name="User Service",
                url=os.getenv("USER_SERVICE_URL", "http://user-service:8000"),
                health_endpoint="/health"
            ),
            "policy_service": ServiceConfig(
                name="Policy Service",
                url=os.getenv("POLICY_SERVICE_URL", "http://policy-service:8000"),
                health_endpoint="/health"
            )
        }
        
        self.feature_flags = {
            "quick_actions": os.getenv("FEATURE_QUICK_ACTIONS", "true").lower() == "true",
            "workflow_visualization": os.getenv("FEATURE_WORKFLOW_VIZ", "true").lower() == "true",
            "performance_metrics": os.getenv("FEATURE_PERFORMANCE_METRICS", "true").lower() == "true",
            "health_dashboard": os.getenv("FEATURE_HEALTH_DASHBOARD", "true").lower() == "true",
            "llm_thinking": os.getenv("FEATURE_LLM_THINKING", "true").lower() == "true",
            "api_monitor": os.getenv("FEATURE_API_MONITOR", "true").lower() == "true",
            "agent_activity": os.getenv("FEATURE_AGENT_ACTIVITY", "true").lower() == "true",
            "advanced_analytics": os.getenv("FEATURE_ADVANCED_ANALYTICS", "true").lower() == "true"
        }


# Quick Actions Configuration
QUICK_ACTIONS = {
    "Domain Agent Tests": {
        "🔧 Claims Processing": {
            "message": "I was in a car accident yesterday and need to file a claim. Policy number POL-AUTO-123456.",
            "description": "Test end-to-end claims processing workflow"
        },
        "🏥 Policy Inquiry": {
            "message": "What does my auto insurance policy cover for accident damage?",
            "description": "Test policy lookup and coverage analysis"
        },
        "💰 Billing Question": {
            "message": "I have a question about my recent premium payment and billing cycle.",
            "description": "Test billing and payment inquiries"
        },
        "🚨 Fraud Detection": {
            "message": "I suspect fraudulent activity on my account. Can you investigate?",
            "description": "Test fraud detection and security workflows"
        },
        "📞 Customer Support": {
            "message": "I need help understanding my policy benefits and deductibles.",
            "description": "Test general customer support capabilities"
        }
    },
    "Technical Agent Tests": {
        "📊 Risk Assessment": {
            "message": "Analyze risk factors for policy POL-AUTO-123456",
            "description": "Test data analysis and risk calculation"
        },
        "📈 Data Analytics": {
            "message": "Generate claims analytics report for the last quarter",
            "description": "Test analytics and reporting capabilities"
        },
        "🔗 System Integration": {
            "message": "Check integration status with external payment systems",
            "description": "Test system integration health"
        },
        "⚡ Performance Analysis": {
            "message": "Analyze system performance metrics for optimization",
            "description": "Test performance monitoring and analysis"
        }
    },
    "MCP Service Direct Tests": {
        "📋 Policy Service": {
            "endpoint": "/policy/lookup",
            "payload": {"policy_number": "POL-AUTO-123456"},
            "description": "Direct policy service call"
        },
        "🏥 Claims Service": {
            "endpoint": "/claims/create",
            "payload": {"customer_id": "CUST-001", "description": "Test claim"},
            "description": "Direct claims service call"
        },
        "👤 Customer Service": {
            "endpoint": "/customer/lookup",
            "payload": {"customer_id": "CUST-001"},
            "description": "Direct customer service call"
        },
        "📊 Analytics Service": {
            "endpoint": "/analytics/report",
            "payload": {"report_type": "claims_summary"},
            "description": "Direct analytics service call"
        }
    }
}

# Chart Configurations
CHART_CONFIGS = {
    "response_times": {
        "title": "API Response Times",
        "x_axis": "Time",
        "y_axis": "Response Time (ms)",
        "chart_type": "line"
    },
    "success_rates": {
        "title": "Success Rates by Service",
        "chart_type": "bar"
    },
    "workflow_distribution": {
        "title": "Workflow Distribution",
        "chart_type": "pie"
    },
    "agent_activity": {
        "title": "Agent Activity Timeline",
        "x_axis": "Time",
        "y_axis": "Number of Requests",
        "chart_type": "area"
    }
}

# System Health Thresholds
HEALTH_THRESHOLDS = {
    "response_time_warning": 1000,  # ms
    "response_time_critical": 5000,  # ms
    "success_rate_warning": 95,     # %
    "success_rate_critical": 85,    # %
    "cpu_usage_warning": 70,        # %
    "cpu_usage_critical": 90,       # %
    "memory_usage_warning": 80,     # %
    "memory_usage_critical": 95     # %
}

# LLM Configuration
LLM_CONFIG = {
    "max_tokens": {
        "min": 100,
        "max": 4000,
        "default": 1000
    },
    "temperature": {
        "min": 0.0,
        "max": 2.0,
        "default": 0.7
    },
    "enable_tracing": True,
    "enable_guardrails": True,
    "thinking_delay": 0.1  # seconds between thinking steps
} 