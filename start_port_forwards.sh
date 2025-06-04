#!/bin/bash

# Start all port forwards for Insurance AI POC
echo "🚀 Starting port forwards for Insurance AI POC..."

# Kill any existing port forwards
pkill -f "kubectl port-forward" || true
sleep 2

# Start port forwards in background
echo "📱 Starting Streamlit UI on port 8501..."
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-streamlit-ui 8501:80 &

echo "🤖 Starting Domain Agent on port 8003..."
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-domain-agent 8003:8003 &

echo "⚙️ Starting Technical Agent on port 8002..."
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-technical-agent 8002:8002 &

echo "📋 Starting Policy Server on port 8001..."
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-policy-server 8001:8001 &

echo "📊 Starting Monitoring on port 8080..."
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-monitoring 8080:8080 &

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