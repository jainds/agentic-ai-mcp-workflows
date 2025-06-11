# Google ADK + LiteLLM + OpenRouter Integration

## 🚀 **Complete Integration Overview**

This document describes the complete integration of **Google ADK v1.2.1** with **LiteLLM** and **OpenRouter** for the Insurance AI POC system, including Kubernetes deployment and Streamlit UI connectivity.

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit UI  │────│ Google ADK Agent │────│   OpenRouter    │
│   (Port 8501)   │    │   (Port 8000)    │    │  (GPT-4o-mini)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         │              ┌──────────────────┐               │
         │              │ Technical Agent  │               │
         └──────────────│   (Port 8001)    │───────────────┘
                        └──────────────────┘
                                 │
                        ┌──────────────────┐
                        │   Policy Server  │
                        │   (MCP) 8003     │
                        └──────────────────┘
```

## 📦 **Components**

### 1. Google ADK Agents
- **Customer Service Agent**: `insurance_customer_service` (LlmAgent)
- **Technical Agent**: `insurance_technical_agent` (LlmAgent with MCP tools)
- **Orchestrator**: `insurance_orchestrator` (LlmAgent for coordination)

### 2. Models & Integration
- **Primary Model**: `openai/gpt-4o-mini` via OpenRouter
- **Orchestrator Model**: `anthropic/claude-3-5-sonnet` via OpenRouter
- **Integration**: Google ADK's `LiteLlm` wrapper
- **API Endpoint**: `https://openrouter.ai/api/v1`

### 3. Supporting Services
- **Policy Server**: MCP server for data access (Port 8003)
- **Streamlit UI**: Customer interface (Port 8501)

## 🔧 **Local Development Setup**

### Prerequisites
```bash
# Ensure you're in the project root
cd /Users/piyushkumarjain/insurance-ai-poc

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Create/update `.env` file:
```env
OPENROUTER_API_KEY=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
DEFAULT_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
POLICY_SERVER_URL=http://localhost:8003/mcp
```

### Run Individual Agents

#### Customer Service Agent
```bash
cd insurance-adk
adk run insurance_customer_service
```

#### Technical Agent  
```bash
cd insurance-adk
adk run insurance_technical_agent
```

#### Web Interface
```bash
cd insurance-adk
adk web insurance_customer_service
# Access at: http://localhost:8000
```

#### API Server
```bash
cd insurance-adk
adk api_server insurance_technical_agent --port 8001
```

### Run Supporting Services

#### Policy Server (MCP)
```bash
cd policy_server
python main.py
# Runs on: http://localhost:8001/mcp
```

#### Streamlit UI
```bash
streamlit run main_ui.py --server.port=8501
# Access at: http://localhost:8501
```

## ☸️ **Kubernetes Deployment**

### 1. Create Namespace
```bash
kubectl create namespace insurance-ai-agentic
```

### 2. Create API Key Secret
```bash
kubectl create secret generic api-keys \
  --from-literal=openrouter-api-key=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 \
  -n insurance-ai-agentic
```

### 3. Deploy All Components
```bash
# Deploy Google ADK agents
kubectl apply -f k8s/manifests/google-adk-agents.yaml

# Verify deployments
kubectl get pods -n insurance-ai-agentic
```

### 4. Port Forwarding for Testing
```bash
# Use the new port forwarding script
./start_port_forwards_adk.sh
```

This will forward:
- **Port 8000**: ADK Customer Service (Web UI)
- **Port 8001**: ADK Technical Agent (API)
- **Port 8002**: ADK Orchestrator
- **Port 8003**: Policy Server (MCP)
- **Port 8501**: Streamlit UI

## 🧪 **Testing the Integration**

### 1. Test Google ADK Customer Service
```bash
# Test via CLI
cd insurance-adk
adk run insurance_customer_service

# Test via Web UI
curl http://localhost:8000/dev-ui/

# Test via API
curl -X POST http://localhost:8000/apps/insurance-adk/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my policy details?", "customer_id": "CUST-001"}'
```

### 2. Test Technical Agent
```bash
curl -X POST http://localhost:8001/technical/process \
  -H "Content-Type: application/json" \
  -d '{"request": "Get policy details", "customer_id": "CUST-001"}'
```

### 3. Test Policy Server
```bash
curl http://localhost:8003/health
```

### 4. Test Streamlit UI
Open browser: `http://localhost:8501`

## 📋 **Agent Configurations**

### Customer Service Agent
```python
# insurance-adk/insurance_customer_service/agent.py
root_agent = LlmAgent(
    name="insurance_customer_service", 
    model=LiteLlm(
        model="openai/gpt-4o-mini",
        api_base="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key
    ),
    instruction="Customer service for insurance inquiries..."
)
```

### Technical Agent
```python  
# insurance-adk/insurance_technical_agent/agent.py
root_agent = LlmAgent(
    name="insurance_technical_agent",
    model=LiteLlm(
        model="openai/gpt-4o-mini",
        api_base="https://openrouter.ai/api/v1", 
        api_key=openrouter_api_key
    ),
    instruction="Technical insurance operations...",
    tools=[policy_toolset]  # MCP integration
)
```

### Orchestrator Agent
```python
# insurance-adk/insurance_orchestrator/agent.py  
root_agent = LlmAgent(
    name="insurance_orchestrator",
    model=LiteLlm(
        model="anthropic/claude-3-5-sonnet",
        api_base="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key
    ),
    instruction="Coordinate between agents..."
)
```

## 🔄 **Streamlit UI Integration**

### Updated Configuration
```python
# ui/components/config.py
ADK_CUSTOMER_SERVICE_ENDPOINTS = [
    "http://insurance-adk-customer-service:8000",   # Kubernetes
    "http://localhost:8000",                        # Port forward
]

ADK_TECHNICAL_AGENT_ENDPOINTS = [
    "http://insurance-adk-technical:8001",          # Kubernetes  
    "http://localhost:8001",                        # Port forward
]
```

### Client Communication
```python
# ui/components/agent_client.py
class ADKAgentClient:
    def send_customer_service_message(self, message: str, customer_id: str):
        # Communicates with Google ADK agents
        url = f"{endpoint}/apps/insurance-adk/chat"
        payload = {"message": message, "customer_id": customer_id}
        response = self.session.post(url, json=payload)
```

## 🚀 **Deployment Commands**

### Quick Start (Local)
```bash
# 1. Start all services locally
cd policy_server && python main.py &
cd insurance-adk && adk web insurance_customer_service &  
streamlit run main_ui.py --server.port=8501 &

# 2. Test the integration
curl http://localhost:8000/dev-ui/
open http://localhost:8501
```

### Production Deployment (Kubernetes)
```bash
# 1. Create secrets
kubectl create secret generic api-keys \
  --from-literal=openrouter-api-key=$OPENROUTER_API_KEY \
  -n insurance-ai-agentic

# 2. Deploy all components
kubectl apply -f k8s/manifests/google-adk-agents.yaml

# 3. Start port forwarding
./start_port_forwards_adk.sh

# 4. Access services
open http://localhost:8000    # Google ADK Web UI
open http://localhost:8501    # Streamlit UI
```

## 📊 **Service Health Monitoring**

### Health Check Endpoints
- **ADK Customer Service**: `http://localhost:8000/health`
- **ADK Technical Agent**: `http://localhost:8001/health`
- **Policy Server**: `http://localhost:8003/health`
- **Streamlit UI**: `http://localhost:8501`

### Kubernetes Monitoring
```bash
# Check pod status
kubectl get pods -n insurance-ai-agentic

# Check service logs
kubectl logs -f deployment/insurance-adk-customer-service -n insurance-ai-agentic
kubectl logs -f deployment/insurance-adk-technical -n insurance-ai-agentic

# Check service endpoints
kubectl get svc -n insurance-ai-agentic
```

## 🔐 **Security Considerations**

1. **API Keys**: Stored as Kubernetes secrets
2. **Network**: Internal cluster communication via services
3. **External Access**: Only through port forwarding or ingress
4. **Model Access**: Authenticated via OpenRouter API key

## 🎯 **Success Criteria**

✅ **Completed Integrations:**
- Google ADK agents using LiteLLM wrapper
- OpenRouter models (GPT-4o-mini, Claude-3.5-Sonnet)
- MCP policy server connectivity
- Streamlit UI communication with ADK agents
- Kubernetes deployment configurations
- Port forwarding for development/testing

✅ **Working Endpoints:**
- Customer Service: `http://localhost:8000`
- Technical Agent: `http://localhost:8001`
- Policy Server: `http://localhost:8003`
- Streamlit UI: `http://localhost:8501`

## 🔍 **Troubleshooting**

### Common Issues

1. **Agent won't start**: Check OpenRouter API key in environment
2. **Port conflicts**: Kill existing processes: `pkill -f 'kubectl port-forward'`
3. **Model errors**: Verify OpenRouter API key validity
4. **Connection refused**: Ensure Kubernetes pods are running

### Debug Commands
```bash
# Check Google ADK installation
pip show google-adk

# Test OpenRouter connection
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models

# Check ADK agent status
cd insurance-adk && adk list

# Verify MCP server
curl http://localhost:8003/mcp
```

## 🎉 **Final Architecture Achievement**

```
Streamlit UI (8501) ──→ Google ADK Customer Service (8000)
                                    ↓
                              LiteLlm Wrapper
                                    ↓  
                               OpenRouter API
                                    ↓
                            GPT-4o-mini/Claude-3.5
                                    ↓
                          Insurance Customer Response

Technical Requests ──→ Google ADK Technical Agent (8001)
                                    ↓
                               MCP Toolset
                                    ↓
                          Policy Server (8003)
                                    ↓
                          Insurance Data Access
```

The integration is now **complete** with Google ADK agents running LiteLLM + OpenRouter models, connected to the Streamlit UI, and deployable in Kubernetes! 🚀 