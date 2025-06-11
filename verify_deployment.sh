#!/bin/bash

# Insurance AI POC - Deployment Verification Script
echo "🔍 Insurance AI POC - Deployment Verification"
echo "=============================================="

# Check Kubernetes pods
echo "📋 Checking Kubernetes pods..."
kubectl get pods -n insurance-ai-poc

# Verify all required pods are running
echo ""
echo "🔍 Verifying all required components..."
echo "----------------------------------------"

# Check Domain Agent pod
echo -n "🤖 Domain Agent (Customer Service): "
if kubectl get pods -n insurance-ai-poc | grep -q "domain-agent.*Running"; then
    echo "✅ RUNNING"
else
    echo "❌ NOT RUNNING"
fi

# Check Technical Agent pod
echo -n "⚙️  Technical Agent: "
if kubectl get pods -n insurance-ai-poc | grep -q "technical-agent.*Running"; then
    echo "✅ RUNNING"
else
    echo "❌ NOT RUNNING"
fi

# Check Policy Server pod
echo -n "📋 Policy Server (MCP): "
if kubectl get pods -n insurance-ai-poc | grep -q "policy-server.*Running"; then
    echo "✅ RUNNING"
else
    echo "❌ NOT RUNNING"
fi

# Check Streamlit UI pod
echo -n "🖥️  Streamlit UI: "
if kubectl get pods -n insurance-ai-poc | grep -q "streamlit-ui.*Running"; then
    echo "✅ RUNNING"
else
    echo "❌ NOT RUNNING"
fi

echo ""
echo "🌐 Verifying service accessibility..."
echo "----------------------------------------"

# Test Streamlit UI
echo -n "🖥️  Streamlit UI (8501): "
if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ ACCESSIBLE"
else
    echo "❌ NOT ACCESSIBLE"
fi

# Test Policy Server
echo -n "📋 Policy Server (8001): "
if curl -s http://localhost:8001/mcp > /dev/null 2>&1; then
    echo "✅ ACCESSIBLE"
else
    echo "❌ NOT ACCESSIBLE" 
fi

# Test Domain Agent endpoint
echo -n "🤖 Domain Agent API (8002): "
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "✅ ACCESSIBLE"
else
    echo "❌ NOT ACCESSIBLE"
fi

# Test Technical Agent endpoint
echo -n "⚙️  Technical Agent API (8003): "
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo "✅ ACCESSIBLE"
else
    echo "❌ NOT ACCESSIBLE"
fi

echo ""
echo "🔄 Testing Agent Communication..."
echo "----------------------------------------"

# Test Domain to Technical Agent communication
echo -n "🤖➡️⚙️  Domain to Technical Agent: "
COMMUNICATION_TEST=$(curl -s -X POST http://localhost:8002/test-technical-agent)
if [[ "$COMMUNICATION_TEST" == *"success"* ]]; then
    echo "✅ WORKING"
else
    echo "❌ FAILED"
fi

# Test Technical Agent to MCP connection
echo -n "⚙️➡️📋 Technical Agent to MCP: "
MCP_TEST=$(curl -s -X POST http://localhost:8003/test-mcp-connection)
if [[ "$MCP_TEST" == *"success"* ]]; then
    echo "✅ CONNECTED"
else
    echo "❌ NOT CONNECTED"
fi

echo ""
echo "🚀 Access URLs for Manual Testing:"
echo "   🖥️  Streamlit UI:       http://localhost:8501"
echo "   📋 Policy Server MCP:   http://localhost:8001/mcp"
echo "   🔍 Policy Server Root:  http://localhost:8001/"
echo "   🤖 Domain Agent API:    http://localhost:8002/"
echo "   ⚙️  Technical Agent API: http://localhost:8003/"

echo ""
echo "👥 Test Customer Data Available:"
echo "   CUST001 - John Smith (Auto + Home policies)"
echo "   CUST002 - Jane Doe (Home policy)"
echo "   CUST003 - Bob Johnson (Life insurance)" 
echo "   CUST004 - Alice Williams (Auto policy)"

echo ""
echo "📊 Test Results Summary:"
TOTAL_CHECKS=8
PASSED_CHECKS=$(grep -c "✅" <<< "$(cat /dev/stdin)")
echo "   ✓ $PASSED_CHECKS/$TOTAL_CHECKS checks passed"

if [ $PASSED_CHECKS -eq $TOTAL_CHECKS ]; then
    echo "   ✅ All components running and accessible"
    echo "   ✅ Agent communication verified"
    echo "   ✅ MCP connection confirmed"
    echo "   ✅ System status: PRODUCTION READY"
else
    echo "   ❌ Some checks failed. See details above."
    echo "   ❌ System status: REQUIRES ATTENTION"
fi

echo ""
echo "🎯 Ready for manual testing!" 