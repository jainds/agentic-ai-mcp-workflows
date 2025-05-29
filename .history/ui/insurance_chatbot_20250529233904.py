"""
Insurance AI PoC - Single Chatbot Interface
Proper A2A/MCP Architecture Implementation
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="🛡️ Insurance AI Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'thinking_steps' not in st.session_state:
    st.session_state.thinking_steps = []

class InsuranceAIClient:
    """Client for interacting with the Insurance AI system"""
    
    def __init__(self):
        self.claims_agent_url = "http://claims-agent:8000"
        self.timeout = 30
    
    def send_message(self, user_message: str) -> Dict[str, Any]:
        """Send message to Claims Agent (Domain Agent) which will orchestrate everything"""
        try:
            # The Claims Agent (Domain Agent) will:
            # 1. Analyze the user's request
            # 2. Determine what Technical Agents to call via A2A
            # 3. Technical Agents will use MCP tools to access enterprise systems
            # 4. Return a comprehensive response
            
            payload = {
                "message": user_message,
                "user_id": "dashboard_user",
                "conversation_id": f"chat_{int(time.time())}",
                "enable_orchestration": True,  # Enable A2A orchestration
                "enable_thinking": True        # Show thinking process
            }
            
            response = requests.post(
                f"{self.claims_agent_url}/process",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "response": response.json(),
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.ConnectionError:
            # Fallback to demo mode when services aren't available
            return self._demo_response(user_message)
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}",
                "status_code": 0
            }
    
    def _demo_response(self, user_message: str) -> Dict[str, Any]:
        """Demo response when actual services aren't available"""
        
        # Simulate thinking process
        thinking_steps = [
            "🤔 Analyzing your request...",
            "🔍 Determining required actions...",
            "🤖 Orchestrating technical agents...",
            "📊 Gathering data from enterprise systems...",
            "✅ Preparing comprehensive response..."
        ]
        
        # Simulate orchestration based on message content
        orchestration_steps = []
        demo_response = ""
        
        if "claim" in user_message.lower():
            orchestration_steps = [
                "📋 Claims Agent analyzing request",
                "🔄 Calling Data Agent via A2A protocol",
                "📊 Data Agent using MCP tools to access Claims Service",
                "👤 Data Agent using MCP tools to access Customer Service", 
                "🔍 Data Agent performing fraud analysis",
                "📧 Calling Notification Agent via A2A protocol",
                "✉️ Notification Agent preparing claim confirmation"
            ]
            demo_response = """I've processed your claim request. Here's what I've done:

**Claim Analysis Completed:**
- ✅ Policy validation successful (Policy: POL-AUTO-123456)
- ✅ Customer verification completed
- ✅ Fraud risk assessment: Low risk
- ✅ Coverage confirmation: Accident damage covered up to $50,000

**Actions Taken:**
- 📋 Claim #CLM-2024-001234 created
- 📧 Confirmation email sent to your registered address
- 🔔 SMS notification sent
- 📄 Required documents list sent via email

**Next Steps:**
1. Upload photos of vehicle damage via our app
2. Schedule inspection appointment
3. Estimated processing time: 3-5 business days

Is there anything specific about your claim you'd like me to help with?"""

        elif "policy" in user_message.lower():
            orchestration_steps = [
                "📋 Claims Agent analyzing policy inquiry",
                "🔄 Calling Data Agent via A2A protocol", 
                "📊 Data Agent using MCP tools to access Policy Service",
                "👤 Data Agent using MCP tools to access Customer Service",
                "📈 Data Agent generating coverage summary"
            ]
            demo_response = """I've retrieved your policy information:

**Policy Overview:**
- 📄 Policy Number: POL-AUTO-123456
- 🚗 Vehicle: 2022 Honda Accord
- 📅 Coverage Period: Jan 1, 2024 - Dec 31, 2024
- 💰 Premium: $1,200/year

**Coverage Details:**
- ✅ Liability: $100,000 per person / $300,000 per accident
- ✅ Collision: $50,000 deductible $500
- ✅ Comprehensive: $50,000 deductible $250
- ✅ Medical Payments: $10,000
- ✅ Uninsured Motorist: $100,000

**Recent Activity:**
- Last payment: $300 (Quarterly - Dec 1, 2024)
- Next payment due: Mar 1, 2025

Would you like me to explain any specific coverage or help with policy changes?"""

        elif "payment" in user_message.lower() or "billing" in user_message.lower():
            orchestration_steps = [
                "📋 Claims Agent analyzing billing inquiry",
                "🔄 Calling Data Agent via A2A protocol",
                "💳 Data Agent using MCP tools to access Billing Service",
                "👤 Data Agent using MCP tools to access Customer Service",
                "📊 Data Agent retrieving payment history"
            ]
            demo_response = """Here's your billing information:

**Current Billing Status:**
- 📊 Account Status: Current (No outstanding balance)
- 💰 Last Payment: $300.00 on Dec 1, 2024
- 🔄 Payment Method: Auto-pay from Bank ****1234
- 📅 Next Payment: $300.00 due Mar 1, 2025

**Payment History (Last 6 months):**
- Dec 1, 2024: $300.00 ✅
- Sep 1, 2024: $300.00 ✅
- Jun 1, 2024: $300.00 ✅

**Available Options:**
- 🔄 Change payment method
- 📅 Update payment schedule  
- 💳 Make one-time payment
- 📧 Update billing notifications

Would you like me to help with any billing changes or have questions about your payments?"""

        else:
            orchestration_steps = [
                "📋 Claims Agent analyzing general inquiry",
                "🔄 Calling Data Agent via A2A protocol",
                "👤 Data Agent using MCP tools to access Customer Service",
                "🤖 Claims Agent preparing general assistance response"
            ]
            demo_response = """Hello! I'm your Insurance AI Assistant. I can help you with:

**🔧 Claims & Incidents:**
- File new claims
- Check claim status
- Upload documents
- Schedule inspections

**📄 Policy Management:**
- View policy details
- Check coverage
- Update information
- Add/remove vehicles

**💰 Billing & Payments:**
- View payment history
- Update payment methods
- Make payments
- Billing questions

**🆘 General Support:**
- Coverage explanations
- Policy questions
- Account assistance
- Emergency claims

What would you like help with today? Just describe your question in natural language!"""

        return {
            "success": True,
            "response": {
                "message": demo_response,
                "thinking_steps": thinking_steps,
                "orchestration_steps": orchestration_steps,
                "agent_interactions": len(orchestration_steps),
                "response_time_ms": 1500
            },
            "status_code": 200
        }

def render_header():
    """Render the main header"""
    st.markdown('<h1 class="main-header">🛡️ Insurance AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### Your Intelligent Insurance Companion")
    st.markdown("Ask me anything about your insurance policies, claims, billing, or general questions. I'll orchestrate all the necessary services to help you!")
    st.markdown("---")

def render_chat_interface():
    """Render the main chat interface"""
    
    # Initialize client
    client = InsuranceAIClient()
    
    # Chat input
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask me anything about your insurance:",
            placeholder="e.g., 'I was in an accident and need to file a claim' or 'What does my policy cover?'",
            key="user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("💬 Send", type="primary", use_container_width=True)
    
    # Handle user input
    if send_button and user_input:
        # Add user message to history
        st.session_state.conversation_history.append({
            "type": "user",
            "message": user_input,
            "timestamp": datetime.now()
        })
        
        # Show thinking indicator
        with st.spinner("🤔 Analyzing your request and orchestrating agents..."):
            # Send to Claims Agent (Domain Agent)
            response = client.send_message(user_input)
        
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
                "timestamp": datetime.now()
            })
        else:
            # Add error response
            st.session_state.conversation_history.append({
                "type": "error",
                "message": f"I'm sorry, I encountered an issue: {response['error']}",
                "timestamp": datetime.now()
            })
        
        # Clear input and rerun
        st.rerun()
    
    # Display conversation history
    st.markdown("### 💬 Conversation")
    
    if not st.session_state.conversation_history:
        st.info("👋 Welcome! Ask me anything about your insurance. I can help with claims, policies, billing, and general questions.")
    
    # Show conversation in reverse order (newest first)
    for i, chat in enumerate(reversed(st.session_state.conversation_history)):
        if chat["type"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>You ({chat["timestamp"].strftime("%H:%M:%S")}):</strong><br>
                {chat["message"]}
            </div>
            """, unsafe_allow_html=True)
            
        elif chat["type"] == "agent":
            # Show thinking process if available
            if "thinking_steps" in chat and chat["thinking_steps"]:
                with st.expander(f"🧠 AI Thinking Process ({len(chat['thinking_steps'])} steps)", expanded=False):
                    for step in chat["thinking_steps"]:
                        st.markdown(f'<div class="thinking-indicator">{step}</div>', unsafe_allow_html=True)
            
            # Show orchestration process if available  
            if "orchestration_steps" in chat and chat["orchestration_steps"]:
                with st.expander(f"🔄 Agent Orchestration ({chat.get('agent_interactions', 0)} interactions)", expanded=False):
                    for step in chat["orchestration_steps"]:
                        st.markdown(f'<div class="agent-orchestration">{step}</div>', unsafe_allow_html=True)
            
            # Show main response
            st.markdown(f"""
            <div class="chat-message agent-message">
                <strong>Insurance AI Assistant ({chat["timestamp"].strftime("%H:%M:%S")}):</strong><br>
                {chat["message"].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
            
            # Show performance info
            if "response_time" in chat:
                st.caption(f"⚡ Response time: {chat['response_time']}ms | Agent interactions: {chat.get('agent_interactions', 0)}")
        
        elif chat["type"] == "error":
            st.error(f"**Error ({chat['timestamp'].strftime('%H:%M:%S')}):** {chat['message']}")

def render_sidebar():
    """Render sidebar with system info"""
    with st.sidebar:
        st.title("🛡️ System Info")
        
        st.subheader("🏗️ Architecture")
        st.markdown("""
        **Proper A2A/MCP Design:**
        - 🤖 You chat with ONE Domain Agent
        - 🔄 Domain Agent orchestrates Technical Agents
        - 🛠️ Technical Agents use MCP tools
        - 📊 Enterprise systems accessed via MCP
        """)
        
        st.subheader("📊 Current Session")
        total_messages = len(st.session_state.conversation_history)
        user_messages = len([c for c in st.session_state.conversation_history if c["type"] == "user"])
        st.metric("Total Messages", total_messages)
        st.metric("Your Messages", user_messages)
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.conversation_history = []
            st.rerun()
        
        st.subheader("💡 Sample Questions")
        st.markdown("""
        **Claims:**
        - "I was in an accident and need to file a claim"
        - "What's the status of claim #CLM-123?"
        
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
    
    # Main content
    col1, col2 = st.columns([4, 1])
    
    with col1:
        render_chat_interface()
    
    with col2:
        render_sidebar()

if __name__ == "__main__":
    main() 