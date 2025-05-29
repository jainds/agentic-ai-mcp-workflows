#!/bin/bash

echo "🚀 Deploying FastMCP-enabled Insurance Services"
echo "=============================================="

# Set the namespace
NAMESPACE="cursor-insurance-ai-poc"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

echo "📦 Step 1: Building FastMCP-enabled Docker images..."

# Build claims service with FastMCP
echo "  Building claims service..."
docker build -t insurance-ai/claims-service:fastmcp -f services/claims_service/Dockerfile services/claims_service/

# Build policy service with FastMCP (when we create it)
echo "  Building policy service..."
docker build -t insurance-ai/policy-service:fastmcp -f services/policy_service/Dockerfile services/policy_service/ || echo "⚠️  Policy service Dockerfile not found, skipping"

# Build user service with FastMCP (when we create it)
echo "  Building user service..."
docker build -t insurance-ai/user-service:fastmcp -f services/user_service/Dockerfile services/user_service/ || echo "⚠️  User service Dockerfile not found, skipping"

echo "🔄 Step 2: Updating Kubernetes deployments..."

# Update claims service deployment
kubectl set image deployment/claims-agent claims-agent=insurance-ai/claims-service:fastmcp -n $NAMESPACE

# Restart services to pick up new images
echo "♻️  Step 3: Restarting services..."
kubectl rollout restart deployment/claims-agent -n $NAMESPACE

# Wait for rollout to complete
echo "⏳ Step 4: Waiting for rollout to complete..."
kubectl rollout status deployment/claims-agent -n $NAMESPACE --timeout=300s

# Check service health
echo "🔍 Step 5: Checking service health..."
kubectl get pods -n $NAMESPACE

echo ""
echo "✅ FastMCP deployment complete!"
echo ""
echo "🔗 Access services:"
echo "   Claims Service: kubectl port-forward service/claims-agent 8000:8000 -n $NAMESPACE"
echo "   UI Service: kubectl port-forward service/simple-insurance-ui 8503:8503 -n $NAMESPACE"
echo ""
echo "🧪 Test FastMCP integration:"
echo "   python test_fastmcp_data_agent.py"
echo "" 