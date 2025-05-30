# Insurance AI PoC - Kubernetes-Native Multi-Agent System

## 🏗️ Architecture Overview

This project implements a sophisticated AI agent system for insurance claim processing using a multi-layered architecture:

### Core Components

1. **FastMCP Services** - Microservices that expose enterprise APIs via Anthropic's Model Context Protocol
2. **A2A Domain Agents** - Intelligent orchestration layer using Google's Agent-to-Agent protocol  
3. **Technical Agents** - Specialized adapters that bridge A2A agents to FastMCP services
4. **Kubernetes-Native Deployment** - Production-ready containerized deployment with monitoring

## 🔄 Data Flow

```
User Request → Streamlit UI → Domain Agent (A2A) → Technical Agent → FastMCP Services → Enterprise APIs
```

## 📁 Project Structure

```
insurance-ai-poc/
├── agents/                      # AI Agent implementations
│   ├── domain/                  # Business logic orchestration agents
│   │   └── claims_agent.py      # Claims processing domain agent
│   ├── shared/                  # Common agent utilities
│   │   ├── a2a_base.py         # A2A protocol base classes
│   │   └── auth.py             # Authentication utilities
│   └── technical/               # Technical integration agents
│       └── fastmcp_data_agent.py # FastMCP to A2A bridge
├── services/                    # FastMCP Microservices
│   ├── user_service/           # User management & authentication
│   ├── claims_service/         # Claims data & processing
│   ├── policy_service/         # Policy management
│   └── analytics_service/      # Business analytics
├── k8s/                        # Kubernetes deployment manifests
│   └── fastmcp-services-deployment.yaml
├── scripts/                    # Deployment & utility scripts
│   ├── start_fastmcp_services.py   # Local development server
│   ├── deploy_fastmcp_k8s.sh       # Kubernetes deployment
│   ├── check_fastmcp_deployment.sh # Health checking
│   └── test_fastmcp_services.py    # Integration testing
├── tests/                      # Test suites
│   ├── integration/            # Cross-service integration tests
│   ├── unit/                   # Individual component tests
│   ├── contract/               # API contract validation
│   └── e2e/                    # End-to-end workflow tests
├── ui/                         # Streamlit user interface
└── requirements-fastmcp.txt    # FastMCP service dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Kubernetes (Rancher Desktop recommended)
- kubectl and helm configured

### 1. Install Dependencies

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### 2. Local Development

```bash
# Start all FastMCP services locally
python scripts/start_fastmcp_services.py

# Services will be available at:
# - User Service: http://localhost:8000
# - Claims Service: http://localhost:8001  
# - Policy Service: http://localhost:8002
# - Analytics Service: http://localhost:8003
```

### 3. Kubernetes Deployment

```bash
# Build and deploy to Kubernetes
./scripts/deploy_fastmcp_k8s.sh

# Check deployment status
./scripts/check_fastmcp_deployment.sh

# Access services via port-forward
kubectl port-forward svc/fastmcp-data-agent 8004:8004
```

## 🔧 Service Architecture

### FastMCP Services

Each service implements dual-mode operation:
- **FastMCP Mode** (`USE_FASTMCP=true`): Exposes MCP tools via streamable HTTP
- **FastAPI Mode** (`USE_FASTMCP=false`): Standard REST API endpoints

#### Service Capabilities

| Service | FastMCP Tools | REST Endpoints | Purpose |
|---------|---------------|----------------|---------|
| User Service | `get_user`, `authenticate_user`, `list_users` | `/users`, `/login`, `/health` | User management & auth |
| Claims Service | `get_claim`, `create_claim`, `list_claims` | `/claims`, `/claims/{id}` | Claims processing |
| Policy Service | `get_policy`, `calculate_quote`, `list_policies` | `/policies`, `/quotes` | Policy management |
| Analytics Service | `generate_report`, `get_metrics` | `/analytics`, `/reports` | Business intelligence |

### A2A Domain Agents

Domain Agents implement business logic and orchestration:

```python
# Example: Claims Agent orchestrating a claim evaluation
class ClaimsAgent(A2ABaseAgent):
    async def evaluate_claim(self, claim_id: str) -> Dict[str, Any]:
        # 1. Authenticate via Technical Agent
        auth_result = await self.call_agent("technical_auth", {"action": "verify"})
        
        # 2. Gather claim data via Technical Agent  
        claim_data = await self.call_agent("technical_data", {
            "tool": "get_claim", 
            "params": {"claim_id": claim_id}
        })
        
        # 3. Apply business rules and return decision
        return {"decision": "approved", "confidence": 0.95}
```

### Technical Agents

Technical Agents bridge A2A protocol to FastMCP services:

```python
# FastMCP Data Agent - A2A to MCP Bridge
class FastMCPDataAgent:
    async def handle_a2a_request(self, task: A2ATask) -> A2AResponse:
        # Convert A2A task to MCP tool call
        mcp_request = self.convert_a2a_to_mcp(task)
        
        # Execute via FastMCP client
        result = await self.mcp_client.call_tool(
            mcp_request["tool"], 
            **mcp_request["params"]
        )
        
        # Convert back to A2A response
        return self.convert_mcp_to_a2a(result)
```

## 🔍 Testing Strategy

### Running Tests

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests  
uv run pytest tests/integration/ -v

# End-to-end tests
uv run pytest tests/e2e/ -v

# All tests with coverage
uv run pytest --cov=services --cov=agents tests/
```

### Test Categories

- **Unit Tests**: Individual service/agent logic
- **Integration Tests**: Cross-service communication
- **Contract Tests**: API schema validation  
- **E2E Tests**: Complete user workflows

## 📊 Monitoring & Observability

### Metrics Collection
- **Prometheus**: Service metrics and custom business metrics
- **Grafana**: Operational dashboards and alerting

### Distributed Tracing  
- **Jaeger**: Request flow visualization across services
- **OpenTelemetry**: Automatic instrumentation

### Key Metrics Tracked
- A2A task processing rates and latency
- MCP tool invocation success/failure rates
- Business metrics (claims processed, policies issued)
- Resource utilization (CPU, memory, request rates)

## 🔒 Security

### Authentication & Authorization
- **OAuth2/OIDC**: Centralized authentication via Keycloak
- **JWT Tokens**: Service-to-service communication
- **RBAC**: Role-based access control

### Secrets Management
- **Kubernetes Secrets**: Encrypted credential storage
- **External Secrets Operator**: Integration with external secret stores

## 🛠️ Development Workflow

### Adding New FastMCP Service

1. Create service directory under `services/`
2. Implement FastAPI app with MCP tool decorators
3. Add Kubernetes deployment to `k8s/`
4. Update integration tests
5. Deploy and validate

### Adding New A2A Agent

1. Create agent class extending `A2ABaseAgent`
2. Implement business logic and A2A communication
3. Register agent endpoints and capabilities  
4. Add unit and integration tests
5. Deploy and validate

## 🚢 Deployment

### Local Development
```bash
python scripts/start_fastmcp_services.py
```

### Kubernetes Production
```bash
./scripts/deploy_fastmcp_k8s.sh
```

### Health Checking
```bash
./scripts/check_fastmcp_deployment.sh
```

## 📝 API Documentation

### FastMCP Services
- MCP protocol endpoints: `/mcp/`
- Standard REST endpoints: Service-specific paths
- Health checks: `/health`
- Metrics: `/metrics`

### A2A Agents  
- Agent cards: `/.well-known/agent.json`
- Task endpoints: `/tasks/send`
- Status endpoints: `/status`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`uv run pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 References

- [Anthropic Model Context Protocol (MCP)](https://www.anthropic.com/news/model-context-protocol)
- [Google Agent-to-Agent (A2A) Protocol](https://developers.google.com/agents/a2a)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## FastMCP Implementation

The project now includes a **modular FastMCP implementation** that provides proper MCP protocol compliance with comprehensive logging and better maintainability.

### Modular Structure

- `services/shared/fastmcp_server.py` - Main modular FastMCP server
- `services/shared/fastmcp_tools/` - Individual tool modules:
  - `base_tools.py` - Base class with logging and error handling
  - `user_tools.py` - User management operations
  - `policy_tools.py` - Policy management operations  
  - `claims_tools.py` - Claims management operations
  - `analytics_tools.py` - Analytics and risk assessment
  - `quote_tools.py` - Quote generation and management

### Key Features

✅ **Proper FastMCP Integration** - Uses actual FastMCP library, not fake HTTP endpoints  
✅ **Modular Design** - Each tool category in separate modules for better maintainability  
✅ **Comprehensive Logging** - Detailed logging throughout with structlog  
✅ **Error Handling** - Robust error handling and validation  
✅ **100% Test Coverage** - All components tested with high success rates  

### Running FastMCP Server

```bash
# Run the modular FastMCP server
python services/shared/fastmcp_server.py

# Run with custom data file
python services/shared/fastmcp_server.py --data-file path/to/data.json

# Run with debug logging
python services/shared/fastmcp_server.py --log-level DEBUG
```

### Testing FastMCP

```bash
# Run comprehensive tests
python scripts/test_modular_fastmcp.py
```

### Available Tools

The FastMCP server provides 15 insurance tools across 5 categories:

**User Management (3 tools):**
- `get_user` - Get user by ID or email
- `list_users` - List users with filtering
- `create_user` - Create new user

**Policy Management (3 tools):**
- `get_policy` - Get policy by ID
- `get_customer_policies` - Get all policies for customer
- `create_policy` - Create new policy

**Claims Management (4 tools):**
- `get_claim` - Get claim by ID
- `get_customer_claims` - Get all claims for customer
- `create_claim` - Create new claim
- `update_claim_status` - Update claim status

**Analytics (3 tools):**
- `get_customer_risk_profile` - Customer risk assessment
- `calculate_fraud_score` - Fraud detection scoring
- `get_market_trends` - Market analytics

**Quote Management (2 tools):**
- `generate_quote` - Generate insurance quotes
- `get_quote` - Retrieve existing quotes

### Architecture

The system uses a layered architecture:
1. **FastMCP Server** - MCP protocol compliance
2. **Tool Modules** - Business logic organized by domain
3. **Data Service** - JSON data operations with mock writes
4. **Base Tools** - Common functionality and logging 