#!/usr/bin/env python3
"""
Domain Agent Client Component for Insurance AI UI
"""

import streamlit as st
import requests
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any
from ui.components.config import UIConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainAgentClient:
    """Client to communicate with actual domain agent"""
    
    def __init__(self):
        self.base_url = None
        self._find_active_endpoint()
    
    def _find_active_endpoint(self):
        """Find the active domain agent endpoint"""
        for endpoint in UIConfig.DOMAIN_AGENT_ENDPOINTS:
            try:
                response = requests.get(f"{endpoint}/health", timeout=2)
                if response.status_code == 200:
                    self.base_url = endpoint
                    logger.info(f"Connected to domain agent at {endpoint}")
                    return
            except requests.RequestException:
                continue
        
        logger.warning("No active domain agent endpoint found")
    
    def send_message(self, message: str, customer_id: str) -> Dict[str, Any]:
        """Send message to real domain agent"""
        if not self.base_url:
            return {
                "response": "❌ Domain agent is not available. Please check system health.",
                "error": "No active domain agent endpoint",
                "thinking_steps": [],
                "orchestration_events": [],
                "api_calls": []
            }
        
        try:
            # Log the outgoing API call
            call_start = time.time()
            
            payload = {
                "message": message,
                "customer_id": customer_id,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            call_duration = time.time() - call_start
            
            # Log this API call for monitoring (if enabled)
            if UIConfig.ENABLE_API_MONITORING:
                self._log_api_call(
                    "Domain Agent",
                    "/chat",
                    "POST",
                    payload,
                    response.json() if response.status_code == 200 else {"error": response.text},
                    response.status_code,
                    call_duration
                )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract real orchestration data from agent response (if features enabled)
                if UIConfig.ENABLE_THINKING_STEPS and "thinking_steps" in result:
                    if 'thinking_steps' not in st.session_state:
                        st.session_state.thinking_steps = []
                    st.session_state.thinking_steps.extend(result["thinking_steps"])
                
                if UIConfig.ENABLE_ORCHESTRATION_VIEW and "orchestration_events" in result:
                    if 'orchestration_data' not in st.session_state:
                        st.session_state.orchestration_data = []
                    st.session_state.orchestration_data.extend(result["orchestration_events"])
                
                if UIConfig.ENABLE_API_MONITORING and "api_calls" in result:
                    if 'api_calls' not in st.session_state:
                        st.session_state.api_calls = []
                    st.session_state.api_calls.extend(result["api_calls"])
                
                return result
            else:
                error_msg = f"Domain agent error: HTTP {response.status_code}"
                logger.error(error_msg)
                return {
                    "response": f"❌ {error_msg}",
                    "error": error_msg,
                    "thinking_steps": [],
                    "orchestration_events": [],
                    "api_calls": []
                }
                
        except requests.RequestException as e:
            error_msg = f"Failed to communicate with domain agent: {str(e)}"
            logger.error(error_msg)
            return {
                "response": f"❌ {error_msg}",
                "error": error_msg,
                "thinking_steps": [],
                "orchestration_events": [],
                "api_calls": []
            }
    
    def _log_api_call(self, service: str, endpoint: str, method: str, 
                     request_data: Dict = None, response_data: Dict = None, 
                     status_code: int = 200, response_time: float = 0.0):
        """Log API call for monitoring"""
        if not UIConfig.ENABLE_API_MONITORING:
            return
            
        call_id = str(uuid.uuid4())[:8]
        api_call = {
            "call_id": call_id,
            "timestamp": datetime.now(),
            "service": service,
            "endpoint": endpoint,
            "method": method,
            "request_data": request_data or {},
            "response_data": response_data or {},
            "status_code": status_code,
            "response_time_ms": round(response_time * 1000, 2),
            "success": 200 <= status_code < 400
        }
        
        if 'api_calls' not in st.session_state:
            st.session_state.api_calls = []
        
        st.session_state.api_calls.append(api_call)
        
        # Keep only last 50 API calls
        if len(st.session_state.api_calls) > 50:
            st.session_state.api_calls = st.session_state.api_calls[-50:]

def send_chat_message_simple(message: str, customer_id: str) -> Dict[str, Any]:
    """Simple fallback chat function for basic mode"""
    try:
        # Try domain agent first (Kubernetes service name)
        agent_url = "http://claims-agent:8000/chat"
        
        response = requests.post(
            agent_url,
            json={
                "message": message,
                "customer_id": customer_id
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"response": f"Error: HTTP {response.status_code}"}
            
    except requests.RequestException as e:
        # Fallback response
        return {
            "response": f"I'm here to help with your insurance needs. However, I'm currently unable to connect to the backend services. Please try again later. (Error: {str(e)})",
            "thinking_steps": ["Connection attempt to domain agent", "Fallback response generated"],
            "orchestration_events": ["Chat request received", "Backend connection failed", "Fallback response sent"]
        } 