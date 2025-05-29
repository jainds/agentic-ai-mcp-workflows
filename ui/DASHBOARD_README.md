# Insurance AI PoC - Comprehensive Dashboard

A sophisticated Streamlit-based dashboard for monitoring and interacting with the Insurance AI Multi-Agent LLM system with Model Context Protocol (MCP) integration.

## 🚀 Features

### Core Functionality
- **Multi-Agent Interaction**: Connect with Claims Agents, Data Agents, or Notification Agents directly
- **Real-time Monitoring**: Live tracking of agent activities, API calls, and system health
- **LLM Thinking Visualization**: See how the AI processes requests step-by-step
- **Comprehensive Analytics**: Performance metrics and workflow statistics
- **Quick Actions**: Pre-configured test scenarios for rapid testing
- **Health Monitoring**: Real-time service health checks and status monitoring

### 📊 Dashboard Tabs

1. **💬 Chat Interface**: Interactive chat with agents and services
2. **🧠 LLM Thinking**: Real-time view of AI processing steps and reasoning
3. **🔍 Agent Activity**: Monitor agent activities, responses, and performance
4. **📡 API Monitor**: Track API calls, response times, and status codes
5. **📊 Analytics**: Performance charts and comprehensive workflow statistics
6. **🏥 System Health**: Health monitoring for all services and agents
7. **🔄 Workflow Viewer**: Visualize system architecture and active workflows

### 🎯 Quick Actions

**Domain Agent Tests:**
- 🔧 Claims Processing workflows
- 🏥 Policy Inquiries and coverage analysis
- 💰 Billing Questions and payment inquiries
- 🚨 Fraud Detection scenarios
- 📞 Customer Support interactions

**Technical Agent Tests:**
- 📊 Risk Assessment and analysis
- 📈 Data Analytics and reporting
- 🔗 System Integration health checks
- ⚡ Performance Analysis and optimization

**MCP Service Direct Tests:**
- 📋 Policy Service operations
- 🏥 Claims Service management
- 👤 Customer Service queries
- 📊 Analytics Service reports

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip package manager
- Running Insurance AI PoC services

### Quick Setup

1. **Install required packages:**
```bash
pip install -r requirements-streamlit.txt
```

2. **Set environment variables (optional):**
```bash
export CLAIMS_AGENT_URL="http://claims-agent:8000"
export DATA_AGENT_URL="http://data-agent:8002"
export NOTIFICATION_AGENT_URL="http://notification-agent:8003"
```

3. **Run the dashboard:**
```bash
python run_dashboard.py
```

Or directly with Streamlit:
```bash
streamlit run streamlit_dashboard.py
```

### Advanced Setup

Use the configuration script for custom setups:

```bash
# Run with custom ports and hosts
python run_dashboard.py --port 8502 --host 0.0.0.0 \
    --claims-agent http://localhost:8000 \
    --data-agent http://localhost:8002 \
    --notification-agent http://localhost:8003

# Run in development mode with auto-reload
python run_dashboard.py --dev

# View all options
python run_dashboard.py --help
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAIMS_AGENT_URL` | `http://claims-agent:8000` | Claims agent service URL |
| `DATA_AGENT_URL` | `http://data-agent:8002` | Data agent service URL |
| `NOTIFICATION_AGENT_URL` | `http://notification-agent:8003` | Notification agent service URL |
| `DASHBOARD_HOST` | `0.0.0.0` | Dashboard bind address |
| `DASHBOARD_PORT` | `8501` | Dashboard port |
| `DEBUG_MODE` | `false` | Enable debug logging |
| `ENABLE_ANALYTICS` | `true` | Enable analytics features |
| `ENABLE_HEALTH_MONITORING` | `true` | Enable health monitoring |
| `ENABLE_AUTO_REFRESH` | `false` | Enable auto-refresh |

### Feature Flags

Control dashboard features via environment variables:

| Feature | Environment Variable | Default |
|---------|---------------------|---------|
| Quick Actions | `FEATURE_QUICK_ACTIONS` | `true` |
| Workflow Visualization | `FEATURE_WORKFLOW_VIZ` | `true` |
| Performance Metrics | `FEATURE_PERFORMANCE_METRICS` | `true` |
| Health Dashboard | `FEATURE_HEALTH_DASHBOARD` | `true` |
| LLM Thinking Viewer | `FEATURE_LLM_THINKING` | `true` |
| API Monitor | `FEATURE_API_MONITOR` | `true` |
| Agent Activity Tracker | `FEATURE_AGENT_ACTIVITY` | `true` |
| Advanced Analytics | `FEATURE_ADVANCED_ANALYTICS` | `true` |

### Custom Configuration

Edit `dashboard_config.py` to customize:
- Service timeouts and retry settings
- UI themes and layouts
- LLM processing parameters
- Security and privacy settings
- Chart configurations and thresholds

## 📋 Usage

### Basic Usage

1. **Start the dashboard** using one of the installation methods above
2. **Open your browser** to `http://localhost:8501`
3. **Select interaction type** in the sidebar:
   - Claims Agent: For insurance claims processing
   - Data Agent: For data operations and analytics
   - Notification Agent: For alerts and notifications

4. **Choose a quick action** or enter custom messages
5. **Monitor real-time activity** across all dashboard tabs

### Advanced Features

#### Custom Agent Calls
Configure custom parameters in the Advanced Options:
- Enable/disable LLM tracing for detailed reasoning
- Enable/disable guardrails for safety
- Adjust max tokens (100-4000)
- Set temperature (0.0-2.0) for response creativity

#### Health Monitoring
The System Health tab provides:
- Real-time service status indicators
- Response time trends and analysis
- Error rate monitoring and alerts
- Performance recommendations

#### Analytics Dashboard
Track comprehensive system performance:
- API response time charts and trends
- Workflow distribution analysis
- Agent performance metrics
- Success rate monitoring and insights

#### Workflow Visualization
Understand system architecture:
- Interactive system architecture diagrams
- Active workflow status tracking
- Pattern analysis and insights
- Performance bottleneck identification

## 🔌 API Integration

The dashboard integrates with three main service types:

### Claims Agent
**Endpoint**: `/process`
**Capabilities**:
- Natural language claim processing
- Fraud detection and analysis
- Policy validation and lookup
- Customer communication orchestration

### Data Agent
**Endpoint**: `/process`
**Capabilities**:
- Customer data retrieval and analysis
- Policy information management
- Claims data processing
- Analytics and reporting

### Notification Agent
**Endpoint**: `/process`
**Capabilities**:
- Email notifications and alerts
- SMS messaging services
- System alerts and monitoring
- Template-based communications

## 🎨 User Interface

### Dashboard Layout
- **Header**: System title and navigation
- **Sidebar**: Configuration options and quick actions
- **Main Area**: Tabbed interface with specialized views
- **Status Bar**: Real-time system status indicators

### Color Coding
- 🟢 **Green**: Healthy services and successful operations
- 🟡 **Yellow**: Warning states and pending operations  
- 🔴 **Red**: Error states and failed operations
- 🔵 **Blue**: Information and system messages

### Interactive Elements
- **Expandable Panels**: Detailed information on demand
- **Real-time Charts**: Live performance visualization
- **Progress Indicators**: Workflow and task progress
- **Status Cards**: Service health and metrics

## 🔧 Troubleshooting

### Common Issues

**Dashboard won't start:**
- Check if all required packages are installed: `pip install -r requirements-streamlit.txt`
- Verify Python version compatibility (3.8+ required)
- Ensure no port conflicts on the specified port (default 8501)

**Services show as offline:**
- Verify service URLs in configuration
- Check if Insurance AI services are running: `kubectl get pods -n cursor-insurance-ai-poc`
- Test connectivity: `curl http://claims-agent:8000/health`

**No data in analytics:**
- Interact with agents to generate data
- Check if analytics features are enabled in configuration
- Verify API calls are being logged in the API Monitor tab

**Performance issues:**
- Reduce max conversation history in config
- Disable auto-refresh if not needed: `ENABLE_AUTO_REFRESH=false`
- Check service response times in System Health tab

### Debug Mode

Enable debug mode for detailed logging:
```bash
export DEBUG_MODE=true
python run_dashboard.py
```

### Health Checks

Test service connectivity:
```bash
# Check claims agent
curl http://claims-agent:8000/health

# Check data agent  
curl http://data-agent:8002/health

# Check notification agent
curl http://notification-agent:8003/health
```

## 🏗️ Development

### Project Structure
```
ui/
├── streamlit_dashboard.py      # Main dashboard application
├── dashboard_config.py         # Configuration management
├── run_dashboard.py           # Startup script with CLI options
├── requirements-streamlit.txt  # Dashboard dependencies
└── DASHBOARD_README.md        # This documentation
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-dashboard-feature`
3. Make your changes and test thoroughly
4. Test with the dashboard in development mode: `python run_dashboard.py --dev`
5. Submit a pull request with detailed description

### Extending the Dashboard

To add new features:

1. **New Quick Actions**: Edit `QUICK_ACTIONS` in `dashboard_config.py`
2. **New Charts**: Add configurations to `CHART_CONFIGS`
3. **New Tabs**: Add to the main tab list in `streamlit_dashboard.py`
4. **New Services**: Update service configurations in `Config` class

### Testing

```bash
# Test with development mode
python run_dashboard.py --dev

# Test with specific configuration
python run_dashboard.py --claims-agent http://localhost:8000 --debug

# Test health monitoring
python -c "from dashboard_config import Config; config = Config(); print(config.services)"
```

## 🔒 Security Considerations

- **Sensitive Data**: The dashboard may display sensitive insurance information
- **Network Access**: Secure your service endpoints with proper authentication
- **Authentication**: Consider adding authentication for production deployments
- **Data Retention**: Configure appropriate log retention policies
- **Access Control**: Implement proper access controls for production use

## ⚡ Performance Optimization

- **Auto-refresh**: Use sparingly to reduce server load and network traffic
- **Log Retention**: Configure appropriate retention periods for API calls and logs
- **Service Timeouts**: Adjust timeouts based on network conditions and service performance
- **Caching**: Consider implementing response caching for frequently accessed data
- **Resource Limits**: Monitor dashboard resource usage in production environments

## 🐛 Known Issues

- **Large Datasets**: Performance may degrade with very large conversation histories
- **Network Latency**: High latency networks may cause timeout issues
- **Browser Compatibility**: Best performance with modern browsers (Chrome, Firefox, Safari)
- **Mobile Responsiveness**: Dashboard is optimized for desktop use

## 📚 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Documentation](https://plotly.com/python/)
- [Insurance AI PoC Architecture Guide](../docs/SYSTEM_STATUS.md)
- [Kubernetes Deployment Guide](../docs/KUBERNETES_DEPLOYMENT_SUMMARY.md)

## 📞 Support

For issues and questions:
1. Check this README and troubleshooting section
2. Review logs in debug mode: `DEBUG_MODE=true python run_dashboard.py`
3. Test individual service endpoints using health check commands
4. Check system health dashboard for service status
5. Create an issue in the project repository with detailed logs

## 📄 License

This dashboard is part of the Insurance AI PoC project. Please refer to the main project license for usage terms and conditions. 