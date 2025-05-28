# AI-Driven Insurance Support & Claims PoC

A microservices-based, multi-agent architecture for insurance customer support and claims processing, running on local Kubernetes. This proof-of-concept demonstrates end-to-end workflows using domain agents for orchestration and technical agents for data access, with A2A protocol communication and MCP tool integration.

## Architecture Overview

### Core Components

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
- **Backend Services**: FastAPI + Uvicorn
- **Orchestration**: Kubernetes (Kind/Minikube)
- **Communication**: HTTPX for service calls, A2A for agent communication

## Project Structure

```
insurance-ai-poc/
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
- OpenRouter API key (optional, for LLM features)

### 1. Environment Setup

```bash
# Clone and navigate to project
cd insurance-ai-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Local Kubernetes Cluster

```bash
# Start Kind cluster
kind create cluster --name insurance-poc

# Verify cluster
kubectl cluster-info
kubectl create namespace insurance-poc
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your OpenRouter API key
OPENROUTER_API_KEY=your_key_here
```

### 4. Deploy Services

```bash
# Build and deploy all services
./scripts/deploy.sh

# Check deployment status
kubectl get pods -n insurance-poc
kubectl get services -n insurance-poc
```

### 5. Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/
```

## Usage Examples

### Policy Status Inquiry

```bash
# Direct API call to SupportDomainAgent
curl -X POST http://localhost:8005/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of policy 202?"}'
```

### Claim Creation

```bash
# File a new claim
curl -X POST http://localhost:8007/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to file a claim for a car accident on 2024-01-15"}'
```

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

## API Documentation

### Agent Endpoints

- **SupportDomainAgent**: `http://support-agent:8005`
  - Skills: `CheckPolicyStatus`, `HandleGeneralInquiry`
- **ClaimsDomainAgent**: `http://claims-agent:8007`
  - Skills: `CreateClaim`, `CheckClaimStatus`

### Service Endpoints

- **Customer Service**: `http://customer-service:8000`
  - `GET /customer/{id}`: Get customer information
- **Policy Service**: `http://policy-service:8001`
  - `GET /policy/{id}`: Get policy details
- **Claims Service**: `http://claims-service:8002`
  - `POST /claim`: Create new claim
  - `GET /claim/{id}`: Get claim status

## Monitoring and Debugging

### Logs

```bash
# View agent logs
kubectl logs -f deployment/support-agent -n insurance-poc

# View service logs
kubectl logs -f deployment/customer-service -n insurance-poc
```

### Health Checks

```bash
# Check service health
kubectl get pods -n insurance-poc
curl http://localhost:8000/health  # Customer service
curl http://localhost:8001/health  # Policy service
curl http://localhost:8002/health  # Claims service
```

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Environment setup and dependencies
- [ ] Mock backend services (Customer, Policy, Claims)
- [ ] Basic technical agents
- [ ] Unit tests for services and agents

### Phase 2: Core Agents (Weeks 3-4)
- [ ] Domain agents with basic LLM integration
- [ ] A2A communication between agents
- [ ] Integration tests
- [ ] Kubernetes deployment

### Phase 3: Advanced Features (Weeks 5-6)
- [ ] OpenRouter LLM integration
- [ ] MCP tool integration
- [ ] End-to-end workflows
- [ ] Performance optimization

### Phase 4: Production Readiness (Weeks 7-8)
- [ ] Comprehensive testing
- [ ] Monitoring and logging
- [ ] Documentation and demos
- [ ] Security hardening

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

## License

MIT License - see LICENSE file for details.

## Support

For questions and support:
- Create an issue in the repository
- Review the docs/ directory for detailed documentation
- Check the troubleshooting guide in docs/troubleshooting.md