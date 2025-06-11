#!/usr/bin/env python3
"""
Insurance AI Assistant - Modular Streamlit UI
Supports both Simple and Advanced modes with toggleable features
"""

import streamlit as st
import sys
import os

# Add ui directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.components import (
    UIConfig,
    # Authentication
    render_authentication, ensure_authentication, 
    # Chat Interface  
    initialize_chat_state, render_chat_interface, render_quick_actions,
    # Monitoring (conditionally imported based on config)
    render_system_health, render_api_monitoring, render_performance_metrics,
    # Thinking & Orchestration (conditionally imported based on config)
    render_thinking_steps, render_orchestration_view, render_architecture_flow
)

def initialize_session_state():
    """Initialize all session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Initialize chat state
    initialize_chat_state()

def render_header():
    """Render page header with mode indicator"""
    st.set_page_config(
        page_title="Insurance AI Assistant",
        page_icon="🏢",
        layout="wide" if UIConfig.is_advanced_mode() else "centered",
        initial_sidebar_state="expanded"
    )
    
    # Header with feature toggles info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏢 Insurance AI Assistant")
        if UIConfig.is_simple_mode():
            st.caption("Simple Chat Mode - Basic functionality")
        else:
            st.caption("Advanced Mode - Full monitoring and debugging capabilities")
    
    with col2:
        # Feature toggle instructions
        with st.expander("🎛️ Feature Controls"):
            st.write("**Environment Variables:**")
            st.code("""
# Toggle UI mode
UI_MODE=simple|advanced

# Enable/disable specific features
ENABLE_ADVANCED_FEATURES=true|false
ENABLE_SYSTEM_MONITORING=true|false
ENABLE_API_MONITORING=true|false
ENABLE_THINKING_STEPS=true|false
ENABLE_ORCHESTRATION_VIEW=true|false
            """)
            
            # Current feature status
            st.write("**Current Status:**")
            features = UIConfig.get_enabled_features()
            for feature, enabled in features.items():
                icon = "✅" if enabled else "❌"
                st.write(f"{icon} {feature.replace('_', ' ').title()}")

def render_simple_mode():
    """Render simple chat interface"""
    # Minimal authentication in sidebar
    render_authentication()
    
    # Main chat interface
    if ensure_authentication():
        render_chat_interface()
        
        # Quick actions (always available)
        render_quick_actions()
    else:
        st.info("👋 Please log in to start chatting with the Insurance AI Assistant")
        st.markdown("""
        **Available Demo Customers:**
        - `CUST-001` - John Smith (Premium)
        - `CUST-002` - Jane Doe (Standard)  
        - `CUST-003` - Bob Johnson (Basic)
        - `TEST-CUSTOMER` - Test User (Demo)
        """)

def render_advanced_mode():
    """Render advanced interface with full monitoring"""
    # Create tabs for different views
    tabs = []
    tab_names = ["💬 Chat"]
    
    # Add tabs based on enabled features
    if UIConfig.ENABLE_SYSTEM_MONITORING:
        tab_names.append("🏥 System Health")
    if UIConfig.ENABLE_API_MONITORING:
        tab_names.append("📊 API Monitoring")
    if UIConfig.ENABLE_THINKING_STEPS:
        tab_names.append("🧠 Thinking Steps")
    if UIConfig.ENABLE_ORCHESTRATION_VIEW:
        tab_names.append("🎭 Orchestration")
    
    tabs = st.tabs(tab_names)
    
    # Authentication in sidebar (always present)
    render_authentication()
    
    if not ensure_authentication():
        with tabs[0]:  # Chat tab
            st.info("👋 Please log in to access the Insurance AI Assistant")
            st.markdown("""
            **Available Demo Customers:**
            - `CUST-001` - John Smith (Premium)
            - `CUST-002` - Jane Doe (Standard)  
            - `CUST-003` - Bob Johnson (Basic)
            - `TEST-CUSTOMER` - Test User (Demo)
            """)
        return
    
    # Chat Tab (always first)
    with tabs[0]:
        render_chat_interface()
        render_quick_actions()
    
    # Conditional tabs based on enabled features
    tab_index = 1
    
    if UIConfig.ENABLE_SYSTEM_MONITORING and len(tabs) > tab_index:
        with tabs[tab_index]:
            render_system_health()
            render_performance_metrics()
        tab_index += 1
    
    if UIConfig.ENABLE_API_MONITORING and len(tabs) > tab_index:
        with tabs[tab_index]:
            render_api_monitoring()
        tab_index += 1
    
    if UIConfig.ENABLE_THINKING_STEPS and len(tabs) > tab_index:
        with tabs[tab_index]:
            render_thinking_steps()
        tab_index += 1
    
    if UIConfig.ENABLE_ORCHESTRATION_VIEW and len(tabs) > tab_index:
        with tabs[tab_index]:
            render_orchestration_view()
            render_architecture_flow()

def render_sidebar_info():
    """Render additional sidebar information for advanced mode"""
    if not UIConfig.is_advanced_mode():
        return
    
    with st.sidebar:
        st.markdown("---")
        st.subheader("📊 Session Summary")
        
        # Conversation summary
        conversation_count = len(st.session_state.get('conversation_history', []))
        api_calls_count = len(st.session_state.get('api_calls', []))
        thinking_steps_count = len(st.session_state.get('thinking_steps', []))
        orchestration_count = len(st.session_state.get('orchestration_data', []))
        
        st.metric("Conversations", conversation_count)
        if UIConfig.ENABLE_API_MONITORING:
            st.metric("API Calls", api_calls_count)
        if UIConfig.ENABLE_THINKING_STEPS:
            st.metric("Thinking Steps", thinking_steps_count)
        if UIConfig.ENABLE_ORCHESTRATION_VIEW:
            st.metric("Orchestration Events", orchestration_count)
        
        # Quick feature status
        st.markdown("---")
        st.subheader("🎛️ Active Features")
        
        features = UIConfig.get_enabled_features()
        for feature, enabled in features.items():
            if feature not in ['simple_mode', 'advanced_mode']:  # Skip mode indicators
                icon = "✅" if enabled else "❌"
                feature_name = feature.replace('_', ' ').replace('enable ', '').title()
                st.write(f"{icon} {feature_name}")

def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Render based on mode
    if UIConfig.is_simple_mode():
        render_simple_mode()
    else:
        render_advanced_mode()
    
    # Render sidebar info for advanced mode
    render_sidebar_info()

if __name__ == "__main__":
    main() 