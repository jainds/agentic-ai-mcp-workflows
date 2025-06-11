"""
Insurance Technical Agent - Google ADK v1.2.1 with Native MCP Integration

This agent uses ADK's built-in MCPToolset for automatic MCP tool discovery
and registration, eliminating the need for manual tool wrappers.
"""

import os
import logging
from typing import Dict, Any, List
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("✅ Technical Agent: Monitoring enabled")
    else:
        logger.info("ℹ️  Technical Agent: Monitoring disabled")
except ImportError:
    monitoring = None
    monitoring_enabled = False
    logger.info("ℹ️  Technical Agent: Monitoring not available")

# Use ADK's native MCP integration for automatic tool discovery
def create_mcp_tools():
    """Create MCP toolset using ADK's native capabilities."""
    try:
        # ADK automatically discovers and registers all MCP tools
        mcp_toolset = MCPToolset(
            connection_params=StdioServerParameters(
                command='python',
                args=['../policy_server/main.py']  # Path to policy server
            ),
            # Optional: Filter specific tools if needed
            tool_filter=['policy_lookup', 'claims_data', 'coverage_analysis']
        )
        
        logger.info("✅ Technical Agent: ADK MCPToolset created - tools will be auto-discovered")
        return [mcp_toolset]
        
    except Exception as e:
        logger.error(f"⚠️  Technical Agent: MCP toolset creation failed: {e}")
        return []

# Load session management tool (local, not MCP)
def load_session_tool():
    """Load local session management tool."""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
        
        from session_tools import SessionManagementTool
        return SessionManagementTool()
        
    except ImportError as e:
        logger.warning(f"Could not load session tool: {e}")
        return None

# Create tools list combining MCP and local tools
tools = create_mcp_tools()
session_tool = load_session_tool()
if session_tool:
    tools.append(session_tool)

logger.info(f"✅ Technical Agent: Initialized with {len(tools)} tool(s)")

# Load prompt configuration
def load_prompts():
    """Load prompts from YAML configuration."""
    try:
        import yaml
        prompt_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'prompts', 'technical_agent.yaml')
        
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r') as f:
                prompts = yaml.safe_load(f)
            return prompts.get('system_prompt', get_default_prompt())
        else:
            logger.warning(f"Prompt file not found: {prompt_file}")
            return get_default_prompt()
    except Exception as e:
        logger.warning(f"Could not load prompts: {e}")
        return get_default_prompt()

def get_default_prompt():
    """Default technical agent prompt."""
    return (
        "You are a technical insurance agent powered by OpenRouter with MCP policy server access. "
        "Handle complex insurance operations, policy analysis, claims processing, "
        "risk assessment, and backend technical tasks. "
        "Access policy data through available MCP tools when needed and provide detailed analysis. "
        "Use professional insurance terminology and provide technical insights based on real data. "
        
        "YOUR MCP CAPABILITIES:\n"
        "- policy_lookup: Search and retrieve policy information by customer ID or policy number\n"
        "- claims_data: Access claims history and status information\n"
        "- coverage_analysis: Analyze coverage details and limits\n"
        "- risk_assessment: Evaluate risk factors and premium calculations\n"
        "- session_management: Manage customer session data and context\n"
        
        "TECHNICAL PROCESSING GUIDELINES:\n"
        "1. Always verify customer identity before accessing sensitive data\n"
        "2. Use MCP tools to retrieve real-time policy information\n"
        "3. Provide specific details with policy numbers, dates, and amounts\n"
        "4. Explain technical insurance terms in context\n"
        "5. Escalate complex issues to human agents when appropriate\n"
        
        "When using MCP tools, always:\n"
        "- Log the operation for audit trails\n"
        "- Handle errors gracefully with fallback responses\n"
        "- Validate data before presenting to customers\n"
        "- Maintain data privacy and security standards"
    )

# Create the insurance technical agent with enhanced MCP capabilities
root_agent = LlmAgent(
    name="insurance_technical_agent",
    model=technical_model,
    instruction=load_prompts(),
    description=(
        "Technical agent for complex insurance operations, policy analysis, and backend processing "
        "using OpenRouter models with MCP policy server integration"
    ),
    tools=tools  # MCP tools for policy server access
)

# Add MCP connection validation
def validate_mcp_connection():
    """Validate MCP connection to policy server."""
    try:
        # Test basic connectivity
        import requests
        response = requests.get(f"{policy_server_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Technical Agent: Policy server health check passed")
            return True
        else:
            logger.warning(f"⚠️  Technical Agent: Policy server health check failed with status {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"⚠️  Technical Agent: Policy server connectivity issue: {e}")
        return False

# Validate connection on startup
mcp_connected = validate_mcp_connection()
if mcp_connected:
    logger.info("🔗 Technical Agent: MCP integration ready")
else:
    logger.warning("⚠️  Technical Agent: Operating without MCP connectivity")

# Export agent configuration
__all__ = ['root_agent', 'validate_mcp_connection', 'mcp_connected'] 