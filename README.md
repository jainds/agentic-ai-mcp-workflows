# AI-Driven Insurance Support & Claims PoC

A microservices-based, multi-agent architecture for insurance customer support and claims processing, running on local Kubernetes. This proof-of-concept demonstrates end-to-end workflows using domain agents for orchestration and technical agents for data access, with A2A protocol communication and MCP tool integration.

**🎯 Featured: Interactive UI Dashboard with Real-time Agent Monitoring and LLM Thinking Process Visualization**

## Architecture Overview

### Core Components

- **🎭 Interactive UI Dashboard**: Real-time Streamlit interface for PoC demonstration
  - Multi-agent chat interface with dropdown selection
  - Real-time LLM thinking process visualization  
  - Agent activity and API call monitoring
  - Communication flow diagrams and health status

- **Domain Agents (LLM-driven)**: Orchestrate workflows and user interaction
  - `SupportDomainAgent`: Handles customer inquiries, policy status, general support
  - `ClaimsDomainAgent`: Manages claim workflows (initiation, status, follow-ups)

- **Technical Agents (API integration)**: Provide data access and operations
  - `CustomerDataAgent`: Customer record management
  - `PolicyDataAgent`: Policy information access
  - `ClaimsDataAgent`: Claims creation and status management

- **Mock Backend Services (FastAPI)**: Simulate insurance data systems
  - Customer Service: Customer data and profiles
  - Policy Service: Policy information and status
  - Claims Service: Claims processing and tracking

### Technology Stack

- **Agent Framework**: python-a2a (Agent-to-Agent protocol)
- **Tool Integration**: FastMCP (Model Context Protocol)
- **LLM Access**: OpenRouter API with fallback models
- **UI Dashboard**: Streamlit with real-time monitoring
- **Backend Services**: FastAPI + Uvicorn
- **Orchestration**: Kubernetes (Kind/Minikube)
- **Communication**: HTTPX for service calls, A2A for agent communication

## Project Structure

```
insurance-ai-poc/
├── ui/
│   ├── streamlit_app.py          # Interactive dashboard
│   ├── Dockerfile                # UI container image
│   └── requirements.txt          # UI dependencies
├── agents/
│   ├── domain/
│   │   ├── support_agent.py      # SupportDomainAgent
│   │   └── claims_agent.py       # ClaimsDomainAgent
│   └── technical/
│       ├── customer_agent.py     # CustomerDataAgent
│       ├── policy_agent.py       # PolicyDataAgent
│       └── claims_agent.py       # ClaimsDataAgent
├── services/
│   ├── customer/
│   │   ├── app.py                # Customer FastAPI service
│   │   └── models.py             # Customer data models
│   ├── policy/
│   │   ├── app.py                # Policy FastAPI service
│   │   └── models.py             # Policy data models
│   └── claims/
│       ├── app.py                # Claims FastAPI service
│       └── models.py             # Claims data models
├── k8s/
│   ├── manifests/                # Kubernetes deployment files
│   └── configs/                  # ConfigMaps and Secrets
├── tests/
│   ├── unit/                     # Unit tests for individual components
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end scenario tests
└── docs/                         # Architecture and API documentation
```

## Quick Start

### Prerequisites

- Python 3.9+
- Docker
- kubectl
- Kind or Minikube
- OpenRouter API key ([get one here](https://openrouter.ai/keys))

### 1. Environment Setup

**🔐 Secure Setup (Recommended)**
```bash
# Clone and navigate to project
cd insurance-ai-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Interactive environment setup (will prompt for API key)
./scripts/setup_env.sh
```

**Manual Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your OpenRouter API key (never commit this file!)
nano .env
# Add: OPENROUTER_API_KEY=your_actual_key_here
```

**CI/CD Setup**
```bash
# For automated deployments, export environment variable
export OPENROUTER_API_KEY=your_key_here
```

### 2. Test LLM Integration

```bash
# Test your API key works
python scripts/test_llm_integration.py smoke

# Run comprehensive LLM tests
python scripts/test_llm_integration.py all
```

### 3. Local Kubernetes Cluster

```bash
# Start Kind cluster
kind create cluster --name insurance-poc

# Verify cluster
kubectl cluster-info
kubectl create namespace insurance-poc
```

### 4. Deploy Services

```bash
# Build and deploy all services (uses your .env file securely)
./scripts/deploy_k8s.sh

# Check deployment status
kubectl get pods -n insurance-poc
kubectl get services -n insurance-poc
```

### 5. Access the Interactive Dashboard

```bash
# Open the main dashboard (primary interface)
open http://localhost:30501

# Or check if it's running
curl http://localhost:30501
```

**🎯 Dashboard Features:**
- **Multi-Agent Chat**: Switch between Support and Claims agents
- **Real-time LLM Thinking**: Watch how AI processes requests step-by-step
- **Agent Activity Monitor**: See all backend agent communications
- **API Call Visualization**: Monitor all HTTP requests and responses
- **Health Status**: Real-time agent availability indicators

## Usage Examples

### Through the Interactive Dashboard (Recommended)

1. **Open Dashboard**: Navigate to http://localhost:30501
2. **Select Agent**: Choose "Support Domain Agent" or "Claims Domain Agent"
3. **Enter Customer ID**: Optional, use `12345` for testing
4. **Try Quick Tests**: Use sidebar buttons for pre-built scenarios
5. **Watch Real-time Processing**: Monitor the "LLM Thinking" and "Agent Activity" tabs

### Direct API Access

**Policy Status Inquiry:**
```bash
# Direct API call to SupportDomainAgent
curl -X POST http://localhost:30005/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "HandleGeneralSupport",
    "parameters": {
      "user_message": "What is the status of my auto insurance policy?"
    }
  }'
```

**Claim Creation:**
```bash
# File a new claim
curl -X POST http://localhost:30008/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "HandleGeneralClaimsSupport",
    "parameters": {
      "user_message": "I want to file a claim for a car accident"
    }
  }'
```

## Dashboard Capabilities

### 💬 Interactive Chat Interface
- **Agent Selection**: Dropdown to choose between Support and Claims agents
- **Customer Context**: Optional customer ID for personalized responses
- **Pre-built Scenarios**: Quick test buttons for common use cases
- **Conversation History**: Last 5 interactions with full context and metadata

### 🧠 LLM Thinking Process Visualization
- **Real-time Processing**: Watch how the LLM analyzes and responds to requests
- **Step-by-step Breakdown**: From initial processing to final response generation
- **Workflow Detection**: See when agents identify specific workflows (policy_inquiry, claim_filing, etc.)
- **Intent Recognition**: Monitor how agents extract user intent from natural language
- **Error Tracking**: Visualize any processing errors or exceptions

### 🔍 Agent Activity Monitor
- **Skill Execution**: Track when specific agent skills are invoked
- **Parameter Inspection**: View input parameters and processing details
- **Success/Failure States**: Visual indicators for all agent operations
- **Response Analysis**: Inspect full agent responses and metadata
- **Timing Information**: Precise timestamps for all activities

### 📡 API Call Visualization
- **HTTP Request Tracking**: Monitor all backend API communications
- **Request/Response Inspection**: Full visibility into payload and response data
- **Status Code Monitoring**: Visual success/failure indicators
- **Real-time Updates**: Live view of all inter-service communication
- **Error Analysis**: Detailed error information for failed requests

### 📊 System Health and Metrics
- **Agent Status**: Real-time health indicators for all deployed agents
- **Activity Metrics**: Count and frequency of agent activities
- **Workflow Patterns**: Analysis of recent interaction types and trends
- **Communication Flow**: Visual diagrams showing agent-to-agent interactions

## Development Workflow

### Adding New Agents

1. Create agent file in appropriate directory (`agents/domain/` or `agents/technical/`)
2. Implement using python-a2a decorators (`@agent`, `@skill`)
3. Add corresponding Dockerfile and Kubernetes manifest
4. Write unit and integration tests
5. Update deployment scripts

### Adding New Services

1. Create FastAPI service in `services/`
2. Define Pydantic models for data structures
3. (Optional) Add FastMCP wrapper for MCP tool exposure
4. Write API tests using FastAPI TestClient
5. Create Kubernetes deployment manifests

### Testing Strategy

- **Unit Tests**: Test individual agent skills and service endpoints
- **Integration Tests**: Test agent-to-agent communication and service integration
- **E2E Tests**: Test complete user workflows from request to response
- **Interactive Testing**: Use the dashboard for manual testing and demonstration

## API Documentation

### Agent Endpoints

- **SupportDomainAgent**: `http://localhost:30005`
  - Skills: `HandleCustomerInquiry`, `HandlePolicyInquiry`, `HandleGeneralSupport`
- **ClaimsDomainAgent**: `http://localhost:30008`
  - Skills: `HandleClaimFiling`, `HandleClaimStatusCheck`, `HandleGeneralClaimsSupport`

### Service Endpoints

- **Customer Service**: `http://customer-service:8000`
  - `GET /customer/{id}`: Get customer information
- **Policy Service**: `http://policy-service:8001`
  - `GET /policy/{id}`: Get policy details
- **Claims Service**: `http://claims-service:8002`
  - `POST /claim`: Create new claim
  - `GET /claim/{id}`: Get claim status

## Security Best Practices

### ✅ Implemented Security Features

- **No Hardcoded Secrets**: API keys loaded from environment variables
- **Template-based Deployment**: Uses `envsubst` for secure variable substitution
- **Git-ignored Credentials**: `.env` file is never committed to repository
- **Interactive Setup**: `setup_env.sh` script guides secure configuration
- **Kubernetes Secrets**: Sensitive data stored in cluster secrets

### 🔐 API Key Management

```bash
# Check API key is properly configured (shows first 10 chars only)
kubectl get secret llm-api-keys -n insurance-poc -o jsonpath='{.data.OPENROUTER_API_KEY}' | base64 -d | cut -c1-10

# Rotate API key
echo "OPENROUTER_API_KEY=new-key" > .env
envsubst < k8s/manifests/secrets.yaml | kubectl apply -f -
kubectl rollout restart deployment -n insurance-poc
```

## Monitoring and Debugging

### Logs

```bash
# View agent logs
kubectl logs -f deployment/support-agent -n insurance-poc

# View UI dashboard logs
kubectl logs -f deployment/ui-dashboard -n insurance-poc

# View service logs
kubectl logs -f deployment/customer-service -n insurance-poc
```

### Health Checks

```bash
# Check service health
kubectl get pods -n insurance-poc

# UI Dashboard
curl http://localhost:30501/_stcore/health

# Agent APIs
curl http://localhost:30005/health  # Support agent
curl http://localhost:30008/health  # Claims agent
```

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [x] Environment setup and dependencies
- [x] Mock backend services (Customer, Policy, Claims)
- [x] Basic technical agents
- [x] Unit tests for services and agents

### Phase 2: Core Agents (Weeks 3-4)
- [x] Domain agents with basic LLM integration
- [x] A2A communication between agents
- [x] Integration tests
- [x] Kubernetes deployment

### Phase 3: Advanced Features (Weeks 5-6)
- [x] OpenRouter LLM integration
- [x] MCP tool integration
- [x] End-to-end workflows
- [x] Performance optimization

### Phase 4: Interactive Dashboard (Week 7)
- [x] Streamlit-based UI with real-time monitoring
- [x] LLM thinking process visualization
- [x] Agent activity and API call monitoring
- [x] Multi-agent chat interface

### Phase 5: Production Readiness (Week 8)
- [x] Comprehensive testing
- [x] Security hardening with environment variable management
- [x] Documentation and demos
- [ ] Monitoring and logging
- [ ] CI/CD pipeline

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-agent`)
3. Make changes and add tests
4. Run the test suite (`pytest`)
5. Submit a pull request

## Architecture Decisions

### Why A2A Protocol?
- Standardized agent communication
- Loose coupling between domain and technical agents
- Scalable multi-agent architecture

### Why MCP for Tools?
- LLM-native tool integration
- Standardized tool discovery and invocation
- Future-proof for additional tool types

### Why OpenRouter?
- Unified LLM access across multiple providers
- Easy model switching and fallbacks
- Cost-effective for development and testing

### Why Streamlit for UI?
- Rapid prototyping and development
- Real-time data visualization capabilities
- Python-native integration with backend agents
- Built-in state management for interactive features

## License

MIT License - see LICENSE file for details.

## Support

For questions and support:
- Create an issue in the repository
- Review the docs/ directory for detailed documentation
- Check the troubleshooting guide in docs/troubleshooting.md