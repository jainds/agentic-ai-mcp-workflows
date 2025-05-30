#!/bin/bash

# Test script for Kubernetes deployment
set -e

echo "🧪 Testing Kubernetes deployment..."

NAMESPACE="cursor-insurance-ai-poc"

# Get minikube IP if available
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    MINIKUBE_IP=$(minikube ip)
    echo "📡 Minikube IP: $MINIKUBE_IP"
    
    # Test endpoints
    DOMAIN_AGENT_URL="http://$MINIKUBE_IP:30800"
    UI_URL="http://$MINIKUBE_IP:30801"
else
    echo "🔄 Using port-forwarding for testing..."
    # Set up port forwarding for testing
    kubectl port-forward svc/enhanced-domain-agent -n $NAMESPACE 8000:8000 &
    PF_PID1=$!
    kubectl port-forward svc/streamlit-ui -n $NAMESPACE 8501:8501 &
    PF_PID2=$!
    
    sleep 5  # Wait for port forwarding to establish
    
    DOMAIN_AGENT_URL="http://localhost:8000"
    UI_URL="http://localhost:8501"
fi

echo "🔍 Testing services..."

# Test 1: Health checks
echo "Test 1: Health checks"
echo "  Testing Domain Agent health..."
if curl -s "$DOMAIN_AGENT_URL/health" | grep -q "healthy"; then
    echo "  ✅ Domain Agent health check passed"
else
    echo "  ❌ Domain Agent health check failed"
fi

echo "  Testing FastMCP services..."
kubectl get pods -n $NAMESPACE -l component=fastmcp-service -o jsonpath='{.items[*].status.phase}' | grep -q "Running" && echo "  ✅ FastMCP services are running" || echo "  ❌ FastMCP services not running"

# Test 2: Chat functionality
echo "Test 2: Chat functionality"
CHAT_RESPONSE=$(curl -s -X POST "$DOMAIN_AGENT_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my current policy details?", "customer_id": "CUST-123"}' || echo "ERROR")

if echo "$CHAT_RESPONSE" | grep -q "response"; then
    echo "  ✅ Chat endpoint responded successfully"
    echo "  📝 Response preview: $(echo "$CHAT_RESPONSE" | jq -r '.response' 2>/dev/null | head -c 100)..."
else
    echo "  ❌ Chat endpoint failed"
    echo "  📝 Error: $CHAT_RESPONSE"
fi

# Test 3: Agent card
echo "Test 3: Agent card"
if curl -s "$DOMAIN_AGENT_URL/agent-card" | grep -q "name"; then
    echo "  ✅ Agent card endpoint working"
else
    echo "  ❌ Agent card endpoint failed"
fi

# Test 4: Technical agent connectivity
echo "Test 4: Technical agent connectivity"
TECH_AGENTS=$(kubectl get pods -n $NAMESPACE -l component=technical-agent -o jsonpath='{.items[*].status.phase}' | tr ' ' '\n' | grep -c "Running" || echo "0")
echo "  📊 Technical agents running: $TECH_AGENTS/3"

if [ "$TECH_AGENTS" -eq 3 ]; then
    echo "  ✅ All technical agents are running"
else
    echo "  ⚠️  Not all technical agents are running"
fi

# Test 5: UI accessibility
echo "Test 5: UI accessibility"
if curl -s "$UI_URL" | grep -q "Streamlit" || curl -s "$UI_URL/_stcore/health" &>/dev/null; then
    echo "  ✅ Streamlit UI is accessible"
else
    echo "  ❌ Streamlit UI is not accessible"
fi

# Test 6: Logs check
echo "Test 6: Recent logs check"
DOMAIN_LOGS=$(kubectl logs --tail=5 deployment/enhanced-domain-agent -n $NAMESPACE 2>/dev/null | wc -l)
if [ "$DOMAIN_LOGS" -gt 0 ]; then
    echo "  ✅ Domain agent is generating logs"
else
    echo "  ❌ No recent logs from domain agent"
fi

# Cleanup port forwarding if used
if [ -n "$PF_PID1" ]; then
    kill $PF_PID1 $PF_PID2 2>/dev/null || true
fi

echo ""
echo "🎯 Test Summary:"
echo "   Domain Agent URL: $DOMAIN_AGENT_URL"
echo "   Streamlit UI URL: $UI_URL"
echo ""
echo "🔗 Access URLs:"
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
    echo "   🤖 Domain Agent: http://$MINIKUBE_IP:30800"
    echo "   🎨 Streamlit UI: http://$MINIKUBE_IP:30801"
else
    echo "   🤖 Domain Agent: Use 'kubectl port-forward svc/enhanced-domain-agent -n $NAMESPACE 8000:8000'"
    echo "   🎨 Streamlit UI: Use 'kubectl port-forward svc/streamlit-ui -n $NAMESPACE 8501:8501'"
fi

echo ""
echo "✅ Kubernetes deployment testing completed!" 