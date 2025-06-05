# Insurance AI with Google ADK v1.0.0

**Pure Google Agent Development Kit (ADK) implementation of the insurance AI agent system** 

[![Google ADK](https://img.shields.io/badge/Google%20ADK-v1.0.0-blue)](https://google.github.io/adk-docs/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-1.55+-purple)](https://litellm.ai/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Compatible-orange)](https://openrouter.ai/)

## 🚀 Overview

This is a **complete migration** of the insurance AI agent system to use **Google's official Agent Development Kit (ADK) v1.0.0**. The system provides intelligent insurance customer service through multiple specialized agents coordinated by ADK workflows.

### Key Features

- **🤖 Pure Google ADK**: Official ADK v1.0.0 with sequential and parallel workflows
- **🔄 Multi-Agent Orchestration**: Domain agent + Technical agent coordination
- **🌐 OpenRouter Integration**: LiteLLM integration for all model providers
- **📡 MCP Integration**: Preserved policy server connectivity
- **🔒 Session Management**: Preserved authentication and session handling
- **📊 Monitoring**: Langfuse and Prometheus integration maintained
- **🔌 API Compatibility**: FastAPI server with legacy A2A endpoint support

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server (8000)                    │
│                   ┌─────────────────┐                      │
│                   │ ADK Orchestrator │                      │
│                   └─────────────────┘                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐              ┌──────────────────────┐   │
│  │  Domain Agent   │◄────────────►│  Technical Agent     │   │
│  │  (Customer      │              │  (A2A + MCP          │   │
│  │   Service)      │              │   Integration)       │   │
│  └─────────────────┘              └──────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│             Google ADK v1.0.0 Framework                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │
│  │ Sequential      │  │ Function        │  │ LiteLLM      │  │
│  │ Workflows       │  │ Tools           │  │ Models       │  │
│  └─────────────────┘  └─────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Policy Server   │
                    │ (MCP on 8001)   │
                    └─────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.9+
- Google ADK v1.0.0 (`pip install google-adk`)
- OpenRouter API key
- Policy server running on port 8001

### Quick Start

1. **Install the official Google ADK**:
```bash
pip install google-adk>=1.0.0
```

2. **Install dependencies**:
```bash
cd insurance-adk
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
cp config.env.example .env
# Edit .env with your API keys
```

4. **Start the system**:
```bash
# Start policy server (terminal 1)
cd ../policy_server && python main.py

# Start ADK system (terminal 2)  
cd insurance-adk
python server/main.py
```

## 🔧 Configuration

### Environment Variables

```bash
# OpenRouter Integration
OPENROUTER_API_KEY=your_openrouter_key

# Langfuse Monitoring
LANGFUSE_SECRET_KEY=your_langfuse_secret
LANGFUSE_PUBLIC_KEY=your_langfuse_public
LANGFUSE_HOST=https://cloud.langfuse.com

# MCP Server
MCP_SERVER_URL=http://localhost:8001/mcp

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG_MODE=true
```

### Model Configuration

Edit `config/models.yaml`:

```yaml
models:
  domain_agent:
    primary: "openrouter/anthropic/claude-3.5-sonnet"
    fallback: "openrouter/openai/gpt-4o-mini" 
    max_tokens: 4096
    temperature: 0.3
  
  technical_agent:
    primary: "openrouter/meta-llama/llama-3.1-70b-instruct"
    fallback: "openrouter/openai/gpt-4o-mini"
    max_tokens: 4096
    temperature: 0.1
```

## 🤖 Agents

### Domain Agent
- **Purpose**: Customer service and conversation management
- **Framework**: Google ADK Agent with FunctionTools
- **Capabilities**: Intent analysis, response formatting, authentication
- **Model**: Claude 3.5 Sonnet via OpenRouter

### Technical Agent  
- **Purpose**: A2A operations and MCP data retrieval
- **Framework**: Google ADK Agent with MCP integration
- **Capabilities**: Request parsing, policy data retrieval, response formatting
- **Model**: Llama 3.1 70B via OpenRouter

### Orchestrator
- **Purpose**: Coordinate multi-agent workflows
- **Framework**: Google ADK SequentialWorkflow
- **Workflows**: Customer inquiry processing, technical data processing

## 🔄 Workflows

### Customer Inquiry Workflow

```yaml
1. Intent Analysis (Domain Agent)
   ├─ Analyze customer message
   ├─ Determine authentication needs
   └─ Identify required data
   
2. Authentication Check (Domain Agent)
   ├─ Verify customer identity  
   └─ Update session status
   
3. Data Retrieval (Technical Agent)
   ├─ Parse requirements
   ├─ Execute MCP calls
   └─ Format policy data
   
4. Response Synthesis (Domain Agent)
   ├─ Generate customer response
   └─ Update conversation history
```

## 🌐 API Endpoints

### Customer Service
```bash
# Customer inquiry
POST /customer/inquiry
{
  "message": "What are my policy details?",
  "session_id": "optional-session-id",
  "customer_id": "CUST123"
}

# Session management
POST /sessions
{
  "customer_id": "CUST123"
}
```

### Technical Operations
```bash
# Policy data retrieval
POST /technical/data
{
  "customer_id": "CUST123", 
  "operation": "get_customer_policies",
  "parameters": {}
}

# Legacy A2A compatibility
POST /a2a/handle_task
{
  "customer_id": "CUST123",
  "operation": "get_customer_policies"
}
```

### System Management
```bash
# Health check
GET /health

# Available workflows
GET /workflows

# Agent status
GET /agents/status
```

## 🧪 Testing

### Run Migration Validation
```bash
cd insurance-adk
python tests/test_adk_migration.py
```

### Run Complete Test Suite
```bash
cd insurance-adk
pytest tests/ -v
```

### Manual Testing
```bash
# Test customer inquiry
curl -X POST "http://localhost:8000/customer/inquiry" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my policies?", "customer_id": "CUST123"}'

# Test technical data
curl -X POST "http://localhost:8000/technical/data" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST123", "operation": "get_customer_policies"}'
```

## 🚀 Deployment

### Development
```bash
# Start with hot reload
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
# Install in production environment
pip install google-adk litellm fastapi uvicorn[standard]

# Run with production settings
uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Monitoring

### Langfuse Integration
- **Tracing**: All agent interactions traced
- **Metrics**: Token usage, latency, costs
- **Dashboard**: Real-time monitoring

### Prometheus Metrics
- **Endpoint**: `/metrics`
- **Metrics**: Request counts, response times, error rates

### Health Checks
- **System**: `/health`
- **Components**: ADK agents, MCP server, workflows

## 🔄 Migration Notes

### From Previous System
- ✅ **Complete ADK migration**: No hybrid components
- ✅ **Preserved functionality**: All existing features maintained  
- ✅ **API compatibility**: Legacy endpoints supported
- ✅ **MCP integration**: Policy server connectivity preserved
- ✅ **Monitoring**: Langfuse and Prometheus maintained

### Breaking Changes
- **Dependencies**: Now requires `google-adk>=1.0.0`
- **Internal architecture**: Agents now use ADK framework
- **Workflows**: Migrated to ADK SequentialWorkflow

### Migration Benefits
- **Official framework**: Using Google's production-ready ADK
- **Better orchestration**: Native workflow management
- **Improved scalability**: ADK's built-in scaling capabilities
- **Future-proof**: Direct Google support and updates

## 🆘 Troubleshooting

### Common Issues

**Import errors for ADK**:
```bash
# Install official Google ADK
pip install google-adk>=1.0.0
```

**MCP connection failures**:
```bash
# Ensure policy server is running
cd policy_server && python main.py
```

**OpenRouter authentication**:
```bash
# Set API key in environment
export OPENROUTER_API_KEY=your_key
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG_MODE=true
export LOG_LEVEL=DEBUG
```

## 📚 Documentation

- **Google ADK**: https://google.github.io/adk-docs/
- **LiteLLM**: https://litellm.ai/
- **OpenRouter**: https://openrouter.ai/docs
- **FastAPI**: https://fastapi.tiangolo.com/

## 🤝 Contributing

1. Follow Google ADK best practices
2. Maintain test coverage >90%
3. Update documentation for changes
4. Preserve MCP integration compatibility

## 📄 License

MIT License - see LICENSE file for details

---

**🎉 Successfully migrated to Google ADK v1.0.0!**

*This system now uses the official Google Agent Development Kit for production-ready AI agent orchestration.* 