#!/usr/bin/env python3
"""
Insurance AI UI Components Package
"""

from .config import UIConfig
from .auth import CustomerValidator, render_authentication, ensure_authentication
from .agent_client import DomainAgentClient, send_chat_message_simple
from .chat import initialize_chat_state, render_chat_interface, render_quick_actions, get_conversation_summary
from .monitoring import render_system_health, render_api_monitoring, render_performance_metrics, get_system_status_summary
from .thinking import render_thinking_steps, render_orchestration_view, render_architecture_flow, add_thinking_step, add_orchestration_event, get_thinking_summary

__all__ = [
    # Config
    'UIConfig',
    
    # Authentication
    'CustomerValidator',
    'render_authentication', 
    'ensure_authentication',
    
    # Agent Communication
    'DomainAgentClient',
    'send_chat_message_simple',
    
    # Chat Interface
    'initialize_chat_state',
    'render_chat_interface',
    'render_quick_actions',
    'get_conversation_summary',
    
    # Monitoring
    'render_system_health',
    'render_api_monitoring', 
    'render_performance_metrics',
    'get_system_status_summary',
    
    # Thinking & Orchestration
    'render_thinking_steps',
    'render_orchestration_view',
    'render_architecture_flow', 
    'add_thinking_step',
    'add_orchestration_event',
    'get_thinking_summary'
] 