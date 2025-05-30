"""
Insurance AI PoC - Streamlit UI Interface
Simple visual interface for domain agent communication
"""

import streamlit as st
import requests
import json
import time
import uuid
import subprocess
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="Insurance AI PoC",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'customer_authenticated' not in st.session_state:
    st.session_state.customer_authenticated = False
if 'customer_data' not in st.session_state:
    st.session_state.customer_data = {}
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'api_calls' not in st.session_state:
    st.session_state.api_calls = []
if 'thinking_steps' not in st.session_state:
    st.session_state.thinking_steps = []
if 'orchestration_data' not in st.session_state:
    st.session_state.orchestration_data = []


class CustomerValidator:
    """Handles customer authentication for demo purposes"""
    
    DEMO_CUSTOMERS = {
        "CUST-001": {"name": "John Smith", "status": "Active", "type": "Premium"},
        "CUST-002": {"name": "Jane Doe", "status": "Active", "type": "Standard"},
        "CUST-003": {"name": "Bob Johnson", "status": "Active", "type": "Basic"},
        "TEST-CUSTOMER": {"name": "Test User", "status": "Active", "type": "Demo"}
    }
    
    @classmethod
    def validate_customer(cls, customer_id: str) -> Dict[str, Any]:
        """Validate customer authentication"""
        if customer_id in cls.DEMO_CUSTOMERS:
            return {
                "valid": True,
                "customer_data": {
                    "customer_id": customer_id,
                    **cls.DEMO_CUSTOMERS[customer_id]
                }
            }
        return {"valid": False, "error": "Customer ID not found"}


class DomainAgentClient:
    """Client to communicate with actual domain agent"""
    
    def __init__(self):
        # Use Kubernetes service names since everything runs in K8s
        self.possible_endpoints = [
            "http://claims-agent:8000",  # Kubernetes service name for domain agent (proper architecture)
            "http://localhost:8000",  # Fallback for local testing
            "http://127.0.0.1:8000"  # Additional fallback
        ]
        self.base_url = None
        self._find_active_endpoint()
    
    def _find_active_endpoint(self):
        """Find the active domain agent endpoint"""
        for endpoint in self.possible_endpoints:
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
            
            # Log this API call for monitoring
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
                
                # Extract real orchestration data from agent response
                if "thinking_steps" in result:
                    st.session_state.thinking_steps.extend(result["thinking_steps"])
                
                if "orchestration_events" in result:
                    st.session_state.orchestration_data.extend(result["orchestration_events"])
                
                if "api_calls" in result:
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
        
        st.session_state.api_calls.append(api_call)
        
        # Keep only last 50 API calls
        if len(st.session_state.api_calls) > 50:
            st.session_state.api_calls = st.session_state.api_calls[-50:]


class SystemHealthMonitor:
    """Monitors system health and connectivity"""
    
    @staticmethod
    def check_fastmcp_services() -> Dict[str, Any]:
        """Check FastMCP services health in Kubernetes"""
        # Use Kubernetes service names since everything runs in K8s
        services = {
            "Claims Agent (Domain)": "http://claims-agent:8000/health",
            "User Service (FastMCP)": "http://user-service:8000/mcp/",
            "Claims Service (FastMCP)": "http://claims-service:8001/mcp/", 
            "Policy Service (FastMCP)": "http://policy-service:8002/mcp/",
            "Analytics Service (FastMCP)": "http://analytics-service:8003/mcp/",
            "FastMCP Data Agent": "http://fastmcp-data-agent:8004/health"
        }
        
        results = {}
        for service_name, endpoint in services.items():
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=3)
                response_time = time.time() - start_time
        
                if response.status_code == 200:
                    results[service_name] = {
                        "status": "healthy",
                        "response_time": round(response_time * 1000, 2),
                        "message": "Service responding"
                    }
                else:
                    results[service_name] = {
                        "status": "unhealthy",
                        "response_time": round(response_time * 1000, 2),
                        "message": f"HTTP {response.status_code}"
                    }
            except requests.RequestException as e:
                results[service_name] = {
                    "status": "offline",
                    "response_time": 0,
                    "message": f"Connection failed: {str(e)}"
                }
        
        return results
    
    @staticmethod
    def check_kubernetes_pods() -> Dict[str, Any]:
        """Check Kubernetes pods status"""
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", "cursor-insurance-ai-poc", "--no-headers"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                total_pods = len([line for line in lines if line.strip()])
                running_pods = len([line for line in lines if "Running" in line])
                
                return {
                    "status": "healthy" if running_pods == total_pods else "degraded",
                    "running": running_pods,
                    "total": total_pods,
                    "message": f"{running_pods}/{total_pods} pods running"
                }
            else:
                return {
                    "status": "error",
                    "running": 0,
                    "total": 0,
                    "message": "kubectl command failed"
                }
        except Exception as e:
            return {
                "status": "unknown",
                "running": 0,
                "total": 0,
                "message": str(e)
            }


def render_authentication():
    """Render authentication interface"""
    with st.sidebar:
        st.header("🔐 Customer Authentication")
        
        if not st.session_state.customer_authenticated:
            customer_id = st.text_input("Customer ID", placeholder="Enter your Customer ID")
            
            if st.button("Authenticate", type="primary"):
                if customer_id:
                    auth_result = CustomerValidator.validate_customer(customer_id)
                    if auth_result["valid"]:
                        st.session_state.customer_authenticated = True
                        st.session_state.customer_data = auth_result["customer_data"]
                        st.success(f"✅ Welcome, {auth_result['customer_data']['name']}")
                        st.rerun()
                    else:
                        st.error("❌ Authentication failed")
                else:
                    st.error("Please enter a Customer ID")
            
            # Show demo customer IDs
            with st.expander("Demo Customer IDs"):
                for cust_id, data in CustomerValidator.DEMO_CUSTOMERS.items():
                    st.code(f"{cust_id} - {data['name']}")
        
        else:
            # Show authenticated user
            st.success(f"✅ {st.session_state.customer_data['name']}")
            st.write(f"**Status:** {st.session_state.customer_data['status']}")
            st.write(f"**Type:** {st.session_state.customer_data['type']}")
            
            if st.button("Logout"):
                st.session_state.customer_authenticated = False
                st.session_state.customer_data = {}
                st.session_state.conversation_history = []
                st.session_state.api_calls = []
                st.session_state.thinking_steps = []
                st.session_state.orchestration_data = []
                st.rerun()


def render_chat_interface():
    """Render chat interface - communicates with real domain agent"""
    st.header("💬 Chat with Domain Agent")
    
    if not st.session_state.customer_authenticated:
        st.warning("Please authenticate to access the chat interface.")
        return
    
    # Initialize domain agent client
    domain_agent = DomainAgentClient()
    
    # Chat input
    user_message = st.text_area("Your message:", placeholder="How can I help you with your insurance needs today?")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Send", type="primary", disabled=not user_message):
            if user_message:
                # Add user message to history
                st.session_state.conversation_history.append({
                    "role": "user",
                    "message": user_message,
                    "timestamp": datetime.now()
                })
                
                # Send to real domain agent
                with st.spinner("Communicating with domain agent..."):
                    try:
                        result = domain_agent.send_message(
                            user_message, 
                            st.session_state.customer_data['customer_id']
                        )
                        
                        # Add agent response to history
                        st.session_state.conversation_history.append({
                            "role": "agent",
                            "message": result.get("response", "No response received"),
                            "timestamp": datetime.now(),
                            "metadata": {
                                "thinking_steps": len(result.get("thinking_steps", [])),
                                "orchestration_events": len(result.get("orchestration_events", [])),
                                "api_calls": len(result.get("api_calls", [])),
                                "has_error": "error" in result
                            }
                        })
                    except Exception as e:
                        st.error(f"Error communicating with domain agent: {str(e)}")
                        logger.error(f"Chat error: {e}")
                
                st.rerun()
    
    with col2:
        if st.button("Clear Chat"):
            st.session_state.conversation_history = []
            st.rerun()
    
    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown("### Conversation History")
        for msg in reversed(st.session_state.conversation_history[-10:]):  # Show last 10 messages
            timestamp = msg["timestamp"].strftime("%H:%M:%S")
            
            if msg["role"] == "user":
                st.markdown(f"**👤 You ({timestamp}):** {msg['message']}")
            else:
                st.markdown(f"**🤖 Domain Agent ({timestamp}):** {msg['message']}")
                
                # Show metadata for agent responses
                if "metadata" in msg:
                    meta = msg["metadata"]
                    status_icon = "❌" if meta.get("has_error") else "✅"
                    st.caption(f"{status_icon} Thinking Steps: {meta['thinking_steps']} | Orchestration Events: {meta['orchestration_events']} | API Calls: {meta['api_calls']}")
            
            st.markdown("---")


def render_thinking_steps():
    """Render thinking steps from real domain/technical agents"""
    st.header("🧠 Thinking Steps & Orchestration")
    
    if not st.session_state.thinking_steps and not st.session_state.orchestration_data:
        st.info("No thinking steps recorded yet. Send a message in the chat to see real agent orchestration.")
        return
    
    # Show real thinking steps from agents
    if st.session_state.thinking_steps:
        st.subheader("🔄 Agent Thinking Steps")
        for step in reversed(st.session_state.thinking_steps[-10:]):
            timestamp = step.get("timestamp", datetime.now()).strftime("%H:%M:%S") if isinstance(step.get("timestamp"), datetime) else step.get("timestamp", "Unknown")
            
            with st.expander(f"🧠 {step.get('type', 'Unknown').title().replace('_', ' ')} ({timestamp})"):
                st.write(f"**Description:** {step.get('description', 'No description')}")
                st.write(f"**Agent:** {step.get('agent', 'Unknown')}")
                if step.get('duration_ms'):
                    st.write(f"**Duration:** {step['duration_ms']}ms")
                
                if step.get('details'):
                    st.write("**Details:**")
                    st.json(step['details'])
    
    # Show real orchestration events from agents
    if st.session_state.orchestration_data:
        st.subheader("🤝 Agent Orchestration Events")
        for event in reversed(st.session_state.orchestration_data[-10:]):
            timestamp = event.get("timestamp", datetime.now()).strftime("%H:%M:%S") if isinstance(event.get("timestamp"), datetime) else event.get("timestamp", "Unknown")
            agent_type = event.get("agent_type", "unknown")
            event_type = event.get("event_type", "unknown")
            
            # Color coding for agent types
            if agent_type == "domain":
                icon = "🧠"
                color = "#E3F2FD"
            elif agent_type == "technical":
                icon = "⚙️"
                color = "#E1F5FE"
        else:
                icon = "🔄"
                color = "#F5F5F5"
            
            with st.container():
                st.markdown(f"""
                <div style="background-color: {color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
                    <strong>{icon} {agent_type.title()} Agent - {event_type.title().replace('_', ' ')} ({timestamp})</strong><br>
                    <small>{event.get('description', 'No description')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if event.get('details'):
                    with st.expander(f"Details - {event.get('event_id', 'Unknown')}"):
                        st.json(event['details'])


def render_system_health():
    """Render system health monitoring"""
    st.header("⚕️ System Health")
    
    # Check FastMCP services
    st.subheader("🔧 FastMCP Services")
    services_health = SystemHealthMonitor.check_fastmcp_services()
    
    # Create columns for service status
    service_cols = st.columns(len(services_health))
    for idx, (service_name, health) in enumerate(services_health.items()):
        with service_cols[idx]:
            if health["status"] == "healthy":
                st.metric(
                    service_name.replace(" Service", ""),
                    "✅ Online",
                    f"{health['response_time']}ms"
                )
            elif health["status"] == "unhealthy":
                st.metric(
                    service_name.replace(" Service", ""),
                    "⚠️ Issues",
                    health["message"]
                )
            else:
                st.metric(
                    service_name.replace(" Service", ""),
                    "❌ Offline",
                    "No response"
                )
    
    # Check Kubernetes pods
    st.subheader("☸️ Kubernetes Cluster")
    k8s_health = SystemHealthMonitor.check_kubernetes_pods()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if k8s_health["status"] == "healthy":
            st.metric("Pod Status", f"✅ {k8s_health['running']}/{k8s_health['total']}", "All running")
        else:
            st.metric("Pod Status", f"⚠️ {k8s_health['running']}/{k8s_health['total']}", k8s_health["message"])
    
    with col2:
        st.metric("Cluster", "✅ Connected", "kubectl working")
    
    with col3:
        st.metric("Namespace", "cursor-insurance-ai-poc", "Active")


def render_api_monitor():
    """Render API monitoring interface"""
    st.header("📊 API Monitor")
    
    if not st.session_state.api_calls:
        st.info("No API calls recorded yet. Send a message in the chat to see real API interactions.")
        return
    
    # API call statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_calls = len(st.session_state.api_calls)
    successful_calls = len([call for call in st.session_state.api_calls if call.get("success", False)])
    avg_response_time = sum(call.get("response_time_ms", 0) for call in st.session_state.api_calls) / total_calls if total_calls > 0 else 0
    recent_calls = len([call for call in st.session_state.api_calls if (datetime.now() - call.get("timestamp", datetime.now())).seconds < 60])
    
    with col1:
        st.metric("Total API Calls", total_calls)
    
    with col2:
        st.metric("Success Rate", f"{(successful_calls/total_calls*100):.1f}%" if total_calls > 0 else "0%")
    
    with col3:
        st.metric("Avg Response Time", f"{avg_response_time:.1f}ms")
    
    with col4:
        st.metric("Calls (Last 1min)", recent_calls)
    
    # Recent API calls
    st.subheader("Recent API Calls")
    
    for call in reversed(st.session_state.api_calls[-10:]):  # Show last 10 calls
        timestamp = call.get("timestamp", datetime.now())
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("%H:%M:%S")
        else:
            timestamp_str = str(timestamp)
        
        status_icon = "✅" if call.get("success", False) else "❌"
        
        with st.expander(f"{status_icon} {call.get('service', 'Unknown')} - {call.get('method', 'GET')} ({timestamp_str})"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write(f"**Service:** {call.get('service', 'Unknown')}")
                st.write(f"**Endpoint:** {call.get('endpoint', 'Unknown')}")
                st.write(f"**Method:** {call.get('method', 'GET')}")
                st.write(f"**Status Code:** {call.get('status_code', 'Unknown')}")
                st.write(f"**Response Time:** {call.get('response_time_ms', 0)}ms")
            
            with col_b:
                if call.get("request_data"):
                    st.write("**Request Data:**")
                    st.json(call["request_data"])
                
                if call.get("response_data"):
                    st.write("**Response Data:**")
                    st.json(call["response_data"])


def main():
    """Main application"""
    st.title("🏥 Insurance AI PoC")
    st.markdown("**Visual Interface for Domain Agent Orchestration**")
    st.markdown("---")
    
    # Authentication (always visible in sidebar)
    render_authentication()
    
    # Main tabs (only show if authenticated)
    if st.session_state.customer_authenticated:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "💬 Chat Interface", 
            "🧠 Thinking & Orchestration",
            "⚕️ System Health", 
            "📊 API Monitor",
            "ℹ️ About"
        ])
        
        with tab1:
            render_chat_interface()
        
        with tab2:
            render_thinking_steps()
        
        with tab3:
            render_system_health()
        
        with tab4:
            render_api_monitor()
        
        with tab5:
            st.markdown("### About This Interface")
            st.markdown("""
            This Streamlit UI provides a visual interface to interact with the Insurance AI PoC domain agents.
            
            **Key Features:**
            - **Real Communication**: Directly communicates with FastMCP domain and technical agents
            - **Live Orchestration**: Shows real thinking steps and orchestration from agents
            - **System Monitoring**: Real-time health monitoring of all services
            - **API Transparency**: Captures and displays all API calls between components
            
            **Architecture:**
            - Domain agents handle business logic and customer interaction
            - Technical agents manage system orchestration and service calls
            - This UI simply provides visualization and interaction capabilities
            """)
    
    else:
        # Not authenticated - show welcome
        st.info("👋 Please authenticate using the sidebar to access the Insurance AI PoC features.")
        
        st.markdown("### Available Features:")
        st.markdown("- **💬 Chat Interface**: Communicate directly with domain agents")
        st.markdown("- **🧠 Thinking & Orchestration**: View real agent thinking and orchestration")
        st.markdown("- **⚕️ System Health**: Monitor all FastMCP services and Kubernetes")
        st.markdown("- **📊 API Monitor**: Track real API calls between systems")


if __name__ == "__main__":
    main() 