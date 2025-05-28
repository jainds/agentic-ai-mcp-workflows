#!/bin/bash

set -e

echo "🚀 Deploying Insurance AI PoC to Kubernetes"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️  No .env file found. Make sure OPENROUTER_API_KEY is set in environment."
fi

# Check if API key is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ Error: OPENROUTER_API_KEY environment variable is not set!"
    echo "Please set it in your .env file or export it directly:"
    echo "export OPENROUTER_API_KEY=your-api-key-here"
    exit 1
fi

echo "✅ API key found (${OPENROUTER_API_KEY:0:10}...)"

# Build Docker images
echo "📦 Building Docker images..."
docker build -t insurance-ai-poc:latest .
docker build -t insurance-ai-poc-ui:latest ./ui

# Apply Kubernetes manifests
echo "🔧 Applying Kubernetes manifests..."

# Create namespace first
kubectl apply -f k8s/manifests/namespace.yaml

# Process secrets template and apply
echo "🔑 Setting up secrets with environment variables..."
envsubst < k8s/manifests/secrets.yaml | kubectl apply -f -

# Apply technical agents (dependencies)
kubectl apply -f k8s/manifests/technical-agents.yaml

# Apply domain agents
kubectl apply -f k8s/manifests/support-agent.yaml
kubectl apply -f k8s/manifests/claims-agent.yaml

# Apply UI dashboard
kubectl apply -f k8s/manifests/ui-dashboard.yaml

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/customer-agent -n insurance-poc
kubectl wait --for=condition=available --timeout=300s deployment/policy-agent -n insurance-poc
kubectl wait --for=condition=available --timeout=300s deployment/claims-data-agent -n insurance-poc
kubectl wait --for=condition=available --timeout=300s deployment/support-agent -n insurance-poc
kubectl wait --for=condition=available --timeout=300s deployment/claims-agent -n insurance-poc
kubectl wait --for=condition=available --timeout=300s deployment/ui-dashboard -n insurance-poc

echo "✅ Deployment complete!"

# Show status
echo "📊 Deployment status:"
kubectl get pods -n insurance-poc
kubectl get services -n insurance-poc

echo ""
echo "🌐 Access URLs:"
echo "📊 UI Dashboard: http://localhost:30501"
echo "🏥 Support Agent API: http://localhost:30005"
echo "📋 Claims Agent API: http://localhost:30008"

echo ""
echo "🧪 To run tests in Kubernetes:"
echo "kubectl exec -it deployment/support-agent -n insurance-poc -- python scripts/test_llm_integration.py smoke"

echo ""
echo "🎯 Quick Start:"
echo "1. Open UI Dashboard: http://localhost:30501"
echo "2. Select an agent from the dropdown"
echo "3. Type a message or use quick test buttons"
echo "4. Watch real-time agent activity and API calls" 