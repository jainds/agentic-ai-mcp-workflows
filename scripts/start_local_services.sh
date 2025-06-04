#!/bin/bash

# Start Local Services for Session Fix Testing
echo "🚀 Starting Insurance AI POC Services Locally"
echo "=============================================="

# Set environment variables
export ENVIRONMENT="development"
export LOG_LEVEL="INFO"
export TECHNICAL_AGENT_URL="http://localhost:8002"
export POLICY_SERVER_URL="http://localhost:8001"
export DOMAIN_AGENT_URL="http://localhost:8003"

# Override MCP URLs for local development
export POLICY_SERVICE_URL="http://localhost:8001/mcp/"

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python policy_server/main.py" 2>/dev/null || true
pkill -f "python technical_agent/main.py" 2>/dev/null || true
pkill -f "python domain_agent/main.py" 2>/dev/null || true
pkill -f "streamlit run main_ui.py" 2>/dev/null || true

sleep 2

# Start Policy Server
echo "📋 Starting Policy Server on port 8001..."
python policy_server/main.py &
POLICY_PID=$!

sleep 3

# Start Technical Agent
echo "🔧 Starting Technical Agent on port 8002..."
python technical_agent/main.py &
TECH_PID=$!

sleep 3

# Start Domain Agent
echo "🎯 Starting Domain Agent on port 8003..."
python domain_agent/main.py &
DOMAIN_PID=$!

sleep 3

# Start Streamlit UI
echo "🌐 Starting Streamlit UI on port 8501..."
streamlit run main_ui.py --server.port=8501 --server.address=localhost &
UI_PID=$!

sleep 5

echo ""
echo "✅ All services started!"
echo ""
echo "📊 Process IDs:"
echo "   Policy Server: $POLICY_PID"
echo "   Technical Agent: $TECH_PID"
echo "   Domain Agent: $DOMAIN_PID"
echo "   Streamlit UI: $UI_PID"
echo ""
echo "🔗 Service URLs:"
echo "   Policy Server:   http://localhost:8001"
echo "   Technical Agent: http://localhost:8002"
echo "   Domain Agent:    http://localhost:8003"
echo "   Streamlit UI:    http://localhost:8501"
echo ""
echo "🧪 To test the session fix:"
echo "   curl -X POST http://localhost:8003/chat -H 'Content-Type: application/json' -d '{\"message\": \"What are my policies?\", \"session_data\": {\"customer_id\": \"CUST-001\", \"authenticated\": true}}'"
echo ""
echo "🛑 To stop all services:"
echo "   kill $POLICY_PID $TECH_PID $DOMAIN_PID $UI_PID" 