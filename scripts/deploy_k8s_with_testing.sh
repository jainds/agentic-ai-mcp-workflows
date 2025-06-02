#!/bin/bash

# Kubernetes Deployment Script with Testing Setup
# Deploy Insurance AI POC to Kubernetes cluster with proper monitoring and testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="insurance-ai-poc"
RELEASE_NAME="insurance-ai-poc"
CHART_PATH="./k8s/insurance-ai-poc"
IMAGE_TAG="llm-only-$(date +%s)"

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        print_error "helm not found. Please install Helm."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "docker not found. Please install Docker."
        exit 1
    fi
    
    # Check if cluster is accessible
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    print_info "Building Docker image with tag: $IMAGE_TAG"
    
    docker build -t insurance-ai-poc:$IMAGE_TAG .
    
    # If using minikube, load image into minikube
    if kubectl config current-context | grep -q minikube; then
        print_info "Loading image into minikube..."
        minikube image load insurance-ai-poc:$IMAGE_TAG
    fi
    
    print_success "Docker image built and loaded"
}

# Create namespace
create_namespace() {
    print_info "Creating namespace: $NAMESPACE"
    
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Namespace created/updated"
}

# Create secrets for API keys
create_secrets() {
    print_info "Creating secrets for API keys..."
    
    # Check if required environment variables are set
    if [[ -z "$OPENROUTER_API_KEY" ]]; then
        print_error "OPENROUTER_API_KEY environment variable not set"
        exit 1
    fi
    
    if [[ -z "$LANGFUSE_SECRET_KEY" || -z "$LANGFUSE_PUBLIC_KEY" ]]; then
        print_warning "Langfuse keys not set. Monitoring will be limited."
    fi
    
    # Create secret
    kubectl create secret generic api-keys \
        --namespace=$NAMESPACE \
        --from-literal=OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
        --from-literal=LANGFUSE_SECRET_KEY="${LANGFUSE_SECRET_KEY:-}" \
        --from-literal=LANGFUSE_PUBLIC_KEY="${LANGFUSE_PUBLIC_KEY:-}" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Secrets created/updated"
}

# Deploy using Helm
deploy_helm() {
    print_info "Deploying with Helm..."
    
    helm upgrade --install $RELEASE_NAME $CHART_PATH \
        --namespace $NAMESPACE \
        --set image.tag=$IMAGE_TAG \
        --set secrets.useExistingSecret=true \
        --set secrets.secretName=api-keys \
        --set monitoring.enabled=true \
        --set deploymentUpdate.timestamp="$(date +%Y-%m-%d-%H-%M)" \
        --wait --timeout=10m
    
    print_success "Helm deployment completed"
}

# Wait for deployments
wait_for_deployments() {
    print_info "Waiting for deployments to be ready..."
    
    kubectl wait --for=condition=available \
        --timeout=300s \
        deployment/insurance-ai-poc-policy-server \
        deployment/insurance-ai-poc-technical-agent \
        deployment/insurance-ai-poc-domain-agent \
        deployment/insurance-ai-poc-streamlit-ui \
        --namespace=$NAMESPACE
    
    print_success "All deployments are ready"
}

# Port forward for testing
setup_port_forwarding() {
    print_info "Setting up port forwarding for testing..."
    
    # Kill any existing port forwards
    pkill -f "kubectl.*port-forward" || true
    sleep 2
    
    # Port forward services in background
    kubectl port-forward service/insurance-ai-poc-policy-server 8001:8001 -n $NAMESPACE &
    kubectl port-forward service/insurance-ai-poc-technical-agent 8002:8002 -n $NAMESPACE &
    kubectl port-forward service/insurance-ai-poc-domain-agent 8003:8003 -n $NAMESPACE &
    kubectl port-forward service/insurance-ai-poc-streamlit-ui 8501:8501 -n $NAMESPACE &
    
    # Wait for port forwards to be established
    sleep 5
    
    print_success "Port forwarding established"
    print_info "Services available at:"
    print_info "  - Policy Server: http://localhost:8001"
    print_info "  - Technical Agent: http://localhost:8002/a2a/agent.json"
    print_info "  - Domain Agent: http://localhost:8003/a2a/agent.json"
    print_info "  - Streamlit UI: http://localhost:8501"
}

# Test deployments
test_deployments() {
    print_info "Testing deployments..."
    
    # Test Policy Server health
    if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
        print_success "Policy Server is healthy"
    else
        print_warning "Policy Server health check failed"
    fi
    
    # Test Technical Agent
    if curl -f -s http://localhost:8002/a2a/agent.json > /dev/null 2>&1; then
        print_success "Technical Agent is responding"
    else
        print_warning "Technical Agent health check failed"
    fi
    
    # Test Domain Agent
    if curl -f -s http://localhost:8003/a2a/agent.json > /dev/null 2>&1; then
        print_success "Domain Agent is responding"
    else
        print_warning "Domain Agent health check failed"
    fi
    
    # Test Streamlit UI
    if curl -f -s http://localhost:8501 > /dev/null 2>&1; then
        print_success "Streamlit UI is responding"
    else
        print_warning "Streamlit UI health check failed"
    fi
}

# Run LLM-based intent analysis test
test_llm_intent_analysis() {
    print_info "Testing LLM-based intent analysis..."
    
    # Test Domain Agent intent analysis
    kubectl exec -n $NAMESPACE deployment/insurance-ai-poc-domain-agent -- \
        python -c "
from domain_agent.main import DomainAgent
agent = DomainAgent()
result = agent.intent_analyzer.analyze_customer_intent('I want to see my policies')
print('✅ LLM Intent Analysis Result:', result)
assert result['method'] == 'llm', 'Expected LLM method'
assert 'primary_intent' in result, 'Expected primary_intent in result'
print('✅ Domain Agent LLM intent analysis working correctly')
" || print_error "Domain Agent LLM test failed"
    
    # Test Technical Agent request parsing
    kubectl exec -n $NAMESPACE deployment/insurance-ai-poc-technical-agent -- \
        python -c "
from technical_agent.main import TechnicalAgent
agent = TechnicalAgent()
result = agent.request_parser.parse_request('Show me my policies')
print('✅ LLM Request Parsing Result:', result)
assert result['method'] == 'llm', 'Expected LLM method'
assert 'intent' in result, 'Expected intent in result'
print('✅ Technical Agent LLM request parsing working correctly')
" || print_error "Technical Agent LLM test failed"
    
    print_success "LLM tests completed"
}

# Display cluster information
show_cluster_info() {
    print_info "Cluster Information:"
    kubectl get pods -n $NAMESPACE -o wide
    print_info ""
    print_info "Service Information:"
    kubectl get services -n $NAMESPACE
    print_info ""
    print_info "Deployment Status:"
    kubectl get deployments -n $NAMESPACE
}

# Cleanup function
cleanup() {
    print_info "Cleaning up port forwards..."
    pkill -f "kubectl.*port-forward" || true
}

# Main deployment function
main() {
    print_info "Starting Kubernetes deployment for Insurance AI POC (LLM-only mode)"
    
    # Set up cleanup on exit
    trap cleanup EXIT
    
    check_prerequisites
    build_image
    create_namespace
    create_secrets
    deploy_helm
    wait_for_deployments
    setup_port_forwarding
    test_deployments
    test_llm_intent_analysis
    show_cluster_info
    
    print_success "Deployment completed successfully!"
    print_info ""
    print_info "To access the services:"
    print_info "  - Streamlit UI: http://localhost:8501"
    print_info "  - Technical Agent API: http://localhost:8002/a2a/agent.json"
    print_info "  - Domain Agent API: http://localhost:8003/a2a/agent.json"
    print_info ""
    print_info "To view logs:"
    print_info "  kubectl logs -f deployment/insurance-ai-poc-domain-agent -n $NAMESPACE"
    print_info "  kubectl logs -f deployment/insurance-ai-poc-technical-agent -n $NAMESPACE"
    print_info ""
    print_info "To clean up:"
    print_info "  helm uninstall $RELEASE_NAME -n $NAMESPACE"
    print_info "  kubectl delete namespace $NAMESPACE"
    print_info ""
    print_info "Press Ctrl+C to stop port forwarding and exit"
    
    # Keep the script running to maintain port forwards
    wait
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 