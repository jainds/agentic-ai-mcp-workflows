# Insurance AI POC - Complete Deployment Solution

## 🎯 Overview

This repository includes a comprehensive **single-script deployment solution** for the Insurance AI POC system. The `deploy.sh` script handles everything from prerequisites checking to full Kubernetes deployment with monitoring and port forwarding.

## ⚡ Quick Start

```bash
# 1. Set your API key
export OPENROUTER_API_KEY="sk-or-v1-xxxxxx"

# 2. Deploy everything with one command
./deploy.sh

# 3. Access the system
open http://localhost:8501  # Streamlit UI
```

**That's it!** ✨ The script handles all the complexity for you.

## 📁 Deployment Files

| File | Purpose |
|------|---------|
| `deploy.sh` | **Main deployment script** - handles everything |
| `start_port_forwards.sh` | Port forwarding helper (auto-created) |
| `DEPLOYMENT_GUIDE.md` | Comprehensive deployment documentation |
| `DEPLOY_EXAMPLES.md` | Common usage examples and troubleshooting |
| `README_DEPLOYMENT.md` | This overview document |

## 🏗️ What Gets Deployed

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │  Domain Agent   │    │ Technical Agent │
│     :8501       │ -> │     :8003       │ -> │     :8002       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       v
                                               ┌─────────────────┐
                                               │ Policy Server   │
                                               │     :8001       │
                                               └─────────────────┘
```

### Components Deployed

- **Policy Server** (port 8001) - FastMCP server with insurance data
- **Technical Agent** (port 8002) - A2A bridge with LLM intelligence  
- **Domain Agent** (port 8003) - Customer-facing conversational AI
- **Streamlit UI** (port 8501) - Web interface for users
- **Monitoring** (port 8080) - Observability dashboard (optional)

### Kubernetes Resources

- **Namespace**: `insurance-ai-agentic`
- **Deployments**: 4 microservices
- **Services**: ClusterIP services for internal communication
- **Secrets**: API keys and monitoring credentials
- **ConfigMaps**: Application configuration

## 🛠️ Features

### ✅ What the Script Does

1. **Prerequisites Check** - Validates kubectl, helm, docker, etc.
2. **Environment Validation** - Checks required API keys
3. **Docker Build** - Builds container images locally
4. **Kubernetes Setup** - Creates namespace and secrets
5. **Helm Deployment** - Deploys all components via Helm charts
6. **Health Monitoring** - Waits for pods to be ready
7. **Port Forwarding** - Sets up local access
8. **Service Validation** - Tests all endpoints
9. **Monitoring Setup** - Configures observability (optional)

### 🎛️ Command Options

```bash
./deploy.sh deploy      # Full deployment (default)
./deploy.sh build       # Build Docker image only
./deploy.sh secrets     # Setup secrets only
./deploy.sh ports       # Setup port forwarding only
./deploy.sh validate    # Validate services only
./deploy.sh clean       # Clean up deployment
./deploy.sh help        # Show help
```

## 🔑 Configuration

### Required Environment Variables

```bash
export OPENROUTER_API_KEY="sk-or-v1-xxxxxx"  # Required for LLM operations
```

### Optional Environment Variables

```bash
export OPENAI_API_KEY="sk-xxxxxx"           # Backup LLM provider
export ANTHROPIC_API_KEY="sk-ant-xxxxxx"    # Alternative LLM provider
export LANGFUSE_SECRET_KEY="lf_sk_xxxxxx"   # LLM observability
export LANGFUSE_PUBLIC_KEY="lf_pk_xxxxxx"   # LLM observability
```

### Customization

The script uses sensible defaults but can be customized:

```bash
# Edit these variables in deploy.sh
NAMESPACE="insurance-ai-agentic"
RELEASE_NAME="insurance-ai-poc"
DOCKER_IMAGE="insurance-ai-poc:session-fix"
```

## 📊 Monitoring & Observability

### Built-in Health Checks

- **Automated validation** of all service endpoints
- **Pod readiness** and liveness monitoring
- **Resource usage** tracking
- **Error detection** and alerting

### Langfuse Integration (Optional)

When Langfuse keys are provided:
- **LLM call tracing** - See every AI interaction
- **Performance metrics** - Response times and token usage
- **Cost tracking** - Monitor LLM API costs
- **Error analysis** - Debug failed requests

### Monitoring Commands

```bash
# Check service health
./deploy.sh validate

# View logs
kubectl logs -l app.kubernetes.io/name=insurance-ai-poc -n insurance-ai-agentic

# Resource usage
kubectl top pods -n insurance-ai-agentic
```

## 🧪 Testing & Validation

### Automated Tests

The script includes built-in validation:

```bash
# Test all services
./deploy.sh validate

# Expected output:
# ✅ Policy Server is responding
# ✅ Technical Agent is responding  
# ✅ Domain Agent is responding
# ✅ Streamlit UI is responding
```

### Manual Testing

```bash
# Test customer interaction
curl -X POST http://localhost:8003/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "task": "ask",
    "parameters": {
      "question": "What are my policy premiums?",
      "customer_id": "CUST-2024-001"
    }
  }'
```

### Billing Cycle Accuracy Test

```bash
# Test the billing frequency fix
curl -X POST http://localhost:8003/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "task": "ask", 
    "parameters": {
      "question": "What are my current policy premiums and billing frequencies?",
      "customer_id": "CUST-2024-001"
    }
  }' | jq -r '.artifacts[0].parts[0].text'

# Should show: "$95 (quarterly)" not "$95/month"
```

## 🚀 Production Readiness

### Security Features

- **Kubernetes secrets** for API key management
- **Resource limits** to prevent resource exhaustion
- **Health checks** for automatic recovery
- **Least privilege** service accounts

### Scalability

```bash
# Scale components individually
kubectl scale deployment insurance-ai-poc-technical-agent --replicas=3 -n insurance-ai-agentic
kubectl scale deployment insurance-ai-poc-domain-agent --replicas=2 -n insurance-ai-agentic
```

### High Availability

- **Multi-replica deployments** supported
- **Rolling updates** with zero downtime
- **Health-based** pod replacement
- **Service discovery** for resilient networking

## 🔧 Troubleshooting

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| API key missing | `export OPENROUTER_API_KEY="your-key"` |
| Pod not ready | `kubectl logs <pod-name> -n insurance-ai-agentic` |
| Port forward failed | `./deploy.sh ports` |
| Service not responding | `./deploy.sh validate` |

### Debug Commands

```bash
# Check everything
kubectl get all -n insurance-ai-agentic

# View events
kubectl get events -n insurance-ai-agentic --sort-by='.lastTimestamp'

# Check secrets
kubectl describe secret api-keys -n insurance-ai-agentic
```

### Emergency Recovery

```bash
# Complete system reset
./deploy.sh clean
sleep 30
export OPENROUTER_API_KEY="your-key"
./deploy.sh
```

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive deployment guide
- **[DEPLOY_EXAMPLES.md](DEPLOY_EXAMPLES.md)** - Common examples and use cases
- **[Kubernetes Templates](k8s/insurance-ai-poc/templates/)** - Helm chart definitions

## 🎯 Key Benefits

### For Developers
- **One-command deployment** - No complex setup
- **Local development** - Full stack on localhost
- **Rapid iteration** - Quick rebuilds and updates
- **Comprehensive logging** - Easy debugging

### For Operations
- **Production-ready** - Kubernetes best practices
- **Monitoring included** - Built-in observability
- **Scalable architecture** - Horizontal scaling support
- **Clean separation** - Microservices design

### For Business
- **Fast deployment** - Minutes, not hours
- **Cost effective** - Efficient resource usage
- **Reliable operation** - Self-healing capabilities
- **Easy maintenance** - Automated management

## 🔮 Next Steps

After successful deployment:

1. **Access the UI**: http://localhost:8501
2. **Test customer interactions** via the web interface
3. **Monitor performance** with Langfuse (if configured)
4. **Scale components** based on usage patterns
5. **Configure ingress** for external access (production)

## 📞 Support

For deployment issues:

1. Check the [troubleshooting section](DEPLOYMENT_GUIDE.md#troubleshooting)
2. Review [common examples](DEPLOY_EXAMPLES.md)
3. Validate environment variables
4. Check Kubernetes cluster resources

---

**🎉 You're now ready to deploy the Insurance AI POC with a single command!**

```bash
export OPENROUTER_API_KEY="your-key"
./deploy.sh
``` 