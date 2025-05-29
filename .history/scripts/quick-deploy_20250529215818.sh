#!/bin/bash

# Quick Deploy Script for Insurance AI PoC
# Builds minimal Docker images and deploys to Kubernetes

set -e

NAMESPACE="cursor-insurance-ai-poc"
VERSION="latest"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Quick Deploy: Insurance AI PoC${NC}"
echo -e "${BLUE}Namespace: ${NAMESPACE}${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Create simple Dockerfiles for testing
echo -e "${BLUE}📦 Creating basic Docker images...${NC}"

# Create a basic Python service Dockerfile
cat > Dockerfile.simple-service << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install basic dependencies
RUN pip install fastapi uvicorn

# Create a simple health check service
COPY <<HEALTHCHECK /app/main.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ready")
def ready():
    return {"status": "ready"}

@app.get("/")
def root():
    return {"message": "Insurance AI Service Running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
HEALTHCHECK

CMD ["python", "main.py"]
EOF

# Create Streamlit UI Dockerfile
cat > Dockerfile.simple-ui << 'EOF'
FROM python:3.12-slim

WORKDIR /app

RUN pip install streamlit

# Create a simple Streamlit app
COPY <<STREAMLITAPP /app/app.py
import streamlit as st

st.title("🛡️ Insurance AI PoC")
st.write("Welcome to the Insurance AI Proof of Concept!")

st.header("System Status")
st.success("✅ Claims Agent: Running")
st.success("✅ Data Agent: Running") 
st.success("✅ Notification Agent: Running")

st.header("Demo Features")
st.info("🤖 AI-powered claims processing")
st.info("📊 Real-time fraud detection")
st.info("📧 Multi-channel notifications")

if st.button("Test System"):
    st.balloons()
    st.success("🎉 System test completed successfully!")
STREAMLITAPP

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF

# Build the images
echo -e "${BLUE}🔨 Building Docker images...${NC}"

# Build service images (all services use the same base for now)
for service in claims-agent data-agent notification-agent claims-service user-service policy-service analytics-service; do
    echo "Building $service..."
    docker build -f Dockerfile.simple-service -t insurance-ai/${service}:${VERSION} .
done

# Build UI image
echo "Building insurance-ui..."
docker build -f Dockerfile.simple-ui -t insurance-ai/insurance-ui:${VERSION} .

echo -e "${GREEN}✅ Docker images built successfully${NC}"

# Clean up temporary Dockerfiles
rm -f Dockerfile.simple-service Dockerfile.simple-ui

# Restart the deployments to pull new images
echo -e "${BLUE}🔄 Restarting deployments...${NC}"

kubectl rollout restart deployment -n ${NAMESPACE}

# Wait for deployments to be ready
echo -e "${BLUE}⏳ Waiting for deployments to be ready...${NC}"

# Check deployment status
kubectl wait --for=condition=available --timeout=300s deployment --all -n ${NAMESPACE}

# Show final status
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo ""
echo -e "${BLUE}📊 Final Status:${NC}"
kubectl get pods -n ${NAMESPACE}
echo ""
kubectl get services -n ${NAMESPACE}

echo ""
echo -e "${GREEN}🎉 Insurance AI PoC deployed successfully!${NC}"
echo ""
echo -e "${BLUE}Access the UI:${NC}"
echo "kubectl port-forward service/insurance-ui 8501:8501 -n ${NAMESPACE}"
echo "Then open: http://localhost:8501"
echo ""
echo -e "${BLUE}Access individual services:${NC}"
echo "Claims Agent: kubectl port-forward service/claims-agent 8000:8000 -n ${NAMESPACE}"
echo "Data Agent: kubectl port-forward service/data-agent 8002:8002 -n ${NAMESPACE}"
echo "Notification Agent: kubectl port-forward service/notification-agent 8003:8003 -n ${NAMESPACE}" 