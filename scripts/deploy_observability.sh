#!/bin/bash
"""
Deploy Observability Stack for Insurance AI Multi-Agent System
Deploys Jaeger, Prometheus, and Grafana for comprehensive monitoring
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Deploying Observability Stack for Insurance AI System${NC}"
echo "==============================================="

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is required but not installed${NC}"
    exit 1
fi

# Check if namespace exists
echo -e "${YELLOW}📋 Checking namespace...${NC}"
if ! kubectl get namespace insurance-poc &> /dev/null; then
    echo -e "${YELLOW}⚠️  Creating insurance-poc namespace...${NC}"
    kubectl create namespace insurance-poc
fi

# Deploy observability stack
echo -e "${YELLOW}🚀 Deploying observability components...${NC}"

# Deploy Jaeger
echo -e "${BLUE}  📊 Deploying Jaeger (Distributed Tracing)...${NC}"
kubectl apply -f ../k8s/manifests/observability.yaml

# Wait for deployments to be ready
echo -e "${YELLOW}⏳ Waiting for deployments to be ready...${NC}"

echo -e "${BLUE}  Waiting for Jaeger...${NC}"
kubectl wait --for=condition=available --timeout=120s deployment/jaeger -n insurance-poc

echo -e "${BLUE}  Waiting for Prometheus...${NC}"
kubectl wait --for=condition=available --timeout=120s deployment/prometheus -n insurance-poc

echo -e "${BLUE}  Waiting for Grafana...${NC}"
kubectl wait --for=condition=available --timeout=120s deployment/grafana -n insurance-poc

# Check deployment status
echo -e "${YELLOW}📋 Checking deployment status...${NC}"
kubectl get pods -n insurance-poc -l 'app in (jaeger,prometheus,grafana)'

# Display access information
echo ""
echo -e "${GREEN}✅ Observability Stack Deployed Successfully!${NC}"
echo "==============================================="
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo ""
echo -e "${GREEN}📊 Jaeger (Distributed Tracing):${NC}"
echo "  🔗 URL: http://localhost:30016"
echo "  📝 Use: View distributed traces across agents"
echo "  🎯 Features: Request flows, latency analysis, error tracking"
echo ""
echo -e "${GREEN}📈 Prometheus (Metrics):${NC}"
echo "  🔗 URL: http://localhost:30090"
echo "  📝 Use: Query metrics and alerts"
echo "  🎯 Features: Agent metrics, LLM usage, workflow success rates"
echo ""
echo -e "${GREEN}📊 Grafana (Dashboards):${NC}"
echo "  🔗 URL: http://localhost:30030"
echo "  👤 Username: admin"
echo "  🔐 Password: admin123"
echo "  📝 Use: Visual dashboards and monitoring"
echo "  🎯 Features: Pre-built insurance agent dashboards"
echo ""

# Example queries
echo -e "${BLUE}📝 Example Prometheus Queries:${NC}"
echo ""
echo "• Agent Request Rate:"
echo "  rate(agent_requests_total[5m])"
echo ""
echo "• LLM Token Usage:"
echo "  sum by (model) (rate(llm_tokens_total[5m]))"
echo ""
echo "• Workflow Success Rate:"
echo "  rate(workflow_executions_total{status=\"success\"}[5m]) / rate(workflow_executions_total[5m]) * 100"
echo ""
echo "• Agent Health Status:"
echo "  agent_health_status"
echo ""

# LangFuse setup instructions
echo -e "${BLUE}🔧 Optional: LangFuse Setup${NC}"
echo "For LLM observability with LangFuse:"
echo "1. Sign up at https://cloud.langfuse.com"
echo "2. Get your API keys"
echo "3. Add to secrets:"
echo "   kubectl create secret generic langfuse-keys -n insurance-poc \\"
echo "     --from-literal=LANGFUSE_PUBLIC_KEY=\"pk-your-key\" \\"
echo "     --from-literal=LANGFUSE_SECRET_KEY=\"sk-your-key\""
echo ""

# Testing instructions
echo -e "${BLUE}🧪 Testing Observability:${NC}"
echo "1. Generate some agent traffic:"
echo "   curl -X POST http://localhost:30008/execute \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"skill_name\": \"HandleClaimInquiry\", \"parameters\": {\"user_message\": \"test\"}}'"
echo ""
echo "2. Check metrics in Prometheus (30090)"
echo "3. View traces in Jaeger (30016)"
echo "4. Monitor dashboards in Grafana (30030)"
echo ""

# Troubleshooting
echo -e "${YELLOW}🔧 Troubleshooting:${NC}"
echo "• Check pod logs: kubectl logs -f deployment/prometheus -n insurance-poc"
echo "• Check services: kubectl get services -n insurance-poc"
echo "• Port forwards: kubectl port-forward svc/grafana 3000:3000 -n insurance-poc"
echo ""

echo -e "${GREEN}🎉 Observability setup complete!${NC}"
echo "The insurance AI system now has comprehensive monitoring capabilities." 