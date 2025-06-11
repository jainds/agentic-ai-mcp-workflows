# Insurance AI POC - Google ADK v1.2.1

**Production-ready insurance AI agent system built with Google's official Agent Development Kit**

[![Google ADK](https://img.shields.io/badge/Google%20ADK-v1.2.1-blue)](https://google.github.io/adk-docs/)
[![A2A Protocol](https://img.shields.io/badge/A2A%20Protocol-python--a2a%20v0.5.6-green)](https://github.com/google/adk-python)
[![Monitoring](https://img.shields.io/badge/Monitoring-Langfuse%20%2B%20Prometheus-purple)](https://langfuse.com/)

## 🚀 Overview

This is a **complete production implementation** of an insurance AI agent system using **Google's official Agent Development Kit (ADK) v1.2.1**. The system follows patterns from [google/adk-samples](https://github.com/google/adk-samples) and eliminates the need for custom FastAPI servers.

### ✨ Key Features

- 🤖 **Multiple Agent Types**: Customer service (LlmAgent) + Technical operations (BaseAgent)
- 🛠️ **Native Google ADK**: Uses built-in `adk web`, `adk run`, and `adk api_server` commands
- 🎛️ **No Custom FastAPI**: Leverages Google ADK's built-in runtime and web UI
- 📊 **Built-in Evaluation**: Google ADK evaluation framework included
- 🚀 **Production Ready**: Deployment tools and monitoring integrated
- 📝 **Automatic Logging**: Built-in tracing and observability

## 🏗️ Architecture

```
insurance-adk/
├── insurance_customer_service/    # LlmAgent for customer interactions
│   ├── __init__.py
│   └── agent.py                  # root_agent = LlmAgent(...)
├── insurance_technical_agent/     # BaseAgent for backend operations  
│   ├── __init__.py
│   └── agent.py                  # root_agent = BaseAgent(...)
├── agent.py                      # Simple agent example
└── .env                          # Google API configuration
```

## 🛠️ Google ADK Commands

### Available Commands

```bash
# Interactive CLI mode
adk run insurance_customer_service
adk run insurance_technical_agent

# Web UI for testing (recommended)
adk web

# REST API server  
adk api_server

# Evaluation framework
adk eval <agent> <eval_set>

# Create new agents
adk create <app_name>
```

## 🚦 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set up Google API key
export GOOGLE_API_KEY=your_google_ai_studio_api_key
# OR configure Vertex AI in .env file
```

### Run Agents

```bash
cd insurance-adk

# Option 1: Web UI (recommended)
adk web

# Option 2: CLI mode
adk run insurance_customer_service

# Option 3: API server
adk api_server
```

## 🎯 Agent Capabilities

### Insurance Customer Service Agent (LlmAgent)
- 💬 Customer support and inquiries
- 📋 Policy information assistance  
- 🤝 Claims guidance and support
- 📞 Professional customer interactions

### Insurance Technical Agent (BaseAgent)  
- ⚙️ Complex backend operations
- 📊 Policy analysis and validation
- 🔧 Technical system integrations
- 📈 Data processing workflows

## 📊 Benefits Over FastAPI

| **Google ADK** | **Custom FastAPI** |
|----------------|-------------------|
| ✅ Built-in web UI | ❌ Manual UI development |
| ✅ Automatic evaluation | ❌ Custom testing framework |
| ✅ Production deployment | ❌ Manual deployment setup |
| ✅ Integrated logging | ❌ Custom logging configuration |
| ✅ CLI tools included | ❌ Manual CLI development |
| ✅ Official Google support | ❌ Community maintenance |

## 🔧 Configuration

### Environment Variables (.env)

```env
# Google AI Configuration
GOOGLE_API_KEY=your_google_ai_studio_api_key

# OR Vertex AI (production)
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Model Configuration  
MODEL_NAME=gemini-2.0-flash
```

## 🧪 Testing

```bash
# Run Google ADK tests
python tests/google-adk-tests/test_google_adk_agents.py

# Demo commands
python tests/google-adk-tests/demo_adk_commands.py

# A2A communication tests  
python tests/google-adk-tests/test_a2a_communication.py
```

## 📈 Monitoring & Observability

- **Langfuse**: LLM observability and tracing
- **Google ADK Logs**: Built-in agent logging
- **Evaluation Framework**: Automated testing suite

## 🌟 Production Features

- 🔄 **Hot Reloading**: Automatic agent updates
- 📊 **Built-in Metrics**: Performance monitoring
- 🚀 **Easy Deployment**: `adk deploy` commands
- 🔒 **Security**: Google Cloud integration
- 📝 **Documentation**: Auto-generated API docs

## 🎉 Migration Complete

✅ **FastAPI Server Removed**: No longer needed - Google ADK provides all runtime capabilities  
✅ **Agent Structure**: Following [google/adk-samples](https://github.com/google/adk-samples) patterns  
✅ **Built-in Tools**: Using native `adk` commands instead of custom scripts  
✅ **Clean Architecture**: Simplified and production-ready  

---

**Ready to use Google ADK v1.2.1!** 🚀

Start with: `cd insurance-adk && adk web` 