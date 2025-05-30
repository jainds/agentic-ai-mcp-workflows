#!/usr/bin/env python3
"""
Thinking Steps and Orchestration Component for Insurance AI UI
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, List
from ui.components.config import UIConfig

def render_thinking_steps():
    """Render LLM thinking steps visualization"""
    if not UIConfig.ENABLE_THINKING_STEPS:
        return
    
    st.subheader("🧠 LLM Thinking Steps")
    
    thinking_steps = st.session_state.get('thinking_steps', [])
    
    if not thinking_steps:
        st.info("No thinking steps recorded yet. Start a conversation to see how the AI thinks through problems.")
        return
    
    # Show recent thinking steps
    st.write(f"**Latest {min(10, len(thinking_steps))} Thinking Steps**")
    
    recent_steps = thinking_steps[-10:] if len(thinking_steps) > 10 else thinking_steps
    
    for i, step in enumerate(reversed(recent_steps)):  # Show newest first
        with st.container():
            # Parse step data
            if isinstance(step, dict):
                step_content = step.get("content", str(step))
                step_type = step.get("type", "reasoning")
                timestamp = step.get("timestamp", datetime.now())
            else:
                step_content = str(step)
                step_type = "reasoning"
                timestamp = datetime.now()
            
            # Step header
            col1, col2 = st.columns([4, 1])
            with col1:
                step_icon = "🎯" if step_type == "decision" else "💭" if step_type == "reasoning" else "🔍"
                st.write(f"**{step_icon} Step {len(recent_steps) - i}**")
            with col2:
                if isinstance(timestamp, datetime):
                    st.caption(timestamp.strftime("%H:%M:%S"))
                else:
                    st.caption("Recent")
            
            # Step content
            with st.container():
                if len(step_content) > 200:
                    with st.expander("View full thinking step", expanded=False):
                        st.write(step_content)
                else:
                    st.write(step_content)
                
                if isinstance(step, dict) and "confidence" in step:
                    confidence = step["confidence"]
                    st.progress(confidence / 100, text=f"Confidence: {confidence}%")

def render_orchestration_view():
    """Render agent orchestration and A2A communication"""
    if not UIConfig.ENABLE_ORCHESTRATION_VIEW:
        return
    
    st.subheader("🎭 Agent Orchestration")
    
    orchestration_data = st.session_state.get('orchestration_data', [])
    
    if not orchestration_data:
        st.info("No orchestration events recorded yet. Start a conversation to see agent communication.")
        return
    
    # Show orchestration events
    st.write(f"**Latest {min(15, len(orchestration_data))} Orchestration Events**")
    
    recent_events = orchestration_data[-15:] if len(orchestration_data) > 15 else orchestration_data
    
    for i, event in enumerate(reversed(recent_events)):  # Show newest first
        with st.container():
            # Parse event data
            if isinstance(event, dict):
                event_type = event.get("type", "unknown")
                source = event.get("source", "Unknown Agent")
                target = event.get("target", "Unknown Target")
                message = event.get("message", str(event))
                timestamp = event.get("timestamp", datetime.now())
                protocol = event.get("protocol", "unknown")
            else:
                event_type = "event"
                source = "System"
                target = "Agent"
                message = str(event)
                timestamp = datetime.now()
                protocol = "internal"
            
            # Event visualization
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # Source and target with protocol
                if protocol.lower() == "a2a":
                    protocol_icon = "🔄"
                    protocol_color = "blue"
                elif protocol.lower() == "mcp":
                    protocol_icon = "🔧"
                    protocol_color = "green"
                else:
                    protocol_icon = "📨"
                    protocol_color = "gray"
                
                st.markdown(f"**{source}** {protocol_icon} **{target}**")
                st.caption(f"Protocol: {protocol.upper()}")
            
            with col2:
                # Event type and message
                event_icon = {
                    "request": "📤",
                    "response": "📥",
                    "thinking": "🧠",
                    "decision": "🎯",
                    "tool_call": "🔧",
                    "orchestration": "🎭"
                }.get(event_type, "📝")
                
                st.write(f"{event_icon} **{event_type.title()}**")
                
                if len(message) > 100:
                    with st.expander("View full message", expanded=False):
                        st.write(message)
                else:
                    st.write(message)
            
            with col3:
                if isinstance(timestamp, datetime):
                    st.caption(timestamp.strftime("%H:%M:%S"))
                else:
                    st.caption("Recent")
            
            st.divider()

def render_architecture_flow():
    """Render visual representation of the architecture flow"""
    if not UIConfig.ENABLE_ORCHESTRATION_VIEW:
        return
    
    st.subheader("🏗️ Architecture Flow")
    
    # Visual flow diagram
    st.markdown("""
    ```
    📱 Streamlit UI
         ↓ (User Input)
    🧠 Domain Agent (LLM Reasoning)
         ↓ (A2A Protocol)
    🔧 Technical Agent (FastMCP)
         ↓ (MCP Tools)
    🏢 Insurance Services
    ```
    """)
    
    # Current flow status
    conversation_count = len(st.session_state.get('conversation_history', []))
    api_calls_count = len(st.session_state.get('api_calls', []))
    thinking_steps_count = len(st.session_state.get('thinking_steps', []))
    orchestration_count = len(st.session_state.get('orchestration_data', []))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("User Interactions", conversation_count)
        st.metric("LLM Thinking Steps", thinking_steps_count)
    
    with col2:
        st.metric("API Communications", api_calls_count)
        st.metric("Orchestration Events", orchestration_count)
    
    # Flow health indicator
    if conversation_count > 0 and api_calls_count > 0:
        st.success("✅ Full architecture flow is active")
    elif conversation_count > 0:
        st.warning("⚠️ UI active, but limited backend communication")
    else:
        st.info("💤 Waiting for user interaction to activate flow")

def add_thinking_step(content: str, step_type: str = "reasoning", confidence: int = None):
    """Add a thinking step to the session state"""
    if not UIConfig.ENABLE_THINKING_STEPS:
        return
    
    if 'thinking_steps' not in st.session_state:
        st.session_state.thinking_steps = []
    
    step = {
        "content": content,
        "type": step_type,
        "timestamp": datetime.now()
    }
    
    if confidence is not None:
        step["confidence"] = confidence
    
    st.session_state.thinking_steps.append(step)
    
    # Keep only last 100 thinking steps
    if len(st.session_state.thinking_steps) > 100:
        st.session_state.thinking_steps = st.session_state.thinking_steps[-100:]

def add_orchestration_event(event_type: str, source: str, target: str, 
                          message: str, protocol: str = "internal"):
    """Add an orchestration event to the session state"""
    if not UIConfig.ENABLE_ORCHESTRATION_VIEW:
        return
    
    if 'orchestration_data' not in st.session_state:
        st.session_state.orchestration_data = []
    
    event = {
        "type": event_type,
        "source": source,
        "target": target,
        "message": message,
        "protocol": protocol,
        "timestamp": datetime.now()
    }
    
    st.session_state.orchestration_data.append(event)
    
    # Keep only last 50 orchestration events
    if len(st.session_state.orchestration_data) > 50:
        st.session_state.orchestration_data = st.session_state.orchestration_data[-50:]

def get_thinking_summary() -> Dict[str, Any]:
    """Get thinking and orchestration summary for other components"""
    if not (UIConfig.ENABLE_THINKING_STEPS or UIConfig.ENABLE_ORCHESTRATION_VIEW):
        return {"features_disabled": True}
    
    thinking_steps = st.session_state.get('thinking_steps', [])
    orchestration_data = st.session_state.get('orchestration_data', [])
    
    # Recent activity (last 5 minutes)
    recent_threshold = datetime.now() - timedelta(minutes=5)
    recent_thinking = [
        step for step in thinking_steps 
        if isinstance(step, dict) and isinstance(step.get("timestamp"), datetime) 
        and step["timestamp"] > recent_threshold
    ]
    recent_orchestration = [
        event for event in orchestration_data
        if isinstance(event, dict) and isinstance(event.get("timestamp"), datetime)
        and event["timestamp"] > recent_threshold
    ]
    
    return {
        "total_thinking_steps": len(thinking_steps),
        "total_orchestration_events": len(orchestration_data),
        "recent_thinking_steps": len(recent_thinking),
        "recent_orchestration_events": len(recent_orchestration),
        "last_thinking_step": thinking_steps[-1] if thinking_steps else None,
        "last_orchestration_event": orchestration_data[-1] if orchestration_data else None
    } 