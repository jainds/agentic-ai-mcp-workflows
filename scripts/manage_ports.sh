#!/bin/bash

# Port Forwarding Management Script for Insurance AI POC
# Usage: ./scripts/manage_ports.sh [start|stop|restart|status]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="insurance-ai-agentic"
APP_NAME="insurance-ai-poc"

# Port configuration
STREAMLIT_LOCAL_PORT=8501
DOMAIN_AGENT_LOCAL_PORT=8003
TECHNICAL_AGENT_LOCAL_PORT=8002
POLICY_SERVER_LOCAL_PORT=8001

PID_FILE="/tmp/insurance-ai-port-forwards.pids"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to stop all port forwards
stop_port_forwards() {
    echo -e "${BLUE}🛑 Stopping all port forwards${NC}"
    
    # Kill kubectl port-forward processes for our app
    pkill -f "kubectl port-forward.*$APP_NAME" || true
    
    # Kill specific PIDs if file exists
    if [ -f "$PID_FILE" ]; then
        source "$PID_FILE"
        
        for pid in $STREAMLIT_PID $DOMAIN_PID $TECHNICAL_PID $POLICY_PID; do
            if [ ! -z "$pid" ] && ps -p $pid > /dev/null 2>&1; then
                echo -e "  Killing PID $pid"
                kill $pid 2>/dev/null || true
            fi
        done
        
        rm -f "$PID_FILE"
    fi
    
    # Clean up any remaining processes on our ports
    for port in $STREAMLIT_LOCAL_PORT $DOMAIN_AGENT_LOCAL_PORT $TECHNICAL_AGENT_LOCAL_PORT $POLICY_SERVER_LOCAL_PORT; do
        if check_port $port; then
            echo -e "  Freeing port $port"
            lsof -ti :$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    sleep 1
    echo -e "${GREEN}✅ Port forwards stopped${NC}"
}

# Function to start port forwards
start_port_forwards() {
    echo -e "${BLUE}🚀 Starting port forwards${NC}"
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        echo -e "${RED}❌ Namespace $NAMESPACE not found. Deploy the application first.${NC}"
        exit 1
    fi
    
    # Check if services are available
    if ! kubectl get service "$APP_NAME-streamlit-ui" -n "$NAMESPACE" >/dev/null 2>&1; then
        echo -e "${RED}❌ Application services not found. Deploy the application first.${NC}"
        exit 1
    fi
    
    # Wait for pods to be ready
    echo -e "${BLUE}⏳ Waiting for pods to be ready${NC}"
    kubectl wait --for=condition=ready pod -l component=streamlit-ui -n "$NAMESPACE" --timeout=60s || {
        echo -e "${YELLOW}⚠️  Streamlit UI pod not ready, continuing anyway${NC}"
    }
    kubectl wait --for=condition=ready pod -l component=domain-agent -n "$NAMESPACE" --timeout=60s || {
        echo -e "${YELLOW}⚠️  Domain Agent pod not ready, continuing anyway${NC}"
    }
    kubectl wait --for=condition=ready pod -l component=technical-agent -n "$NAMESPACE" --timeout=60s || {
        echo -e "${YELLOW}⚠️  Technical Agent pod not ready, continuing anyway${NC}"
    }
    kubectl wait --for=condition=ready pod -l component=policy-server -n "$NAMESPACE" --timeout=60s || {
        echo -e "${YELLOW}⚠️  Policy Server pod not ready, continuing anyway${NC}"
    }
    
    # Start port forwards in background
    echo -e "  Starting Streamlit UI on port $STREAMLIT_LOCAL_PORT"
    kubectl port-forward -n "$NAMESPACE" service/"$APP_NAME"-streamlit-ui "$STREAMLIT_LOCAL_PORT":80 >/dev/null 2>&1 &
    STREAMLIT_PID=$!
    
    echo -e "  Starting Domain Agent on port $DOMAIN_AGENT_LOCAL_PORT"
    kubectl port-forward -n "$NAMESPACE" service/"$APP_NAME"-domain-agent "$DOMAIN_AGENT_LOCAL_PORT":8003 >/dev/null 2>&1 &
    DOMAIN_PID=$!
    
    echo -e "  Starting Technical Agent on port $TECHNICAL_AGENT_LOCAL_PORT"
    kubectl port-forward -n "$NAMESPACE" service/"$APP_NAME"-technical-agent "$TECHNICAL_AGENT_LOCAL_PORT":8002 >/dev/null 2>&1 &
    TECHNICAL_PID=$!
    
    echo -e "  Starting Policy Server on port $POLICY_SERVER_LOCAL_PORT"
    kubectl port-forward -n "$NAMESPACE" service/"$APP_NAME"-policy-server "$POLICY_SERVER_LOCAL_PORT":8001 >/dev/null 2>&1 &
    POLICY_PID=$!
    
    # Save PIDs to file
    cat > "$PID_FILE" << EOF
STREAMLIT_PID=$STREAMLIT_PID
DOMAIN_PID=$DOMAIN_PID
TECHNICAL_PID=$TECHNICAL_PID
POLICY_PID=$POLICY_PID
EOF
    
    # Wait for port forwards to establish
    sleep 3
    
    # Verify port forwards
    echo -e "${BLUE}🔍 Verifying port forwards${NC}"
    local working_count=0
    
    if check_port $STREAMLIT_LOCAL_PORT; then
        echo -e "  ✅ Streamlit UI: http://localhost:$STREAMLIT_LOCAL_PORT"
        working_count=$((working_count + 1))
    else
        echo -e "  ❌ Streamlit UI port forward failed"
    fi
    
    if check_port $DOMAIN_AGENT_LOCAL_PORT; then
        echo -e "  ✅ Domain Agent: http://localhost:$DOMAIN_AGENT_LOCAL_PORT"
        working_count=$((working_count + 1))
    else
        echo -e "  ❌ Domain Agent port forward failed"
    fi
    
    if check_port $TECHNICAL_AGENT_LOCAL_PORT; then
        echo -e "  ✅ Technical Agent: http://localhost:$TECHNICAL_AGENT_LOCAL_PORT"
        working_count=$((working_count + 1))
    else
        echo -e "  ❌ Technical Agent port forward failed"
    fi
    
    if check_port $POLICY_SERVER_LOCAL_PORT; then
        echo -e "  ✅ Policy Server: http://localhost:$POLICY_SERVER_LOCAL_PORT"
        working_count=$((working_count + 1))
    else
        echo -e "  ❌ Policy Server port forward failed"
    fi
    
    if [ $working_count -eq 4 ]; then
        echo -e "${GREEN}🎉 All port forwards are working!${NC}"
    elif [ $working_count -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $working_count out of 4 port forwards are working${NC}"
    else
        echo -e "${RED}❌ No port forwards are working. Check if pods are ready.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Port forwards started${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Port Forward Status${NC}"
    
    if [ -f "$PID_FILE" ]; then
        source "$PID_FILE"
        echo -e "  PID file exists: $PID_FILE"
        
        local active_count=0
        for pid in $STREAMLIT_PID $DOMAIN_PID $TECHNICAL_PID $POLICY_PID; do
            if [ ! -z "$pid" ] && ps -p $pid > /dev/null 2>&1; then
                active_count=$((active_count + 1))
            fi
        done
        echo -e "  Active processes: $active_count/4"
    else
        echo -e "  No PID file found"
    fi
    
    echo ""
    echo -e "${BLUE}Port Status:${NC}"
    
    if check_port $STREAMLIT_LOCAL_PORT; then
        echo -e "  🟢 Port $STREAMLIT_LOCAL_PORT (Streamlit UI): Active - http://localhost:$STREAMLIT_LOCAL_PORT"
    else
        echo -e "  🔴 Port $STREAMLIT_LOCAL_PORT (Streamlit UI): Inactive"
    fi
    
    if check_port $DOMAIN_AGENT_LOCAL_PORT; then
        echo -e "  🟢 Port $DOMAIN_AGENT_LOCAL_PORT (Domain Agent): Active - http://localhost:$DOMAIN_AGENT_LOCAL_PORT"
    else
        echo -e "  🔴 Port $DOMAIN_AGENT_LOCAL_PORT (Domain Agent): Inactive"
    fi
    
    if check_port $TECHNICAL_AGENT_LOCAL_PORT; then
        echo -e "  🟢 Port $TECHNICAL_AGENT_LOCAL_PORT (Technical Agent): Active - http://localhost:$TECHNICAL_AGENT_LOCAL_PORT"
    else
        echo -e "  🔴 Port $TECHNICAL_AGENT_LOCAL_PORT (Technical Agent): Inactive"
    fi
    
    if check_port $POLICY_SERVER_LOCAL_PORT; then
        echo -e "  🟢 Port $POLICY_SERVER_LOCAL_PORT (Policy Server): Active - http://localhost:$POLICY_SERVER_LOCAL_PORT"
    else
        echo -e "  🔴 Port $POLICY_SERVER_LOCAL_PORT (Policy Server): Inactive"
    fi
}

# Function to restart port forwards
restart_port_forwards() {
    echo -e "${BLUE}🔄 Restarting port forwards${NC}"
    stop_port_forwards
    sleep 2
    start_port_forwards
}

# Main script logic
case "${1:-status}" in
    start)
        start_port_forwards
        ;;
    stop)
        stop_port_forwards
        ;;
    restart)
        restart_port_forwards
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "${BLUE}Insurance AI POC Port Forward Manager${NC}"
        echo ""
        echo -e "${YELLOW}Usage: $0 [start|stop|restart|status]${NC}"
        echo ""
        echo -e "Commands:"
        echo -e "  start    - Start all port forwards"
        echo -e "  stop     - Stop all port forwards"
        echo -e "  restart  - Restart all port forwards"
        echo -e "  status   - Show current status (default)"
        echo ""
        echo -e "Ports:"
        echo -e "  $STREAMLIT_LOCAL_PORT  - Streamlit UI (main interface)"
        echo -e "  $DOMAIN_AGENT_LOCAL_PORT  - Domain Agent API"
        echo -e "  $TECHNICAL_AGENT_LOCAL_PORT  - Technical Agent API"
        echo -e "  $POLICY_SERVER_LOCAL_PORT  - Policy Server API"
        exit 1
        ;;
esac 