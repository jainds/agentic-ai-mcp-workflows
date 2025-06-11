#!/usr/bin/env python3
"""
Chat Interface Component for Insurance AI UI
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any
from .config import UIConfig
from .agent_client import DomainAgentClient, send_chat_message_simple

def initialize_chat_state():
    """Initialize chat-related session state"""
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'api_calls' not in st.session_state:
        st.session_state.api_calls = []
    if 'thinking_steps' not in st.session_state:
        st.session_state.thinking_steps = []
    if 'orchestration_data' not in st.session_state:
        st.session_state.orchestration_data = []

def render_chat_interface():
    """Render the main chat interface"""
    st.title("💬 Insurance AI Assistant")
    
    if UIConfig.is_simple_mode():
        st.info("🎯 Simple Chat Mode - Basic functionality")
    elif UIConfig.is_advanced_mode():
        st.info("🔧 Advanced Mode - Full monitoring and debugging")
    
    # Display conversation history
    if st.session_state.conversation_history:
        st.subheader("📝 Conversation")
        for i, exchange in enumerate(st.session_state.conversation_history):
            with st.expander(f"Exchange {i+1} - {exchange['timestamp'].strftime('%H:%M:%S')}", expanded=(i == len(st.session_state.conversation_history) - 1)):
                st.markdown(f"**You:** {exchange['user_message']}")
                st.markdown(f"**Assistant:** {exchange['assistant_response']}")
    
    # Chat input
    message = st.text_input("💬 Ask about insurance, claims, policies, or account details:", 
                           placeholder="How can I help you with your insurance today?")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        send_button = st.button("Send", type="primary", use_container_width=True)
    with col2:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.conversation_history = []
            if UIConfig.ENABLE_API_MONITORING:
                st.session_state.api_calls = []
            if UIConfig.ENABLE_THINKING_STEPS:
                st.session_state.thinking_steps = []
            if UIConfig.ENABLE_ORCHESTRATION_VIEW:
                st.session_state.orchestration_data = []
            st.rerun()
    
    # Process message
    if send_button and message:
        process_chat_message(message)

def process_chat_message(message: str):
    """Process a chat message and get response"""
    customer_id = st.session_state.get('customer_id', 'TEST-CUSTOMER')
    
    with st.spinner("🤔 Processing your request..."):
        if UIConfig.is_advanced_mode():
            # Use advanced client with full monitoring
            agent_client = DomainAgentClient()
            result = agent_client.send_message(message, customer_id)
        else:
            # Use simple chat function
            result = send_chat_message_simple(message, customer_id)
        
        # Add to conversation history
        exchange = {
            "timestamp": datetime.now(),
            "user_message": message,
            "assistant_response": result.get("response", "No response received"),
            "metadata": {
                "customer_id": customer_id,
                "thinking_steps_count": len(result.get("thinking_steps", [])),
                "orchestration_events_count": len(result.get("orchestration_events", [])),
                "api_calls_count": len(result.get("api_calls", []))
            }
        }
        
        st.session_state.conversation_history.append(exchange)
        
        # Success message with details (if advanced features enabled)
        if UIConfig.is_advanced_mode():
            thinking_count = exchange["metadata"]["thinking_steps_count"]
            orchestration_count = exchange["metadata"]["orchestration_events_count"]
            api_count = exchange["metadata"]["api_calls_count"]
            
            st.success(f"✅ Response generated! "
                      f"Thinking: {thinking_count} steps, "
                      f"Orchestration: {orchestration_count} events, "
                      f"API calls: {api_count}")
        else:
            st.success("✅ Response generated!")
        
        st.rerun()

def render_quick_actions():
    """Render quick action buttons for common queries"""
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Check Claims", use_container_width=True):
            process_chat_message("Show me my recent claims status")
    
    with col2:
        if st.button("📄 View Policies", use_container_width=True):
            process_chat_message("What insurance policies do I have?")
    
    with col3:
        if st.button("💰 Get Quote", use_container_width=True):
            process_chat_message("I'd like to get a quote for auto insurance")

def get_conversation_summary() -> Dict[str, Any]:
    """Get conversation summary for other components"""
    if not st.session_state.conversation_history:
        return {"total_exchanges": 0, "last_activity": None}
    
    last_exchange = st.session_state.conversation_history[-1]
    
    return {
        "total_exchanges": len(st.session_state.conversation_history),
        "last_activity": last_exchange["timestamp"],
        "last_user_message": last_exchange["user_message"],
        "last_response_length": len(last_exchange["assistant_response"])
    } 