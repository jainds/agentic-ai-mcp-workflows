#!/bin/bash

# =============================================================================
# Insurance AI POC - Complete Deployment Script
# =============================================================================
# This script deploys the entire Insurance AI system to Kubernetes with:
# - All components (Policy Server, Technical Agent, Domain Agent, Streamlit UI)
# - Monitoring and observability
# - Port forwarding setup
# - Health checks and validation
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
NAMESPACE="insurance-ai-agentic"
RELEASE_NAME="insurance-ai-poc"
CHART_PATH="./k8s/insurance-ai-poc"
DOCKER_IMAGE="insurance-ai-poc:session-fix"
PORT_FORWARD_SCRIPT="./start_port_forwards.sh"

# Timeouts (in seconds)
DEPLOY_TIMEOUT=300
POD_READY_TIMEOUT=180
PORT_FORWARD_TIMEOUT=30

# =============================================================================
# Environment Setup
# =============================================================================

load_env_file() {
    step "Loading environment variables..."
    
    # Check for .env file in project root
    if [[ -f ".env" ]]; then
        log "Found .env file in project root"
        
        # Source the .env file more robustly
        set -a  # Automatically export all variables
        
        # Process .env file line by line to handle various formats
        while IFS= read -r line; do
            # Skip comments and empty lines
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$line" ]] && continue
            
            # Remove leading/trailing whitespace
            line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            
            # Skip if still empty after trimming
            [[ -z "$line" ]] && continue
            
            # Export the variable
            if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
                export "$line"
            fi
        done < .env
        
        set +a  # Stop auto-exporting
        
        # Count loaded variables
        local env_vars=$(grep -v '^[[:space:]]*#' .env | grep -v '^[[:space:]]*$' | grep '=' | wc -l | tr -d ' ')
        success "Loaded $env_vars environment variables from .env"
        
        # Debug: Show what was actually loaded for key variables
        log "Checking loaded variables..."
        
        # Show which key variables were loaded (without values)
        local loaded_keys=()
        if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
            loaded_keys+=("OPENROUTER_API_KEY")
            log "✓ OPENROUTER_API_KEY loaded (${#OPENROUTER_API_KEY} chars)"
        else
            warning "✗ OPENROUTER_API_KEY not found or empty"
        fi
        
        if [[ -n "${OPENAI_API_KEY:-}" ]] || [[ -n "${OPENAI_KEY:-}" ]]; then
            loaded_keys+=("OPENAI_API_KEY")
            if [[ -n "${OPENAI_KEY:-}" ]]; then
                log "✓ OPENAI_KEY found, will map to OPENAI_API_KEY"
            fi
        fi
        
        if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
            loaded_keys+=("ANTHROPIC_API_KEY")
        fi
        
        if [[ -n "${LANGFUSE_SECRET_KEY:-}" ]]; then
            loaded_keys+=("LANGFUSE_SECRET_KEY")
        fi
        
        if [[ -n "${LANGFUSE_PUBLIC_KEY:-}" ]]; then
            loaded_keys+=("LANGFUSE_PUBLIC_KEY")
        fi
        
        if [[ ${#loaded_keys[@]} -gt 0 ]]; then
            info "API keys found: ${loaded_keys[*]}"
        else
            warning "No API keys found in .env file"
        fi
        
        # Handle OPENAI_KEY vs OPENAI_API_KEY naming convention
        if [[ -n "${OPENAI_KEY:-}" ]] && [[ -z "${OPENAI_API_KEY:-}" ]]; then
            export OPENAI_API_KEY="$OPENAI_KEY"
            info "Mapped OPENAI_KEY to OPENAI_API_KEY"
        fi
        
    else
        warning "No .env file found in project root"
        info "You can create a .env file with your API keys, or export them manually"
        info "Example .env file:"
        echo "  OPENROUTER_API_KEY=sk-or-v1-xxxxxx"
        echo "  OPENAI_API_KEY=sk-xxxxxx"
        echo "  ANTHROPIC_API_KEY=sk-ant-xxxxxx"
        echo "  LANGFUSE_SECRET_KEY=lf_sk_xxxxxx"
        echo "  LANGFUSE_PUBLIC_KEY=lf_pk_xxxxxx"
    fi
}

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
# Prerequisite Checks
# =============================================================================

check_prerequisites() {
    step "Checking prerequisites..."
    
    # Check if kubectl is installed and configured
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        error "Helm is not installed. Please install Helm first."
        exit 1
    fi
    
    # Check if Docker is available (for building images)
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if jq is available (for JSON parsing)
    if ! command -v jq &> /dev/null; then
        warning "jq is not installed. Installing via brew (if available)..."
        if command -v brew &> /dev/null; then
            brew install jq || warning "Failed to install jq. Some features may not work."
        else
            warning "jq is not available. Some features may not work optimally."
        fi
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
    
    success "All prerequisites satisfied"
}

# =============================================================================
# Environment Validation
# =============================================================================

validate_environment() {
    step "Validating environment variables..."
    
    local missing_vars=()
    
    # Check for required API keys
    if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
        missing_vars+=("OPENROUTER_API_KEY")
    fi
    
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        warning "OPENAI_API_KEY is not set (optional fallback)"
    fi
    
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        warning "ANTHROPIC_API_KEY is not set (optional)"
    fi
    
    # Optional monitoring keys
    if [[ -z "${LANGFUSE_SECRET_KEY:-}" ]]; then
        info "LANGFUSE_SECRET_KEY is not set (monitoring will be limited)"
    fi
    
    if [[ -z "${LANGFUSE_PUBLIC_KEY:-}" ]]; then
        info "LANGFUSE_PUBLIC_KEY is not set (monitoring will be limited)"
    fi
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        error "Missing required environment variables: ${missing_vars[*]}"
        info "Please set these variables and run the script again:"
        for var in "${missing_vars[@]}"; do
            echo "  export $var=\"your-key-here\""
        done
        exit 1
    fi
    
    success "Environment validation complete"
}

# =============================================================================
# Docker Image Building
# =============================================================================

build_docker_image() {
    step "Building Docker image..."
    
    if [[ ! -f "Dockerfile" ]]; then
        error "Dockerfile not found in current directory"
        exit 1
    fi
    
    log "Building $DOCKER_IMAGE..."
    if docker build -t "$DOCKER_IMAGE" .; then
        success "Docker image built successfully"
    else
        error "Failed to build Docker image"
        exit 1
    fi
}

# =============================================================================
# Kubernetes Setup
# =============================================================================

setup_namespace() {
    step "Setting up Kubernetes namespace..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        info "Namespace '$NAMESPACE' already exists"
    else
        log "Creating namespace '$NAMESPACE'..."
        kubectl create namespace "$NAMESPACE"
        success "Namespace created"
    fi
}

setup_secrets() {
    step "Setting up Kubernetes secrets..."
    
    local secret_name="api-keys"
    
    # Prepare secret data
    local secret_data=()
    
    if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
        secret_data+=(--from-literal=OPENROUTER_API_KEY="$OPENROUTER_API_KEY")
    fi
    
    if [[ -n "${OPENAI_API_KEY:-}" ]]; then
        secret_data+=(--from-literal=OPENAI_API_KEY="$OPENAI_API_KEY")
    fi
    
    if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
        secret_data+=(--from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY")
    fi
    
    if [[ -n "${LANGFUSE_SECRET_KEY:-}" ]]; then
        secret_data+=(--from-literal=LANGFUSE_SECRET_KEY="$LANGFUSE_SECRET_KEY")
    fi
    
    if [[ -n "${LANGFUSE_PUBLIC_KEY:-}" ]]; then
        secret_data+=(--from-literal=LANGFUSE_PUBLIC_KEY="$LANGFUSE_PUBLIC_KEY")
    fi
    
    # Delete existing secret if it exists
    if kubectl get secret "$secret_name" -n "$NAMESPACE" &> /dev/null; then
        log "Updating existing secret '$secret_name'..."
        kubectl delete secret "$secret_name" -n "$NAMESPACE"
    else
        log "Creating new secret '$secret_name'..."
    fi
    
    # Create the secret
    if [[ ${#secret_data[@]} -gt 0 ]]; then
        kubectl create secret generic "$secret_name" -n "$NAMESPACE" "${secret_data[@]}"
        success "Secret '$secret_name' created with ${#secret_data[@]} keys"
    else
        error "No API keys available to create secret"
        exit 1
    fi
}

# =============================================================================
# Helm Deployment
# =============================================================================

deploy_helm_chart() {
    step "Deploying Helm chart..."
    
    if [[ ! -d "$CHART_PATH" ]]; then
        error "Helm chart not found at $CHART_PATH"
        exit 1
    fi
    
    log "Deploying release '$RELEASE_NAME' to namespace '$NAMESPACE'..."
    
    # Prepare Helm values
    local helm_args=(
        --namespace "$NAMESPACE"
        --create-namespace
        --wait
        --timeout "${DEPLOY_TIMEOUT}s"
        --set "image.tag=session-fix"
        --set "image.pullPolicy=Never"
        --set "secrets.useExistingSecret=true"
        --set "secrets.secretName=api-keys"
        --set "deploymentUpdate.timestamp=$(date +%s)"
    )
    
    # Deploy or upgrade
    if helm list -n "$NAMESPACE" | grep -q "$RELEASE_NAME"; then
        log "Upgrading existing release..."
        helm upgrade "$RELEASE_NAME" "$CHART_PATH" "${helm_args[@]}"
    else
        log "Installing new release..."
        helm install "$RELEASE_NAME" "$CHART_PATH" "${helm_args[@]}"
    fi
    
    success "Helm deployment completed"
}

# =============================================================================
# Health Checks
# =============================================================================

wait_for_pods() {
    step "Waiting for pods to be ready..."
    
    local components=("domain-agent" "technical-agent" "policy-server" "streamlit-ui")
    local start_time=$(date +%s)
    
    for component in "${components[@]}"; do
        log "Waiting for $component to be ready..."
        
        local pod_selector="app.kubernetes.io/name=insurance-ai-poc,component=$component"
        
        if kubectl wait --for=condition=ready pod -l "$pod_selector" -n "$NAMESPACE" --timeout="${POD_READY_TIMEOUT}s"; then
            success "$component is ready"
        else
            error "$component failed to become ready within timeout"
            kubectl get pods -l "$pod_selector" -n "$NAMESPACE"
            kubectl logs -l "$pod_selector" -n "$NAMESPACE" --tail=20
            exit 1
        fi
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    success "All pods ready in ${duration}s"
}

check_pod_health() {
    step "Checking pod health..."
    
    log "Current pod status:"
    kubectl get pods -n "$NAMESPACE" -o wide
    
    log "Checking for any failed pods..."
    local failed_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Failed -o jsonpath='{.items[*].metadata.name}')
    
    if [[ -n "$failed_pods" ]]; then
        error "Failed pods detected: $failed_pods"
        for pod in $failed_pods; do
            echo "Logs for failed pod $pod:"
            kubectl logs "$pod" -n "$NAMESPACE" --tail=50
        done
        exit 1
    fi
    
    success "All pods are healthy"
}

# =============================================================================
# Port Forwarding
# =============================================================================

setup_port_forwarding() {
    step "Setting up port forwarding..."
    
    # Kill any existing port forwards
    log "Cleaning up existing port forwards..."
    pkill -f "kubectl.*port-forward" || true
    sleep 2
    
    # Check if port forward script exists
    if [[ ! -f "$PORT_FORWARD_SCRIPT" ]]; then
        warning "Port forward script not found at $PORT_FORWARD_SCRIPT"
        create_port_forward_script
    fi
    
    # Make script executable
    chmod +x "$PORT_FORWARD_SCRIPT"
    
    # Run port forwarding script
    log "Starting port forwards..."
    if ./"$PORT_FORWARD_SCRIPT"; then
        success "Port forwarding started"
    else
        error "Failed to start port forwarding"
        exit 1
    fi
    
    # Wait a moment for port forwards to establish
    sleep 5
}

create_port_forward_script() {
    log "Creating port forward script..."
    
    cat > "$PORT_FORWARD_SCRIPT" << 'EOF'
#!/bin/bash

echo "🚀 Starting port forwards for Insurance AI POC..."

# Kill any existing port forwards
pkill -f "kubectl port-forward" || true
sleep 2

NAMESPACE="insurance-ai-agentic"

# Start port forwards in background
echo "📱 Starting Streamlit UI on port 8501..."
kubectl port-forward -n "$NAMESPACE" service/insurance-ai-poc-streamlit-ui 8501:80 &

echo "🤖 Starting Domain Agent on port 8003..."
kubectl port-forward -n "$NAMESPACE" service/insurance-ai-poc-domain-agent 8003:8003 &

echo "⚙️ Starting Technical Agent on port 8002..."
kubectl port-forward -n "$NAMESPACE" service/insurance-ai-poc-technical-agent 8002:8002 &

echo "📋 Starting Policy Server on port 8001..."
kubectl port-forward -n "$NAMESPACE" service/insurance-ai-poc-policy-server 8001:8001 &

echo "📊 Starting Monitoring on port 8080..."
kubectl port-forward -n "$NAMESPACE" service/insurance-ai-poc-monitoring 8080:8080 &

# Wait for port forwards to establish
sleep 5

echo ""
echo "✅ All port forwards started!"
echo ""
echo "🌟 Application URLs:"
echo "   🖥️  Streamlit UI:      http://localhost:8501"
echo "   🤖 Domain Agent:      http://localhost:8003"
echo "   ⚙️  Technical Agent:   http://localhost:8002"
echo "   📋 Policy Server:     http://localhost:8001"
echo "   📊 Monitoring:        http://localhost:8080"
echo ""
echo "💡 To stop all port forwards, run: pkill -f 'kubectl port-forward'"
EOF
    
    chmod +x "$PORT_FORWARD_SCRIPT"
    success "Port forward script created"
}

# =============================================================================
# Service Validation
# =============================================================================

validate_services() {
    step "Validating deployed services..."
    
    local services=("8001" "8002" "8003" "8501")
    local service_names=("Policy Server" "Technical Agent" "Domain Agent" "Streamlit UI")
    local all_healthy=true
    
    for i in "${!services[@]}"; do
        local port="${services[$i]}"
        local name="${service_names[$i]}"
        
        log "Testing $name on port $port..."
        
        # Give the service a moment to start
        sleep 2
        
        # Test the service
        if curl -s --max-time 10 "http://localhost:$port/health" > /dev/null 2>&1 || \
           curl -s --max-time 10 "http://localhost:$port/" > /dev/null 2>&1; then
            success "$name is responding"
        else
            error "$name is not responding on port $port"
            all_healthy=false
        fi
    done
    
    if [[ "$all_healthy" == "true" ]]; then
        success "All services are healthy and responding"
    else
        error "Some services are not responding properly"
        warning "Check the logs with: kubectl logs -l app.kubernetes.io/name=insurance-ai-poc -n $NAMESPACE"
        exit 1
    fi
}

# =============================================================================
# Monitoring Setup
# =============================================================================

setup_monitoring() {
    step "Configuring monitoring..."
    
    log "Checking monitoring components..."
    
    # Check if monitoring pods are running
    local monitoring_pods=$(kubectl get pods -n "$NAMESPACE" -l component=monitoring -o jsonpath='{.items[*].metadata.name}')
    
    if [[ -n "$monitoring_pods" ]]; then
        success "Monitoring components are running: $monitoring_pods"
        
        # Test monitoring endpoints if available
        if [[ -n "${LANGFUSE_SECRET_KEY:-}" ]] && [[ -n "${LANGFUSE_PUBLIC_KEY:-}" ]]; then
            info "Langfuse monitoring is configured"
        else
            warning "Langfuse monitoring is not fully configured (missing API keys)"
        fi
        
    else
        warning "No monitoring components found"
    fi
}

# =============================================================================
# Cleanup Functions
# =============================================================================

cleanup_on_error() {
    if [[ $? -ne 0 ]]; then
        error "Deployment failed. Cleaning up..."
        
        # Show recent events
        echo "Recent Kubernetes events:"
        kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
        
        # Show pod statuses
        echo "Pod statuses:"
        kubectl get pods -n "$NAMESPACE"
        
        # Optionally rollback
        read -p "Do you want to rollback the deployment? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            helm rollback "$RELEASE_NAME" -n "$NAMESPACE" || true
        fi
    fi
}

# =============================================================================
# Main Deployment Function
# =============================================================================

deploy() {
    echo "============================================================================="
    echo "🚀 Insurance AI POC - Complete Kubernetes Deployment"
    echo "============================================================================="
    echo ""
    
    local start_time=$(date +%s)
    
    # Set up error handling
    trap cleanup_on_error EXIT
    
    # Run deployment steps
    load_env_file
    check_prerequisites
    validate_environment
    build_docker_image
    setup_namespace
    setup_secrets
    deploy_helm_chart
    wait_for_pods
    check_pod_health
    setup_port_forwarding
    validate_services
    setup_monitoring
    
    # Calculate total deployment time
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    
    echo ""
    echo "============================================================================="
    success "🎉 Deployment completed successfully in ${total_duration}s!"
    echo "============================================================================="
    echo ""
    
    # Display access information
    echo "🌟 Application Access URLs:"
    echo "   🖥️  Streamlit UI:      http://localhost:8501"
    echo "   🤖 Domain Agent:      http://localhost:8003"
    echo "   ⚙️  Technical Agent:   http://localhost:8002"
    echo "   📋 Policy Server:     http://localhost:8001"
    echo "   📊 Monitoring:        http://localhost:8080"
    echo ""
    
    # Display useful commands
    echo "📋 Useful Commands:"
    echo "   View pods:           kubectl get pods -n $NAMESPACE"
    echo "   View logs:           kubectl logs -l app.kubernetes.io/name=insurance-ai-poc -n $NAMESPACE"
    echo "   Stop port forwards:  pkill -f 'kubectl port-forward'"
    echo "   Uninstall:           helm uninstall $RELEASE_NAME -n $NAMESPACE"
    echo ""
    
    # Display test command
    echo "🧪 Test the deployment:"
    echo "   curl -X POST http://localhost:8003/a2a/tasks/send \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"task\": \"ask\", \"parameters\": {\"question\": \"What policies do I have?\", \"customer_id\": \"CUST-2024-001\"}}'"
    echo ""
    
    # Remove error trap since we succeeded
    trap - EXIT
}

# =============================================================================
# Command Line Interface
# =============================================================================

show_help() {
    echo "Insurance AI POC Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy     Full deployment (default)"
    echo "  build      Build Docker image only"
    echo "  secrets    Setup secrets only"
    echo "  ports      Setup port forwarding only"
    echo "  validate   Validate services only"
    echo "  clean      Clean up deployment"
    echo "  help       Show this help"
    echo ""
    echo "Environment Variables:"
    echo "  OPENROUTER_API_KEY   Required: OpenRouter API key"
    echo "  OPENAI_API_KEY       Optional: OpenAI API key"
    echo "  ANTHROPIC_API_KEY    Optional: Anthropic API key"
    echo "  LANGFUSE_SECRET_KEY  Optional: Langfuse secret key"
    echo "  LANGFUSE_PUBLIC_KEY  Optional: Langfuse public key"
    echo ""
    echo "Configuration:"
    echo "  The script automatically loads environment variables from .env file"
    echo "  if it exists in the project root. You can also export variables manually."
    echo ""
    echo "Example .env file:"
    echo "  OPENROUTER_API_KEY=sk-or-v1-xxxxxx"
    echo "  OPENAI_API_KEY=sk-xxxxxx"
    echo "  LANGFUSE_SECRET_KEY=lf_sk_xxxxxx"
    echo "  LANGFUSE_PUBLIC_KEY=lf_pk_xxxxxx"
    echo ""
}

case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "build")
        load_env_file
        check_prerequisites
        build_docker_image
        ;;
    "secrets")
        load_env_file
        check_prerequisites
        validate_environment
        setup_namespace
        setup_secrets
        ;;
    "ports")
        check_prerequisites
        setup_port_forwarding
        ;;
    "validate")
        check_prerequisites
        validate_services
        ;;
    "clean")
        echo "🧹 Cleaning up deployment..."
        pkill -f "kubectl.*port-forward" || true
        helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" || true
        kubectl delete namespace "$NAMESPACE" || true
        success "Cleanup completed"
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac 