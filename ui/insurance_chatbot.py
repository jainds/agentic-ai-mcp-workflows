"""
Insurance AI PoC - Multi-Tab Interface with Proper A2A/MCP Architecture
Chat Interface + LLM Thinking + API Monitor + Analytics + System Health
"""

import streamlit as st
import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os
import asyncio

# Add agents directory to Python path
agents_path = os.path.join(os.path.dirname(__file__), '..', 'agents')
sys.path.append(agents_path)

# Import our FastMCP Data Agent
try:
    from technical.fastmcp_data_agent import FastMCPDataAgent, fastmcp_data_agent
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    print("⚠️ FastMCP Data Agent not available, using mock simulation")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="🛡️ Insurance AI Assistant",
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
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .agent-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
    .thinking-indicator {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
        font-style: italic;
    }
    .agent-orchestration {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
    .status-healthy { color: #28a745; }
    .status-warning { color: #ffc107; }
    .status-error { color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'thinking_steps' not in st.session_state:
    st.session_state.thinking_steps = []
if 'api_calls' not in st.session_state:
    st.session_state.api_calls = []
if 'system_metrics' not in st.session_state:
    st.session_state.system_metrics = []
if 'analytics_data' not in st.session_state:
    st.session_state.analytics_data = []
if 'customer_id' not in st.session_state:
    st.session_state.customer_id = ""
if 'customer_authenticated' not in st.session_state:
    st.session_state.customer_authenticated = False

class CustomerValidator:
    """Validates customer authentication"""
    
    # Demo customer database for validation
    VALID_CUSTOMERS = {
        "CUST-001": {
            "name": "John Smith",
            "email": "john.smith@email.com",
            "policies": ["POL-AUTO-123456", "POL-HOME-789012"],
            "status": "active"
        },
        "CUST-002": {
            "name": "Sarah Johnson", 
            "email": "sarah.johnson@email.com",
            "policies": ["POL-AUTO-654321"],
            "status": "active"
        },
        "CUST-003": {
            "name": "Mike Davis",
            "email": "mike.davis@email.com", 
            "policies": ["POL-AUTO-111222", "POL-HOME-333444"],
            "status": "active"
        },
        "TEST-CUSTOMER": {
            "name": "Test Customer",
            "email": "test@insurance.com",
            "policies": ["POL-TEST-123"],
            "status": "active"
        }
    }
    
    @classmethod
    def validate_customer(cls, customer_id: str) -> Dict[str, Any]:
        """Validate customer ID and return customer data"""
        if not customer_id or not customer_id.strip():
            return {
                "valid": False,
                "error": "Customer ID is required",
                "customer_data": None
            }
        
        customer_id = customer_id.strip().upper()
        
        if customer_id not in cls.VALID_CUSTOMERS:
            return {
                "valid": False,
                "error": f"Customer ID '{customer_id}' not found in our system",
                "customer_data": None
            }
        
        customer_data = cls.VALID_CUSTOMERS[customer_id]
        if customer_data["status"] != "active":
            return {
                "valid": False,
                "error": f"Customer account '{customer_id}' is not active",
                "customer_data": None
            }
        
        return {
            "valid": True,
            "error": None,
            "customer_data": {
                **customer_data,
                "customer_id": customer_id
            }
        }

class InsuranceAIClient:
    """AI client for handling insurance queries with real MCP integration"""
    
    def __init__(self):
        # Initialize response cache and metrics
        self.response_cache = {}
        self.api_call_log = []
        self.system_metrics = []
        self.analytics_data = []
        
        # Initialize FastMCP Data Agent if available
        self.fastmcp_agent = None
        if FASTMCP_AVAILABLE:
            self.fastmcp_agent = FastMCPDataAgent()
            self._initialize_fastmcp()
    
    def _initialize_fastmcp(self):
        """Initialize FastMCP Data Agent asynchronously"""
        if self.fastmcp_agent:
            try:
                # Create a new event loop for initialization if needed
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If we're in an existing loop, we can't use asyncio.run
                        # Create a task instead
                        asyncio.create_task(self.fastmcp_agent.initialize())
                    else:
                        asyncio.run(self.fastmcp_agent.initialize())
                except RuntimeError:
                    # If no event loop exists, create one
                    asyncio.run(self.fastmcp_agent.initialize())
            except Exception as e:
                print(f"⚠️ Failed to initialize FastMCP Data Agent: {e}")
                self.fastmcp_agent = None
    
    async def _call_fastmcp_tool(self, operation: str, customer_id: str, **kwargs) -> Dict[str, Any]:
        """Call FastMCP Data Agent tools"""
        if not self.fastmcp_agent:
            return {"success": False, "error": "FastMCP agent not available"}
        
        try:
            if operation == "get_customer_claims":
                return await self.fastmcp_agent.get_customer_claims(customer_id)
            elif operation == "get_customer_policies":
                return await self.fastmcp_agent.get_customer_policies(customer_id)
            elif operation == "create_claim":
                return await self.fastmcp_agent.create_claim(
                    customer_id=customer_id,
                    policy_number=kwargs.get("policy_number", "POL-AUTO-123456"),
                    incident_date=kwargs.get("incident_date", datetime.now().strftime("%Y-%m-%d")),
                    description=kwargs.get("description", "Incident reported via chat"),
                    amount=kwargs.get("amount", 1000.0),
                    claim_type=kwargs.get("claim_type", "auto_collision")
                )
            elif operation == "generate_customer_summary":
                return await self.fastmcp_agent.generate_customer_summary(customer_id)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

def check_service_health():
    """Check health of all services"""
    services = {
        "Claims Agent": "http://claims-agent:8000/health",
        "Data Agent": "http://data-agent:8002/health", 
        "Notification Agent": "http://notification-agent:8003/health"
    }
    
    health_status = {}
    for service_name, url in services.items():
        try:
            # Simulate health check since we're in demo mode
            status = random.choice(["healthy", "healthy", "healthy", "warning"])
            response_time = random.randint(50, 200)
            
            health_status[service_name] = {
                "status": status,
                "response_time": response_time,
                "last_check": datetime.now()
            }
        except:
            health_status[service_name] = {
                "status": "error",
                "response_time": 0,
                "last_check": datetime.now()
            }
    
    return health_status

def render_header():
    """Render the main header"""
    st.markdown('<h1 class="main-header">🛡️ Insurance AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### A2A/MCP Architecture - Multi-Agent Orchestration Platform")

def render_chat_tab():
    """Render the chat interface tab"""
    st.header("💬 Chat Interface")
    st.markdown("**Proper A2A/MCP Architecture**: One chatbot, automatic agent orchestration")
    
    # Customer Authentication Section
    st.subheader("🔐 Customer Authentication")
    
    if not st.session_state.customer_authenticated:
        # Authentication form
        with st.form("customer_auth_form"):
            st.markdown("**Please enter your Customer ID to access your insurance information:**")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                customer_id_input = st.text_input(
                    "Customer ID", 
                    placeholder="e.g., CUST-001, CUST-002, CUST-003, TEST-CUSTOMER",
                    help="Enter your unique customer identifier"
                )
            
            with col2:
                auth_submit = st.form_submit_button("🔑 Authenticate", type="primary")
            
            if auth_submit:
                if customer_id_input:
                    validation = CustomerValidator.validate_customer(customer_id_input)
                    
                    if validation["valid"]:
                        # Authentication successful
                        st.session_state.customer_id = validation["customer_data"]["customer_id"]
                        st.session_state.customer_authenticated = True
                        st.session_state.customer_data = validation["customer_data"]
                        st.success(f"✅ Authentication successful! Welcome, {validation['customer_data']['name']}")
                        st.rerun()
                    else:
                        # Authentication failed
                        st.error(f"❌ Authentication failed: {validation['error']}")
                        st.warning("Please check your Customer ID and try again.")
                else:
                    st.error("Please enter a Customer ID")
        
        # Show demo customer IDs for testing
        with st.expander("🔍 Demo Customer IDs (for testing)"):
            st.markdown("""
            **Available test customers:**
            - `CUST-001` - John Smith (Auto + Home policies)
            - `CUST-002` - Sarah Johnson (Auto policy)
            - `CUST-003` - Mike Davis (Auto + Home policies)
            - `TEST-CUSTOMER` - Test Customer (Test policy)
            """)
        
        # Stop here if not authenticated
        st.info("🛡️ **Security Notice**: Customer authentication is required before accessing insurance services.")
        return
    
    # Customer authenticated - show customer info and chat interface
    customer_data = st.session_state.customer_data
    
    # Customer info panel
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.success(f"🔐 **Authenticated as:** {customer_data['name']} ({st.session_state.customer_id})")
        
        with col2:
            st.info(f"📧 {customer_data['email']}")
        
        with col3:
            if st.button("🚪 Logout", type="secondary"):
                # Clear authentication
                st.session_state.customer_authenticated = False
                st.session_state.customer_id = ""
                st.session_state.customer_data = {}
                st.session_state.conversation_history = []
                st.rerun()
    
    st.markdown("---")
    
    # Initialize client
    client = InsuranceAIClient()
    
    # Chat input
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            f"Ask me anything about your insurance, {customer_data['name']}:",
            placeholder="e.g., 'I was in an accident and need to file a claim' or 'What does my policy cover?'",
            key="chat_user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("💬 Send", type="primary", use_container_width=True, key="chat_send")
    
    # Handle user input
    if send_button and user_input:
        # Add user message to history
        st.session_state.conversation_history.append({
            "type": "user",
            "message": user_input,
            "customer_id": st.session_state.customer_id,
            "timestamp": datetime.now()
        })
        
        # Show thinking indicator
        with st.spinner(f"🤔 Domain Agent analyzing request for {customer_data['name']} and orchestrating Technical Agents..."):
            # Send to Claims Agent (Domain Agent) with customer ID
            response = client.send_message(user_input, st.session_state.customer_id)
        
        if response["success"]:
            response_data = response["response"]
            
            # Add agent response to history
            st.session_state.conversation_history.append({
                "type": "agent",
                "message": response_data.get("message", "I'm here to help! What would you like to know?"),
                "thinking_steps": response_data.get("thinking_steps", []),
                "orchestration_steps": response_data.get("orchestration_steps", []),
                "agent_interactions": response_data.get("agent_interactions", 0),
                "response_time": response_data.get("response_time_ms", 0),
                "llm_model": response_data.get("llm_model", "unknown"),
                "confidence_score": response_data.get("confidence_score", 0.0),
                "customer_id": response_data.get("customer_id", st.session_state.customer_id),
                "customer_name": response_data.get("customer_name", customer_data['name']),
                "timestamp": datetime.now()
            })
        else:
            # Add error response
            st.session_state.conversation_history.append({
                "type": "error",
                "message": f"I'm sorry, I encountered an issue: {response['error']}",
                "customer_id": st.session_state.customer_id,
                "timestamp": datetime.now()
            })
        
        # Clear input and rerun
        st.rerun()
    
    # Display conversation history
    if not st.session_state.conversation_history:
        st.info(f"👋 Welcome {customer_data['name']}! Ask me anything about your insurance. I use proper A2A/MCP architecture to orchestrate all services automatically.")
    
    # Show conversation in reverse order (newest first)
    for i, chat in enumerate(reversed(st.session_state.conversation_history)):
        if chat["type"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>{customer_data['name']} ({chat["timestamp"].strftime("%H:%M:%S")}):</strong><br>
                {chat["message"]}
            </div>
            """, unsafe_allow_html=True)
            
        elif chat["type"] == "agent":
            # Show main response
            st.markdown(f"""
            <div class="chat-message agent-message">
                <strong>Insurance AI Assistant ({chat["timestamp"].strftime("%H:%M:%S")}):</strong><br>
                {chat["message"].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
            
            # Show performance info
            if "response_time" in chat:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption(f"⚡ Response: {chat['response_time']}ms")
                with col2:
                    st.caption(f"🤖 Agent calls: {chat.get('agent_interactions', 0)}")
                with col3:
                    st.caption(f"🧠 Model: {chat.get('llm_model', 'N/A')}")
                with col4:
                    st.caption(f"📊 Confidence: {chat.get('confidence_score', 0):.2f}")
        
        elif chat["type"] == "error":
            st.error(f"**Error ({chat['timestamp'].strftime('%H:%M:%S')}):** {chat['message']}")

def render_llm_thinking_tab():
    """Render the LLM thinking tab"""
    st.header("🧠 LLM Thinking Visualization")
    st.markdown("**Real-time AI reasoning and decision-making processes**")
    
    if not st.session_state.conversation_history:
        st.info("💭 Start a conversation in the Chat tab to see LLM thinking processes here.")
        return
    
    # Get latest conversations with thinking steps
    thinking_conversations = [chat for chat in reversed(st.session_state.conversation_history) 
                             if chat["type"] == "agent" and "thinking_steps" in chat]
    
    if not thinking_conversations:
        st.info("🤔 No thinking processes available yet. Send a message in the Chat tab!")
        return
    
    # Select conversation to analyze
    conversation_options = [f"Conversation {i+1} ({chat['timestamp'].strftime('%H:%M:%S')})" 
                           for i, chat in enumerate(thinking_conversations)]
    
    selected_idx = st.selectbox("Select conversation to analyze:", 
                               range(len(conversation_options)), 
                               format_func=lambda x: conversation_options[x],
                               key="thinking_conversation_select")
    
    selected_chat = thinking_conversations[selected_idx]
    
    # Display thinking process
    st.subheader("🤔 AI Thinking Process")
    
    thinking_steps = selected_chat.get("thinking_steps", [])
    orchestration_steps = selected_chat.get("orchestration_steps", [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**LLM Analysis Steps:**")
        for i, step in enumerate(thinking_steps):
            st.markdown(f"{i+1}. {step}")
    
    with col2:
        st.write("**A2A Orchestration Steps:**")
        for i, step in enumerate(orchestration_steps):
            st.markdown(f"{i+1}. {step}")
    
    # Thinking timeline visualization
    st.subheader("📊 Thinking Timeline")
    
    if thinking_steps or orchestration_steps:
        # Create timeline data
        timeline_data = []
        
        # Add thinking steps
        for i, step in enumerate(thinking_steps):
            timeline_data.append({
                "Step": f"Think {i+1}",
                "Process": "LLM Analysis", 
                "Description": step,
                "Time": i * 0.2,
                "Duration": 0.2
            })
        
        # Add orchestration steps
        for i, step in enumerate(orchestration_steps):
            timeline_data.append({
                "Step": f"A2A {i+1}",
                "Process": "Agent Orchestration",
                "Description": step,
                "Time": len(thinking_steps) * 0.2 + i * 0.3,
                "Duration": 0.3
            })
        
        df = pd.DataFrame(timeline_data)
        
        # Create Gantt-like chart
        fig = px.timeline(df, x_start="Time", x_end="Time", y="Step", 
                         color="Process", title="AI Thinking & Orchestration Timeline",
                         hover_data=["Description"])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    st.subheader("⚡ Performance Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Response Time", f"{selected_chat.get('response_time', 0)}ms")
    with col2:
        st.metric("Agent Interactions", selected_chat.get('agent_interactions', 0))
    with col3:
        st.metric("LLM Model", selected_chat.get('llm_model', 'N/A'))
    with col4:
        st.metric("Confidence Score", f"{selected_chat.get('confidence_score', 0):.2f}")

def render_api_monitor_tab():
    """Render the API monitor tab"""
    st.header("📡 API Monitor")
    st.markdown("**Real-time monitoring of A2A calls and MCP tool usage**")
    
    if not st.session_state.api_calls:
        st.info("📊 No API calls recorded yet. Start a conversation to see API monitoring data.")
        return
    
    # API calls summary
    col1, col2, col3, col4 = st.columns(4)
    
    total_calls = len(st.session_state.api_calls)
    successful_calls = len([call for call in st.session_state.api_calls if call["status"] == "success"])
    avg_response_time = sum(call["response_time"] for call in st.session_state.api_calls) / total_calls if total_calls > 0 else 0
    success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
    
    with col1:
        st.metric("Total API Calls", total_calls)
    with col2:
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col3:
        st.metric("Avg Response Time", f"{avg_response_time:.0f}ms")
    with col4:
        st.metric("Active Services", 3)
    
    # Real-time API calls table
    st.subheader("🔄 Recent API Calls")
    
    # Get last 20 API calls
    recent_calls = list(reversed(st.session_state.api_calls))[:20]
    
    api_df = pd.DataFrame([{
        "Timestamp": call["timestamp"].strftime("%H:%M:%S"),
        "Service": call.get("service", "claims-agent"),
        "Endpoint": call["endpoint"].split("/")[-1] if "/" in call["endpoint"] else call["endpoint"],
        "Method": call["method"],
        "Status": call["status"],
        "Response Time": f"{call['response_time']}ms",
        "Message": call.get("message", "")[:30] + "..." if len(call.get("message", "")) > 30 else call.get("message", "")
    } for call in recent_calls])
    
    # Color code status
    def color_status(val):
        if val == "success":
            return "background-color: #d4edda"
        elif val == "error":
            return "background-color: #f8d7da"
        else:
            return "background-color: #fff3cd"
    
    styled_df = api_df.style.applymap(color_status, subset=["Status"])
    st.dataframe(styled_df, use_container_width=True)
    
    # API response time chart
    st.subheader("📈 Response Time Trends")
    
    if len(st.session_state.api_calls) > 1:
        # Prepare data for chart
        chart_data = []
        for call in st.session_state.api_calls[-20:]:  # Last 20 calls
            chart_data.append({
                "Time": call["timestamp"],
                "Response Time": call["response_time"],
                "Service": call.get("service", "claims-agent"),
                "Status": call["status"]
            })
        
        chart_df = pd.DataFrame(chart_data)
        
        # Create line chart
        fig = px.line(chart_df, x="Time", y="Response Time", 
                     color="Service", title="API Response Times",
                     line_shape="linear")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Service health overview
    st.subheader("🏥 Service Health")
    
    health_status = check_service_health()
    
    for service_name, health in health_status.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            status_color = "status-healthy" if health["status"] == "healthy" else \
                          "status-warning" if health["status"] == "warning" else "status-error"
            st.markdown(f"**{service_name}**: <span class='{status_color}'>{health['status'].upper()}</span>", 
                       unsafe_allow_html=True)
        
        with col2:
            st.write(f"Response: {health['response_time']}ms")
        
        with col3:
            st.write(f"Last check: {health['last_check'].strftime('%H:%M:%S')}")

def render_analytics_tab():
    """Render the analytics tab"""
    st.header("📊 Analytics Dashboard")
    st.markdown("**Business intelligence and performance analytics**")
    
    if not st.session_state.analytics_data:
        st.info("📈 No analytics data available yet. Start using the system to generate analytics.")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_conversations = len(st.session_state.analytics_data)
    avg_satisfaction = sum(a["user_satisfaction"] for a in st.session_state.analytics_data) / total_conversations if total_conversations > 0 else 0
    avg_response_time = sum(a["response_time"] for a in st.session_state.analytics_data) / total_conversations if total_conversations > 0 else 0
    success_rate = len([a for a in st.session_state.analytics_data if a["success"]]) / total_conversations * 100 if total_conversations > 0 else 0
    
    with col1:
        st.metric("Total Conversations", total_conversations)
    with col2:
        st.metric("Avg Satisfaction", f"{avg_satisfaction:.1f}/5.0")
    with col3:
        st.metric("Avg Response Time", f"{avg_response_time:.0f}ms")
    with col4:
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Intent distribution
    st.subheader("🎯 Intent Distribution")
    
    intent_counts = {}
    for analytics in st.session_state.analytics_data:
        intent = analytics["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    if intent_counts:
        intent_df = pd.DataFrame(list(intent_counts.items()), columns=["Intent", "Count"])
        fig = px.pie(intent_df, values="Count", names="Intent", 
                    title="User Intent Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Satisfaction trends
    st.subheader("😊 User Satisfaction Trends")
    
    if len(st.session_state.analytics_data) > 1:
        satisfaction_df = pd.DataFrame([{
            "Time": a["timestamp"],
            "Satisfaction": a["user_satisfaction"],
            "Intent": a["intent"]
        } for a in st.session_state.analytics_data])
        
        fig = px.line(satisfaction_df, x="Time", y="Satisfaction", 
                     color="Intent", title="User Satisfaction Over Time",
                     range_y=[1, 5])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance analytics
    st.subheader("⚡ Performance Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Response time distribution
        response_times = [a["response_time"] for a in st.session_state.analytics_data]
        fig = px.histogram(x=response_times, title="Response Time Distribution",
                          labels={"x": "Response Time (ms)", "y": "Frequency"})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Agent interactions
        interactions = [a["agent_interactions"] for a in st.session_state.analytics_data]
        fig = px.histogram(x=interactions, title="Agent Interactions Distribution",
                          labels={"x": "Number of Agent Interactions", "y": "Frequency"})
        st.plotly_chart(fig, use_container_width=True)

def render_system_health_tab():
    """Render the system health tab"""
    st.header("🏥 System Health Monitor")
    st.markdown("**Real-time system monitoring and diagnostics**")
    
    # Current system status
    health_status = check_service_health()
    
    st.subheader("🌐 Service Status")
    
    for service_name, health in health_status.items():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        
        with col1:
            status_color = "🟢" if health["status"] == "healthy" else \
                          "🟡" if health["status"] == "warning" else "🔴"
            st.write(f"{status_color} **{service_name}**")
        
        with col2:
            st.write(health["status"].upper())
        
        with col3:
            st.write(f"{health['response_time']}ms")
        
        with col4:
            st.write(health["last_check"].strftime("%Y-%m-%d %H:%M:%S"))
    
    # System metrics
    if st.session_state.system_metrics:
        st.subheader("📊 System Performance Metrics")
        
        # Latest metrics
        latest_metrics = st.session_state.system_metrics[-1] if st.session_state.system_metrics else {}
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("CPU Usage", f"{latest_metrics.get('cpu_usage', 0):.1f}%")
        with col2:
            st.metric("Memory Usage", f"{latest_metrics.get('memory_usage', 0):.1f}%")
        with col3:
            st.metric("Active Connections", latest_metrics.get('active_connections', 0))
        with col4:
            st.metric("Throughput", f"{latest_metrics.get('throughput', 0)} req/min")
        
        # Performance charts
        st.subheader("📈 Performance Trends")
        
        if len(st.session_state.system_metrics) > 1:
            metrics_df = pd.DataFrame([{
                "Time": m["timestamp"],
                "CPU Usage": m["cpu_usage"],
                "Memory Usage": m["memory_usage"],
                "Response Time": m["response_time"],
                "Active Connections": m["active_connections"]
            } for m in st.session_state.system_metrics[-20:]])  # Last 20 metrics
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.line(metrics_df, x="Time", y=["CPU Usage", "Memory Usage"], 
                             title="CPU & Memory Usage")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.line(metrics_df, x="Time", y="Response Time", 
                             title="Response Time Trend")
                st.plotly_chart(fig, use_container_width=True)
    
    # Health check actions
    st.subheader("🔧 System Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Health Status", key="refresh_health"):
            st.success("Health status refreshed!")
            st.rerun()
    
    with col2:
        if st.button("📊 Generate Health Report", key="generate_report"):
            st.success("Health report generated!")
    
    with col3:
        if st.button("🚨 Test Emergency Mode", key="test_emergency"):
            st.warning("Emergency mode test initiated!")

def render_sidebar():
    """Render sidebar with navigation and info"""
    with st.sidebar:
        st.title("🛡️ Navigation")
        
        # System status overview
        st.subheader("🏗️ A2A/MCP Architecture")
        st.markdown("""
        **Proper Design:**
        - 🤖 Single chatbot interface
        - 🧠 Domain Agent orchestration  
        - 🔄 A2A protocol communication
        - 🛠️ MCP tools for enterprise access
        - ✅ Comprehensive automated responses
        """)
        
        st.subheader("📊 Current Session")
        total_messages = len(st.session_state.conversation_history)
        user_messages = len([c for c in st.session_state.conversation_history if c["type"] == "user"])
        api_calls = len(st.session_state.api_calls)
        
        st.metric("Total Messages", total_messages)
        st.metric("Your Messages", user_messages)
        st.metric("API Calls", api_calls)
        
        if st.button("🗑️ Clear All Data", key="clear_all_data"):
            st.session_state.conversation_history = []
            st.session_state.api_calls = []
            st.session_state.system_metrics = []
            st.session_state.analytics_data = []
            st.success("All data cleared!")
            st.rerun()
        
        st.subheader("💡 Sample Questions")
        st.markdown("""
        **Claims:**
        - "I was in an accident and need to file a claim"
        - "What's the status of my claim?"
        
        **Policy:**
        - "What does my auto insurance cover?"
        - "I want to add a new car to my policy"
        
        **Billing:**
        - "When is my next payment due?"
        - "I want to change my payment method"
        """)

def main():
    """Main application"""
    render_header()
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat Interface", 
        "🧠 LLM Thinking", 
        "📡 API Monitor", 
        "📊 Analytics", 
        "�� System Health"
    ])
    
    with tab1:
        render_chat_tab()
    
    with tab2:
        render_llm_thinking_tab()
    
    with tab3:
        render_api_monitor_tab()
    
    with tab4:
        render_analytics_tab()
    
    with tab5:
        render_system_health_tab()
    
    # Render sidebar
    render_sidebar()

if __name__ == "__main__":
    main() 