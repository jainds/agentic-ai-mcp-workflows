#!/bin/bash

# Script to stop all port forwards for Insurance AI POC

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping Insurance AI POC port forwards${NC}"

# Kill all kubectl port-forward processes
pkill -f "kubectl port-forward.*insurance-ai-poc" || true

# Kill specific PIDs if file exists
if [ -f /tmp/insurance-ai-port-forwards.pids ]; then
    source /tmp/insurance-ai-port-forwards.pids
    
    for pid in $STREAMLIT_PID $DOMAIN_PID $TECHNICAL_PID $POLICY_PID; do
        if [ ! -z "$pid" ] && ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null || true
        fi
    done
    
    rm -f /tmp/insurance-ai-port-forwards.pids
fi

# Clean up any remaining processes on our ports
for port in 8501 8003 8002 8001; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
done

echo -e "${GREEN}✅ Port forwards stopped${NC}"
