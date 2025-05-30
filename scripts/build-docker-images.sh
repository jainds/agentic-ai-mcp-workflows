#!/bin/bash

# Build script for Insurance AI PoC Docker images
set -e

echo "🏗️ Building Docker images for Insurance AI PoC..."

# Check if running in minikube environment
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    echo "📦 Using minikube Docker environment"
    eval $(minikube docker-env)
fi

# Build Enhanced Domain Agent
echo "🤖 Building Enhanced Domain Agent..."
docker build -t insurance-ai/enhanced-domain-agent:latest -f Dockerfile.enhanced-domain-agent .

# Build Python A2A Technical Agent
echo "🔧 Building Python A2A Technical Agent..."
docker build -t insurance-ai/python-a2a-technical-agent:latest -f Dockerfile.python-a2a-technical-agent .

# Build FastMCP Services (multi-stage build)
echo "🚀 Building FastMCP Services..."
docker build -t insurance-ai-poc/fastmcp-services:latest -f Dockerfile.fastmcp-services .

# Build Streamlit UI
echo "🎨 Building Streamlit UI..."
docker build -t insurance-ai-poc/streamlit-ui:latest -f Dockerfile.streamlit-ui .

echo "✅ All Docker images built successfully!"

# List built images
echo "📋 Built images:"
docker images | grep -E "(insurance-ai|insurance-ai-poc)" | head -10

echo "🎯 Ready for Kubernetes deployment!" 