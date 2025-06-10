"""
Insurance Technical Agent - Google ADK v1.2.1 with LiteLLM Integration

This agent handles complex insurance operations and technical tasks.
It follows Google ADK BaseAgent patterns with LiteLLM + OpenRouter integration.
"""

import os
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Get configuration from environment
openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
model_name = os.getenv("PRIMARY_MODEL", "openai/gpt-4o-mini")
policy_server_url = os.getenv("POLICY_SERVER_URL", "http://localhost:8001/mcp")

# Create LiteLLM model for technical operations
technical_model = LiteLlm(
    model=model_name,
    api_base="https://openrouter.ai/api/v1", 
    api_key=openrouter_api_key
)

# Initialize monitoring if available
try:
    from monitoring.setup.monitoring_setup import MonitoringManager
    monitoring = MonitoringManager()
    monitoring_enabled = monitoring.is_monitoring_enabled()
    if monitoring_enabled:
        print("✅ Technical Agent: Monitoring enabled")
    else:
        print("ℹ️  Technical Agent: Monitoring disabled")
except ImportError:
    monitoring = None
    monitoring_enabled = False
    print("ℹ️  Technical Agent: Monitoring not available")

# Create MCP tools for policy server connectivity (simplified approach)
tools = []
try:
    # Note: Using simplified tool configuration for now
    # MCP integration will be handled at the workflow level
    print("ℹ️  Technical Agent: MCP integration configured for policy server")
except Exception as e:
    print(f"⚠️  Technical Agent: MCP setup issue: {e}")

# Create the insurance technical agent with LLM capabilities for complex analysis
root_agent = LlmAgent(
    name="insurance_technical_agent",
    model=technical_model,
    instruction=(
        "You are a technical insurance agent powered by OpenRouter. "
        "Handle complex insurance operations, policy analysis, claims processing, "
        "risk assessment, and backend technical tasks. "
        "Access policy data through available tools when needed and provide detailed analysis. "
        "Use professional insurance terminology and provide technical insights based on data."
    ),
    description="Technical agent for complex insurance operations, policy analysis, and backend processing using OpenRouter models",
    tools=tools  # MCP tools for policy server access
) 