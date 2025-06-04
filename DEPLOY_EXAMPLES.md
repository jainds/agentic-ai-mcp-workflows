# Deployment Examples - Quick Reference

This document provides common deployment scenarios and examples for the Insurance AI POC system.

## 🚀 Common Deployment Scenarios

### 1. Fresh Deployment (Recommended)

```bash
# Set your API keys
export OPENROUTER_API_KEY="sk-or-v1-xxxxxx"
export OPENAI_API_KEY="sk-xxxxxx"  # Optional backup

# Deploy everything
./deploy.sh

# Expected output:
# ✅ Deployment completed successfully in XXXs!
# 🌟 Application URLs:
#    🖥️  Streamlit UI:      http://localhost:8501
#    🤖 Domain Agent:      http://localhost:8003
#    ⚙️  Technical Agent:   http://localhost:8002
#    📋 Policy Server:     http://localhost:8001
```

### 2. Update Existing Deployment

```bash
# Update API keys (if changed)
export OPENROUTER_API_KEY="new-key"

# Redeploy with new secrets
./deploy.sh secrets
./deploy.sh build
./deploy.sh deploy
```

### 3. Development Workflow

```bash
# 1. Build new image after code changes
./deploy.sh build

# 2. Update deployment
helm upgrade insurance-ai-poc ./k8s/insurance-ai-poc \
  -n insurance-ai-agentic \
  --set "deploymentUpdate.timestamp=$(date +%s)"

# 3. Restart port forwarding
./deploy.sh ports

# 4. Validate services
./deploy.sh validate
```

### 4. Port Forwarding Only

```bash
# If services are running but port forwarding stopped
./deploy.sh ports

# Manual port forward (alternative)
kubectl port-forward -n insurance-ai-agentic \
  service/insurance-ai-poc-streamlit-ui 8501:80 &
```

### 5. Monitoring Setup

```bash
# With full monitoring
export LANGFUSE_SECRET_KEY="lf_sk_xxxxxx"
export LANGFUSE_PUBLIC_KEY="lf_pk_xxxxxx"
export OPENROUTER_API_KEY="sk-or-v1-xxxxxx"

./deploy.sh
```

## 🔧 Troubleshooting Examples

### Pod Stuck in Pending

```bash
# Check node resources
kubectl top nodes
kubectl describe nodes

# Check pod events
kubectl describe pod -l app.kubernetes.io/name=insurance-ai-poc -n insurance-ai-agentic

# Solution: Scale down or add more nodes
kubectl scale deployment insurance-ai-poc-technical-agent --replicas=1 -n insurance-ai-agentic
```

### Service Not Responding

```bash
# Check pod logs
kubectl logs -l component=technical-agent -n insurance-ai-agentic --tail=50

# Common issue: API key missing
kubectl get secret api-keys -n insurance-ai-agentic -o yaml

# Fix: Update secret
./deploy.sh secrets
```

### Port Forward Failed

```bash
# Kill all existing port forwards
pkill -f 'kubectl.*port-forward'

# Check if pods are running
kubectl get pods -n insurance-ai-agentic

# Restart port forwarding
./deploy.sh ports
```

### Image Build Issues

```bash
# Check Docker daemon
docker info

# Clean build (if cache issues)
docker system prune -f
./deploy.sh build
```

## 🧪 Testing Examples

### 1. Basic Health Check

```bash
# Automated validation
./deploy.sh validate

# Manual checks
curl -s http://localhost:8001/mcp/ | grep jsonrpc
curl -s http://localhost:8002/health | grep "Technical Agent"
curl -s http://localhost:8003/health | grep "Domain Agent" 
curl -s http://localhost:8501/ | grep "Streamlit"
```

### 2. End-to-End Customer Query

```bash
# Test customer interaction
curl -X POST http://localhost:8003/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "task": "ask",
    "parameters": {
      "question": "I want to login with username john.doe@email.com and password securepass123",
      "customer_id": "CUST-2024-001"
    }
  }' | jq -r '.artifacts[0].parts[0].text'
```

### 3. Policy Data Retrieval

```bash
# Test technical agent integration
curl -X POST http://localhost:8002/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "task": "intelligent_policy_assistant",
    "parameters": {
      "request": "get all policies for customer CUST-2024-001"
    }
  }' | jq '.'
```

### 4. Billing Cycle Accuracy Test

```bash
# Test the billing cycle fix
curl -X POST http://localhost:8003/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "task": "ask",
    "parameters": {
      "question": "What are my policy premiums and billing frequencies?",
      "customer_id": "CUST-2024-001",
      "session_id": "test-session"
    }
  }' | jq -r '.artifacts[0].parts[0].text'

# Expected: Should show "$95 (quarterly)" not "$95/month"
```

## 📊 Monitoring Examples

### Resource Usage

```bash
# Check resource consumption
kubectl top pods -n insurance-ai-agentic
kubectl top nodes

# Memory and CPU details
kubectl describe pod -l component=technical-agent -n insurance-ai-agentic | grep -A 5 Resources
```

### Performance Testing

```bash
# Load test with multiple requests
for i in {1..10}; do
  curl -X POST http://localhost:8003/a2a/tasks/send \
    -H "Content-Type: application/json" \
    -d '{"task": "ask", "parameters": {"question": "Hello", "customer_id": "CUST-'$i'"}}' &
done
wait

# Check logs for performance metrics
kubectl logs -l component=technical-agent -n insurance-ai-agentic | grep "response_time"
```

### Langfuse Monitoring

```bash
# If Langfuse is configured, check traces
# Visit: https://cloud.langfuse.com

# Check if monitoring is working
kubectl logs -l component=technical-agent -n insurance-ai-agentic | grep -i langfuse
```

## 🎯 Production Examples

### Scaling for Load

```bash
# Scale components based on load
kubectl scale deployment insurance-ai-poc-technical-agent --replicas=3 -n insurance-ai-agentic
kubectl scale deployment insurance-ai-poc-domain-agent --replicas=2 -n insurance-ai-agentic

# Check scaling status
kubectl get pods -l app.kubernetes.io/name=insurance-ai-poc -n insurance-ai-agentic
```

### Resource Limits

```bash
# Update resource limits via Helm
helm upgrade insurance-ai-poc ./k8s/insurance-ai-poc \
  -n insurance-ai-agentic \
  --set "technicalAgent.resources.limits.memory=512Mi" \
  --set "technicalAgent.resources.limits.cpu=500m"
```

### Blue-Green Deployment

```bash
# Deploy to new namespace for testing
NAMESPACE=insurance-ai-test ./deploy.sh

# Test new deployment
curl http://localhost:8003/health

# Switch traffic (manual process)
# Update ingress or load balancer configuration
```

## 🧹 Cleanup Examples

### Partial Cleanup

```bash
# Stop port forwards only
pkill -f 'kubectl port-forward'

# Remove deployments but keep namespace and secrets
helm uninstall insurance-ai-poc -n insurance-ai-agentic
```

### Complete Cleanup

```bash
# Remove everything
./deploy.sh clean

# Or manual cleanup
helm uninstall insurance-ai-poc -n insurance-ai-agentic
kubectl delete namespace insurance-ai-agentic
pkill -f 'kubectl port-forward'
```

### Reset and Redeploy

```bash
# Complete reset and fresh deployment
./deploy.sh clean
sleep 10
./deploy.sh
```

## 📋 Common Command Patterns

### Quick Status Check

```bash
# One-liner to check everything
kubectl get pods,services,secrets -n insurance-ai-agentic && ./deploy.sh validate
```

### Log Monitoring

```bash
# Real-time log following
kubectl logs -f -l component=technical-agent -n insurance-ai-agentic

# All component logs
kubectl logs -l app.kubernetes.io/name=insurance-ai-poc -n insurance-ai-agentic --all-containers=true
```

### Configuration Validation

```bash
# Check Helm values
helm get values insurance-ai-poc -n insurance-ai-agentic

# Check configmaps
kubectl get configmaps -n insurance-ai-agentic -o yaml
```

## 🚨 Emergency Procedures

### Service Down

```bash
# 1. Check pod status
kubectl get pods -n insurance-ai-agentic

# 2. Restart failing pods
kubectl delete pod -l component=FAILING_COMPONENT -n insurance-ai-agentic

# 3. Check logs for errors
kubectl logs -l component=FAILING_COMPONENT -n insurance-ai-agentic --previous

# 4. Redeploy if needed
./deploy.sh
```

### Complete System Recovery

```bash
# 1. Clean everything
./deploy.sh clean

# 2. Wait for cleanup
sleep 30

# 3. Fresh deployment
export OPENROUTER_API_KEY="your-key"
./deploy.sh

# 4. Validate everything works
./deploy.sh validate
```

This covers the most common deployment scenarios and troubleshooting steps for the Insurance AI POC system. 