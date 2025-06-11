"""
Insurance Orchestrator Agent - Google ADK v1.2.1 with LiteLLM Integration

This agent orchestrates communication between customer service and technical agents.
It follows Google ADK multi-agent patterns with LiteLLM + OpenRouter integration.
"""

import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
import litellm

# Get configuration from environment
openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "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")
model_name = os.getenv("PRIMARY_MODEL", "anthropic/claude-3-5-sonnet")  # Use more powerful model for orchestration

# Set LiteLLM OpenRouter environment variables per official documentation
# litellm.use_litellm_proxy = True
litellm.set_verbose = True
litellm.set_debug = True


# Convert model name to OpenRouter format per documentation
# openrouter_model = f"openrouter/{model_name}"

print(f"🔧 Orchestrator Agent: Using model {model_name} with OpenRouter")
print(f"🔑 Orchestrator Agent: API key configured: {bool(openrouter_api_key)}")

# Initialize monitoring if available
try:
    from monitoring.setup.monitoring_setup import MonitoringManager
    monitoring = MonitoringManager()
    monitoring_enabled = monitoring.is_monitoring_enabled()
    if monitoring_enabled:
        print("✅ Orchestrator Agent: Monitoring enabled")
    else:
        print("ℹ️  Orchestrator Agent: Monitoring disabled")
except ImportError:
    monitoring = None
    monitoring_enabled = False
    print("ℹ️  Orchestrator Agent: Monitoring not available")

# Create LiteLLM model for orchestration
orchestrator_model = LiteLlm(
    model="openrouter/"+model_name,  # "openrouter/anthropic/claude-3-5-sonnet"
    api_key=openrouter_api_key,
    api_base="https://openrouter.ai/api/v1"
   
)

# Create the insurance orchestrator agent
root_agent = LlmAgent(
    name="insurance_orchestrator",
    model=orchestrator_model,
    instruction=(
        "You are an insurance orchestrator agent powered by OpenRouter. "
        "Coordinate between customer service and technical agents to provide comprehensive insurance services. "
        "Route customer inquiries to appropriate agents, synthesize responses from multiple agents, "
        "manage complex workflows, and ensure seamless customer experience. "
        "For policy data access, route requests to technical agents. "
        "For customer communication, use customer service agents. "
        "Always provide coordinated, coherent responses that combine insights from all relevant agents."
    ),
    description="Orchestrator agent that coordinates multi-agent workflows for comprehensive insurance services using OpenRouter models",
    # Sub-agents will be configured at the application layer through API calls
    # tools=[agent_communication_tool, workflow_management_tool]
) 