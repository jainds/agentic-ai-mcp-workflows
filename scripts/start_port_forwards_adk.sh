#!/bin/bash

# Port forwarding script for Google ADK + LiteLLM + OpenRouter agents
# This script forwards ports for the new Google ADK agent architecture

echo "🚀 Starting port forwards for Google ADK Insurance Agents..."

# Kill any existing port forwards
echo "🧹 Cleaning up existing port forwards..."
pkill -f 'kubectl port-forward' 2>/dev/null || true
sleep 2

# Check if namespace exists
if ! kubectl get namespace insurance-ai-agentic &>/dev/null; then
    echo "⚠️  Namespace 'insurance-ai-agentic' not found. Creating..."
    kubectl create namespace insurance-ai-agentic
fi

echo "🔗 Starting Google ADK agent port forwards..."

# Google ADK Customer Service Agent (Web UI)
echo "📞 Starting ADK Customer Service on port 8000..."
kubectl port-forward -n insurance-ai-agentic service/insurance-adk-customer-service 8000:8000 &
ADK_CUSTOMER_PID=$!

# Google ADK Technical Agent (API Server)
echo "🔧 Starting ADK Technical Agent on port 8001..."
kubectl port-forward -n insurance-ai-agentic service/insurance-adk-technical 8001:8001 &
ADK_TECHNICAL_PID=$!

# Google ADK Orchestrator Agent
echo "🎯 Starting ADK Orchestrator on port 8002..."
kubectl port-forward -n insurance-ai-agentic service/insurance-adk-orchestrator 8002:8002 &
ADK_ORCHESTRATOR_PID=$!

# Policy Server (MCP)
echo "📋 Starting Policy Server (MCP) on port 8003..."
kubectl port-forward -n insurance-ai-agentic service/policy-server 8003:8001 &
POLICY_SERVER_PID=$!

# Streamlit UI
echo "🖥️  Starting Streamlit UI on port 8501..."
kubectl port-forward -n insurance-ai-agentic service/streamlit-ui 8501:8501 &
STREAMLIT_PID=$!

# Wait for port forwards to establish
echo "⏳ Waiting for port forwards to establish..."
sleep 5

echo ""
echo "✅ Google ADK Agents port forwards started!"
echo ""
echo "🌟 Application URLs:"
echo "   🖥️  Google ADK Web UI:        http://localhost:8000"
echo "   📞 ADK Customer Service:      http://localhost:8000/dev-ui/"
echo "   🔧 ADK Technical Agent:       http://localhost:8001"
echo "   🎯 ADK Orchestrator:          http://localhost:8002"
echo "   📋 Policy Server (MCP):       http://localhost:8003/mcp"
echo "   🖼️  Streamlit UI:             http://localhost:8501"
echo ""
echo "🔬 Testing endpoints..."

# Test Google ADK endpoints
echo "Testing ADK Customer Service..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ ADK Customer Service: Ready"
else
    echo "   ⏳ ADK Customer Service: Starting up..."
fi

echo "Testing ADK Technical Agent..."
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✅ ADK Technical Agent: Ready"
else
    echo "   ⏳ ADK Technical Agent: Starting up..."
fi

echo "Testing Policy Server..."
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "   ✅ Policy Server: Ready"
else
    echo "   ⏳ Policy Server: Starting up..."
fi

echo ""
echo "📊 Process IDs:"
echo "   ADK Customer Service: $ADK_CUSTOMER_PID"
echo "   ADK Technical Agent:  $ADK_TECHNICAL_PID"
echo "   ADK Orchestrator:     $ADK_ORCHESTRATOR_PID"
echo "   Policy Server:        $POLICY_SERVER_PID"
echo "   Streamlit UI:         $STREAMLIT_PID"
echo ""
echo "💡 To stop all port forwards, run:"
echo "   pkill -f 'kubectl port-forward'"
echo ""
echo "🎉 Ready to test Google ADK + LiteLLM + OpenRouter integration!"

# Keep script running to monitor port forwards
wait 