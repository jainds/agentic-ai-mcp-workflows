#!/bin/bash

# Insurance AI PoC Deployment Script
# Deploys all services and agents to local Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="insurance-poc"
IMAGE_NAME="insurance-ai-poc"
IMAGE_TAG="latest"
REGISTRY="localhost:5000"  # Local registry for Kind
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Service definitions
declare -A SERVICES=(
    ["customer-service"]="8000"
    ["policy-service"]="8001"
    ["claims-service"]="8002"
)

declare -A TECHNICAL_AGENTS=(
    ["customer-agent"]="8010"
    ["policy-agent"]="8011"
    ["claims-agent"]="8012"
)

declare -A DOMAIN_AGENTS=(
    ["support-agent"]="8005"
    ["claims-domain-agent"]="8007"
)

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed"
        exit 1
    fi
    
    # Check if cluster is running
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes cluster is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_namespace() {
    log_info "Setting up namespace: $NAMESPACE"
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace $NAMESPACE
        log_success "Created namespace: $NAMESPACE"
    fi
}

build_docker_image() {
    log_info "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
    
    cd "$PROJECT_ROOT"
    
    # Build the image
    docker build -t $IMAGE_NAME:$IMAGE_TAG .
    
    # Tag for local registry if using Kind
    if kubectl config current-context | grep -q "kind"; then
        log_info "Detected Kind cluster, loading image..."
        kind load docker-image $IMAGE_NAME:$IMAGE_TAG
    fi
    
    log_success "Docker image built and loaded"
}

create_secrets() {
    log_info "Creating secrets..."
    
    # Create OpenRouter API key secret if .env file exists
    if [ -f "$PROJECT_ROOT/.env" ]; then
        # Extract OpenRouter API key from .env
        OPENROUTER_KEY=$(grep "OPENROUTER_API_KEY" "$PROJECT_ROOT/.env" | cut -d'=' -f2 | tr -d '"')
        
        if [ -n "$OPENROUTER_KEY" ] && [ "$OPENROUTER_KEY" != "your_openrouter_api_key_here" ]; then
            kubectl create secret generic openrouter-secret \
                --namespace=$NAMESPACE \
                --from-literal=api-key="$OPENROUTER_KEY" \
                --dry-run=client -o yaml | kubectl apply -f -
            log_success "Created OpenRouter API key secret"
        else
            log_warning "OpenRouter API key not found or using placeholder value"
        fi
    else
        log_warning ".env file not found, skipping OpenRouter secret creation"
    fi
}

create_configmaps() {
    log_info "Creating ConfigMaps..."
    
    # Global configuration
    kubectl create configmap global-config \
        --namespace=$NAMESPACE \
        --from-literal=LOG_LEVEL="INFO" \
        --from-literal=DEBUG="false" \
        --from-literal=PYTHONPATH="/app" \
        --from-literal=PYTHONUNBUFFERED="1" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Service URLs configuration
    kubectl create configmap service-urls \
        --namespace=$NAMESPACE \
        --from-literal=CUSTOMER_SERVICE_URL="http://customer-service:8000" \
        --from-literal=POLICY_SERVICE_URL="http://policy-service:8001" \
        --from-literal=CLAIMS_SERVICE_URL="http://claims-service:8002" \
        --from-literal=CUSTOMER_AGENT_URL="http://customer-agent:8010" \
        --from-literal=POLICY_AGENT_URL="http://policy-agent:8011" \
        --from-literal=CLAIMS_DATA_AGENT_URL="http://claims-agent:8012" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "ConfigMaps created"
}

deploy_services() {
    log_info "Deploying backend services..."
    
    for service in "${!SERVICES[@]}"; do
        port=${SERVICES[$service]}
        log_info "Deploying $service on port $port"
        
        # Create deployment
        cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $service
  namespace: $NAMESPACE
  labels:
    app: $service
    component: backend-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: $service
  template:
    metadata:
      labels:
        app: $service
        component: backend-service
    spec:
      containers:
      - name: $service
        image: $IMAGE_NAME:$IMAGE_TAG
        imagePullPolicy: IfNotPresent
        command:
          - python
          - -m
          - uvicorn
          - services.$(echo $service | cut -d'-' -f1).app:app
          - --host
          - "0.0.0.0"
          - --port
          - "$port"
        ports:
        - containerPort: $port
          name: http
        env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: LOG_LEVEL
        - name: DEBUG
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: DEBUG
        - name: PYTHONPATH
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: PYTHONPATH
        - name: PYTHONUNBUFFERED
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: PYTHONUNBUFFERED
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: $port
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: $port
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: $service
  namespace: $NAMESPACE
  labels:
    app: $service
    component: backend-service
spec:
  type: ClusterIP
  selector:
    app: $service
  ports:
  - port: $port
    targetPort: $port
    protocol: TCP
    name: http
EOF
    done
    
    log_success "Backend services deployed"
}

deploy_technical_agents() {
    log_info "Deploying technical agents..."
    
    for agent in "${!TECHNICAL_AGENTS[@]}"; do
        port=${TECHNICAL_AGENTS[$agent]}
        log_info "Deploying $agent on port $port"
        
        # Create deployment
        cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $agent
  namespace: $NAMESPACE
  labels:
    app: $agent
    component: technical-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $agent
  template:
    metadata:
      labels:
        app: $agent
        component: technical-agent
    spec:
      containers:
      - name: $agent
        image: $IMAGE_NAME:$IMAGE_TAG
        imagePullPolicy: IfNotPresent
        command:
          - python
          - -m
          - agents.technical.$(echo $agent | sed 's/-/_/g')
        ports:
        - containerPort: $port
          name: http
        env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: LOG_LEVEL
        - name: PYTHONPATH
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: PYTHONPATH
        - name: PYTHONUNBUFFERED
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: PYTHONUNBUFFERED
        - name: CUSTOMER_SERVICE_URL
          valueFrom:
            configMapKeyRef:
              name: service-urls
              key: CUSTOMER_SERVICE_URL
        - name: POLICY_SERVICE_URL
          valueFrom:
            configMapKeyRef:
              name: service-urls
              key: POLICY_SERVICE_URL
        - name: CLAIMS_SERVICE_URL
          valueFrom:
            configMapKeyRef:
              name: service-urls
              key: CLAIMS_SERVICE_URL
        - name: $(echo ${agent^^} | tr '-' '_')_PORT
          value: "$port"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: $port
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: $port
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: $agent
  namespace: $NAMESPACE
  labels:
    app: $agent
    component: technical-agent
spec:
  type: ClusterIP
  selector:
    app: $agent
  ports:
  - port: $port
    targetPort: $port
    protocol: TCP
    name: http
EOF
    done
    
    log_success "Technical agents deployed"
}

deploy_domain_agents() {
    log_info "Deploying domain agents..."
    
    for agent in "${!DOMAIN_AGENTS[@]}"; do
        port=${DOMAIN_AGENTS[$agent]}
        module_name=$(echo $agent | sed 's/-/_/g')
        log_info "Deploying $agent on port $port"
        
        # Create deployment
        cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $agent
  namespace: $NAMESPACE
  labels:
    app: $agent
    component: domain-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $agent
  template:
    metadata:
      labels:
        app: $agent
        component: domain-agent
    spec:
      containers:
      - name: $agent
        image: $IMAGE_NAME:$IMAGE_TAG
        imagePullPolicy: IfNotPresent
        command:
          - python
          - -m
          - agents.domain.$module_name
        ports:
        - containerPort: $port
          name: http
        env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: LOG_LEVEL
        - name: PYTHONPATH
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: PYTHONPATH
        - name: PYTHONUNBUFFERED
          valueFrom:
            configMapKeyRef:
              name: global-config
              key: PYTHONUNBUFFERED
        - name: CUSTOMER_AGENT_URL
          valueFrom:
            configMapKeyRef:
              name: service-urls
              key: CUSTOMER_AGENT_URL
        - name: POLICY_AGENT_URL
          valueFrom:
            configMapKeyRef:
              name: service-urls
              key: POLICY_AGENT_URL
        - name: CLAIMS_DATA_AGENT_URL
          valueFrom:
            configMapKeyRef:
              name: service-urls
              key: CLAIMS_DATA_AGENT_URL
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: openrouter-secret
              key: api-key
              optional: true
        - name: $(echo ${agent^^} | tr '-' '_')_PORT
          value: "$port"
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: $port
          initialDelaySeconds: 45
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: $port
          initialDelaySeconds: 15
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: $agent
  namespace: $NAMESPACE
  labels:
    app: $agent
    component: domain-agent
spec:
  type: ClusterIP
  selector:
    app: $agent
  ports:
  - port: $port
    targetPort: $port
    protocol: TCP
    name: http
EOF
    done
    
    log_success "Domain agents deployed"
}

create_nodeport_services() {
    log_info "Creating NodePort services for external access..."
    
    # Customer service NodePort
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: customer-service-nodeport
  namespace: $NAMESPACE
spec:
  type: NodePort
  selector:
    app: customer-service
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30000
    name: http
---
apiVersion: v1
kind: Service
metadata:
  name: support-agent-nodeport
  namespace: $NAMESPACE
spec:
  type: NodePort
  selector:
    app: support-agent
  ports:
  - port: 8005
    targetPort: 8005
    nodePort: 30005
    name: http
---
apiVersion: v1
kind: Service
metadata:
  name: claims-domain-agent-nodeport
  namespace: $NAMESPACE
spec:
  type: NodePort
  selector:
    app: claims-domain-agent
  ports:
  - port: 8007
    targetPort: 8007
    nodePort: 30007
    name: http
EOF
    
    log_success "NodePort services created"
}

wait_for_deployments() {
    log_info "Waiting for deployments to be ready..."
    
    # Wait for all deployments
    kubectl wait --for=condition=available --timeout=300s deployment --all -n $NAMESPACE
    
    log_success "All deployments are ready"
}

check_deployment_status() {
    log_info "Checking deployment status..."
    
    echo
    echo "=== Pods Status ==="
    kubectl get pods -n $NAMESPACE -o wide
    
    echo
    echo "=== Services Status ==="
    kubectl get services -n $NAMESPACE
    
    echo
    echo "=== External Access URLs ==="
    if kubectl config current-context | grep -q "kind"; then
        echo "Customer Service: http://localhost:30000"
        echo "Support Agent: http://localhost:30005"
        echo "Claims Domain Agent: http://localhost:30007"
    else
        NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')
        if [ -z "$NODE_IP" ]; then
            NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
        fi
        echo "Customer Service: http://$NODE_IP:30000"
        echo "Support Agent: http://$NODE_IP:30005"
        echo "Claims Domain Agent: http://$NODE_IP:30007"
    fi
    
    echo
    echo "=== Health Check Examples ==="
    echo "curl http://localhost:30000/health"
    echo "curl http://localhost:30005/health"
    echo "curl http://localhost:30007/health"
    
    echo
    echo "=== API Examples ==="
    echo "# Get customer info:"
    echo "curl http://localhost:30000/customer/101"
    echo
    echo "# Chat with support agent:"
    echo "curl -X POST http://localhost:30005/chat \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"message\": \"What is my policy status?\", \"customer_id\": 101}'"
    echo
    echo "# File a claim:"
    echo "curl -X POST http://localhost:30007/chat \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"message\": \"I want to file a claim for a car accident\", \"customer_id\": 101}'"
}

cleanup() {
    log_info "Cleaning up deployment..."
    
    kubectl delete namespace $NAMESPACE --ignore-not-found=true
    
    log_success "Cleanup completed"
}

run_tests() {
    log_info "Running smoke tests..."
    
    # Wait a bit for services to fully start
    sleep 10
    
    # Test customer service
    if curl -sf http://localhost:30000/health > /dev/null; then
        log_success "Customer service health check passed"
    else
        log_error "Customer service health check failed"
    fi
    
    # Test support agent
    if curl -sf http://localhost:30005/health > /dev/null; then
        log_success "Support agent health check passed"
    else
        log_error "Support agent health check failed"
    fi
    
    # Test claims domain agent
    if curl -sf http://localhost:30007/health > /dev/null; then
        log_success "Claims domain agent health check passed"
    else
        log_error "Claims domain agent health check failed"
    fi
    
    log_success "Smoke tests completed"
}

show_help() {
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  deploy    Deploy all services and agents (default)"
    echo "  cleanup   Remove all deployed resources"
    echo "  status    Show deployment status"
    echo "  test      Run smoke tests"
    echo "  help      Show this help message"
    echo
    echo "Environment variables:"
    echo "  NAMESPACE    Kubernetes namespace (default: insurance-poc)"
    echo "  IMAGE_TAG    Docker image tag (default: latest)"
}

# Main execution
main() {
    local command=${1:-deploy}
    
    case $command in
        deploy)
            check_prerequisites
            setup_namespace
            build_docker_image
            create_secrets
            create_configmaps
            deploy_services
            deploy_technical_agents
            deploy_domain_agents
            create_nodeport_services
            wait_for_deployments
            check_deployment_status
            run_tests
            ;;
        cleanup)
            cleanup
            ;;
        status)
            check_deployment_status
            ;;
        test)
            run_tests
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"