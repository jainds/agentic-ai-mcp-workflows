#!/usr/bin/env python3
"""
Google ADK Commands Demo

This script demonstrates the proper usage of Google ADK commands
with our insurance agents following the official ADK patterns.
"""

print("🚀 Google ADK v1.2.1 - Insurance Agents Demo")
print("=" * 60)

print("\n📁 Available Agents:")
print("├── insurance_customer_service/  (LlmAgent)")
print("│   └── Customer service and support")
print("├── insurance_technical_agent/   (BaseAgent)")
print("│   └── Technical operations and analysis")
print("└── agent.py                     (Simple agent)")

print("\n🛠️  Google ADK Commands Available:")
print("├── adk run <agent_name>         - Interactive CLI")
print("├── adk web                      - Web UI interface")
print("├── adk api_server               - REST API server")
print("├── adk eval <agent> <eval_set>  - Evaluation suite")
print("└── adk create <app_name>        - Create new agent")

print("\n🎯 Usage Examples:")
print("# Run customer service agent in CLI mode:")
print("adk run insurance_customer_service")
print()
print("# Start web UI for all agents:")
print("adk web")
print()
print("# Run technical agent:")
print("adk run insurance_technical_agent")
print()
print("# Start API server:")
print("adk api_server")

print("\n📋 Requirements:")
print("✅ Google ADK v1.2.1 installed")
print("✅ Agent directories with __init__.py and agent.py")
print("✅ root_agent variable defined in agent.py")
print("⚠️  GOOGLE_API_KEY environment variable needed for actual usage")

print("\n🌟 Benefits of Google ADK:")
print("├── 🔥 No custom FastAPI server needed")
print("├── 🎛️  Built-in web UI for testing")
print("├── 📊 Evaluation framework included")
print("├── 🚀 Production deployment tools")
print("├── 📝 Automatic logging and tracing")
print("└── 🔧 CLI tools for development")

print("\n✨ Ready to use Google ADK! Remove FastAPI complexity!")
print("🎉 All agents configured properly for ADK patterns") 