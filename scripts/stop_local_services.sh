#!/bin/bash

# Stop Local Services
echo "🛑 Stopping Insurance AI POC Services"
echo "====================================="

echo "🧹 Stopping all service processes..."
pkill -f "python policy_server/main.py" 2>/dev/null || true
pkill -f "python technical_agent/main.py" 2>/dev/null || true
pkill -f "python domain_agent/main.py" 2>/dev/null || true
pkill -f "streamlit run main_ui.py" 2>/dev/null || true

sleep 2

echo "✅ All services stopped!"
echo ""
echo "📊 Remaining processes (should be empty):"
ps aux | grep -E "(policy_server|technical_agent|domain_agent|streamlit)" | grep -v grep || echo "   None found" 