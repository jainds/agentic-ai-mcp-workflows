"""
Insurance AI PoC - Comprehensive Streamlit Dashboard
Multi-Agent LLM System with Model Context Protocol (MCP) Integration
"""

import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Any, Optional
import logging

from dashboard_config import Config, QUICK_ACTIONS, CHART_CONFIGS, HEALTH_THRESHOLDS, LLM_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize configuration
config = Config()

# Page configuration
st.set_page_config(
    page_title="🛡️ Insurance AI PoC Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-status {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .warning-status {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .error-status {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    .thinking-step {
        background-color: #e7f3ff;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 0.25rem;
        border-left: 3px solid #007bff;
    }
    .agent-response {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'agent_activity' not in st.session_state:
    st.session_state.agent_activity = []
if 'api_calls' not in st.session_state:
    st.session_state.api_calls = []
if 'llm_thinking_steps' not in st.session_state:
    st.session_state.llm_thinking_steps = []
if 'system_health' not in st.session_state:
    st.session_state.system_health = {}
if 'workflow_data' not in st.session_state:
    st.session_state.workflow_data = []


class APIClient:
    """Client for making API calls to agents and services"""
    
    @staticmethod
    def make_request(url: str, method: str = "GET", data: Dict = None, timeout: int = 30) -> Dict:
        """Make HTTP request with error handling"""
        start_time = time.time()
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            else:
                response = requests.get(url, timeout=timeout)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Log API call
            api_call = {
                "timestamp": datetime.now(),
                "url": url,
                "method": method,
                "response_time": response_time,
                "status_code": response.status_code,
                "success": response.status_code < 400
            }
            st.session_state.api_calls.append(api_call)
            
            if response.status_code < 400:
                return {
                    "success": True,
                    "data": response.json() if response.content else {},
                    "response_time": response_time,
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response_time,
                    "status_code": response.status_code
                }
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Log failed API call
            api_call = {
                "timestamp": datetime.now(),
                "url": url,
                "method": method,
                "response_time": response_time,
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
            st.session_state.api_calls.append(api_call)
            
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time,
                "status_code": 0
            }


def check_service_health(service_name: str, service_config) -> Dict:
    """Check health of a service"""
    health_url = f"{service_config.url}{service_config.health_endpoint}"
    result = APIClient.make_request(health_url, timeout=5)
    
    health_status = {
        "service": service_name,
        "name": service_config.name,
        "url": service_config.url,
        "status": "healthy" if result["success"] else "unhealthy",
        "response_time": result["response_time"],
        "last_check": datetime.now(),
        "details": result.get("data", {})
    }
    
    if not result["success"]:
        health_status["error"] = result["error"]
    
    return health_status


def simulate_llm_thinking(message: str) -> List[str]:
    """Simulate LLM thinking process"""
    thinking_steps = [
        f"🤔 Analyzing user message: '{message[:50]}...'",
        "🔍 Identifying intent and extracting key information",
        "🧠 Determining appropriate agent actions",
        "📋 Planning response strategy",
        "⚡ Executing planned workflow",
        "✅ Generating final response"
    ]
    
    return thinking_steps


def render_header():
    """Render the main dashboard header"""
    st.markdown('<h1 class="main-header">🛡️ Insurance AI PoC Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar():
    """Render the sidebar with configuration options"""
    st.sidebar.title("🔧 Configuration")
    
    # Service selection
    st.sidebar.subheader("🎯 Target Service")
    service_type = st.sidebar.selectbox(
        "Select Service Type:",
        ["Claims Agent", "Data Agent", "Notification Agent", "Direct API Call"]
    )
    
    # Quick actions
    if config.feature_flags["quick_actions"]:
        st.sidebar.subheader("⚡ Quick Actions")
        category = st.sidebar.selectbox("Action Category:", list(QUICK_ACTIONS.keys()))
        
        if category in QUICK_ACTIONS:
            action = st.sidebar.selectbox("Select Action:", list(QUICK_ACTIONS[category].keys()))
            
            if st.sidebar.button("🚀 Execute Quick Action"):
                execute_quick_action(category, action, service_type)
    
    # Advanced options
    with st.sidebar.expander("🔬 Advanced Options"):
        enable_llm_tracing = st.checkbox("Enable LLM Tracing", value=LLM_CONFIG["enable_tracing"])
        enable_guardrails = st.checkbox("Enable Guardrails", value=LLM_CONFIG["enable_guardrails"])
        max_tokens = st.slider("Max Tokens", 
                             LLM_CONFIG["max_tokens"]["min"], 
                             LLM_CONFIG["max_tokens"]["max"], 
                             LLM_CONFIG["max_tokens"]["default"])
        temperature = st.slider("Temperature", 
                               LLM_CONFIG["temperature"]["min"], 
                               LLM_CONFIG["temperature"]["max"], 
                               LLM_CONFIG["temperature"]["default"])
    
    # Auto-refresh
    if config.dashboard.auto_refresh:
        st.sidebar.subheader("🔄 Auto Refresh")
        if st.sidebar.button("Refresh Now"):
            st.rerun()
    
    return {
        "service_type": service_type,
        "enable_llm_tracing": enable_llm_tracing,
        "enable_guardrails": enable_guardrails,
        "max_tokens": max_tokens,
        "temperature": temperature
    }


def execute_quick_action(category: str, action: str, service_type: str):
    """Execute a quick action"""
    action_config = QUICK_ACTIONS[category][action]
    
    if "message" in action_config:
        # Agent interaction
        response = send_agent_message(action_config["message"], service_type)
        
        # Add to conversation history
        st.session_state.conversation_history.append({
            "timestamp": datetime.now(),
            "user_message": action_config["message"],
            "agent_response": response.get("data", {}),
            "service_type": service_type,
            "action_type": "quick_action",
            "category": category,
            "action": action
        })
        
        # Add to agent activity
        st.session_state.agent_activity.append({
            "timestamp": datetime.now(),
            "agent": service_type,
            "action": action,
            "status": "success" if response.get("success") else "error",
            "response_time": response.get("response_time", 0)
        })
        
        st.success(f"Quick action '{action}' executed successfully!")
        
    elif "endpoint" in action_config:
        # Direct API call
        service_config = get_service_config(service_type)
        if service_config:
            url = f"{service_config.url}{action_config['endpoint']}"
            response = APIClient.make_request(url, "POST", action_config["payload"])
            
            st.success(f"Direct API call '{action}' executed!")
            if response["success"]:
                st.json(response["data"])
            else:
                st.error(f"Error: {response['error']}")


def send_agent_message(message: str, service_type: str) -> Dict:
    """Send message to selected agent"""
    service_config = get_service_config(service_type)
    if not service_config:
        return {"success": False, "error": "Service not configured"}
    
    # Simulate LLM thinking steps
    if config.feature_flags["llm_thinking"]:
        thinking_steps = simulate_llm_thinking(message)
        st.session_state.llm_thinking_steps.extend([
            {"step": step, "timestamp": datetime.now()} for step in thinking_steps
        ])
    
    # Make API call
    url = f"{service_config.url}/process" if "agent" in service_type.lower() else f"{service_config.url}/api/chat"
    payload = {
        "message": message,
        "user_id": "dashboard_user",
        "conversation_id": f"dashboard_{int(time.time())}"
    }
    
    return APIClient.make_request(url, "POST", payload)


def get_service_config(service_type: str):
    """Get configuration for service type"""
    service_mapping = {
        "Claims Agent": "claims_agent",
        "Data Agent": "data_agent", 
        "Notification Agent": "notification_agent"
    }
    
    service_key = service_mapping.get(service_type)
    if service_key and service_key in config.services:
        return config.services[service_key]
    return None


def render_chat_interface():
    """Render the chat interface tab"""
    st.header("💬 Chat Interface")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat input
        user_message = st.text_area(
            "Enter your message:",
            placeholder="Ask about insurance policies, file a claim, or request analytics...",
            height=100
        )
        
        if st.button("🚀 Send Message", type="primary"):
            if user_message:
                sidebar_config = render_sidebar()
                response = send_agent_message(user_message, sidebar_config["service_type"])
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "timestamp": datetime.now(),
                    "user_message": user_message,
                    "agent_response": response.get("data", {}),
                    "service_type": sidebar_config["service_type"],
                    "success": response.get("success", False)
                })
                
                st.rerun()
    
    with col2:
        st.subheader("📊 Chat Stats")
        total_messages = len(st.session_state.conversation_history)
        successful_responses = sum(1 for conv in st.session_state.conversation_history if conv.get("success"))
        
        st.metric("Total Messages", total_messages)
        st.metric("Success Rate", f"{(successful_responses/total_messages*100):.1f}%" if total_messages > 0 else "0%")
    
    # Conversation history
    st.subheader("🗨️ Conversation History")
    
    for i, conv in enumerate(reversed(st.session_state.conversation_history[-10:])):
        with st.expander(f"Message {len(st.session_state.conversation_history) - i} - {conv['timestamp'].strftime('%H:%M:%S')}"):
            st.markdown(f"**User:** {conv['user_message']}")
            
            if conv.get("success"):
                st.markdown('<div class="agent-response">', unsafe_allow_html=True)
                st.markdown(f"**{conv['service_type']}:** {conv['agent_response']}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"Error: {conv['agent_response']}")


def render_llm_thinking():
    """Render the LLM thinking visualization tab"""
    st.header("🧠 LLM Thinking Visualization")
    
    if not config.feature_flags["llm_thinking"]:
        st.info("LLM Thinking visualization is disabled. Enable it in the sidebar.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔄 Current Thinking Process")
        
        if st.session_state.llm_thinking_steps:
            for step_data in st.session_state.llm_thinking_steps[-6:]:
                st.markdown(f'<div class="thinking-step">{step_data["step"]}</div>', unsafe_allow_html=True)
                time.sleep(0.1)  # Simulate thinking delay
        else:
            st.info("No thinking steps recorded yet. Send a message to see LLM processing.")
    
    with col2:
        st.subheader("📈 Thinking Analytics")
        
        if st.session_state.llm_thinking_steps:
            thinking_df = pd.DataFrame(st.session_state.llm_thinking_steps)
            thinking_df['hour'] = thinking_df['timestamp'].dt.hour
            
            hourly_thinking = thinking_df.groupby('hour').size().reset_index(columns=['hour', 'count'])
            
            fig = px.bar(hourly_thinking, x='hour', y='count', 
                        title="Thinking Steps by Hour")
            st.plotly_chart(fig, use_container_width=True)


def render_agent_activity():
    """Render the agent activity monitoring tab"""
    st.header("🔍 Agent Activity Monitor")
    
    if not config.feature_flags["agent_activity"]:
        st.info("Agent activity monitoring is disabled.")
        return
    
    # Real-time activity feed
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📡 Live Activity Feed")
        
        if st.session_state.agent_activity:
            for activity in reversed(st.session_state.agent_activity[-10:]):
                status_class = "success-status" if activity["status"] == "success" else "error-status"
                
                st.markdown(f'''
                <div class="status-card {status_class}">
                    <strong>{activity["agent"]}</strong> - {activity["action"]}<br>
                    <small>{activity["timestamp"].strftime("%H:%M:%S")} | 
                    Response: {activity["response_time"]:.0f}ms | 
                    Status: {activity["status"].upper()}</small>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.info("No agent activity recorded yet.")
    
    with col2:
        st.subheader("📊 Activity Summary")
        
        if st.session_state.agent_activity:
            activity_df = pd.DataFrame(st.session_state.agent_activity)
            
            # Agent usage distribution
            agent_counts = activity_df['agent'].value_counts()
            fig = px.pie(values=agent_counts.values, names=agent_counts.index, 
                        title="Agent Usage Distribution")
            st.plotly_chart(fig, use_container_width=True)
            
            # Success rate by agent
            success_rates = activity_df.groupby('agent')['status'].apply(
                lambda x: (x == 'success').mean() * 100
            ).reset_index()
            success_rates.columns = ['agent', 'success_rate']
            
            fig = px.bar(success_rates, x='agent', y='success_rate',
                        title="Success Rate by Agent (%)")
            st.plotly_chart(fig, use_container_width=True)


def render_api_monitor():
    """Render the API monitoring tab"""
    st.header("📡 API Monitor")
    
    if not config.feature_flags["api_monitor"]:
        st.info("API monitoring is disabled.")
        return
    
    # API call statistics
    col1, col2, col3, col4 = st.columns(4)
    
    if st.session_state.api_calls:
        api_df = pd.DataFrame(st.session_state.api_calls)
        
        with col1:
            st.metric("Total API Calls", len(api_df))
        
        with col2:
            avg_response_time = api_df['response_time'].mean()
            st.metric("Avg Response Time", f"{avg_response_time:.0f}ms")
        
        with col3:
            success_rate = (api_df['success'].sum() / len(api_df)) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col4:
            recent_calls = len(api_df[api_df['timestamp'] > datetime.now() - timedelta(minutes=5)])
            st.metric("Calls (5m)", recent_calls)
        
        # Response time chart
        st.subheader("📈 Response Time Trends")
        
        fig = px.line(api_df, x='timestamp', y='response_time', 
                     color='success', title="API Response Times Over Time")
        st.plotly_chart(fig, use_container_width=True)
        
        # API call details
        st.subheader("📋 Recent API Calls")
        
        display_df = api_df[['timestamp', 'url', 'method', 'response_time', 'status_code', 'success']].tail(20)
        st.dataframe(display_df, use_container_width=True)
    
    else:
        st.info("No API calls recorded yet. Interact with the system to see API monitoring data.")


def render_analytics():
    """Render the analytics dashboard tab"""
    st.header("📊 Analytics Dashboard")
    
    if not config.feature_flags["advanced_analytics"]:
        st.info("Advanced analytics are disabled.")
        return
    
    # Generate analytics data
    analytics_data = generate_analytics_data()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Sessions", analytics_data["active_sessions"], "↗️ +5")
    
    with col2:
        st.metric("Avg Resolution Time", f"{analytics_data['avg_resolution_time']:.1f}s", "↘️ -2.3s")
    
    with col3:
        st.metric("Claims Processed", analytics_data["claims_processed"], "↗️ +12")
    
    with col4:
        st.metric("Customer Satisfaction", f"{analytics_data['satisfaction_score']:.1f}%", "↗️ +1.2%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Workflow distribution
        workflow_data = analytics_data["workflow_distribution"]
        fig = px.pie(values=list(workflow_data.values()), names=list(workflow_data.keys()),
                    title="Workflow Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Performance trends
        performance_data = analytics_data["performance_trends"]
        fig = px.line(x=performance_data["time"], y=performance_data["response_time"],
                     title="Performance Trends")
        st.plotly_chart(fig, use_container_width=True)


def render_system_health():
    """Render the system health monitoring tab"""
    st.header("🏥 System Health Monitor")
    
    if not config.feature_flags["health_dashboard"]:
        st.info("Health monitoring is disabled.")
        return
    
    # Check all services
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔍 Service Health Checks")
        
        health_results = {}
        for service_key, service_config in config.services.items():
            with st.spinner(f"Checking {service_config.name}..."):
                health_result = check_service_health(service_key, service_config)
                health_results[service_key] = health_result
                
                # Display health status
                if health_result["status"] == "healthy":
                    st.success(f"✅ {health_result['name']} - Healthy ({health_result['response_time']:.0f}ms)")
                else:
                    st.error(f"❌ {health_result['name']} - Unhealthy: {health_result.get('error', 'Unknown error')}")
        
        # Store health results
        st.session_state.system_health = health_results
    
    with col2:
        st.subheader("📊 Health Summary")
        
        if health_results:
            healthy_count = sum(1 for h in health_results.values() if h["status"] == "healthy")
            total_count = len(health_results)
            
            st.metric("Healthy Services", f"{healthy_count}/{total_count}")
            
            # Average response time
            avg_response_time = sum(h["response_time"] for h in health_results.values()) / len(health_results)
            st.metric("Avg Response Time", f"{avg_response_time:.0f}ms")
            
            # Health status pie chart
            status_counts = {"Healthy": healthy_count, "Unhealthy": total_count - healthy_count}
            fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()),
                        title="Service Health Overview", color_discrete_map={"Healthy": "green", "Unhealthy": "red"})
            st.plotly_chart(fig, use_container_width=True)


def render_workflow_viewer():
    """Render the workflow visualization tab"""
    st.header("🔄 Workflow Viewer")
    
    if not config.feature_flags["workflow_visualization"]:
        st.info("Workflow visualization is disabled.")
        return
    
    st.subheader("🏗️ System Architecture")
    
    # Architecture diagram (simplified representation)
    st.markdown("""
    ```mermaid
    graph TD
        A[User/Dashboard] --> B[Claims Agent]
        B --> C[Data Agent]
        B --> D[Notification Agent]
        C --> E[Claims Service]
        C --> F[Policy Service]
        C --> G[User Service]
        D --> H[Email Service]
        D --> I[SMS Service]
        
        style A fill:#e1f5fe
        style B fill:#f3e5f5
        style C fill:#e8f5e8
        style D fill:#fff3e0
        style E fill:#fce4ec
        style F fill:#fce4ec
        style G fill:#fce4ec
        style H fill:#f1f8e9
        style I fill:#f1f8e9
    ```
    """)
    
    st.subheader("📈 Active Workflows")
    
    # Simulate workflow data
    workflow_data = [
        {"id": "WF-001", "type": "Claims Processing", "status": "Active", "progress": 75},
        {"id": "WF-002", "type": "Policy Inquiry", "status": "Completed", "progress": 100},
        {"id": "WF-003", "type": "Fraud Detection", "status": "Active", "progress": 40},
        {"id": "WF-004", "type": "Customer Support", "status": "Pending", "progress": 10},
    ]
    
    for workflow in workflow_data:
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            st.text(workflow["id"])
        
        with col2:
            st.text(workflow["type"])
        
        with col3:
            status_color = {"Active": "🟡", "Completed": "🟢", "Pending": "🔴"}
            st.text(f"{status_color.get(workflow['status'], '⚪')} {workflow['status']}")
        
        with col4:
            st.progress(workflow["progress"] / 100)


def generate_analytics_data() -> Dict:
    """Generate sample analytics data"""
    return {
        "active_sessions": 45,
        "avg_resolution_time": 32.5,
        "claims_processed": 156,
        "satisfaction_score": 94.2,
        "workflow_distribution": {
            "Claims Processing": 40,
            "Policy Inquiries": 25,
            "Customer Support": 20,
            "Fraud Detection": 15
        },
        "performance_trends": {
            "time": [f"Hour {i}" for i in range(24)],
            "response_time": [300 + i * 10 + (i % 3) * 50 for i in range(24)]
        }
    }


def main():
    """Main dashboard application"""
    render_header()
    
    # Sidebar configuration
    sidebar_config = render_sidebar()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "💬 Chat Interface",
        "🧠 LLM Thinking", 
        "🔍 Agent Activity",
        "📡 API Monitor",
        "📊 Analytics",
        "🏥 System Health",
        "🔄 Workflow Viewer"
    ])
    
    with tab1:
        render_chat_interface()
    
    with tab2:
        render_llm_thinking()
    
    with tab3:
        render_agent_activity()
    
    with tab4:
        render_api_monitor()
    
    with tab5:
        render_analytics()
    
    with tab6:
        render_system_health()
    
    with tab7:
        render_workflow_viewer()
    
    # Auto-refresh
    if config.dashboard.auto_refresh:
        time.sleep(config.dashboard.refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main() 