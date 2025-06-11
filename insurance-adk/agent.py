"""
Insurance Agent following Google ADK Samples Pattern with LiteLLM Integration

This agent follows the structure of google/adk-samples/python/agents/customer-service
and uses LiteLLM wrapper for OpenRouter model integration as per:
https://google.github.io/adk-docs/agents/models/#using-openai-provider
"""

import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from agents import technical_agent, domain_agent, orchestrator_agent

# Get configuration from environment
litellm_base_url = os.getenv("OPENROUTER_BASE_URL", "http://localhost:8090/v1")
litellm_api_key = os.getenv("OPENROUTER_API_KEY", "sk-litellm-insurance-adk")
model_name = os.getenv("PRIMARY_MODEL", "gpt-4o-mini")

# Create LiteLLM model instance for OpenRouter via LiteLLM proxy
litellm_model = LiteLlm(
    model=model_name,  # This will be routed through LiteLLM to OpenRouter
    api_key=litellm_api_key,  # LiteLLM proxy master key
    api_base=litellm_base_url,  # LiteLLM proxy URL
)

# Create the insurance customer service agent using LiteLLM wrapper
root_agent = LlmAgent(
    name="insurance_customer_service",
    model=litellm_model,  # Use LiteLLM wrapper instance
    instruction=(
        "You are a helpful insurance customer service agent powered by OpenRouter via LiteLLM. "
        "Assist customers with policy inquiries, claim status checks, "
        "coverage questions, and general insurance support. "
        "Always be professional, helpful, and empathetic in your responses. "
        "You can access policy information through available tools when needed."
    ),
    description="An insurance customer service agent using OpenRouter models via LiteLLM integration",
    # Add tools here when needed (e.g., MCP tools for policy server)
    # tools=[policy_mcp_tool, search_tool]
    sub_agents=[domain_agent, orchestrator_agent]
) 