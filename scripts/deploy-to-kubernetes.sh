#!/bin/bash

# Kubernetes Deployment Script for Insurance AI PoC
set -e

echo "🚀 Starting Kubernetes deployment for Insurance AI PoC..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if minikube is running (for local development)
if command -v minikube &> /dev/null; then
    if ! minikube status &> /dev/null; then
        echo "🔄 Starting minikube..."
        minikube start
    fi
    echo "📦 Using minikube Docker environment"
    eval $(minikube docker-env)
fi

# Build Docker images
echo "🏗️ Building Docker images..."
./scripts/build-docker-images.sh

# Apply namespace and secrets
echo "🔐 Creating namespace and secrets..."
kubectl apply -f k8s/namespace-and-secrets.yaml

# Wait for namespace to be ready
echo "⏳ Waiting for namespace to be ready..."
kubectl wait --for=condition=Ready --timeout=30s namespace/cursor-insurance-ai-poc || echo "Namespace timeout (continuing anyway)"

# Deploy FastMCP services first
echo "🚀 Deploying FastMCP services..."
kubectl apply -f k8s/fastmcp-services-deployment.yaml

# Wait for FastMCP services to be ready
echo "⏳ Waiting for FastMCP services to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment -l component=fastmcp-service -n cursor-insurance-ai-poc || echo "FastMCP services timeout (continuing anyway)"

# Deploy enhanced domain agent and technical agents
echo "🤖 Deploying Enhanced Domain Agent and Technical Agents..."
kubectl apply -f k8s/enhanced-domain-agent-deployment.yaml

# Wait for agents to be ready
echo "⏳ Waiting for agents to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/enhanced-domain-agent -n cursor-insurance-ai-poc || echo "Domain agent timeout (continuing anyway)"
kubectl wait --for=condition=available --timeout=120s deployment -l component=technical-agent -n cursor-insurance-ai-poc || echo "Technical agents timeout (continuing anyway)"

# Deploy Streamlit UI
echo "🎨 Deploying Streamlit UI..."
kubectl apply -f k8s/streamlit-ui-deployment.yaml

# Wait for UI to be ready
echo "⏳ Waiting for UI to be ready..."
kubectl wait --for=condition=available --timeout=60s deployment -l app=streamlit-ui -n cursor-insurance-ai-poc || echo "UI timeout (continuing anyway)"

# Get deployment status
echo "📊 Deployment Status:"
kubectl get deployments -n cursor-insurance-ai-poc
echo ""
kubectl get services -n cursor-insurance-ai-poc
echo ""
kubectl get pods -n cursor-insurance-ai-poc

# Check pod health
echo "🔍 Checking pod health..."
kubectl get pods -n cursor-insurance-ai-poc -o wide

# Enable ingress addon for minikube if available
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    echo "🌐 Enabling minikube ingress addon..."
    minikube addons enable ingress || echo "Ingress addon already enabled or not available"
fi

# Get service URLs
echo "🌍 Service URLs:"
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    MINIKUBE_IP=$(minikube ip)
    echo "📡 Minikube IP: $MINIKUBE_IP"
    
    # Get NodePort services
    echo "🔗 Domain Agent: http://$MINIKUBE_IP:$(kubectl get svc enhanced-domain-agent -n cursor-insurance-ai-poc -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo 'ClusterIP')"
    echo "🎨 Streamlit UI: http://$MINIKUBE_IP:$(kubectl get svc streamlit-ui -n cursor-insurance-ai-poc -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo 'ClusterIP')"
else
    # Docker Desktop or other K8s - use localhost with NodePort
    echo "📡 Using localhost (Docker Desktop Kubernetes)"
    echo "🔗 Domain Agent: http://localhost:30800"
    echo "🎨 Streamlit UI: http://localhost:30801"
fi

echo "✅ Kubernetes deployment completed!"
echo ""
echo "🔧 To access services:"
echo "   kubectl port-forward svc/enhanced-domain-agent -n cursor-insurance-ai-poc 8000:8000"
echo "   kubectl port-forward svc/streamlit-ui -n cursor-insurance-ai-poc 8501:8501"
echo ""
echo "📝 To view logs:"
echo "   kubectl logs -f deployment/enhanced-domain-agent -n cursor-insurance-ai-poc"
echo "   kubectl logs -f deployment/streamlit-ui -n cursor-insurance-ai-poc" 