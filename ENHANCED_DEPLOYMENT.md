# Enhanced Deployment with Automatic Port Forwarding

## Problem Solved

The original deployment required manual port forwarding setup after each deployment, leading to:
- 🔴 `localhost:8501` not accessible immediately after deployment
- 🔴 Manual kubectl port-forward commands needed every time
- 🔴 Port conflicts and process management issues
- 🔴 Inconsistent access to the application

## Solution Implemented

### 🚀 **Enhanced Deployment Script** (`scripts/deploy.sh`)

The new deployment script automatically:

1. **Cleans up existing port forwards** before deployment
2. **Deploys the application** with latest fixes
3. **Automatically sets up port forwarding** for all services
4. **Verifies connectivity** to ensure everything works
5. **Creates management scripts** for later use

### 🛠️ **Port Management Script** (`scripts/manage_ports.sh`)

Standalone script for managing port forwards independently:

```bash
# Start all port forwards
./scripts/manage_ports.sh start

# Stop all port forwards  
./scripts/manage_ports.sh stop

# Restart all port forwards
./scripts/manage_ports.sh restart

# Check status
./scripts/manage_ports.sh status
```

### 🛑 **Stop Script** (`scripts/stop_port_forwards.sh`)

Automatically created script to cleanly stop all port forwards:

```bash
./scripts/stop_port_forwards.sh
```

## Port Configuration

| Service | Local Port | Kubernetes Port | URL |
|---------|------------|-----------------|-----|
| **Streamlit UI** | 8501 | 80 | http://localhost:8501 |
| **Domain Agent** | 8003 | 8003 | http://localhost:8003 |
| **Technical Agent** | 8002 | 8002 | http://localhost:8002 |
| **Policy Server** | 8001 | 8001 | http://localhost:8001 |

## Features

### 🔧 **Automatic Port Conflict Resolution**
- Detects and kills processes using required ports
- Cleans up orphaned kubectl port-forward processes
- Ensures clean startup every time

### 📊 **Health Verification**
- Waits for pods to be ready before starting port forwards
- Tests connectivity to verify port forwards are working
- Provides clear status feedback

### 💾 **Process Management**
- Saves process IDs for later cleanup
- Tracks all background port-forward processes
- Provides clean shutdown mechanisms

### 🔄 **Robust Restart Logic**
- Can restart individual or all port forwards
- Handles failures gracefully
- Automatic retry mechanisms

## Usage Examples

### 🆕 **New Deployment with Auto Port Forwarding**
```bash
# Deploy and automatically set up port forwarding
./scripts/deploy.sh

# ✅ Application will be immediately accessible at http://localhost:8501
```

### 🔄 **Managing Existing Deployment**
```bash
# Check current port forward status
./scripts/manage_ports.sh status

# Restart port forwards if they're not working
./scripts/manage_ports.sh restart

# Stop all port forwards when done
./scripts/manage_ports.sh stop
```

### 🧹 **Clean Shutdown**
```bash
# Stop all port forwards
./scripts/stop_port_forwards.sh

# Or use the management script
./scripts/manage_ports.sh stop
```

## Troubleshooting

### ❌ **Port Still Not Working?**
```bash
# Check what's using the port
lsof -i :8501

# Restart port forwards
./scripts/manage_ports.sh restart

# Check pod status
kubectl get pods -n insurance-ai-agentic
```

### 🔍 **Debug Port Forward Issues**
```bash
# Check if services exist
kubectl get services -n insurance-ai-agentic

# Check if pods are ready
kubectl get pods -n insurance-ai-agentic

# Manual port forward for debugging
kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-streamlit-ui 8501:80
```

### 🛠️ **Process Management**
```bash
# Check running port forward processes
ps aux | grep "kubectl port-forward"

# Kill all kubectl port forwards
pkill -f "kubectl port-forward"

# Check PID file
cat /tmp/insurance-ai-port-forwards.pids
```

## Benefits

### ✅ **Immediate Access**
- Application accessible at `http://localhost:8501` immediately after deployment
- No manual commands needed

### ✅ **Reliable Operation** 
- Automatic cleanup of conflicting processes
- Robust error handling and retry logic
- Clear status feedback

### ✅ **Easy Management**
- Simple commands to start/stop/restart port forwards
- Status checking and health verification
- Clean shutdown processes

### ✅ **Development Friendly**
- Consistent experience across deployments
- No more manual port-forward setup
- Better developer productivity

## Files Added/Modified

- `scripts/deploy.sh` - Enhanced deployment with auto port forwarding
- `scripts/manage_ports.sh` - Standalone port management
- `scripts/stop_port_forwards.sh` - Auto-generated stop script
- `scripts/deploy_basic.sh` - Original deployment script (backup)

## Next Steps

1. **Deploy**: `./scripts/deploy.sh`
2. **Access**: Open http://localhost:8501 in your browser
3. **Test**: Ask "Show me my auto policy for CUST-001" to verify fixes
4. **Manage**: Use `./scripts/manage_ports.sh` for port management

The system now provides a seamless deployment experience with automatic port forwarding and robust port management! 