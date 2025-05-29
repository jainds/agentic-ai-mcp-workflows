#!/bin/bash

# Insurance AI PoC - Build and Deploy Script
# This script builds Docker images and deploys the entire system to Kubernetes

set -e

# Configuration
REGISTRY="localhost:5000"  # Use local registry for Rancher Desktop
NAMESPACE="insurance-ai"
VERSION="${VERSION:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check if we can connect to Kubernetes
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Build Claims Agent
    log_info "Building Claims Agent..."
    cat > Dockerfile.claims-agent << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
COPY agents/shared ./agents/shared
COPY agents/domain ./agents/domain

# Install uv for dependency management
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Add health check endpoint
COPY scripts/health_check.py ./

# Run the Claims Agent
CMD ["uv", "run", "python", "-m", "agents.domain.claims_agent"]
EOF

    docker build -f Dockerfile.claims-agent -t ${REGISTRY}/insurance-ai/claims-agent:${VERSION} .
    
    # Build Data Agent
    log_info "Building Data Agent..."
    cat > Dockerfile.data-agent << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
COPY agents/shared ./agents/shared
COPY agents/technical ./agents/technical

# Install uv for dependency management
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8002

# Add health check endpoint
COPY scripts/health_check.py ./

# Run the Data Agent
CMD ["uv", "run", "python", "-m", "agents.technical.data_agent"]
EOF

    docker build -f Dockerfile.data-agent -t ${REGISTRY}/insurance-ai/data-agent:${VERSION} .
    
    # Build Notification Agent
    log_info "Building Notification Agent..."
    cat > Dockerfile.notification-agent << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
COPY agents/shared ./agents/shared
COPY agents/technical ./agents/technical

# Install uv for dependency management
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8003

# Add health check endpoint
COPY scripts/health_check.py ./

# Run the Notification Agent
CMD ["uv", "run", "python", "-m", "agents.technical.notification_agent"]
EOF

    docker build -f Dockerfile.notification-agent -t ${REGISTRY}/insurance-ai/notification-agent:${VERSION} .
    
    # Build Services
    for service in claims user policy analytics; do
        log_info "Building ${service}-service..."
        
        cat > Dockerfile.${service}-service << EOF
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
COPY services/${service}_service ./services/${service}_service

# Install uv for dependency management
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Add health check endpoint
COPY scripts/health_check.py ./

# Run the service
CMD ["uv", "run", "python", "-m", "services.${service}_service.main"]
EOF

        docker build -f Dockerfile.${service}-service -t ${REGISTRY}/insurance-ai/${service}-service:${VERSION} .
    done
    
    # Build UI
    log_info "Building Insurance UI..."
    cat > Dockerfile.ui << 'EOF'
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock ./
COPY ui ./ui

# Install uv for dependency management
RUN pip install uv

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8501

# Run Streamlit
CMD ["uv", "run", "streamlit", "run", "ui/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF

    docker build -f Dockerfile.ui -t ${REGISTRY}/insurance-ai/insurance-ui:${VERSION} .
    
    log_success "All Docker images built successfully"
}

# Push images to registry
push_images() {
    log_info "Pushing images to registry..."
    
    # Push all images
    docker push ${REGISTRY}/insurance-ai/claims-agent:${VERSION}
    docker push ${REGISTRY}/insurance-ai/data-agent:${VERSION}
    docker push ${REGISTRY}/insurance-ai/notification-agent:${VERSION}
    docker push ${REGISTRY}/insurance-ai/claims-service:${VERSION}
    docker push ${REGISTRY}/insurance-ai/user-service:${VERSION}
    docker push ${REGISTRY}/insurance-ai/policy-service:${VERSION}
    docker push ${REGISTRY}/insurance-ai/analytics-service:${VERSION}
    docker push ${REGISTRY}/insurance-ai/insurance-ui:${VERSION}
    
    log_success "All images pushed to registry"
}

# Deploy to Kubernetes
deploy_to_k8s() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace and secrets
    log_info "Creating namespace and secrets..."
    kubectl apply -f k8s/namespace-and-secrets.yaml
    
    # Wait for namespace to be ready
    kubectl wait --for=condition=Ready namespace/${NAMESPACE} --timeout=60s
    
    # Deploy applications
    log_info "Deploying applications..."
    kubectl apply -f k8s/agents-deployment.yaml
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/claims-agent -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/data-agent -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/notification-agent -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/claims-service -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/user-service -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/policy-service -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/analytics-service -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/insurance-ui -n ${NAMESPACE}
    
    log_success "All deployments are ready"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Port-forward to check services (in background)
    kubectl port-forward service/claims-agent 8000:8000 -n ${NAMESPACE} &
    CLAIMS_PF_PID=$!
    
    kubectl port-forward service/data-agent 8002:8002 -n ${NAMESPACE} &
    DATA_PF_PID=$!
    
    kubectl port-forward service/notification-agent 8003:8003 -n ${NAMESPACE} &
    NOTIFICATION_PF_PID=$!
    
    kubectl port-forward service/insurance-ui 8501:8501 -n ${NAMESPACE} &
    UI_PF_PID=$!
    
    # Wait a moment for port-forwards to establish
    sleep 5
    
    # Check health endpoints
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Claims Agent health check passed"
    else
        log_warn "Claims Agent health check failed"
    fi
    
    if curl -f http://localhost:8002/health &> /dev/null; then
        log_success "Data Agent health check passed"
    else
        log_warn "Data Agent health check failed"
    fi
    
    if curl -f http://localhost:8003/health &> /dev/null; then
        log_success "Notification Agent health check passed"
    else
        log_warn "Notification Agent health check failed"
    fi
    
    if curl -f http://localhost:8501 &> /dev/null; then
        log_success "Insurance UI health check passed"
    else
        log_warn "Insurance UI health check failed"
    fi
    
    # Clean up port-forwards
    kill $CLAIMS_PF_PID $DATA_PF_PID $NOTIFICATION_PF_PID $UI_PF_PID 2>/dev/null || true
    
    log_success "Health checks completed"
}

# Display deployment status
show_status() {
    log_info "Deployment Status:"
    echo ""
    
    kubectl get pods -n ${NAMESPACE}
    echo ""
    
    kubectl get services -n ${NAMESPACE}
    echo ""
    
    log_info "To access the UI:"
    echo "kubectl port-forward service/insurance-ui 8501:8501 -n ${NAMESPACE}"
    echo "Then open http://localhost:8501 in your browser"
    echo ""
    
    log_info "To access individual agents:"
    echo "Claims Agent: kubectl port-forward service/claims-agent 8000:8000 -n ${NAMESPACE}"
    echo "Data Agent: kubectl port-forward service/data-agent 8002:8002 -n ${NAMESPACE}"
    echo "Notification Agent: kubectl port-forward service/notification-agent 8003:8003 -n ${NAMESPACE}"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f Dockerfile.* 2>/dev/null || true
}

# Main execution
main() {
    log_info "Starting Insurance AI PoC deployment..."
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Parse command line arguments
    SKIP_BUILD=false
    SKIP_PUSH=false
    SKIP_DEPLOY=false
    SKIP_HEALTH=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-push)
                SKIP_PUSH=true
                shift
                ;;
            --skip-deploy)
                SKIP_DEPLOY=true
                shift
                ;;
            --skip-health)
                SKIP_HEALTH=true
                shift
                ;;
            --version)
                VERSION="$2"
                shift 2
                ;;
            --registry)
                REGISTRY="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute deployment steps
    check_prerequisites
    
    if [ "$SKIP_BUILD" = false ]; then
        build_images
    fi
    
    if [ "$SKIP_PUSH" = false ]; then
        push_images
    fi
    
    if [ "$SKIP_DEPLOY" = false ]; then
        deploy_to_k8s
    fi
    
    if [ "$SKIP_HEALTH" = false ]; then
        run_health_checks
    fi
    
    show_status
    
    log_success "Insurance AI PoC deployment completed successfully!"
}

# Run main function
main "$@" 