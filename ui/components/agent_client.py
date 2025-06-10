#!/usr/bin/env python3
"""
Agent Client for Google ADK + LiteLLM + OpenRouter Integration

Updated to communicate with Google ADK agents running with LiteLLM and OpenRouter models.
"""

import requests
import json
import time
from typing import Dict, Any, List, Optional
from ui.components.config import UIConfig

class ADKAgentClient:
    """Client for communicating with Google ADK agents"""
    
    def __init__(self):
        self.config = UIConfig()
        self.session = requests.Session()
        self.session.timeout = 30
        
    def send_customer_service_message(self, message: str, customer_id: str) -> Dict[str, Any]:
        """Send message to Google ADK customer service agent"""
        
        # Try ADK customer service endpoints
        for endpoint in self.config.ADK_CUSTOMER_SERVICE_ENDPOINTS:
            try:
                # Use Google ADK API format
                url = f"{endpoint}/apps/insurance-adk/chat"
                
                payload = {
                    "message": message,
                    "customer_id": customer_id,
                    "session_metadata": {
                        "ui_source": "streamlit",
                        "timestamp": time.time()
                    }
                }
                
                response = self.session.post(url, json=payload, timeout=15)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "response": result.get("response", result.get("content", "Response received")),
                        "agent": "adk_customer_service",
                        "model": self.config.ADK_CONFIG["default_model"],
                        "endpoint": endpoint,
                        "thinking_steps": result.get("thinking_steps", ["ADK customer service response"]),
                        "orchestration_events": result.get("orchestration_events", ["Message processed by ADK agent"])
                    }
                    
            except requests.RequestException as e:
                print(f"ADK Customer Service endpoint {endpoint} failed: {e}")
                continue
        
        # Fallback to orchestrator if customer service unavailable
        return self.send_orchestrator_message(message, customer_id)
    
    def send_technical_message(self, message: str, customer_id: str) -> Dict[str, Any]:
        """Send message to Google ADK technical agent"""
        
        for endpoint in self.config.ADK_TECHNICAL_AGENT_ENDPOINTS:
            try:
                url = f"{endpoint}/technical/process"
                
                payload = {
                    "request": message,
                    "customer_id": customer_id,
                    "operation": "policy_analysis",
                    "include_mcp_data": True
                }
                
                response = self.session.post(url, json=payload, timeout=20)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "response": result.get("analysis", result.get("response", "Technical analysis completed")),
                        "agent": "adk_technical_agent", 
                        "model": self.config.ADK_CONFIG["technical_model"],
                        "endpoint": endpoint,
                        "thinking_steps": result.get("thinking_steps", ["Technical analysis performed"]),
                        "orchestration_events": result.get("orchestration_events", ["Technical request processed"])
                    }
                    
            except requests.RequestException as e:
                print(f"ADK Technical endpoint {endpoint} failed: {e}")
                continue
        
        return self._fallback_response("technical analysis", customer_id)
    
    def send_orchestrator_message(self, message: str, customer_id: str) -> Dict[str, Any]:
        """Send message to Google ADK orchestrator agent"""
        
        for endpoint in self.config.ADK_ORCHESTRATOR_ENDPOINTS:
            try:
                url = f"{endpoint}/orchestrate"
                
                payload = {
                    "customer_request": message,
                    "customer_id": customer_id,
                    "workflow": "customer_inquiry_processing",
                    "require_coordination": True
                }
                
                response = self.session.post(url, json=payload, timeout=25)
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "response": result.get("coordinated_response", result.get("response", "Orchestrated response")),
                        "agent": "adk_orchestrator",
                        "model": self.config.ADK_CONFIG["orchestrator_model"],
                        "endpoint": endpoint,
                        "sub_agents": result.get("agents_consulted", ["customer_service", "technical"]),
                        "thinking_steps": result.get("thinking_steps", ["Orchestration workflow executed"]),
                        "orchestration_events": result.get("orchestration_events", ["Multi-agent coordination completed"])
                    }
                    
            except requests.RequestException as e:
                print(f"ADK Orchestrator endpoint {endpoint} failed: {e}")
                continue
        
        return self._fallback_response("coordinated assistance", customer_id)
    
    def _fallback_response(self, service_type: str, customer_id: str) -> Dict[str, Any]:
        """Fallback response when all endpoints fail"""
        return {
            "response": f"I'm here to help with your insurance needs. However, I'm currently unable to connect to the {service_type} services. Our Google ADK agents are temporarily unavailable. Please try again later.",
            "agent": "fallback",
            "model": "none",
            "endpoint": "none",
            "thinking_steps": [f"Attempted {service_type} connection", "All endpoints failed", "Fallback response generated"],
            "orchestration_events": ["Request received", f"{service_type.title()} connection failed", "Fallback response sent"]
        }

# Legacy class for backwards compatibility
class DomainAgentClient:
    """Legacy client - redirects to ADK client"""
    
    def __init__(self):
        self.adk_client = ADKAgentClient()
    
    def send_message(self, message: str, customer_id: str) -> Dict[str, Any]:
        """Legacy method - redirects to ADK customer service"""
        return self.adk_client.send_customer_service_message(message, customer_id)

def send_chat_message_simple(message: str, customer_id: str) -> Dict[str, Any]:
    """Simple chat function that tries ADK agents first"""
    client = ADKAgentClient()
    return client.send_customer_service_message(message, customer_id) 