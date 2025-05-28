# Insurance AI PoC - Kubernetes Deployment Guide

## 🚀 Deployment Overview

This guide covers the complete deployment of the Insurance AI PoC to Kubernetes, including all agents, their LLM integrations, and the interactive UI dashboard.

## 📋 Prerequisites

- Kubernetes cluster (Docker Desktop, Rancher Desktop, or any K8s cluster)
- kubectl configured and connected to your cluster
- Docker for building images
- OpenRouter API key (get one at https://openrouter.ai/keys)
- `envsubst` command (usually available on Linux/macOS, install with `brew install gettext` on macOS if needed)

## 🏗️ Architecture

The deployment includes:

### Interactive UI Dashboard
- **Streamlit Dashboard** (Port 8501/30501): Real-time monitoring and interaction interface
  - Multi-agent chat interface with dropdown selection
  - Real-time LLM thinking process visualization
  - Agent activity and API call monitoring
  - Communication flow diagrams
  - Health status monitoring

### Domain Agents (LLM-Enabled)
- **Support Agent** (Port 8005/30005): Customer support workflows with LLM intelligence
- **Claims Agent** (Port 8007/30008): Claims processing workflows with LLM intelligence

### Technical Agents (Data Processing)
- **Customer Agent** (Port 8010): Customer data operations
- **Policy Agent** (Port 8011): Policy data operations  
- **Claims Data Agent** (Port 8012): Claims data operations

## 🛠️ Deployment Steps

### 1. Environment Setup

**Option A: Interactive Setup (Recommended)**
```bash
# Run the setup script
./scripts/setup_env.sh
```

**Option B: Manual Setup**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your API key
nano .env  # or vim .env

# Add this line:
OPENROUTER_API_KEY=your-actual-api-key-here
```

**Option C: Export Environment Variable**
```bash
# Export directly (for CI/CD or temporary use)
export OPENROUTER_API_KEY=your-actual-api-key-here
```

### 2. Build and Deploy

```bash
# Make deployment script executable
chmod +x scripts/deploy_k8s.sh

# Deploy everything (will automatically use your API key from .env or environment)
./scripts/deploy_k8s.sh
```

### 3. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n insurance-poc

# Check services
kubectl get services -n insurance-poc

# Check deployment status
kubectl get deployments -n insurance-poc

# Verify API key was properly set (check first few characters)
kubectl get secret llm-api-keys -n insurance-poc -o jsonpath='{.data.OPENROUTER_API_KEY}' | base64 -d | cut -c1-10
```

## 🌐 Access URLs

Once deployed, the following services are available:

### 🎯 Main Access Point
- **📊 UI Dashboard**: http://localhost:30501
  - **Primary interface for PoC demonstration**
  - Real-time agent interaction and monitoring
  - LLM thinking process visualization
  - Multi-agent communication flow

### External API Access (NodePort Services)
- **🏥 Support Agent API**: http://localhost:30005
- **📋 Claims Agent API**: http://localhost:30008

### Internal Services (ClusterIP)
- Customer Agent: http://customer-agent:8010
- Policy Agent: http://policy-agent:8011
- Claims Data Agent: http://claims-data-agent:8012

## 🧪 Testing

### UI Dashboard Testing (Recommended)
```bash
# Open the dashboard
open http://localhost:30501

# Or check if it's running
curl http://localhost:30501
```

**Dashboard Features:**
1. **Agent Selection**: Choose between Support and Claims agents
2. **Quick Test Messages**: Pre-built test scenarios
3. **Real-time Monitoring**: Watch LLM thinking and agent communication
4. **API Call Visualization**: See all backend API interactions
5. **Health Monitoring**: Real-time agent status

### Health Checks
```bash
# UI Dashboard health
curl http://localhost:30501/_stcore/health

# Support Agent health
curl http://localhost:30005/health

# Claims Agent health  
curl http://localhost:30008/health
```

### LLM Integration Tests

#### In-Cluster Testing
```bash
# Run smoke tests
kubectl exec -it deployment/support-agent -n insurance-poc -- \
  python scripts/test_llm_integration.py smoke

# Run all agent tests
kubectl exec -it deployment/support-agent -n insurance-poc -- \
  python scripts/test_llm_integration.py agents

# Run complete integration tests
kubectl exec -it deployment/support-agent -n insurance-poc -- \
  python scripts/test_llm_integration.py integration
```

#### External API Testing

**Support Agent - General Support:**
```bash
curl -X POST "http://localhost:30005/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "HandleGeneralSupport",
    "parameters": {
      "user_message": "How do I file a claim?"
    }
  }'
```

**Claims Agent - Claims Support:**
```bash
curl -X POST "http://localhost:30008/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_name": "HandleGeneralClaimsSupport", 
    "parameters": {
      "user_message": "What documents do I need for a car accident claim?"
    }
  }'
```

## 📊 Available Skills

### Support Agent Skills
- `HandleCustomerInquiry`: Process general customer inquiries and route to appropriate workflow
- `HandlePolicyInquiry`: Handle policy status and information requests
- `HandleClaimStatusInquiry`: Handle claim status check requests
- `HandleBillingInquiry`: Handle billing and payment related questions
- `HandleGeneralSupport`: Handle general support questions
- `CheckPolicyStatus`: Quick policy status check for specific policy

### Claims Agent Skills
- `HandleClaimFiling`: Guide customers through claim filing process
- `HandleClaimInquiry`: Handle general claim-related questions
- `HandleClaimStatusCheck`: Check and report on claim status
- `HandleGeneralClaimsSupport`: Handle general claims support questions
- `CreateClaim`: Create a new claim
- `GetClaimStatus`: Get status of existing claim

## 🎭 UI Dashboard Features

### 💬 Chat Interface
- **Agent Selection**: Dropdown to choose Support or Claims agent
- **Customer ID**: Optional field for personalized responses
- **Quick Test Messages**: Pre-built scenarios for each agent type
- **Conversation History**: Shows last 5 interactions with full context

### 🧠 LLM Thinking Process
- **Real-time Visualization**: See how the LLM processes requests
- **Step-by-step Breakdown**: From intent extraction to response generation
- **Workflow Identification**: Shows detected workflows and intent
- **Error Tracking**: Visualizes any processing errors

### 🔍 Agent Activity Monitor
- **Skill Execution Tracking**: Monitor when skills are called
- **Success/Failure States**: Visual indicators for agent operations
- **Parameter Inspection**: View input parameters and responses
- **Timestamp Tracking**: Precise timing of all activities

### 📡 API Call Monitor
- **HTTP Request Tracking**: See all API calls made by agents
- **Request/Response Inspection**: Full payload and response visibility
- **Status Code Monitoring**: Visual success/failure indicators
- **Real-time Updates**: Live view of API communication

### 📊 Flow Diagram
- **Architecture Visualization**: Mermaid diagrams showing data flow
- **Health Status**: Real-time agent availability indicators
- **Activity Metrics**: Count of activities per agent
- **Workflow Patterns**: Analysis of recent interaction patterns

## 🔧 Configuration

### Environment Variables
All agents receive the following configuration:

**LLM Configuration:**
- `OPENROUTER_API_KEY`: API key for OpenRouter (loaded from .env or environment)
- `PRIMARY_MODEL`: Primary LLM model (qwen/qwen3-30b-a3b:free)
- `FALLBACK_MODEL`: Fallback LLM model (anthropic/claude-3-haiku)
- `OPENROUTER_BASE_URL`: OpenRouter API base URL

**UI Dashboard Configuration:**
- `SUPPORT_AGENT_URL`: http://support-agent:8005
- `CLAIMS_AGENT_URL`: http://claims-agent:8007
- `LOCAL_DEV`: Set to enable localhost URLs for local development

**Service URLs:**
- `CUSTOMER_AGENT_URL`: http://customer-agent:8010
- `POLICY_AGENT_URL`: http://policy-agent:8011
- `CLAIMS_DATA_AGENT_URL`: http://claims-agent:8012

### Resource Allocation
- **UI Dashboard**: 256Mi-1Gi memory, 200m-1000m CPU
- **Domain Agents**: 256Mi-1Gi memory, 200m-1000m CPU
- **Technical Agents**: 128Mi-512Mi memory, 100m-500m CPU

## 🚨 Troubleshooting

### Common Issues

**1. UI Dashboard Not Loading**
```bash
# Check pod status
kubectl get pods -n insurance-poc -l app=ui-dashboard

# Check logs
kubectl logs deployment/ui-dashboard -n insurance-poc

# Verify service
kubectl get service ui-dashboard-nodeport -n insurance-poc
```

**2. Pods in CrashLoopBackOff**
```bash
# Check logs
kubectl logs deployment/<agent-name> -n insurance-poc
```

**3. API Key Issues**
```bash
# Check if API key is properly set
kubectl get secret llm-api-keys -n insurance-poc -o yaml

# Update API key if needed
export OPENROUTER_API_KEY=your-new-key
envsubst < k8s/manifests/secrets.yaml | kubectl apply -f -

# Or update directly
kubectl patch secret llm-api-keys -n insurance-poc \
  --type='json' -p='[{"op": "replace", "path": "/data/OPENROUTER_API_KEY", "value":"'$(echo -n $OPENROUTER_API_KEY | base64)'"}]'
```

**4. Missing envsubst command**
```bash
# On macOS
brew install gettext

# On Ubuntu/Debian
sudo apt-get install gettext-base
```

**5. Service Discovery Issues**
```bash
# Check service endpoints
kubectl get endpoints -n insurance-poc

# Test internal connectivity from UI dashboard
kubectl exec -it deployment/ui-dashboard -n insurance-poc -- \
  curl http://support-agent:8005/health
```

## 🔄 Updates and Maintenance

### Rolling Updates
```bash
# Update image and trigger rolling update
kubectl set image deployment/support-agent support-agent=insurance-ai-poc:v2 -n insurance-poc
kubectl set image deployment/ui-dashboard ui-dashboard=insurance-ai-poc-ui:v2 -n insurance-poc

# Check rollout status
kubectl rollout status deployment/support-agent -n insurance-poc
kubectl rollout status deployment/ui-dashboard -n insurance-poc
```

### Scaling
```bash
# Scale deployment
kubectl scale deployment support-agent --replicas=3 -n insurance-poc
kubectl scale deployment ui-dashboard --replicas=2 -n insurance-poc
```

### Updating API Keys
```bash
# Update your .env file with new key
echo "OPENROUTER_API_KEY=new-key-here" >> .env

# Redeploy secrets
envsubst < k8s/manifests/secrets.yaml | kubectl apply -f -

# Restart deployments to pick up new secret
kubectl rollout restart deployment -n insurance-poc
```

## 📈 Monitoring

### Basic Monitoring
```bash
# Watch pods
kubectl get pods -n insurance-poc -w

# Monitor resources
kubectl top pods -n insurance-poc
kubectl top nodes
```

### Health Checks
All agents include:
- **Liveness Probe**: HTTP GET /health (30s initial delay)
- **Readiness Probe**: HTTP GET /health (5s initial delay)  
- **Startup Probe**: HTTP GET /health (10s initial delay)

**UI Dashboard Health Checks:**
- **Liveness Probe**: HTTP GET /_stcore/health (30s initial delay)
- **Readiness Probe**: HTTP GET /_stcore/health (5s initial delay)
- **Startup Probe**: HTTP GET /_stcore/health (10s initial delay)

## 🔐 Security

### Secrets Management
- ✅ API keys are loaded from environment variables, not hardcoded
- ✅ Secrets stored securely in Kubernetes secrets
- ✅ .env file is git-ignored to prevent accidental commits
- ✅ Template-based deployment with variable substitution

### Best Practices
```bash
# Never commit your .env file
echo ".env" >> .gitignore

# Use least-privilege access
kubectl create serviceaccount insurance-poc-sa -n insurance-poc

# Rotate API keys regularly
# Update .env file and redeploy
```

### RBAC (Optional)
```bash
# Create service account with limited permissions
kubectl create serviceaccount insurance-poc-sa -n insurance-poc
```

## 📝 Next Steps

1. **Production Readiness**: Add monitoring, logging, and alerting
2. **Load Balancing**: Add ingress controller for external access
3. **Database Integration**: Connect to persistent storage
4. **CI/CD Pipeline**: Automate builds and deployments with secure secret management
5. **Security Hardening**: Implement network policies and RBAC
6. **Enhanced UI**: Add more visualization features and customization options

---

## 📞 Support

For technical support or questions about the deployment, refer to the main README.md or project documentation. 