import streamlit as st
import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SUPPORT_AGENT_URL = os.getenv("SUPPORT_AGENT_URL", "http://support-agent:8005")
CLAIMS_AGENT_URL = os.getenv("CLAIMS_AGENT_URL", "http://claims-agent:8007")

# If running locally, use localhost
if "localhost" not in SUPPORT_AGENT_URL and os.getenv("LOCAL_DEV"):
    SUPPORT_AGENT_URL = "http://localhost:30005"
    CLAIMS_AGENT_URL = "http://localhost:30008"

st.set_page_config(
    page_title="Insurance AI PoC Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "agent_logs" not in st.session_state:
    st.session_state.agent_logs = []
if "api_calls" not in st.session_state:
    st.session_state.api_calls = []
if "llm_thinking" not in st.session_state:
    st.session_state.llm_thinking = []

def log_agent_activity(agent_name: str, activity_type: str, details: Dict[str, Any]):
    """Log agent activity for visualization"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = {
        "timestamp": timestamp,
        "agent": agent_name,
        "type": activity_type,
        "details": details
    }
    st.session_state.agent_logs.append(log_entry)
    
def log_api_call(method: str, url: str, payload: Dict[str, Any], response: Dict[str, Any], status_code: int):
    """Log API calls for visualization"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    api_entry = {
        "timestamp": timestamp,
        "method": method,
        "url": url,
        "payload": payload,
        "response": response,
        "status_code": status_code
    }
    st.session_state.api_calls.append(api_entry)

def log_llm_thinking(step: str, content: str, agent: str = ""):
    """Log LLM thinking process"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thinking_entry = {
        "timestamp": timestamp,
        "step": step,
        "content": content,
        "agent": agent
    }
    st.session_state.llm_thinking.append(thinking_entry)

def extract_response_text(response_data: Dict[str, Any]) -> str:
    """Extract the actual response text from nested response structure"""
    if not response_data.get('success', False):
        return response_data.get('error', 'Unknown error occurred')
    
    # Handle nested response structure
    result = response_data.get('result', {})
    if isinstance(result, dict):
        # Try to get response from result
        if 'response' in result:
            return result['response']
        elif 'message' in result:
            return result['message']
    
    # Fallback to direct response field
    if 'response' in response_data:
        return response_data['response']
    
    return "No response text available"

def extract_workflow_info(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract workflow and intent information from response"""
    info = {}
    
    if response_data.get('success', False):
        result = response_data.get('result', {})
        if isinstance(result, dict):
            if 'workflow' in result:
                info['workflow'] = result['workflow']
            if 'intent' in result:
                info['intent'] = result['intent']
            if 'data' in result:
                info['data'] = result['data']
    
    return info

async def call_agent(agent_url: str, agent_name: str, skill_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Call an agent and log the interaction"""
    
    # Log the agent call initiation
    log_agent_activity(
        agent_name, 
        "SKILL_CALL_INITIATED",
        {"skill": skill_name, "parameters": parameters}
    )
    
    # Log LLM thinking process
    log_llm_thinking("PROCESSING_STARTED", f"Starting {skill_name} with user message: {parameters.get('user_message', '')[:100]}...", agent_name)
    
    payload = {
        "skill_name": skill_name,
        "parameters": parameters
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Log pre-API call thinking
            log_llm_thinking("API_CALL_PREPARATION", f"Calling {agent_url}/execute with skill {skill_name}", agent_name)
            
            response = await client.post(
                f"{agent_url}/execute",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            response_data = response.json()
            
            # Log the API call
            log_api_call("POST", f"{agent_url}/execute", payload, response_data, response.status_code)
            
            # Log LLM thinking about response
            if response_data.get('success'):
                response_text = extract_response_text(response_data)
                log_llm_thinking("RESPONSE_GENERATED", f"Successfully generated response: {response_text[:100]}...", agent_name)
                
                # Check for workflow in nested structure
                result = response_data.get('result', {})
                if isinstance(result, dict) and 'workflow' in result:
                    log_llm_thinking("WORKFLOW_IDENTIFIED", f"Identified workflow: {result['workflow']}", agent_name)
            else:
                log_llm_thinking("ERROR_OCCURRED", f"Error in processing: {response_data.get('error', 'Unknown error')}", agent_name)
            
            # Log agent response
            log_agent_activity(
                agent_name,
                "SKILL_CALL_COMPLETED", 
                {"response": response_data, "status_code": response.status_code}
            )
            
            return response_data
            
    except Exception as e:
        error_response = {"success": False, "error": str(e)}
        log_agent_activity(
            agent_name,
            "SKILL_CALL_ERROR",
            {"error": str(e)}
        )
        log_llm_thinking("EXCEPTION_OCCURRED", f"Exception during processing: {str(e)}", agent_name)
        return error_response

def run_async(coro):
    """Helper to run async code in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def main():
    st.title("🏥 Insurance AI PoC Dashboard")
    st.markdown("### Multi-Agent LLM-Powered Insurance Support System")
    
    # Real-time status indicators
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Conversations", len(st.session_state.conversation_history))
    with col2:
        st.metric("API Calls", len(st.session_state.api_calls))
    with col3:
        st.metric("Agent Activities", len(st.session_state.agent_logs))
    
    # Sidebar for agent selection and configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Agent selection
        selected_agent = st.selectbox(
            "Select Agent",
            ["Support Domain Agent", "Claims Domain Agent"],
            help="Choose which agent to interact with"
        )
        
        # Sample customer ID for testing
        customer_id = st.number_input(
            "Customer ID (optional)",
            min_value=1,
            max_value=99999,
            value=12345,
            help="Enter a customer ID for personalized responses"
        )
        
        # Clear logs button
        if st.button("🗑️ Clear All Logs"):
            st.session_state.agent_logs = []
            st.session_state.api_calls = []
            st.session_state.conversation_history = []
            st.session_state.llm_thinking = []
            st.rerun()
        
        st.divider()
        st.header("🔧 Quick Test Messages")
        
        # Quick test buttons
        if selected_agent == "Support Domain Agent":
            st.markdown("**Support Agent Tests:**")
            if st.button("Test Policy Inquiry"):
                st.session_state.test_message = "I want to check my auto insurance policy status"
                st.rerun()
            if st.button("Test General Support"):
                st.session_state.test_message = "How do I update my contact information?"
                st.rerun()
            if st.button("Test Billing Question"):
                st.session_state.test_message = "When is my next premium payment due?"
                st.rerun()
        else:
            st.markdown("**Claims Agent Tests:**")
            if st.button("Test Claim Filing"):
                st.session_state.test_message = "I was in a car accident yesterday and need to file a claim"
                st.rerun()
            if st.button("Test Claim Status"):
                st.session_state.test_message = "What's the status of my claim #12345?"
                st.rerun()
            if st.button("Test Claims Info"):
                st.session_state.test_message = "What documents do I need for a home insurance claim?"
                st.rerun()

    # Main content area with tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat Interface", "🧠 LLM Thinking", "🔍 Agent Activity", "📡 API Calls", "📊 Flow Diagram"])
    
    with tab1:
        st.header(f"Chat with {selected_agent}")
        
        # User input
        user_message = st.text_area(
            "Enter your message:",
            value=getattr(st.session_state, 'test_message', ''),
            height=100,
            help="Type your insurance-related question or request"
        )
        
        # Clear test message after use
        if hasattr(st.session_state, 'test_message'):
            del st.session_state.test_message
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            send_button = st.button("🚀 Send Message", type="primary")
        
        with col2:
            if st.button("🎯 Send with Customer ID"):
                send_button = True
                use_customer_id = True
            else:
                use_customer_id = False
        
        if send_button and user_message.strip():
            # Clear previous thinking logs for this interaction
            st.session_state.llm_thinking = []
            
            with st.spinner(f"Processing with {selected_agent}..."):
                
                # Determine agent URL and skill
                if selected_agent == "Support Domain Agent":
                    agent_url = SUPPORT_AGENT_URL
                    skill_name = "HandleCustomerInquiry"
                    agent_name = "SupportAgent"
                else:
                    agent_url = CLAIMS_AGENT_URL
                    skill_name = "HandleClaimInquiry"
                    agent_name = "ClaimsAgent"
                
                # Prepare parameters
                parameters = {"user_message": user_message}
                if use_customer_id or (customer_id and customer_id > 0):
                    parameters["customer_id"] = customer_id
                
                # Call agent
                response = run_async(call_agent(agent_url, agent_name, skill_name, parameters))
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "user": user_message,
                    "agent": selected_agent,
                    "response": response
                })
        
        # Display conversation history
        st.subheader("💬 Conversation History")
        
        if st.session_state.conversation_history:
            for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:])):  # Show last 5
                with st.expander(f"[{conv['timestamp']}] {conv['agent']}", expanded=(i == 0)):
                    st.markdown(f"**User:** {conv['user']}")
                    
                    if conv['response'].get('success'):
                        # Extract the actual response text using our helper function
                        response_text = extract_response_text(conv['response'])
                        st.success(f"**Agent:** {response_text}")
                        
                        # Extract and show workflow information
                        workflow_info = extract_workflow_info(conv['response'])
                        if 'workflow' in workflow_info:
                            st.info(f"🔄 **Workflow:** {workflow_info['workflow']}")
                        
                        if 'intent' in workflow_info:
                            st.info(f"🎯 **Intent:** {workflow_info['intent']}")
                        
                        # Show additional data if available
                        if 'data' in workflow_info and workflow_info['data']:
                            st.json(workflow_info['data'])
                    else:
                        error_msg = conv['response'].get('error', 'Unknown error')
                        st.error(f"**Error:** {error_msg}")
        else:
            st.info("No conversations yet. Send a message to get started!")
    
    with tab2:
        st.header("🧠 LLM Thinking Process")
        st.markdown("*Real-time view of how the LLM processes your requests*")
        
        if st.session_state.llm_thinking:
            # Show recent thinking process (last 20 entries)
            recent_thinking = st.session_state.llm_thinking[-20:]
            
            for thought in reversed(recent_thinking):
                timestamp = thought["timestamp"]
                step = thought["step"]
                content = thought["content"]
                agent = thought["agent"]
                
                # Color code by thinking step
                if step == "PROCESSING_STARTED":
                    st.info(f"🚀 **[{timestamp}] {agent}** - {step}")
                    st.markdown(f"*{content}*")
                elif step == "API_CALL_PREPARATION":
                    st.warning(f"⚙️ **[{timestamp}] {agent}** - {step}")
                    st.markdown(f"*{content}*")
                elif step == "RESPONSE_GENERATED":
                    st.success(f"✅ **[{timestamp}] {agent}** - {step}")
                    st.markdown(f"*{content}*")
                elif step == "WORKFLOW_IDENTIFIED":
                    st.info(f"🔄 **[{timestamp}] {agent}** - {step}")
                    st.markdown(f"*{content}*")
                elif step == "ERROR_OCCURRED" or step == "EXCEPTION_OCCURRED":
                    st.error(f"❌ **[{timestamp}] {agent}** - {step}")
                    st.markdown(f"*{content}*")
                else:
                    st.markdown(f"🤔 **[{timestamp}] {agent}** - {step}: *{content}*")
                
                st.divider()
        else:
            st.info("No LLM thinking process logged yet. Send a message to see how the AI processes your request!")
    
    with tab3:
        st.header("🔍 Real-time Agent Activity")
        
        # Activity log
        if st.session_state.agent_logs:
            # Show recent activity (last 20 entries)
            recent_logs = st.session_state.agent_logs[-20:]
            
            for log_entry in reversed(recent_logs):
                timestamp = log_entry["timestamp"]
                agent = log_entry["agent"]
                activity_type = log_entry["type"]
                details = log_entry["details"]
                
                # Color code by activity type
                if activity_type == "SKILL_CALL_INITIATED":
                    st.info(f"🚀 **[{timestamp}] {agent}** - Started skill: `{details.get('skill')}`")
                    with st.expander("View parameters"):
                        st.json(details.get('parameters', {}))
                        
                elif activity_type == "SKILL_CALL_COMPLETED":
                    if details.get('response', {}).get('success'):
                        st.success(f"✅ **[{timestamp}] {agent}** - Skill completed successfully")
                    else:
                        st.error(f"❌ **[{timestamp}] {agent}** - Skill failed")
                    with st.expander("View response"):
                        st.json(details.get('response', {}))
                        
                elif activity_type == "SKILL_CALL_ERROR":
                    st.error(f"💥 **[{timestamp}] {agent}** - Error: {details.get('error')}")
                
                st.divider()
        else:
            st.info("No agent activity logged yet. Interact with agents to see their activity here.")
    
    with tab4:
        st.header("📡 API Call Monitor")
        
        if st.session_state.api_calls:
            # Show recent API calls (last 10)
            recent_calls = st.session_state.api_calls[-10:]
            
            for api_call in reversed(recent_calls):
                timestamp = api_call["timestamp"]
                method = api_call["method"]
                url = api_call["url"]
                status_code = api_call["status_code"]
                
                # Color code by status
                status_color = "🟢" if status_code == 200 else "🔴"
                
                st.markdown(f"{status_color} **[{timestamp}] {method}** `{url}` - Status: {status_code}")
                
                col1, col2 = st.columns(2)
                with col1:
                    with st.expander("Request Payload"):
                        st.json(api_call["payload"])
                with col2:
                    with st.expander("Response"):
                        st.json(api_call["response"])
                
                st.divider()
        else:
            st.info("No API calls logged yet. Interact with agents to see API communication here.")
    
    with tab5:
        st.header("📊 Agent Communication Flow")
        
        # Create a visual flow diagram
        st.markdown("""
        ### Current Architecture Flow
        
        ```mermaid
        graph TD
            A[User Input] --> B{Agent Selection}
            B -->|Support| C[Support Domain Agent]
            B -->|Claims| D[Claims Domain Agent]
            
            C --> E[LLM Intent Extraction]
            D --> E
            
            E --> F{Intent Analysis}
            F -->|Policy| G[Policy Technical Agent]
            F -->|Customer| H[Customer Technical Agent]
            F -->|Claims| I[Claims Technical Agent]
            
            G --> J[Backend Services]
            H --> J
            I --> J
            
            J --> K[Data Response]
            K --> L[LLM Response Generation]
            L --> M[Final User Response]
        ```
        """)
        
        # Real-time agent status
        st.subheader("🔄 Agent Health Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                # Check Support Agent health
                health_response = run_async(check_agent_health(SUPPORT_AGENT_URL))
                if health_response.get("status") == "healthy":
                    st.success("✅ Support Agent: Online")
                else:
                    st.error("❌ Support Agent: Offline")
            except:
                st.error("❌ Support Agent: Offline")
        
        with col2:
            try:
                # Check Claims Agent health
                health_response = run_async(check_agent_health(CLAIMS_AGENT_URL))
                if health_response.get("status") == "healthy":
                    st.success("✅ Claims Agent: Online")
                else:
                    st.error("❌ Claims Agent: Offline")
            except:
                st.error("❌ Claims Agent: Offline")
        
        # Activity metrics
        if st.session_state.agent_logs:
            st.subheader("📈 Activity Metrics")
            
            # Count activities by agent
            agent_activity = {}
            for log in st.session_state.agent_logs:
                agent = log["agent"]
                agent_activity[agent] = agent_activity.get(agent, 0) + 1
            
            for agent, count in agent_activity.items():
                st.metric(f"{agent} Activities", count)
        
        # Show recent workflow patterns
        if st.session_state.conversation_history:
            st.subheader("🔄 Recent Workflow Patterns")
            workflows = []
            for conv in st.session_state.conversation_history[-5:]:
                workflow_info = extract_workflow_info(conv['response'])
                if 'workflow' in workflow_info:
                    workflows.append(workflow_info['workflow'])
            
            if workflows:
                workflow_counts = {}
                for wf in workflows:
                    workflow_counts[wf] = workflow_counts.get(wf, 0) + 1
                
                for workflow, count in workflow_counts.items():
                    st.metric(f"{workflow.replace('_', ' ').title()} Workflows", count)

async def check_agent_health(agent_url: str) -> Dict[str, Any]:
    """Check agent health status"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{agent_url}/health")
            return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    main() 