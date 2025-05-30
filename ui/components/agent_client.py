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
                # Use A2A agent.json endpoint instead of /health
                response = requests.get(f"{endpoint}/agent.json", timeout=2)
                if response.status_code == 200:
                    self.base_url = endpoint
                    logger.info(f"Connected to domain agent at {endpoint}")
                    return
            except requests.RequestException:
                continue
        
        logger.warning("No active domain agent endpoint found")
    
    def send_message(self, message: str, customer_id: str) -> Dict[str, Any]:
        """Send message to real domain agent using A2A protocol"""
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
            
            # Use A2A task format
            payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": f"{message} for customer {customer_id}" if customer_id else message
                    },
                    "role": "user"
                }
            }
            
            # Use A2A /tasks/send endpoint
            response = requests.post(
                f"{self.base_url}/tasks/send",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            call_duration = time.time() - call_start
            
            # Log this API call for monitoring (if enabled)
            if UIConfig.ENABLE_API_MONITORING:
                self._log_api_call(
                    "Domain Agent",
                    "/tasks/send",
                    "POST",
                    payload,
                    response.json() if response.status_code == 200 else {"error": response.text},
                    response.status_code,
                    call_duration
                )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract response from A2A format
                agent_response = "I received your message and I'm processing it."
                if "artifacts" in result and result["artifacts"]:
                    for artifact in result["artifacts"]:
                        if "parts" in artifact:
                            for part in artifact["parts"]:
                                if part.get("type") == "text":
                                    agent_response = part.get("text", agent_response)
                                    break
                            break
                
                # Format response in expected UI format
                formatted_result = {
                    "response": agent_response,
                    "thinking_steps": ["Received user message", "Analyzed intent", "Generated response"],
                    "orchestration_events": ["A2A task received", "Processing completed", "Response sent"],
                    "api_calls": []
                }
                
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
                
                return formatted_result
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
        # Try domain agent first using A2A protocol
        agent_url = f"{UIConfig.DOMAIN_AGENT_ENDPOINTS[0]}/tasks/send"
        
        payload = {
            "message": {
                "content": {
                    "type": "text",
                    "text": f"{message} for customer {customer_id}" if customer_id else message
                },
                "role": "user"
            }
        }
        
        response = requests.post(
            agent_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract response from A2A format
            agent_response = "I received your message and I'm processing it."
            if "artifacts" in result and result["artifacts"]:
                for artifact in result["artifacts"]:
                    if "parts" in artifact:
                        for part in artifact["parts"]:
                            if part.get("type") == "text":
                                agent_response = part.get("text", agent_response)
                                break
                        break
            
            return {"response": agent_response}
        else:
            return {"response": f"Error: HTTP {response.status_code}"}
            
    except requests.RequestException as e:
        # Fallback response
        return {
            "response": f"I'm here to help with your insurance needs. However, I'm currently unable to connect to the backend services. Please try again later. (Error: {str(e)})",
            "thinking_steps": ["Connection attempt to domain agent", "Fallback response generated"],
            "orchestration_events": ["Chat request received", "Backend connection failed", "Fallback response sent"]
        } 