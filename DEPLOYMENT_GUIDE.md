# Insurance AI POC - Complete Deployment Guide

This guide explains how to deploy the entire Insurance AI system to Kubernetes using the comprehensive `deploy.sh` script.

## 📋 Prerequisites

### Required Tools
- **kubectl** - Kubernetes command-line tool
- **helm** - Kubernetes package manager
- **docker** - Container runtime
- **jq** - JSON processor (will be auto-installed if missing)

### Required Environment Variables
```bash
# Required
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Optional (for additional LLM providers)
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional (for monitoring)
export LANGFUSE_SECRET_KEY="your-langfuse-secret-key"
export LANGFUSE_PUBLIC_KEY="your-langfuse-public-key"
```

### Kubernetes Cluster
- Access to a running Kubernetes cluster
- kubectl configured with proper context
- Sufficient resources (minimum 2 CPU, 4GB RAM)

## 🚀 Quick Start

### 1. Set Environment Variables
```bash
# Copy and modify your API keys
export OPENROUTER_API_KEY="sk-or-xxxxxx"
export OPENAI_API_KEY="sk-xxxxxx"  # Optional fallback
```

### 2. Run Full Deployment
```bash
./deploy.sh
```

This single command will:
- ✅ Check all prerequisites
- ✅ Build Docker images
- ✅ Create Kubernetes namespace
- ✅ Set up secrets
- ✅ Deploy all components via Helm
- ✅ Wait for pods to be ready
- ✅ Set up port forwarding
- ✅ Validate all services
- ✅ Configure monitoring

## 📖 Detailed Usage

### Available Commands

```bash
# Full deployment (default)
./deploy.sh deploy

# Build Docker image only
./deploy.sh build

# Setup secrets only
./deploy.sh secrets

# Setup port forwarding only
./deploy.sh ports

# Validate services only
./deploy.sh validate

# Clean up everything
./deploy.sh clean

# Show help
./deploy.sh help
```

### Component Overview

The deployment includes:

| Component | Port | Description |
|-----------|------|-------------|
| **Streamlit UI** | 8501 | Web interface for users |
| **Domain Agent** | 8003 | Conversational insurance agent |
| **Technical Agent** | 8002 | A2A bridge to policy systems |
| **Policy Server** | 8001 | MCP server with policy data |
| **Monitoring** | 8080 | Observability dashboard |

## 🔧 Configuration

### Kubernetes Configuration

The deployment uses:
- **Namespace**: `insurance-ai-agentic`
- **Release**: `insurance-ai-poc`
- **Image**: `insurance-ai-poc:session-fix`

### Resource Requirements

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|-------------|----------------|-----------|--------------|
| Domain Agent | 100m | 128Mi | 200m | 256Mi |
| Technical Agent | 100m | 128Mi | 200m | 256Mi |
| Policy Server | 50m | 64Mi | 150m | 128Mi |
| Streamlit UI | 50m | 128Mi | 150m | 256Mi |

### Environment Variables

The deployment automatically configures:

```yaml
# Service Discovery
DOMAIN_AGENT_URL: "http://insurance-ai-poc-domain-agent:8003"
TECHNICAL_AGENT_URL: "http://insurance-ai-poc-technical-agent:8002"  
POLICY_SERVER_URL: "http://insurance-ai-poc-policy-server:8001"

# API Keys (from Kubernetes secrets)
OPENROUTER_API_KEY: <from-secret>
OPENAI_API_KEY: <from-secret>
ANTHROPIC_API_KEY: <from-secret>

# Monitoring (optional)
LANGFUSE_SECRET_KEY: <from-secret>
LANGFUSE_PUBLIC_KEY: <from-secret>
```

## 🔍 Troubleshooting

### Common Issues

#### 1. API Key Missing
```bash
# Error: Missing required environment variables: OPENROUTER_API_KEY
export OPENROUTER_API_KEY="your-key-here"
./deploy.sh
```

#### 2. Pods Not Ready
```bash
# Check pod status
kubectl get pods -n insurance-ai-agentic

# Check logs
kubectl logs -l app.kubernetes.io/name=insurance-ai-poc -n insurance-ai-agentic

# Force restart
kubectl delete pods -l app.kubernetes.io/name=insurance-ai-poc -n insurance-ai-agentic
```

#### 3. Port Forward Issues
```bash
# Kill existing port forwards
pkill -f 'kubectl port-forward'

# Restart port forwarding
./deploy.sh ports
```

#### 4. Service Not Responding
```bash
# Check service status
kubectl get services -n insurance-ai-agentic

# Test direct pod access
kubectl port-forward -n insurance-ai-agentic pod/POD_NAME 8002:8002
curl http://localhost:8002/health
```

### Debug Commands

```bash
# Check all resources
kubectl get all -n insurance-ai-agentic

# View recent events
kubectl get events -n insurance-ai-agentic --sort-by='.lastTimestamp'

# Check secrets
kubectl describe secret api-keys -n insurance-ai-agentic

# View Helm status
helm status insurance-ai-poc -n insurance-ai-agentic

# Check resource usage
kubectl top pods -n insurance-ai-agentic
```

## 📊 Monitoring & Observability

### Health Checks

The deployment includes automatic health monitoring:

```bash
# Check all service health
./deploy.sh validate

# Manual health checks
curl http://localhost:8001/mcp/     # Policy Server
curl http://localhost:8002/health   # Technical Agent  
curl http://localhost:8003/health   # Domain Agent
curl http://localhost:8501/         # Streamlit UI
```

### Logs

```bash
# View all logs
kubectl logs -l app.kubernetes.io/name=insurance-ai-poc -n insurance-ai-agentic --tail=100

# Component-specific logs
kubectl logs -l component=technical-agent -n insurance-ai-agentic
kubectl logs -l component=domain-agent -n insurance-ai-agentic
kubectl logs -l component=policy-server -n insurance-ai-agentic
kubectl logs -l component=streamlit-ui -n insurance-ai-agentic
```

### Langfuse Integration

If Langfuse keys are provided:
- **LLM calls** are automatically traced
- **Performance metrics** are collected
- **Cost tracking** is enabled
- Access dashboard at https://cloud.langfuse.com

## 🧪 Testing the Deployment

### 1. Basic Health Check
```bash
curl -s http://localhost:8002/health | grep -o "Technical Agent"
```

### 2. End-to-End Test
```bash
curl -X POST http://localhost:8003/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "task": "ask",
    "parameters": {
      "question": "What policies do I have?",
      "customer_id": "CUST-2024-001"
    }
  }'
```

### 3. Policy Server Test
```bash
# Test MCP connection via Technical Agent
curl -X POST http://localhost:8002/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "task": "intelligent_policy_assistant",
    "parameters": {
      "request": "get customer policies for CUST-2024-001"
    }
  }'
```

### 4. Web Interface Test
Open in browser: http://localhost:8501

## 🔧 Advanced Configuration

### Custom Helm Values

Create a custom values file:

```yaml
# custom-values.yaml
replicaCount: 2

resources:
  limits:
    cpu: 500m
    memory: 512Mi

monitoring:
  langfuse:
    host: "https://your-langfuse-instance.com"
```

Deploy with custom values:
```bash
helm upgrade insurance-ai-poc ./k8s/insurance-ai-poc \
  -n insurance-ai-agentic \
  -f custom-values.yaml
```

### Scaling

```bash
# Scale Technical Agent
kubectl scale deployment insurance-ai-poc-technical-agent \
  --replicas=3 -n insurance-ai-agentic

# Scale Domain Agent  
kubectl scale deployment insurance-ai-poc-domain-agent \
  --replicas=2 -n insurance-ai-agentic
```

### Resource Monitoring

```bash
# Install metrics-server if not available
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# View resource usage
kubectl top pods -n insurance-ai-agentic
kubectl top nodes
```

## 🧹 Cleanup

### Partial Cleanup
```bash
# Stop port forwards only
pkill -f 'kubectl port-forward'

# Remove Helm release only
helm uninstall insurance-ai-poc -n insurance-ai-agentic
```

### Complete Cleanup
```bash
# Remove everything including namespace
./deploy.sh clean
```

## 📈 Production Considerations

### Security
- Use dedicated Kubernetes secrets for API keys
- Enable RBAC and pod security policies
- Use network policies to restrict inter-pod communication
- Regular security scans of container images

### Performance
- Set appropriate resource requests and limits
- Use horizontal pod autoscaling (HPA)
- Configure persistent volumes for data
- Implement health checks and readiness probes

### Monitoring
- Set up Prometheus and Grafana
- Configure alerting rules
- Use distributed tracing with Jaeger
- Monitor costs with Langfuse

### High Availability
- Deploy across multiple availability zones
- Use pod disruption budgets
- Implement graceful shutdown handlers
- Configure load balancing

## 🆘 Support

For issues or questions:

1. Check the troubleshooting section
2. Review pod logs and events
3. Validate environment variables
4. Test individual components
5. Check Kubernetes cluster resources

### Useful Resources
- [Kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug-application-cluster/) 