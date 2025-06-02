# Secure Deployment Guide

This guide explains how to securely deploy the Insurance AI POC application using the provided deployment script.

## 🔐 Security Best Practices

- **Never commit API keys** to version control
- **Use Kubernetes secrets** for sensitive data in production
- **Keep `.env` file local** and add it to `.gitignore`

## 📋 Prerequisites

1. **Docker** - for building container images
2. **kubectl** - configured to access your Kubernetes cluster
3. **Helm** - for deploying the application
4. **API Keys** - OpenRouter/OpenAI API key for LLM functionality

## 🚀 Quick Start

### 1. Set up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example and fill in your actual API keys
cp .env.example .env
```

Edit `.env` with your actual API keys:

```bash
# OpenRouter API Key (recommended)
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here

# OR OpenAI API Key (fallback)
OPENAI_KEY=sk-your-actual-openai-key-here

# Optional: Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# Model Configuration
PRIMARY_MODEL=openai/gpt-4o-mini
FALLBACK_MODEL=openai/gpt-4o-mini
EMBEDDING_MODEL=microsoft/mai-ds-r1:free

# OpenRouter Configuration
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### 2. Deploy with the Secure Script

Run the deployment script:

```bash
./scripts/deploy.sh
```

The script will:
- ✅ Validate your `.env` file
- ✅ Create Kubernetes secrets from your API keys
- ✅ Build a new Docker image
- ✅ Deploy with Helm using secrets
- ✅ Apply session affinity for better reliability
- ✅ Show you how to access the application

### 3. Access the Application

After deployment, use the provided port-forward commands:

```bash
# Domain Agent (main conversational interface)
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-domain-agent 8003:8003

# Technical Agent (data processing)
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-technical-agent 8002:8002

# Policy Server (data backend)
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-policy-server 8001:8001

# Streamlit UI (web interface)
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-streamlit-ui 8080:80
```

## 🔧 Manual Deployment (Alternative)

If you prefer manual deployment:

### 1. Create Secrets Manually

```bash
# Create namespace
kubectl create namespace insurance-ai-agentic

# Create secret from .env file
source .env
kubectl create secret generic api-keys \
    --from-literal=OPENAI_API_KEY="$OPENROUTER_API_KEY" \
    --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    -n insurance-ai-agentic
```

### 2. Build and Deploy

```bash
# Build image
docker build -t insurance-ai-poc:latest .

# Deploy with Helm using secrets
helm upgrade --install insurance-ai-poc k8s/insurance-ai-poc \
    --namespace insurance-ai-agentic \
    --set image.tag=latest \
    --set secrets.useExistingSecret=true \
    --set secrets.secretName=api-keys
```

## 🛠️ Troubleshooting

### API Key Issues

```bash
# Check if secrets exist
kubectl get secrets -n insurance-ai-agentic

# Check secret contents (base64 encoded)
kubectl get secret api-keys -n insurance-ai-agentic -o yaml

# Check pod environment variables
kubectl describe pod -l component=domain-agent -n insurance-ai-agentic
```

### Deployment Issues

```bash
# Check pod status
kubectl get pods -n insurance-ai-agentic

# Check pod logs
kubectl logs -l component=domain-agent -n insurance-ai-agentic --tail=50

# Check deployment status
kubectl rollout status deployment/insurance-ai-poc-domain-agent -n insurance-ai-agentic
```

### Connection Issues

```bash
# Check services
kubectl get services -n insurance-ai-agentic

# Test internal connectivity
kubectl run debug --image=curlimages/curl -it --rm --restart=Never -- /bin/sh
```

## 🔄 Updates and Maintenance

### Update API Keys

```bash
# Update .env file with new keys
# Then re-run deployment script
./scripts/deploy.sh
```

### Update Application Code

```bash
# The deployment script automatically builds new images
# Just run it again after making code changes
./scripts/deploy.sh
```

### Clean Deployment

```bash
# Delete everything and start fresh
kubectl delete namespace insurance-ai-agentic
./scripts/deploy.sh
```

## 🏗️ Development vs Production

### Development
- Use `.env` file for API keys
- Set `secrets.useExistingSecret: false` in values.yaml
- API keys passed as environment variables

### Production (Recommended)
- Use external secret management (AWS Secrets Manager, etc.)
- Set `secrets.useExistingSecret: true`
- API keys stored in Kubernetes secrets
- Never commit API keys to git

## 📝 Notes

- The `.env` file is automatically excluded from git via `.gitignore`
- Kubernetes secrets are base64 encoded, not encrypted at rest by default
- For production, consider using external secret management solutions
- The deployment script creates timestamped Docker images for better tracking 