# Insurance AI PoC Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [System Components](#system-components)
4. [Technology Stack](#technology-stack)
5. [Communication Protocols](#communication-protocols)
6. [Deployment Architecture](#deployment-architecture)
7. [API Documentation](#api-documentation)
8. [Data Flow Examples](#data-flow-examples)
9. [Development Workflow](#development-workflow)
10. [Testing Strategy](#testing-strategy)
11. [Monitoring and Observability](#monitoring-and-observability)
12. [Security Considerations](#security-considerations)
13. [Troubleshooting](#troubleshooting)
14. [Future Enhancements](#future-enhancements)

## Overview

The Insurance AI PoC is a microservices-based, multi-agent architecture designed to demonstrate end-to-end workflows for insurance customer support and claims processing. The system leverages AI agents that communicate using industry-standard protocols (A2A and MCP) to provide intelligent, contextual assistance to insurance customers.

### Key Features

- **Multi-Agent Architecture**: Domain agents orchestrate business workflows while technical agents handle data access
- **LLM Integration**: OpenRouter provides unified access to multiple LLM providers for natural language understanding
- **Standardized Communication**: A2A (Agent-to-Agent) protocol for inter-agent communication
- **Tool Integration**: MCP (Model Context Protocol) for LLM tool usage
- **Kubernetes Native**: Designed for cloud-native deployment and scaling
- **Comprehensive Testing**: Unit, integration, and end-to-end testing suites

### Business Workflows Supported

1. **Policy Inquiries**: Customers can ask about policy status, coverage details, and renewal information
2. **Claims Filing**: Guided claim submission with intelligent data collection
3. **Claims Status**: Real-time claim status updates and timeline information
4. **General Support**: AI-powered responses to common insurance questions
5. **Account Management**: Customer information retrieval and updates

## Architecture Principles

### 1. Separation of Concerns

- **Domain Agents**: Handle business logic and workflow orchestration
- **Technical Agents**: Manage data access and service integration
- **Backend Services**: Provide core data operations via REST APIs

### 2. Loose Coupling

- Services communicate through well-defined APIs
- Agents use standardized protocols (A2A, MCP)
- No direct database access between components

### 3. Scalability

- Horizontal scaling through Kubernetes
- Stateless service design
- Load balancing across agent instances

### 4. Observability

- Comprehensive logging and monitoring
- Health checks for all components
- Distributed tracing capabilities

### 5. Extensibility

- Plugin architecture for new agents
- Standard protocols enable easy integration
- Modular service design

## System Components

### Domain Agents (LLM-Driven Orchestrators)

#### SupportDomainAgent (`agents/domain/support_agent.py`)
- **Purpose**: Handles general customer support inquiries
- **Port**: 8005
- **Key Skills**:
  - `HandleCustomerInquiry`: Routes inquiries based on intent detection
  - `HandlePolicyInquiry`: Manages policy-related questions
  - `HandleClaimStatusInquiry`: Processes claim status requests
  - `HandleBillingInquiry`: Addresses billing and payment questions
  - `HandleGeneralSupport`: Provides general insurance information

#### ClaimsDomainAgent (`agents/domain/claims_agent.py`)
- **Purpose**: Specializes in claims workflow management
- **Port**: 8007
- **Key Skills**:
  - `HandleClaimInquiry`: Routes claim-related requests
  - `HandleClaimFiling`: Guides new claim submission
  - `HandleClaimStatusCheck`: Provides claim status updates
  - `CreateClaim`: Creates new claims with validation
  - `GetClaimStatus`: Retrieves specific claim information

### Technical Agents (API Integration Layer)

#### CustomerDataAgent (`agents/technical/customer_agent.py`)
- **Purpose**: Customer data operations
- **Port**: 8010
- **Data Source**: Customer Service API
- **Key Skills**:
  - `GetCustomerInfo`: Retrieve detailed customer information
  - `GetCustomerSummary`: Get customer overview with policy count
  - `SearchCustomers`: Find customers by name or email
  - `ValidateCustomer`: Verify customer existence and status
  - `UpdateCustomer`: Modify customer information

#### PolicyDataAgent (`agents/technical/policy_agent.py`)
- **Purpose**: Policy data operations
- **Port**: 8011
- **Data Source**: Policy Service API
- **Key Skills**:
  - `GetPolicyInfo`: Retrieve comprehensive policy details
  - `GetPolicyStatus`: Check policy active status and expiration
  - `GetCustomerPolicies`: List all policies for a customer
  - `GetPolicyCoverages`: Retrieve coverage details and limits
  - `ValidatePolicy`: Verify policy existence and status
  - `CreatePolicyQuote`: Generate quotes for new policies

#### ClaimsDataAgent (`agents/technical/claims_agent.py`)
- **Purpose**: Claims data operations
- **Port**: 8012
- **Data Source**: Claims Service API
- **Key Skills**:
  - `GetClaimInfo`: Retrieve detailed claim information
  - `CreateClaim`: Submit new claims to the system
  - `GetClaimStatus`: Check claim processing status
  - `UpdateClaimStatus`: Modify claim status with tracking
  - `GetCustomerClaims`: List claims for a customer
  - `AddClaimNote`: Add notes and updates to claims

### Backend Services (Data Layer)

#### Customer Service (`services/customer/app.py`)
- **Purpose**: Customer data management
- **Port**: 8000
- **Database**: In-memory mock data
- **Key Endpoints**:
  - `GET /customer/{id}`: Retrieve customer details
  - `GET /customer/{id}/summary`: Get customer summary
  - `POST /customer`: Create new customer
  - `PUT /customer/{id}`: Update customer information
  - `GET /search/customers`: Search customers

#### Policy Service (`services/policy/app.py`)
- **Purpose**: Policy data management
- **Port**: 8001
- **Database**: In-memory mock data
- **Key Endpoints**:
  - `GET /policy/{id}`: Retrieve policy details
  - `GET /policy/{id}/status`: Check policy status
  - `GET /customer/{id}/policies`: List customer policies
  - `POST /policy`: Create new policy
  - `POST /quote`: Generate policy quote

#### Claims Service (`services/claims/app.py`)
- **Purpose**: Claims data management
- **Port**: 8002
- **Database**: In-memory mock data
- **Key Endpoints**:
  - `GET /claim/{id}`: Retrieve claim details
  - `POST /claim`: Create new claim
  - `GET /claim/{id}/status`: Check claim status
  - `POST /claim/{id}/notes`: Add claim notes
  - `GET /customer/{id}/claims`: List customer claims

## Technology Stack

### Core Technologies

- **Python 3.11+**: Primary development language
- **FastAPI**: REST API framework for backend services
- **Uvicorn**: ASGI server for FastAPI applications
- **Pydantic**: Data validation and serialization
- **HTTPX**: Async HTTP client for service communication

### AI and LLM Integration

- **OpenRouter**: Unified LLM API access with fallback support
- **Primary Models**: OpenAI GPT-4o, Anthropic Claude-3-Haiku
- **Intent Detection**: LLM-based natural language understanding
- **Response Generation**: Context-aware response synthesis

### Agent Framework

- **A2A Protocol**: Agent-to-Agent communication standard
- **MCP (Model Context Protocol)**: LLM tool integration
- **Custom Agent Framework**: Built on base classes for consistency

### Infrastructure

- **Kubernetes**: Container orchestration and deployment
- **Docker**: Application containerization
- **Kind/Minikube**: Local development clusters
- **ConfigMaps/Secrets**: Configuration management

### Development and Testing

- **Pytest**: Testing framework with async support
- **FastAPI TestClient**: API testing utilities
- **Black**: Code formatting
- **MyPy**: Type checking
- **Pre-commit**: Git hooks for code quality

## Communication Protocols

### A2A (Agent-to-Agent) Protocol

The A2A protocol enables standardized communication between agents:

```python
# Example A2A call from domain agent to technical agent
result = await self.call_technical_agent(
    "PolicyDataAgent",
    "GetPolicyStatus", 
    {"policy_id": 202}
)
```

**Message Structure**:
```json
{
    "skill_name": "GetPolicyStatus",
    "parameters": {"policy_id": 202},
    "sender": "SupportDomainAgent"
}
```

**Response Structure**:
```json
{
    "success": true,
    "result": {
        "policy_id": 202,
        "status": "active",
        "expiration_date": "2024-12-31"
    },
    "task_id": "task_20241201_123456"
}
```

### MCP (Model Context Protocol)

MCP enables LLMs to call backend services as tools:

```python
# MCP tool definition
{
    "type": "function",
    "function": {
        "name": "get_customer_info",
        "description": "Retrieve customer information by ID",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "integer",
                    "description": "Customer ID to lookup"
                }
            },
            "required": ["customer_id"]
        }
    }
}
```

### LLM Integration

Domain agents use OpenRouter for natural language processing:

```python
# Intent detection
intent = await self.extract_intent(user_message)

# Response generation  
response = await self.generate_response(
    user_message,
    context="Policy inquiry",
    information=policy_data
)
```

## Deployment Architecture

### Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                       │
├─────────────────────────────────────────────────────────────┤
│  Namespace: insurance-poc                                   │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Domain Agents  │  │ Technical Agents │                  │
│  │                 │  │                 │                  │
│  │ Support Agent   │  │ Customer Agent  │                  │
│  │ Claims Agent    │  │ Policy Agent    │                  │
│  │                 │  │ Claims Agent    │                  │
│  │ Port: 8005,8007 │  │ Port: 8010-8012 │                  │
│  └─────────────────┘  └─────────────────┘                  │
│           │                     │                          │
│           └─────────┬───────────┘                          │
│                     │                                      │
│  ┌─────────────────────────────────────┐                   │
│  │          Backend Services           │                   │
│  │                                     │                   │
│  │ Customer Service  Policy Service    │                   │
│  │ Claims Service                      │                   │
│  │ Port: 8000-8002                     │                   │
│  └─────────────────────────────────────┘                   │
│                                                             │
│  ┌─────────────────────────────────────┐                   │
│  │           Configuration             │                   │
│  │                                     │                   │
│  │ ConfigMaps: URLs, Settings          │                   │
│  │ Secrets: API Keys                   │                   │
│  └─────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Service Mesh Communication

```
External User
     │
     ▼
┌─────────────┐    A2A Protocol    ┌──────────────┐
│   Domain    │◄──────────────────►│  Technical   │
│   Agents    │                    │   Agents     │
└─────────────┘                    └──────────────┘
     │                                     │
     │ LLM API Calls                      │ HTTP/REST
     ▼                                     ▼
┌─────────────┐                    ┌──────────────┐
│ OpenRouter  │                    │   Backend    │
│    API      │                    │  Services    │
└─────────────┘                    └──────────────┘
```

### Network Configuration

- **ClusterIP Services**: Internal service-to-service communication
- **NodePort Services**: External access for testing (ports 30000-30007)
- **Service Discovery**: Kubernetes DNS for service resolution
- **Load Balancing**: Kubernetes service load balancing

## API Documentation

### Domain Agent APIs

#### Support Agent Chat API
```http
POST /chat
Content-Type: application/json

{
    "message": "What is my policy status?",
    "customer_id": 101
}
```

**Response**:
```json
{
    "success": true,
    "response": "Your auto policy POL-AUTO-202401-001 is currently active and expires on December 31, 2024. You have 45 days until renewal.",
    "workflow": "policy_inquiry",
    "data": {
        "customer": {...},
        "policies": [...]
    }
}
```

#### Claims Agent Filing API
```http
POST /file-claim  
Content-Type: application/json

{
    "customer_id": 101,
    "message": "I want to file a claim for water damage",
    "claim_details": {
        "incident_date": "2024-01-15",
        "incident_type": "home_water_damage",
        "location": "123 Main St, Springfield",
        "description": "Burst pipe in basement"
    }
}
```

### Backend Service APIs

#### Customer Service
- `GET /customer/{id}` - Get customer details
- `GET /customer/{id}/summary` - Get customer summary
- `POST /customer` - Create customer
- `PUT /customer/{id}` - Update customer
- `GET /search/customers?q={query}` - Search customers

#### Policy Service  
- `GET /policy/{id}` - Get policy details
- `GET /policy/{id}/status` - Get policy status
- `GET /customer/{id}/policies` - List customer policies
- `POST /quote` - Generate policy quote

#### Claims Service
- `GET /claim/{id}` - Get claim details
- `POST /claim` - Create new claim
- `GET /claim/{id}/status` - Get claim status
- `POST /claim/{id}/notes` - Add claim note

### Agent Skill APIs

All agents expose standard endpoints:
- `GET /health` - Health check
- `GET /skills` - List available skills
- `POST /execute` - Execute specific skill

## Data Flow Examples

### Policy Status Inquiry Flow

```
User Request: "What is my policy status?"
     │
     ▼
┌─────────────────┐
│ SupportDomain   │ 1. Extract intent: "policy_inquiry"
│ Agent           │ 2. Validate customer_id
└─────────────────┘
     │ A2A Call
     ▼
┌─────────────────┐
│ CustomerData    │ 3. ValidateCustomer(customer_id)
│ Agent           │ 4. Return customer info
└─────────────────┘
     │ HTTP Call
     ▼
┌─────────────────┐
│ Customer        │ 5. GET /customer/{id}
│ Service         │ 6. Return customer data
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ PolicyData      │ 7. GetCustomerPolicies(customer_id)
│ Agent           │ 8. GetPolicyStatus(policy_id)
└─────────────────┘
     │ HTTP Call
     ▼
┌─────────────────┐
│ Policy          │ 9. GET /customer/{id}/policies
│ Service         │ 10. GET /policy/{id}/status
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ SupportDomain   │ 11. Generate natural language response
│ Agent           │ 12. Return formatted response to user
└─────────────────┘
```

### Claim Filing Flow

```
User Request: "I want to file a claim for car accident"
     │
     ▼
┌─────────────────┐
│ ClaimsDomain    │ 1. Extract intent: "claim_filing"
│ Agent           │ 2. Extract incident details from message
└─────────────────┘
     │ A2A Call
     ▼
┌─────────────────┐
│ CustomerData    │ 3. ValidateCustomer(customer_id)
│ Agent           │ 4. Return customer validation
└─────────────────┘
     │ A2A Call  
     ▼
┌─────────────────┐
│ PolicyData      │ 5. GetCustomerPolicies(customer_id)
│ Agent           │ 6. Return applicable policies
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ ClaimsDomain    │ 7. Determine appropriate policy
│ Agent           │ 8. Check for missing claim details
└─────────────────┘
     │ A2A Call (if complete)
     ▼
┌─────────────────┐
│ ClaimsData      │ 9. CreateClaim(claim_data)
│ Agent           │ 10. Return new claim information
└─────────────────┘
     │ HTTP Call
     ▼
┌─────────────────┐
│ Claims          │ 11. POST /claim
│ Service         │ 12. Return created claim
└─────────────────┘
```

## Development Workflow

### Local Development Setup

1. **Prerequisites**:
   ```bash
   # Install required tools
   brew install kind kubectl docker
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   ```bash
   # Copy environment template
   cp .env.example .env
   # Edit .env with your OpenRouter API key
   ```

3. **Start Local Services**:
   ```bash
   # Option 1: All services
   python scripts/run_local.py start
   
   # Option 2: Single service  
   python scripts/run_local.py start --service customer-service
   ```

4. **Kubernetes Deployment**:
   ```bash
   # Create Kind cluster
   kind create cluster --name insurance-poc
   
   # Deploy all services
   ./scripts/deploy.sh
   ```

### Code Organization

```
insurance-ai-poc/
├── agents/
│   ├── base.py              # Agent base classes
│   ├── llm_client.py        # LLM integration
│   ├── mcp_tools.py         # MCP tool registry
│   ├── domain/              # Domain agents
│   └── technical/           # Technical agents
├── services/
│   ├── customer/            # Customer service
│   ├── policy/              # Policy service  
│   └── claims/              # Claims service
├── k8s/
│   └── manifests/           # Kubernetes YAML
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
└── scripts/                 # Deployment scripts
```

### Development Guidelines

1. **Agent Development**:
   - Inherit from `DomainAgent` or `TechnicalAgent`
   - Use `@skill` decorator for agent capabilities
   - Implement proper error handling and logging

2. **Service Development**:
   - Use FastAPI with Pydantic models
   - Include health check endpoints
   - Implement comprehensive error responses

3. **Testing Requirements**:
   - Unit tests for all agent skills
   - Integration tests for A2A communication
   - E2E tests for complete workflows

## Testing Strategy

### Test Levels

1. **Unit Tests** (`tests/unit/`):
   - Individual service endpoint testing
   - Agent skill function testing
   - Model validation testing
   - Mock external dependencies

2. **Integration Tests** (`tests/integration/`):
   - Agent-to-agent communication
   - Service-to-service integration
   - Database operation testing
   - LLM integration testing

3. **End-to-End Tests** (`tests/e2e/`):
   - Complete user workflow testing
   - Multi-service integration
   - Performance testing
   - Error scenario testing

### Test Execution

```bash
# Run all tests
pytest

# Run specific test categories  
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=agents --cov=services

# Run performance tests
pytest -m performance
```

### Test Data Management

- **Mock Data**: In-memory test data for services
- **Test Fixtures**: Reusable test data and configurations
- **Test Isolation**: Each test uses independent data sets

## Monitoring and Observability

### Health Checks

All services implement health check endpoints:
```http
GET /health
```

Response format:
```json
{
    "status": "healthy",
    "service": "customer-service",
    "timestamp": "2024-01-15T10:30:00Z",
    "dependencies": ["database", "external-api"]
}
```

### Logging

Structured logging with correlation IDs:
```python
self.logger.info(
    "Processing customer inquiry",
    extra={
        "customer_id": customer_id,
        "workflow": "policy_inquiry",
        "correlation_id": correlation_id
    }
)
```

### Metrics Collection

Key metrics to monitor:
- Request/response times
- Success/error rates  
- Agent skill usage
- LLM API calls and costs
- Resource utilization

### Distributed Tracing

Future enhancement to implement OpenTelemetry for:
- Cross-service request tracing
- Performance bottleneck identification
- Error propagation tracking

## Security Considerations

### API Security

1. **Authentication**: JWT tokens for production deployment
2. **Authorization**: Role-based access control (RBAC)
3. **Rate Limiting**: Prevent API abuse
4. **Input Validation**: Strict input sanitization

### Data Protection

1. **Encryption**: TLS for all communications
2. **Secret Management**: Kubernetes secrets for API keys
3. **Data Masking**: PII protection in logs
4. **Access Control**: Principle of least privilege

### Agent Security

1. **Skill Validation**: Verify agent capabilities
2. **Message Integrity**: Prevent message tampering
3. **Resource Limits**: Prevent resource exhaustion
4. **Audit Logging**: Track all agent interactions

## Troubleshooting

### Common Issues

1. **Service Startup Failures**:
   ```bash
   # Check pod status
   kubectl get pods -n insurance-poc
   
   # View logs
   kubectl logs -f deployment/customer-service -n insurance-poc
   ```

2. **Agent Communication Issues**:
   ```bash
   # Test A2A connectivity
   kubectl exec -it pod/support-agent-xxx -n insurance-poc -- \
     curl http://customer-agent:8010/health
   ```

3. **LLM Integration Problems**:
   - Verify OpenRouter API key in secrets
   - Check rate limits and quotas
   - Monitor LLM response times

### Debug Commands

```bash
# Port forward for local testing
kubectl port-forward svc/support-agent 8005:8005 -n insurance-poc

# Check service connectivity
kubectl run debug --image=curlimages/curl -it --rm -- \
  curl http://customer-service:8000/health

# View agent skills
curl http://localhost:8005/skills
```

### Log Analysis

Search for common error patterns:
```bash
# Failed A2A calls
kubectl logs -n insurance-poc -l component=domain-agent | grep "A2A.*failed"

# LLM API errors  
kubectl logs -n insurance-poc -l component=domain-agent | grep "OpenRouter.*error"

# Service connectivity issues
kubectl logs -n insurance-poc -l component=technical-agent | grep "connection.*refused"
```

## Future Enhancements

### Short Term (1-3 months)

1. **Enhanced LLM Features**:
   - Function calling with MCP tools
   - Multi-turn conversation memory
   - Intent confidence scoring

2. **Additional Workflows**:
   - Policy renewal automation
   - Claims adjuster assignment
   - Fraud detection alerts

3. **Improved Testing**:
   - Load testing framework
   - Chaos engineering tests
   - Security penetration testing

### Medium Term (3-6 months)

1. **Production Features**:
   - Real database integration
   - Event sourcing for audit trails
   - Advanced monitoring dashboards

2. **AI Enhancements**:
   - Custom model fine-tuning
   - Retrieval-augmented generation (RAG)
   - Automated workflow optimization

3. **Integration Expansion**:
   - Third-party service integrations
   - Legacy system connectors
   - Real-time notification system

### Long Term (6-12 months)

1. **Advanced AI Capabilities**:
   - Predictive analytics for claims
   - Automated underwriting assistance
   - Customer behavior modeling

2. **Platform Evolution**:
   - Multi-tenant architecture
   - Global deployment support
   - Advanced security features

3. **Business Intelligence**:
   - Real-time analytics dashboards
   - Performance optimization recommendations
   - Automated compliance reporting

---

This architecture provides a solid foundation for an AI-driven insurance platform that can scale from proof-of-concept to production deployment while maintaining flexibility for future enhancements and integrations.