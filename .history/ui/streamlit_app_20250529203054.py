"""
Streamlit UI for Insurance AI PoC
Interactive dashboard for agent communication and real-time flow visualization
"""

import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import httpx

# Page configuration
st.set_page_config(
    page_title="Insurance AI PoC",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-processing {
        color: #ffc107;
        font-weight: bold;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
AGENT_ENDPOINTS = {
    "Claims Agent": "http://localhost:8000",
    "Data Agent": "http://localhost:8002", 
    "Support Agent": "http://localhost:8003",
    "Policy Agent": "http://localhost:8004",
    "Notification Agent": "http://localhost:8005",
    "Integration Agent": "http://localhost:8006"
}

DEMO_TOKEN = "demo-token-for-testing-please-change-in-production"

# Session state initialization
if 'agent_registry' not in st.session_state:
    st.session_state.agent_registry = {}

if 'task_history' not in st.session_state:
    st.session_state.task_history = []

if 'communication_flow' not in st.session_state:
    st.session_state.communication_flow = []

if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

# Utility functions
def make_request(url: str, method: str = "GET", data: Dict = None, headers: Dict = None) -> Optional[Dict]:
    """Make HTTP request with error handling"""
    try:
        if headers is None:
            headers = {"Authorization": f"Bearer {DEMO_TOKEN}"}
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Request failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {str(e)}")
        return None

def discover_agents():
    """Discover available agents"""
    agents = {}
    
    for agent_name, endpoint in AGENT_ENDPOINTS.items():
        try:
            agent_card = make_request(f"{endpoint}/.well-known/agent.json")
            if agent_card:
                agents[agent_name] = {
                    "endpoint": endpoint,
                    "card": agent_card,
                    "status": "online"
                }
            else:
                agents[agent_name] = {
                    "endpoint": endpoint,
                    "card": None,
                    "status": "offline"
                }
        except Exception as e:
            agents[agent_name] = {
                "endpoint": endpoint,
                "card": None,
                "status": "error",
                "error": str(e)
            }
    
    return agents

def send_task_to_agent(agent_endpoint: str, task_data: Dict) -> Optional[Dict]:
    """Send task to agent via A2A protocol"""
    task_request = {
        "taskId": f"task-{int(time.time())}",
        "user": task_data,
        "context": {"source": "streamlit_ui"},
        "metadata": {"timestamp": datetime.utcnow().isoformat()}
    }
    
    response = make_request(
        f"{agent_endpoint}/tasks/send",
        method="POST",
        data=task_request
    )
    
    if response:
        # Add to task history
        st.session_state.task_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_endpoint,
            "task": task_request,
            "response": response
        })
        
        # Add to communication flow
        st.session_state.communication_flow.append({
            "timestamp": datetime.utcnow().isoformat(),
            "source": "User",
            "target": agent_endpoint.split("//")[1] if "//" in agent_endpoint else agent_endpoint,
            "task_id": task_request["taskId"],
            "task_type": task_data.get("type", "unknown"),
            "status": response.get("status", "unknown")
        })
    
    return response

def format_task_response(response: Dict) -> str:
    """Format task response for display"""
    if not response:
        return "No response"
    
    parts = response.get("parts", [])
    if parts:
        return "\n".join(part.get("text", "") for part in parts)
    else:
        return json.dumps(response, indent=2)

# Main UI
def main():
    st.markdown('<h1 class="main-header">🏢 Insurance AI PoC</h1>', unsafe_allow_html=True)
    st.markdown("### Kubernetes-Native A2A/MCP Microservices Architecture")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh)
        
        if st.button("🔄 Discover Agents"):
            with st.spinner("Discovering agents..."):
                st.session_state.agent_registry = discover_agents()
        
        if st.button("🗑️ Clear History"):
            st.session_state.task_history = []
            st.session_state.communication_flow = []
            st.success("History cleared!")
        
        # Agent status
        st.subheader("🤖 Agent Status")
        if st.session_state.agent_registry:
            for agent_name, agent_info in st.session_state.agent_registry.items():
                status = agent_info["status"]
                if status == "online":
                    st.markdown(f"🟢 {agent_name}")
                elif status == "offline":
                    st.markdown(f"🔴 {agent_name}")
                else:
                    st.markdown(f"🟡 {agent_name}")
        else:
            st.info("Click 'Discover Agents' to check status")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Agent Interaction", 
        "📊 Agent Registry", 
        "🌊 Communication Flow", 
        "📈 Analytics", 
        "🔍 System Monitoring"
    ])
    
    with tab1:
        agent_interaction_tab()
    
    with tab2:
        agent_registry_tab()
    
    with tab3:
        communication_flow_tab()
    
    with tab4:
        analytics_tab()
    
    with tab5:
        monitoring_tab()
    
    # Auto-refresh
    if st.session_state.auto_refresh:
        time.sleep(5)
        st.rerun()

def agent_interaction_tab():
    """Agent interaction interface"""
    st.header("🎯 Agent Interaction")
    
    # Agent selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.session_state.agent_registry:
            online_agents = [
                name for name, info in st.session_state.agent_registry.items() 
                if info["status"] == "online"
            ]
            
            if online_agents:
                selected_agent = st.selectbox("Select Agent", online_agents)
                agent_endpoint = st.session_state.agent_registry[selected_agent]["endpoint"]
                
                # Task type selection based on agent capabilities
                agent_card = st.session_state.agent_registry[selected_agent]["card"]
                if agent_card:
                    capabilities = agent_card.get("capabilities", {})
                    st.info(f"**Agent:** {agent_card.get('name', 'Unknown')}")
                    st.info(f"**Description:** {agent_card.get('description', 'No description')}")
                    
                    # Show capabilities
                    if capabilities:
                        st.write("**Capabilities:**")
                        for cap, enabled in capabilities.items():
                            if enabled:
                                st.write(f"✅ {cap.replace('_', ' ').title()}")
            else:
                st.warning("No online agents found. Please discover agents first.")
                return
        else:
            st.warning("No agents discovered. Please discover agents first.")
            return
    
    with col2:
        st.subheader("Task Configuration")
        
        # Task type based on selected agent
        if selected_agent == "Claims Agent":
            task_type = st.selectbox("Task Type", [
                "process_claim", "analyze_claim", "fraud_detection", 
                "claim_status", "approve_claim", "reject_claim"
            ])
            
            if task_type == "process_claim":
                st.subheader("Process New Claim")
                claim_id = st.text_input("Claim ID", value=f"CLM-{int(time.time())}")
                policy_number = st.text_input("Policy Number", value="POL-001")
                description = st.text_area("Incident Description")
                amount = st.number_input("Claim Amount", min_value=0.0, value=1000.0)
                
                task_data = {
                    "type": task_type,
                    "claim": {
                        "claim_id": claim_id,
                        "policy_number": policy_number,
                        "description": description,
                        "amount": amount
                    }
                }
            
            elif task_type in ["analyze_claim", "fraud_detection", "claim_status"]:
                claim_id = st.text_input("Claim ID", value="CLM-001")
                task_data = {
                    "type": task_type,
                    "claim_id": claim_id
                }
            
            elif task_type in ["approve_claim", "reject_claim"]:
                claim_id = st.text_input("Claim ID", value="CLM-001")
                approver = st.text_input("Approver", value="admin")
                reason = st.text_area("Reason (for rejection)", "") if task_type == "reject_claim" else ""
                
                task_data = {
                    "type": task_type,
                    "claim_id": claim_id,
                    "approver": approver
                }
                if reason:
                    task_data["reason"] = reason
        
        elif selected_agent == "Data Agent":
            task_type = st.selectbox("Task Type", ["data_query", "analytics", "report"])
            
            if task_type == "data_query":
                query_type = st.selectbox("Query Type", [
                    "get_policy", "get_customer", "get_recent_claims"
                ])
                
                if query_type == "get_policy":
                    policy_number = st.text_input("Policy Number", value="POL-001")
                    task_data = {
                        "type": task_type,
                        "query_type": query_type,
                        "params": {"policy_number": policy_number}
                    }
                elif query_type == "get_customer":
                    customer_id = st.text_input("Customer ID", value="CUST-001")
                    task_data = {
                        "type": task_type,
                        "query_type": query_type,
                        "params": {"customer_id": customer_id}
                    }
                elif query_type == "get_recent_claims":
                    customer_id = st.text_input("Customer ID", value="CUST-001")
                    days = st.number_input("Days", min_value=1, value=90)
                    task_data = {
                        "type": task_type,
                        "query_type": query_type,
                        "params": {"customer_id": customer_id, "days": days}
                    }
            
            elif task_type == "analytics":
                analysis_type = st.selectbox("Analysis Type", ["fraud_risk", "claim_statistics"])
                task_data = {
                    "type": task_type,
                    "analysis_type": analysis_type,
                    "params": {}
                }
            
            elif task_type == "report":
                report_type = st.selectbox("Report Type", [
                    "claims_summary", "fraud_analysis", "customer_risk"
                ])
                task_data = {
                    "type": task_type,
                    "report_type": report_type,
                    "filters": {}
                }
        
        else:
            # Generic task interface
            task_type = st.text_input("Task Type", value="generic_task")
            custom_data = st.text_area("Custom Task Data (JSON)", value="{}")
            
            try:
                custom_json = json.loads(custom_data) if custom_data else {}
                task_data = {
                    "type": task_type,
                    **custom_json
                }
            except json.JSONDecodeError:
                st.error("Invalid JSON in custom task data")
                return
        
        # Send task button
        if st.button("🚀 Send Task", type="primary"):
            with st.spinner("Sending task..."):
                response = send_task_to_agent(agent_endpoint, task_data)
                
                if response:
                    st.success("Task sent successfully!")
                    
                    # Display response
                    st.subheader("Response")
                    
                    status = response.get("status", "unknown")
                    if status == "completed":
                        st.markdown('<span class="status-success">✅ Completed</span>', unsafe_allow_html=True)
                    elif status == "failed":
                        st.markdown('<span class="status-error">❌ Failed</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="status-processing">⏳ Processing</span>', unsafe_allow_html=True)
                    
                    # Response content
                    response_text = format_task_response(response)
                    st.code(response_text, language="json")
                    
                    # Show metadata
                    if response.get("metadata"):
                        with st.expander("Response Metadata"):
                            st.json(response["metadata"])
                else:
                    st.error("Failed to send task")

def agent_registry_tab():
    """Agent registry and capabilities display"""
    st.header("📊 Agent Registry")
    
    if not st.session_state.agent_registry:
        st.info("No agents discovered. Please discover agents first.")
        return
    
    # Overview metrics
    total_agents = len(st.session_state.agent_registry)
    online_agents = sum(1 for info in st.session_state.agent_registry.values() if info["status"] == "online")
    offline_agents = total_agents - online_agents
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Agents", total_agents)
    with col2:
        st.metric("Online", online_agents)
    with col3:
        st.metric("Offline", offline_agents)
    
    # Agent cards
    for agent_name, agent_info in st.session_state.agent_registry.items():
        with st.expander(f"🤖 {agent_name}", expanded=agent_info["status"] == "online"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if agent_info["card"]:
                    card = agent_info["card"]
                    st.write(f"**Name:** {card.get('name', 'Unknown')}")
                    st.write(f"**Description:** {card.get('description', 'No description')}")
                    st.write(f"**Version:** {card.get('version', 'Unknown')}")
                    st.write(f"**URL:** {card.get('url', 'Unknown')}")
                    
                    # Capabilities
                    capabilities = card.get("capabilities", {})
                    if capabilities:
                        st.write("**Capabilities:**")
                        cap_cols = st.columns(3)
                        for i, (cap, enabled) in enumerate(capabilities.items()):
                            with cap_cols[i % 3]:
                                icon = "✅" if enabled else "❌"
                                st.write(f"{icon} {cap.replace('_', ' ').title()}")
                    
                    # Endpoints
                    endpoints = card.get("endpoints", {})
                    if endpoints:
                        st.write("**Endpoints:**")
                        for endpoint, path in endpoints.items():
                            st.code(f"{endpoint}: {path}")
                else:
                    st.warning("Agent card not available")
            
            with col2:
                status = agent_info["status"]
                if status == "online":
                    st.success("🟢 Online")
                elif status == "offline":
                    st.error("🔴 Offline")
                else:
                    st.warning("🟡 Error")
                    if "error" in agent_info:
                        st.error(agent_info["error"])
                
                st.write(f"**Endpoint:** {agent_info['endpoint']}")
                
                # Health check button
                if st.button(f"Health Check", key=f"health_{agent_name}"):
                    health = make_request(f"{agent_info['endpoint']}/health")
                    if health:
                        st.json(health)
                    else:
                        st.error("Health check failed")

def communication_flow_tab():
    """Real-time communication flow visualization"""
    st.header("🌊 Communication Flow")
    
    if not st.session_state.communication_flow:
        st.info("No communication flows recorded. Interact with agents to see flows.")
        return
    
    # Flow metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Messages", len(st.session_state.communication_flow))
    
    with col2:
        recent_flows = [f for f in st.session_state.communication_flow 
                       if datetime.fromisoformat(f["timestamp"]) > datetime.utcnow() - timedelta(minutes=5)]
        st.metric("Last 5 mins", len(recent_flows))
    
    with col3:
        task_types = [f["task_type"] for f in st.session_state.communication_flow]
        unique_types = len(set(task_types))
        st.metric("Task Types", unique_types)
    
    with col4:
        success_count = sum(1 for f in st.session_state.communication_flow if f["status"] == "completed")
        success_rate = (success_count / len(st.session_state.communication_flow)) * 100 if st.session_state.communication_flow else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Flow visualization
    st.subheader("Flow Diagram")
    
    # Create flow diagram data
    flow_data = []
    for flow in st.session_state.communication_flow[-20:]:  # Last 20 flows
        flow_data.append({
            "timestamp": flow["timestamp"],
            "source": flow["source"],
            "target": flow["target"],
            "task_type": flow["task_type"],
            "status": flow["status"],
            "task_id": flow["task_id"]
        })
    
    if flow_data:
        df = pd.DataFrame(flow_data)
        
        # Timeline chart
        fig = px.timeline(
            df,
            x_start="timestamp",
            x_end="timestamp",
            y="target",
            color="status",
            hover_data=["task_type", "task_id"],
            title="Agent Communication Timeline"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Flow table
        st.subheader("Recent Flows")
        st.dataframe(
            df[["timestamp", "source", "target", "task_type", "status", "task_id"]],
            use_container_width=True
        )
    
    # Task history
    if st.session_state.task_history:
        st.subheader("Task History")
        
        for i, task in enumerate(reversed(st.session_state.task_history[-10:])):  # Last 10 tasks
            with st.expander(f"Task {task['task']['taskId']} - {task['response'].get('status', 'unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Request:**")
                    st.json(task['task'])
                
                with col2:
                    st.write("**Response:**")
                    st.json(task['response'])

def analytics_tab():
    """Analytics and metrics dashboard"""
    st.header("📈 Analytics Dashboard")
    
    # Mock analytics data (in production, fetch from analytics service)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Task Performance")
        
        if st.session_state.communication_flow:
            # Task type distribution
            task_types = [f["task_type"] for f in st.session_state.communication_flow]
            task_type_counts = pd.Series(task_types).value_counts()
            
            fig = px.pie(
                values=task_type_counts.values,
                names=task_type_counts.index,
                title="Task Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Status distribution
            statuses = [f["status"] for f in st.session_state.communication_flow]
            status_counts = pd.Series(statuses).value_counts()
            
            fig = px.bar(
                x=status_counts.index,
                y=status_counts.values,
                title="Task Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Agent Activity")
        
        if st.session_state.communication_flow:
            # Agent activity
            targets = [f["target"] for f in st.session_state.communication_flow]
            target_counts = pd.Series(targets).value_counts()
            
            fig = px.bar(
                x=target_counts.values,
                y=target_counts.index,
                orientation='h',
                title="Agent Activity Levels"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Time series of tasks
            if len(st.session_state.communication_flow) > 1:
                df = pd.DataFrame(st.session_state.communication_flow)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['hour'] = df['timestamp'].dt.floor('H')
                
                hourly_counts = df.groupby('hour').size().reset_index(name='count')
                
                fig = px.line(
                    hourly_counts,
                    x='hour',
                    y='count',
                    title="Task Volume Over Time"
                )
                st.plotly_chart(fig, use_container_width=True)

def monitoring_tab():
    """System monitoring and health checks"""
    st.header("🔍 System Monitoring")
    
    # System health overview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Service Health")
        
        services = ["Claims Service", "User Service", "Policy Service", "Analytics Service"]
        service_ports = [8000, 8001, 8002, 8003]
        
        for service, port in zip(services, service_ports):
            try:
                health = make_request(f"http://localhost:{port}/health")
                if health:
                    st.success(f"✅ {service}")
                    with st.expander(f"{service} Details"):
                        st.json(health)
                else:
                    st.error(f"❌ {service}")
            except:
                st.error(f"❌ {service} (Connection Error)")
    
    with col2:
        st.subheader("Resource Usage")
        
        # Mock resource usage data
        import random
        
        resources = {
            "CPU Usage": f"{random.randint(10, 80)}%",
            "Memory Usage": f"{random.randint(30, 70)}%",
            "Disk Usage": f"{random.randint(20, 60)}%",
            "Network I/O": f"{random.randint(5, 25)} MB/s"
        }
        
        for resource, value in resources.items():
            st.metric(resource, value)
    
    with col3:
        st.subheader("Error Rates")
        
        # Mock error data
        error_rates = {
            "HTTP 4xx": f"{random.uniform(0.1, 2.0):.1f}%",
            "HTTP 5xx": f"{random.uniform(0.0, 0.5):.1f}%",
            "Timeouts": f"{random.uniform(0.0, 1.0):.1f}%",
            "Failed Tasks": f"{random.uniform(0.0, 3.0):.1f}%"
        }
        
        for error_type, rate in error_rates.items():
            st.metric(error_type, rate)
    
    # Logs viewer
    st.subheader("Recent Logs")
    
    if st.session_state.task_history:
        log_entries = []
        for task in st.session_state.task_history[-5:]:
            log_entries.append({
                "timestamp": task["timestamp"],
                "level": "INFO" if task["response"].get("status") == "completed" else "ERROR",
                "message": f"Task {task['task']['taskId']} - {task['response'].get('status', 'unknown')}",
                "agent": task["agent"]
            })
        
        log_df = pd.DataFrame(log_entries)
        st.dataframe(log_df, use_container_width=True)
    else:
        st.info("No recent logs available")

if __name__ == "__main__":
    main() 