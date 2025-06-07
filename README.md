# Insurance AI POC - Google ADK v1.0.0

**Production-ready insurance AI agent system built with Google's official Agent Development Kit**

[![Google ADK](https://img.shields.io/badge/Google%20ADK-v1.0.0-blue)](https://google.github.io/adk-docs/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-1.55+-purple)](https://litellm.ai/)
[![Monitoring](https://img.shields.io/badge/Monitoring-Langfuse%20%2B%20Prometheus-purple)](https://langfuse.com/)

## 🚀 Overview

This is a **complete production implementation** of an insurance AI agent system using **Google's official Agent Development Kit (ADK) v1.0.0**. The system provides intelligent insurance customer service through coordinated multi-agent workflows with enterprise-grade monitoring and deployment.

### ✨ Key Features

- **🤖 Google ADK v1.0.0**: Official framework with sequential workflows and orchestration
- **🔄 Multi-Agent System**: Specialized domain and technical agents
- **🌐 OpenRouter Integration**: LiteLLM abstraction for all major model providers
- **📡 MCP Integration**: Policy server connectivity for real-time data
- **🔒 Enterprise Security**: Session management and authentication
- **📊 Production Monitoring**: Langfuse observability + Prometheus metrics
- **🚀 Cloud Deployment**: Kubernetes manifests with GitHub Actions CI/CD
- **🔌 API Compatibility**: FastAPI with legacy A2A endpoint support

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       FastAPI Server (8000)                      │
│                     ┌─────────────────────┐                      │
│                     │   ADK Orchestrator  │                      │
│                     │  (Sequential Flows) │                      │
│                     └─────────────────────┘                      │
├──────────────────────────────────────────────────────────────────┤
│   ┌─────────────────┐              ┌──────────────────────────┐   │
│   │  Domain Agent   │◄────────────►│    Technical Agent       │   │
│   │ (Claude 3.5     │              │   (Llama 3.1 70B +      │   │
│   │  Sonnet)        │              │    MCP Integration)      │   │
│   └─────────────────┘              └──────────────────────────┘   │
├──────────────────────────────────────────────────────────────────┤
│                    Google ADK v1.0.0 Framework                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐  │
│  │ Sequential      │ │ Function        │ │ LiteLLM Model       │  │
│  │ Workflows       │ │ Tools           │ │ Management          │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                      ┌─────────────────────┐
                      │   Policy Server     │
                      │   (MCP on 8001)     │
                      └─────────────────────┘
```

## 📁 Repository Structure

```
insurance-ai-poc/
├── insurance-adk/          # Main Google ADK implementation
│   ├── agents/            # ADK agents (domain, technical)
│   ├── server/            # FastAPI server with ADK integration
│   ├── config/            # Model and workflow configurations
│   ├── tools/             # ADK-compatible tools
│   ├── workflows/         # ADK workflow definitions
│   └── tests/             # Comprehensive test suite
├── policy_server/         # MCP server for policy data
├── monitoring/            # Langfuse + Prometheus integration
├── k8s/                   # Kubernetes deployment manifests
├── .github/              # GitHub Actions CI/CD workflows
└── tests/                # System integration tests
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone and setup
git clone <repository-url>
cd insurance-ai-poc

# Install Google ADK and dependencies
cd insurance-adk
pip install google-adk>=1.0.0
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Configure environment
cp insurance-adk/config.env.example .env
# Edit .env with your API keys:
# - OPENROUTER_API_KEY
# - LANGFUSE_SECRET_KEY
# - LANGFUSE_PUBLIC_KEY
```

### 3. Run the System

```bash
# Terminal 1: Start policy server
cd policy_server && python main.py

# Terminal 2: Start ADK system
cd insurance-adk && python server/main.py
```

### 4. Test the API

```bash
# Test customer inquiry
curl -X POST "http://localhost:8000/customer/inquiry" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are my policy details?",
    "customer_id": "CUST123"
  }'
```

## 🌐 API Reference

### Customer Service Endpoints

- `POST /customer/inquiry` - Process customer inquiries
- `POST /sessions` - Create/manage customer sessions
- `GET /sessions/{session_id}` - Get session details

### Technical Endpoints

- `POST /technical/data` - Policy data retrieval
- `GET /workflows` - Available workflow information
- `GET /health` - System health check

### Legacy Compatibility

- `POST /a2a/handle_task` - A2A compatibility endpoint

## 🔧 Configuration

### Model Configuration (`config/models.yaml`)

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

### Workflow Configuration (`config/workflows.yaml`)

```yaml
workflows:
  customer_inquiry:
    steps:
      - intent_analysis
      - authentication_check
      - data_retrieval
      - response_synthesis
    
  technical_processing:
    steps:
      - request_parsing
      - mcp_operations
      - response_formatting
```

## 🚀 Deployment

### Local Development

```bash
# Use port forwarding script
./start_port_forwards.sh
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
cd k8s
kubectl apply -f manifests/
```

### Production Deployment

```bash
# Use deployment script
./deploy.sh production
```

## 📊 Monitoring

- **Langfuse**: LLM observability and tracing at `https://cloud.langfuse.com`
- **Prometheus**: Metrics collection
- **Health Endpoints**: System status monitoring

### Monitoring URLs

- Langfuse Dashboard: Configure in `.env`
- Prometheus: `http://localhost:8080` (when port-forwarded)
- Health Check: `http://localhost:8000/health`

## 🧪 Testing

```bash
# Run ADK migration validation tests
cd insurance-adk
python -m pytest tests/test_adk_migration.py -v

# Run comprehensive system tests
cd tests
python -m pytest README.md -v
```

## 🔒 Security

- Session-based authentication
- API key management via environment variables
- Secure MCP server communication
- Input validation and sanitization

## 📚 Documentation

- **Google ADK**: [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)
- **API Documentation**: Available at `http://localhost:8000/docs` when running
- **Architecture Guide**: See `insurance-adk/README.md`
- **Migration Summary**: See `insurance-adk/GOOGLE_ADK_MIGRATION_SUMMARY.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following ADK patterns
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the [Google ADK documentation](https://google.github.io/adk-docs/)
- Review the comprehensive README in `insurance-adk/`
- Test the system using the validation suite
- Check monitoring dashboards for operational issues

---

**Ready for production deployment with Google ADK v1.0.0** 🚀 