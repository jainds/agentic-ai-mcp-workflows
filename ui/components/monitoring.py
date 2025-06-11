#!/usr/bin/env python3
"""
System Monitoring Component for Insurance AI UI
"""

import streamlit as st
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from .config import UIConfig

def check_service_health() -> Dict[str, Dict[str, Any]]:
    """Check health of all monitored services"""
    health_status = {}
    
    for service_name, endpoint in UIConfig.MONITORED_SERVICES.items():
        try:
            start_time = time.time()
            
            # Adjust endpoint for FastMCP services (they use /mcp/ instead of /health)
            if "FastMCP" in service_name:
                # For FastMCP services, try to ping the base MCP endpoint
                health_url = endpoint  # Already has /mcp/
            else:
                # For regular services, use /health
                if not endpoint.endswith('/health'):
                    health_url = endpoint.rstrip('/') + '/health'
                else:
                    health_url = endpoint
            
            response = requests.get(health_url, timeout=3)
            response_time = (time.time() - start_time) * 1000
            
            health_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "endpoint": health_url,
                "last_checked": datetime.now()
            }
            
        except requests.RequestException as e:
            health_status[service_name] = {
                "status": "unreachable",
                "status_code": None,
                "response_time_ms": None,
                "endpoint": endpoint,
                "error": str(e),
                "last_checked": datetime.now()
            }
    
    return health_status

def render_system_health():
    """Render system health monitoring dashboard"""
    if not UIConfig.ENABLE_SYSTEM_MONITORING:
        return
    
    st.subheader("🏥 System Health")
    
    # Auto-refresh toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Service status across the insurance AI architecture")
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Check service health
    health_status = check_service_health()
    
    # Count healthy/unhealthy services
    healthy_count = sum(1 for status in health_status.values() if status["status"] == "healthy")
    total_count = len(health_status)
    
    # Overall health indicator
    if healthy_count == total_count:
        st.success(f"✅ All {total_count} services are healthy")
    elif healthy_count > total_count / 2:
        st.warning(f"⚠️ {healthy_count}/{total_count} services are healthy")
    else:
        st.error(f"❌ Only {healthy_count}/{total_count} services are healthy")
    
    # Service details
    for service_name, status in health_status.items():
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                if status["status"] == "healthy":
                    st.success(f"✅ {service_name}")
                elif status["status"] == "unhealthy":
                    st.error(f"❌ {service_name}")
                else:
                    st.error(f"🔌 {service_name} (unreachable)")
            
            with col2:
                if status["status_code"]:
                    st.write(f"HTTP {status['status_code']}")
                else:
                    st.write("No response")
            
            with col3:
                if status["response_time_ms"]:
                    st.write(f"{status['response_time_ms']}ms")
                else:
                    st.write("-")
            
            with col4:
                time_ago = datetime.now() - status["last_checked"]
                st.write(f"{time_ago.seconds}s ago")

def render_api_monitoring():
    """Render API call monitoring"""
    if not UIConfig.ENABLE_API_MONITORING:
        return
        
    st.subheader("📊 API Call Monitoring")
    
    if not st.session_state.get('api_calls'):
        st.info("No API calls logged yet. Start a conversation to see API activity.")
        return
    
    # API calls summary
    api_calls = st.session_state.api_calls
    total_calls = len(api_calls)
    successful_calls = sum(1 for call in api_calls if call["success"])
    avg_response_time = sum(call["response_time_ms"] for call in api_calls) / total_calls if total_calls > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total API Calls", total_calls)
    with col2:
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col3:
        st.metric("Avg Response Time", f"{avg_response_time:.1f}ms")
    
    # Recent API calls table
    st.write("**Recent API Calls**")
    
    # Show last 10 API calls
    recent_calls = api_calls[-10:] if len(api_calls) > 10 else api_calls
    
    for call in reversed(recent_calls):  # Show newest first
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            
            with col1:
                timestamp_str = call["timestamp"].strftime("%H:%M:%S") if isinstance(call["timestamp"], datetime) else str(call["timestamp"])
                st.write(f"**{call['service']}**")
                st.caption(timestamp_str)
            
            with col2:
                st.write(f"{call['method']} {call['endpoint']}")
                st.caption(f"ID: {call['call_id']}")
            
            with col3:
                if call["success"]:
                    st.success(f"✅ {call['status_code']}")
                else:
                    st.error(f"❌ {call['status_code']}")
            
            with col4:
                st.write(f"{call['response_time_ms']}ms")
            
            with col5:
                if st.button("📋", key=f"details_{call['call_id']}", help="View details"):
                    st.session_state[f"show_details_{call['call_id']}"] = True
        
        # Show call details if requested
        if st.session_state.get(f"show_details_{call['call_id']}", False):
            with st.expander(f"API Call Details - {call['call_id']}", expanded=True):
                st.json({
                    "request_data": call.get("request_data", {}),
                    "response_data": call.get("response_data", {}),
                    "full_endpoint": call.get("endpoint", ""),
                    "timestamp": call["timestamp"].isoformat() if isinstance(call["timestamp"], datetime) else str(call["timestamp"])
                })
                if st.button("Close Details", key=f"close_{call['call_id']}"):
                    st.session_state[f"show_details_{call['call_id']}"] = False
                    st.rerun()

def render_performance_metrics():
    """Render performance metrics"""
    if not UIConfig.ENABLE_SYSTEM_MONITORING:
        return
        
    st.subheader("⚡ Performance Metrics")
    
    # Conversation metrics
    conversation_count = len(st.session_state.get('conversation_history', []))
    thinking_steps_count = len(st.session_state.get('thinking_steps', []))
    orchestration_events_count = len(st.session_state.get('orchestration_data', []))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Conversations", conversation_count)
    with col2:
        st.metric("Thinking Steps", thinking_steps_count)
    with col3:
        st.metric("Orchestration Events", orchestration_events_count)
    
    # Feature status
    st.write("**Active Features**")
    features = UIConfig.get_enabled_features()
    
    feature_cols = st.columns(3)
    feature_items = list(features.items())
    
    for i, (feature, enabled) in enumerate(feature_items):
        with feature_cols[i % 3]:
            status_icon = "✅" if enabled else "❌"
            feature_name = feature.replace("_", " ").title()
            st.write(f"{status_icon} {feature_name}")

def get_system_status_summary() -> Dict[str, Any]:
    """Get system status summary for other components"""
    if not UIConfig.ENABLE_SYSTEM_MONITORING:
        return {"monitoring_disabled": True}
    
    health_status = check_service_health()
    healthy_count = sum(1 for status in health_status.values() if status["status"] == "healthy")
    total_count = len(health_status)
    
    api_calls = st.session_state.get('api_calls', [])
    recent_api_calls = [call for call in api_calls if isinstance(call.get("timestamp"), datetime) and 
                       call["timestamp"] > datetime.now() - timedelta(minutes=5)]
    
    return {
        "services_healthy": healthy_count,
        "services_total": total_count,
        "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0,
        "recent_api_calls": len(recent_api_calls),
        "total_api_calls": len(api_calls),
        "last_health_check": datetime.now()
    } 