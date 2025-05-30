#!/bin/bash

set -e

echo "🚀 Deploying FastMCP Services to Kubernetes"
echo "============================================"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

# Stop local services if running
echo "🛑 Stopping local FastMCP services..."
pkill -f "python.*service" || true
pkill -f "start_fastmcp_services" || true
sleep 2

# Build Docker images
echo "🔨 Building FastMCP Docker images..."

echo "  Building User Service..."
docker build -f Dockerfile.fastmcp-services --target user-service -t insurance-ai/fastmcp-user-service:latest .

echo "  Building Claims Service..."
docker build -f Dockerfile.fastmcp-services --target claims-service -t insurance-ai/fastmcp-claims-service:latest .

echo "  Building Policy Service..."
docker build -f Dockerfile.fastmcp-services --target policy-service -t insurance-ai/fastmcp-policy-service:latest .

echo "  Building Analytics Service..."
docker build -f Dockerfile.fastmcp-services --target analytics-service -t insurance-ai/fastmcp-analytics-service:latest .

echo "  Building FastMCP Data Agent..."
docker build -f Dockerfile.fastmcp-services --target fastmcp-data-agent -t insurance-ai/fastmcp-data-agent:latest .

echo "  Building Streamlit UI..."
docker build -f Dockerfile.streamlit-ui -t insurance-ai/streamlit-ui:latest .

echo "✅ All images built successfully"

# Create namespace and secrets if they don't exist
echo "📦 Setting up Kubernetes namespace and secrets..."
kubectl apply -f k8s/namespace-and-secrets.yaml

# Add JWT secret if not present
if ! kubectl get secret llm-secrets -n cursor-insurance-ai-poc -o jsonpath='{.data.jwt-secret-key}' &> /dev/null; then
    echo "🔑 Adding JWT secret..."
    JWT_SECRET=$(openssl rand -base64 32)
    kubectl patch secret llm-secrets -n cursor-insurance-ai-poc --type='merge' -p="{\"data\":{\"jwt-secret-key\":\"$(echo -n $JWT_SECRET | base64)\"}}" || \
    kubectl create secret generic jwt-secret -n cursor-insurance-ai-poc --from-literal=jwt-secret-key="$JWT_SECRET"
fi

# Deploy FastMCP services
echo "🚀 Deploying FastMCP services to Kubernetes..."
kubectl apply -f k8s/fastmcp-services-deployment.yaml

echo "🌐 Deploying Streamlit UI..."
kubectl apply -f k8s/streamlit-ui-deployment.yaml

# Wait for deployments to be ready
echo "⏳ Waiting for services to be ready..."
kubectl wait --for=condition=available deployment/user-service -n cursor-insurance-ai-poc --timeout=300s
kubectl wait --for=condition=available deployment/claims-service -n cursor-insurance-ai-poc --timeout=300s
kubectl wait --for=condition=available deployment/policy-service -n cursor-insurance-ai-poc --timeout=300s
kubectl wait --for=condition=available deployment/analytics-service -n cursor-insurance-ai-poc --timeout=300s
kubectl wait --for=condition=available deployment/fastmcp-data-agent -n cursor-insurance-ai-poc --timeout=300s
kubectl wait --for=condition=available deployment/streamlit-ui -n cursor-insurance-ai-poc --timeout=300s

# Check deployment status
echo "📊 Deployment Status:"
kubectl get deployments -n cursor-insurance-ai-poc -l component=fastmcp-service
kubectl get deployments -n cursor-insurance-ai-poc -l component=technical-agent
kubectl get deployments -n cursor-insurance-ai-poc -l component=ui

echo "📋 Service Status:"
kubectl get services -n cursor-insurance-ai-poc -l component=fastmcp-service
kubectl get services -n cursor-insurance-ai-poc -l component=ui

echo "🌐 Pod Status:"
kubectl get pods -n cursor-insurance-ai-poc -l component=fastmcp-service
kubectl get pods -n cursor-insurance-ai-poc -l component=technical-agent
kubectl get pods -n cursor-insurance-ai-poc -l component=ui

# Port forward for testing (optional)
echo ""
echo "🔗 To test the services locally, run:"
echo "  kubectl port-forward svc/user-service 8000:8000 -n cursor-insurance-ai-poc"
echo "  kubectl port-forward svc/claims-service 8001:8001 -n cursor-insurance-ai-poc"
echo "  kubectl port-forward svc/policy-service 8002:8002 -n cursor-insurance-ai-poc"
echo "  kubectl port-forward svc/analytics-service 8003:8003 -n cursor-insurance-ai-poc"
echo "  kubectl port-forward svc/fastmcp-data-agent 8004:8004 -n cursor-insurance-ai-poc"
echo "  kubectl port-forward svc/streamlit-ui 8501:8501 -n cursor-insurance-ai-poc"

echo ""
echo "🎉 Insurance AI PoC deployed successfully!"
echo "🌐 Streamlit UI: http://localhost:8501 (after port forwarding)"
echo "📊 FastMCP Data Agent: http://localhost:8004 (after port forwarding)"
echo "📝 Check logs with: kubectl logs -f deployment/streamlit-ui -n cursor-insurance-ai-poc" 