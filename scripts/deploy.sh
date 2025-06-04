#!/bin/bash

# Enhanced Deployment Script with Automatic Port Forwarding for Insurance AI POC
# This script handles deployment and automatically sets up port forwarding

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="insurance-ai-agentic"
APP_NAME="insurance-ai-poc"
ENV_FILE=".env"

# Port forwarding configuration
STREAMLIT_LOCAL_PORT=8501
DOMAIN_AGENT_LOCAL_PORT=8003
TECHNICAL_AGENT_LOCAL_PORT=8002
POLICY_SERVER_LOCAL_PORT=8001

# Function to kill existing port forwards
cleanup_port_forwards() {
    echo -e "${BLUE}🧹 Cleaning up existing port forwards${NC}"
    
    # Kill any existing kubectl port-forward processes
    pkill -f "kubectl port-forward" || true
    
    # Wait a moment for processes to die
    sleep 2
    
    # Check specific ports and kill processes using them
    for port in $STREAMLIT_LOCAL_PORT $DOMAIN_AGENT_LOCAL_PORT $TECHNICAL_AGENT_LOCAL_PORT $POLICY_SERVER_LOCAL_PORT; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Port $port is in use, attempting to free it${NC}"
            lsof -ti :$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    sleep 1
}

# Function to setup port forwarding
setup_port_forwards() {
    echo -e "${PURPLE}🌐 Setting up port forwarding${NC}"
    
    # Wait for all pods to be ready
    echo -e "${BLUE}⏳ Waiting for all pods to be ready${NC}"
    kubectl wait --for=condition=ready pod -l component=streamlit-ui -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l component=domain-agent -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l component=technical-agent -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l component=policy-server -n "$NAMESPACE" --timeout=300s
    
    # Start port forwards in background
    echo -e "${BLUE}🚀 Starting port forwards${NC}"
    
    # Streamlit UI (main interface)
    kubectl port-forward -n "$NAMESPACE" service/"$APP_NAME"-streamlit-ui "$STREAMLIT_LOCAL_PORT":80 &
    STREAMLIT_PID=$!
    
    # Domain Agent
    kubectl port-forward -n "$NAMESPACE" service/"$APP_NAME"-domain-agent "$DOMAIN_AGENT_LOCAL_PORT":8003 &
    DOMAIN_PID=$!
    
    # Technical Agent
    kubectl port-forward -n "$NAMESPACE" service/"$APP_NAME"-technical-agent "$TECHNICAL_AGENT_LOCAL_PORT":8002 &
    TECHNICAL_PID=$!
    
    # Policy Server
    kubectl port-forward -n "$NAMESPACE" service/"$APP_NAME"-policy-server "$POLICY_SERVER_LOCAL_PORT":8001 &
    POLICY_PID=$!
    
    # Wait a moment for port forwards to establish
    sleep 3
    
    # Check if port forwards are working
    echo -e "${BLUE}🔍 Verifying port forwards${NC}"
    
    local all_good=true
    
    if ! curl -s http://localhost:$STREAMLIT_LOCAL_PORT >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Streamlit UI port forward may not be ready yet${NC}"
        all_good=false
    fi
    
    if ! curl -s http://localhost:$POLICY_SERVER_LOCAL_PORT >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Policy Server port forward may not be ready yet${NC}"
        all_good=false
    fi
    
    # Save PIDs to file for later cleanup
    cat > /tmp/insurance-ai-port-forwards.pids << EOF
STREAMLIT_PID=$STREAMLIT_PID
DOMAIN_PID=$DOMAIN_PID
TECHNICAL_PID=$TECHNICAL_PID
POLICY_PID=$POLICY_PID
EOF
    
    if [ "$all_good" = true ]; then
        echo -e "${GREEN}✅ All port forwards are active${NC}"
    else
        echo -e "${YELLOW}⚠️  Some port forwards may still be starting up${NC}"
    fi
    
    # Display access information
    echo -e "${GREEN}🌟 Application is now accessible at:${NC}"
    echo -e "${PURPLE}   🖥️  Streamlit UI:      ${YELLOW}http://localhost:$STREAMLIT_LOCAL_PORT${NC}"
    echo -e "${PURPLE}   🤖 Domain Agent:      ${YELLOW}http://localhost:$DOMAIN_AGENT_LOCAL_PORT${NC}"
    echo -e "${PURPLE}   ⚙️  Technical Agent:   ${YELLOW}http://localhost:$TECHNICAL_AGENT_LOCAL_PORT${NC}"
    echo -e "${PURPLE}   📋 Policy Server:     ${YELLOW}http://localhost:$POLICY_SERVER_LOCAL_PORT${NC}"
    echo ""
    echo -e "${BLUE}📝 Port forward PIDs saved to /tmp/insurance-ai-port-forwards.pids${NC}"
}

# Function to create a stop script
create_stop_script() {
    cat > scripts/stop_port_forwards.sh << 'EOF'
#!/bin/bash

# Script to stop all port forwards for Insurance AI POC

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping Insurance AI POC port forwards${NC}"

# Kill all kubectl port-forward processes
pkill -f "kubectl port-forward.*insurance-ai-poc" || true

# Kill specific PIDs if file exists
if [ -f /tmp/insurance-ai-port-forwards.pids ]; then
    source /tmp/insurance-ai-port-forwards.pids
    
    for pid in $STREAMLIT_PID $DOMAIN_PID $TECHNICAL_PID $POLICY_PID; do
        if [ ! -z "$pid" ] && ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null || true
        fi
    done
    
    rm -f /tmp/insurance-ai-port-forwards.pids
fi

# Clean up any remaining processes on our ports
for port in 8501 8003 8002 8001; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

echo -e "${GREEN}✅ Port forwards stopped${NC}"
EOF

    chmod +x scripts/stop_port_forwards.sh
    echo -e "${BLUE}📝 Created scripts/stop_port_forwards.sh to stop port forwards later${NC}"
}

echo -e "${BLUE}🚀 Starting enhanced deployment with auto port forwarding${NC}"

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

# Clean up any existing port forwards first
cleanup_port_forwards

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
kubectl rollout status deployment/"$APP_NAME"-streamlit-ui -n "$NAMESPACE" --timeout=300s

# Apply session affinity for better reliability
echo -e "${BLUE}🔧 Applying session affinity to policy server${NC}"
kubectl patch service "$APP_NAME"-policy-server -n "$NAMESPACE" -p '{"spec":{"sessionAffinity":"ClientIP"}}'

# Show deployment status
echo -e "${BLUE}📊 Deployment Status:${NC}"
kubectl get pods -n "$NAMESPACE"
echo ""
kubectl get services -n "$NAMESPACE"

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"

# Set up automatic port forwarding
setup_port_forwards

# Create stop script for later use
create_stop_script

echo ""
echo -e "${GREEN}✅ Enhanced deployment with auto port forwarding completed!${NC}"
echo -e "${YELLOW}💡 Tips:${NC}"
echo -e "   • The main UI is at: ${PURPLE}http://localhost:$STREAMLIT_LOCAL_PORT${NC}"
echo -e "   • To stop port forwards: ${PURPLE}./scripts/stop_port_forwards.sh${NC}"
echo -e "   • Port forwards run in background - close terminal carefully"
echo -e "   • If ports don't work, wait 30 seconds and try again" 