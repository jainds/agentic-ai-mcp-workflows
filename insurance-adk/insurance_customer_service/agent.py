"""
Insurance Customer Service Agent - Google ADK v1.2.1

This agent follows the structure of google/adk-samples/python/agents/customer-service
to provide proper Google ADK implementation for insurance customer service.
"""

import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Get configuration from environment
openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
model_name = os.getenv("PRIMARY_MODEL", "openai/gpt-4o-mini")

# Initialize monitoring if available
try:
    from monitoring.setup.monitoring_setup import MonitoringManager
    monitoring = MonitoringManager()
    monitoring_enabled = monitoring.is_monitoring_enabled()
    if monitoring_enabled:
        print("✅ Customer Service Agent: Monitoring enabled")
    else:
        print("ℹ️  Customer Service Agent: Monitoring disabled")
except ImportError:
    monitoring = None
    monitoring_enabled = False
    print("ℹ️  Customer Service Agent: Monitoring not available")

# Create the insurance customer service agent using direct OpenRouter integration
root_agent = LlmAgent(
    name="insurance_customer_service", 
    model=LiteLlm(
        model=model_name,
        api_base="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key
    ),
    instruction=(
        "You are a helpful insurance customer service agent powered by OpenRouter. "
        "Assist customers with policy inquiries, claim status checks, "
        "coverage questions, and general insurance support. "
        "Always be professional, helpful, and empathetic in your responses. "
        "If you need to access policy data or perform complex operations, "
        "let the customer know you'll look that up for them."
    ),
    description="An insurance customer service agent that helps with policy and claim inquiries using OpenRouter models",
    # Add tools here when needed - for now keeping it simple
    # tools=[policy_search_tool, claim_lookup_tool]
) 