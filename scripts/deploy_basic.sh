#!/bin/bash

# Secure Deployment Script for Insurance AI POC
# This script reads API keys from .env and creates Kubernetes secrets

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="insurance-ai-agentic"
APP_NAME="insurance-ai-poc"
ENV_FILE=".env"

echo -e "${BLUE}🚀 Starting secure deployment for Insurance AI POC${NC}"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: $ENV_FILE file not found!${NC}"
    echo -e "${YELLOW}Please create a .env file with your API keys:${NC}"
    echo "OPENAI_API_KEY=your-openrouter-api-key"
    echo "ANTHROPIC_API_KEY=your-anthropic-api-key"
    exit 1
fi

# Source environment variables
echo -e "${BLUE}📁 Loading environment variables from $ENV_FILE${NC}"
source "$ENV_FILE"

# Validate required environment variables
if [ -z "$OPENAI_KEY" ] && [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${RED}❌ Error: Neither OPENAI_KEY nor OPENROUTER_API_KEY found in $ENV_FILE${NC}"
    exit 1
fi

# Use OPENROUTER_API_KEY if available, otherwise fall back to OPENAI_KEY
OPENAI_API_KEY="${OPENROUTER_API_KEY:-$OPENAI_KEY}"

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ Error: OPENAI_API_KEY is empty${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables loaded successfully${NC}"

# Create namespace if it doesn't exist
echo -e "${BLUE}🏗️  Creating namespace: $NAMESPACE${NC}"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Delete existing secrets (if any) to ensure clean state
echo -e "${BLUE}🧹 Cleaning up existing secrets${NC}"
kubectl delete secret api-keys -n "$NAMESPACE" --ignore-not-found=true

# Create Kubernetes secret from environment variables
echo -e "${BLUE}🔐 Creating Kubernetes secrets${NC}"
kubectl create secret generic api-keys \
    --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
    --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
    -n "$NAMESPACE"

echo -e "${GREEN}✅ Secrets created successfully${NC}"

# Build Docker image with timestamp tag
TIMESTAMP=$(date +%s)
IMAGE_TAG="$APP_NAME:secure-deploy-$TIMESTAMP"

echo -e "${BLUE}🐳 Building Docker image: $IMAGE_TAG${NC}"
docker build -t "$IMAGE_TAG" .

echo -e "${GREEN}✅ Docker image built successfully${NC}"

# Deploy with Helm, using the new image and referencing the secret
echo -e "${BLUE}⚡ Deploying with Helm${NC}"
helm upgrade --install "$APP_NAME" k8s/insurance-ai-poc \
    --namespace "$NAMESPACE" \
    --set image.tag="secure-deploy-$TIMESTAMP" \
    --set secrets.useExistingSecret=true \
    --set secrets.secretName=api-keys

# Wait for deployment to complete
echo -e "${BLUE}⏳ Waiting for deployment to complete${NC}"
kubectl rollout status deployment/"$APP_NAME"-domain-agent -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$APP_NAME"-technical-agent -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/"$APP_NAME"-policy-server -n "$NAMESPACE" --timeout=300s

# Apply session affinity for better reliability
echo -e "${BLUE}🔧 Applying session affinity to policy server${NC}"
kubectl patch service "$APP_NAME"-policy-server -n "$NAMESPACE" -p '{"spec":{"sessionAffinity":"ClientIP"}}'

# Show deployment status
echo -e "${BLUE}📊 Deployment Status:${NC}"
kubectl get pods -n "$NAMESPACE"
echo ""
kubectl get services -n "$NAMESPACE"

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${YELLOW}📝 To access the application:${NC}"
echo "Domain Agent:     kubectl port-forward -n $NAMESPACE service/$APP_NAME-domain-agent 8003:8003"
echo "Technical Agent:  kubectl port-forward -n $NAMESPACE service/$APP_NAME-technical-agent 8002:8002"
echo "Policy Server:    kubectl port-forward -n $NAMESPACE service/$APP_NAME-policy-server 8001:8001"
echo "Streamlit UI:     kubectl port-forward -n $NAMESPACE service/$APP_NAME-streamlit-ui 8080:80"

echo -e "${GREEN}✅ Secure deployment script completed!${NC}" 