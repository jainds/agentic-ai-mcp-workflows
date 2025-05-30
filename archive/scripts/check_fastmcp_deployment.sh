#!/bin/bash

echo "🔍 FastMCP Kubernetes Deployment Status"
echo "========================================"

echo ""
echo "📊 Deployment Status:"
kubectl get deployments -n cursor-insurance-ai-poc -l component=fastmcp-service
kubectl get deployments -n cursor-insurance-ai-poc -l component=technical-agent

echo ""
echo "🌐 Service Status:"
kubectl get services -n cursor-insurance-ai-poc -l component=fastmcp-service
kubectl get services -n cursor-insurance-ai-poc -l component=technical-agent

echo ""
echo "🟢 Running Pods:"
kubectl get pods -n cursor-insurance-ai-poc -l component=fastmcp-service --field-selector=status.phase=Running
kubectl get pods -n cursor-insurance-ai-poc -l component=technical-agent --field-selector=status.phase=Running

echo ""
echo "🔍 Pod Health Status:"
kubectl get pods -n cursor-insurance-ai-poc -l component=fastmcp-service -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount"
kubectl get pods -n cursor-insurance-ai-poc -l component=technical-agent -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount"

echo ""
echo "📋 Quick Test Commands:"
echo "  # Test Data Agent:"
echo "  kubectl port-forward svc/fastmcp-data-agent 8004:8004 -n cursor-insurance-ai-poc &"
echo "  curl http://localhost:8004/health"
echo "  curl http://localhost:8004/tools"
echo ""
echo "  # Test User Service FastMCP:"
echo "  kubectl port-forward svc/user-service 8000:8000 -n cursor-insurance-ai-poc &"
echo "  curl -H 'Accept: text/event-stream' http://localhost:8000/mcp/"
echo ""
echo "✅ FastMCP Services Deployment Complete!" 