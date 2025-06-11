#!/bin/bash

# =============================================================================
# Google ADK Insurance Agents - Kubernetes Deployment Script
# =============================================================================
# This script deploys the Google ADK insurance agent system to Kubernetes
# =============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="insurance-poc"
DOCKER_IMAGE="insurance-ai-poc:adk"

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

step() {
    echo -e "\n${PURPLE}🚀 $1${NC}"
}

# =============================================================================
# Main Deployment Functions
# =============================================================================

check_prerequisites() {
    step "Checking prerequisites..."
    
    # Check if kubectl is installed and configured
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    success "All prerequisites met"
}

build_docker_image() {
    step "Building Google ADK Docker image..."
    
    log "Building image: $DOCKER_IMAGE"
    docker build -f Dockerfile.adk -t $DOCKER_IMAGE .
    
    success "Docker image built successfully"
}

create_namespace() {
    step "Creating Kubernetes namespace..."
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        info "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f k8s/manifests/namespace.yaml
        success "Namespace $NAMESPACE created"
    fi
}

setup_secrets() {
    step "Setting up secrets..."
    
    # Check if Google API key is provided
    if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
        log "Found GOOGLE_API_KEY environment variable"
        
        # Create secret with actual API key
        kubectl create secret generic google-adk-secrets \
            --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
            --namespace=$NAMESPACE \
            --dry-run=client -o yaml | kubectl apply -f -
        
        success "Google API key secret created"
    else
        warning "GOOGLE_API_KEY not found in environment"
        info "Deploying with placeholder secret - update later with:"
        echo "  kubectl create secret generic google-adk-secrets --from-literal=GOOGLE_API_KEY=your_api_key --namespace=$NAMESPACE"
        
        # Apply the manifest with placeholder
        kubectl apply -f k8s/manifests/google-adk-agent.yaml
    fi
}

deploy_agents() {
    step "Deploying Google ADK agents..."
    
    log "Applying Google ADK agent manifest..."
    kubectl apply -f k8s/manifests/google-adk-agent.yaml
    
    log "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/google-adk-agent -n $NAMESPACE
    
    success "Google ADK agents deployed successfully"
}

setup_port_forwarding() {
    step "Setting up port forwarding..."
    
    log "Starting port forwarding script..."
    if [[ -f "start_port_forwards_adk.sh" ]]; then
        ./start_port_forwards_adk.sh
        success "Port forwarding started"
    else
        warning "Port forwarding script not found"
        info "You can manually port forward with:"
        echo "  kubectl port-forward -n $NAMESPACE service/google-adk-web 8000:8000"
        echo "  kubectl port-forward -n $NAMESPACE service/google-adk-api 8001:8001"
    fi
}

display_access_info() {
    step "Deployment complete!"
    
    echo ""
    success "Google ADK Insurance Agents deployed successfully!"
    echo ""
    info "🌟 Application URLs:"
    echo "   🎛️  ADK Web UI:        http://localhost:8000"
    echo "   📡 ADK API Server:    http://localhost:8001/docs"
    echo ""
    info "🎯 Available Agents:"
    echo "   🤖 insurance_customer_service  (LlmAgent)"
    echo "   ⚙️  insurance_technical_agent   (BaseAgent)"
    echo ""
    info "🔧 Management Commands:"
    echo "   Check status: kubectl get pods -n $NAMESPACE"
    echo "   View logs:    kubectl logs -f deployment/google-adk-agent -n $NAMESPACE"
    echo "   Update secret: kubectl create secret generic google-adk-secrets --from-literal=GOOGLE_API_KEY=your_key -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
    echo ""
    info "🚀 Next Steps:"
    echo "   1. Set your GOOGLE_API_KEY if not already done"
    echo "   2. Open http://localhost:8000 to access the ADK Web UI"
    echo "   3. Test agents using the built-in interface"
    echo ""
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo "🚀 Google ADK Insurance Agents - Kubernetes Deployment"
    echo "=" * 60
    
    check_prerequisites
    build_docker_image
    create_namespace
    setup_secrets
    deploy_agents
    setup_port_forwarding
    display_access_info
}

# Check for help flag
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Google ADK Insurance Agents Deployment Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Environment Variables:"
    echo "  GOOGLE_API_KEY    Your Google AI Studio API key (required for actual usage)"
    echo ""
    echo "Examples:"
    echo "  GOOGLE_API_KEY=your_key $0    # Deploy with API key"
    echo "  $0                            # Deploy with placeholder (update secret later)"
    echo ""
    exit 0
fi

# Run main function
main "$@" 