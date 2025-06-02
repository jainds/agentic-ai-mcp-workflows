#!/bin/bash

# Deploy Insurance AI PoC with Monitoring Integration
# This script deploys the system with comprehensive monitoring capabilities

set -e

echo "🚀 Deploying Insurance AI PoC with Monitoring Integration"
echo "========================================================="

# Configuration
NAMESPACE="insurance-ai-agentic"
RELEASE_NAME="insurance-ai-poc"
CHART_PATH="k8s/insurance-ai-poc"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi
    
    # Check docker
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build and tag Docker image
build_image() {
    log_info "Building Docker image with monitoring integration..."
    
    # Get current timestamp for unique tag
    TIMESTAMP=$(date +%s)
    IMAGE_TAG="monitoring-${TIMESTAMP}"
    
    # Build image
    docker build -t insurance-ai-poc:${IMAGE_TAG} .
    
    # Update values.yaml with new tag
    sed -i.bak "s/tag: .*/tag: ${IMAGE_TAG}/" ${CHART_PATH}/values.yaml
    
    log_success "Docker image built: insurance-ai-poc:${IMAGE_TAG}"
    echo "IMAGE_TAG=${IMAGE_TAG}" > .deployment_vars
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace ${NAMESPACE}..."
    
    if kubectl get namespace ${NAMESPACE} &> /dev/null; then
        log_warning "Namespace ${NAMESPACE} already exists"
    else
        kubectl create namespace ${NAMESPACE}
        log_success "Namespace ${NAMESPACE} created"
    fi
}

# Setup monitoring secrets
setup_monitoring_secrets() {
    log_info "Setting up monitoring secrets..."
    
    # Check if secrets already exist
    if kubectl get secret api-keys -n ${NAMESPACE} &> /dev/null; then
        log_warning "Secrets already exist. To update, delete first: kubectl delete secret api-keys -n ${NAMESPACE}"
        return
    fi
    
    # Create secrets with placeholder values
    kubectl create secret generic api-keys \
        --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
        --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
        --from-literal=LANGFUSE_SECRET_KEY="${LANGFUSE_SECRET_KEY:-}" \
        --from-literal=LANGFUSE_PUBLIC_KEY="${LANGFUSE_PUBLIC_KEY:-}" \
        --from-literal=PROMETHEUS_GATEWAY_URL="${PROMETHEUS_GATEWAY_URL:-}" \
        --from-literal=GRAFANA_API_KEY="${GRAFANA_API_KEY:-}" \
        -n ${NAMESPACE}
    
    log_success "Monitoring secrets created"
    
    if [[ -z "${LANGFUSE_SECRET_KEY}" || -z "${LANGFUSE_PUBLIC_KEY}" ]]; then
        log_warning "Langfuse keys not provided. LLM observability will be disabled."
        log_info "To enable Langfuse, set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY environment variables"
    fi
}

# Deploy with Helm
deploy_helm() {
    log_info "Deploying with Helm..."
    
    # Update deployment timestamp to force pod restart
    DEPLOY_TIMESTAMP=$(date +"%Y-%m-%d-%H-%M")
    
    helm upgrade --install ${RELEASE_NAME} ${CHART_PATH} \
        --namespace ${NAMESPACE} \
        --set deploymentUpdate.timestamp=${DEPLOY_TIMESTAMP} \
        --set secrets.useExistingSecret=true \
        --set monitoring.enabled=true \
        --wait --timeout=300s
    
    log_success "Helm deployment completed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Wait for pods to be ready
    log_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=${RELEASE_NAME} -n ${NAMESPACE} --timeout=300s
    
    # Check pod status
    log_info "Pod status:"
    kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME}
    
    # Check services
    log_info "Service status:"
    kubectl get services -n ${NAMESPACE} -l app.kubernetes.io/instance=${RELEASE_NAME}
    
    log_success "Deployment verification completed"
}

# Test monitoring integration
test_monitoring() {
    log_info "Testing monitoring integration..."
    
    # Get domain agent pod
    DOMAIN_POD=$(kubectl get pods -n ${NAMESPACE} -l component=domain-agent -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "${DOMAIN_POD}" ]]; then
        log_info "Testing monitoring in domain agent pod: ${DOMAIN_POD}"
        
        # Test monitoring import
        kubectl exec -n ${NAMESPACE} ${DOMAIN_POD} -- python -c "
from monitoring.setup.monitoring_setup import get_monitoring_manager
monitoring = get_monitoring_manager()
print('✅ Monitoring manager created successfully')
print(f'🟢 Monitoring enabled: {monitoring.is_monitoring_enabled()}')
status = monitoring.get_monitoring_status()
print(f'📊 Providers: {list(status[\"providers\"].keys())}')
"
        
        log_success "Monitoring integration test passed"
    else
        log_warning "Could not find domain agent pod for testing"
    fi
}

# Display connection information
show_connection_info() {
    log_info "Connection Information:"
    echo ""
    echo "To access the services, use port forwarding:"
    echo ""
    echo "# Domain Agent (port 8003)"
    echo "kubectl port-forward -n ${NAMESPACE} service/${RELEASE_NAME}-domain-agent 8003:8003"
    echo ""
    echo "# Technical Agent (port 8002)"  
    echo "kubectl port-forward -n ${NAMESPACE} service/${RELEASE_NAME}-technical-agent 8002:8002"
    echo ""
    echo "# Policy Server (port 8001)"
    echo "kubectl port-forward -n ${NAMESPACE} service/${RELEASE_NAME}-policy-server 8001:8001"
    echo ""
    echo "# Streamlit UI (port 8501)"
    echo "kubectl port-forward -n ${NAMESPACE} service/${RELEASE_NAME}-streamlit-ui 8501:8501"
    echo ""
    
    if [[ -n "${LANGFUSE_SECRET_KEY}" && -n "${LANGFUSE_PUBLIC_KEY}" ]]; then
        log_success "Langfuse LLM observability is enabled"
        echo "Visit your Langfuse dashboard to see LLM metrics"
    else
        log_warning "Langfuse LLM observability is disabled"
        echo "To enable: export LANGFUSE_SECRET_KEY=sk-xxx LANGFUSE_PUBLIC_KEY=pk-xxx"
    fi
    
    echo ""
    log_success "Deployment with monitoring integration completed!"
}

# Main execution
main() {
    check_prerequisites
    build_image
    create_namespace
    setup_monitoring_secrets
    deploy_helm
    verify_deployment
    test_monitoring
    show_connection_info
}

# Run main function
main "$@" 