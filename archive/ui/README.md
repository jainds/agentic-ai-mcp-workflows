# Insurance AI UI - Modular Architecture

A flexible, component-based Streamlit UI that supports both simple chat and advanced monitoring modes with toggleable features.

## 🏗️ Architecture Overview

```
ui/
├── components/                 # Modular components package
│   ├── __init__.py            # Package exports
│   ├── config.py              # Configuration and feature toggles
│   ├── auth.py                # Authentication logic
│   ├── agent_client.py        # Domain agent communication
│   ├── chat.py                # Chat interface components
│   ├── monitoring.py          # System health and API monitoring
│   └── thinking.py            # LLM thinking steps and orchestration
└── streamlit_app.py           # Main application entry point
```

## 🎛️ Feature Toggles

The UI supports runtime feature configuration via environment variables:

### Core Modes
- `UI_MODE=simple|advanced` - Basic chat vs full monitoring interface

### Feature Flags
- `ENABLE_ADVANCED_FEATURES=true|false` - Master toggle for advanced features
- `ENABLE_SYSTEM_MONITORING=true|false` - Service health monitoring
- `ENABLE_API_MONITORING=true|false` - API call tracking and metrics
- `ENABLE_THINKING_STEPS=true|false` - LLM reasoning visualization
- `ENABLE_ORCHESTRATION_VIEW=true|false` - Agent communication flow

## 🚀 Usage Examples

### Import Specific Components
```python
from ui.components import UIConfig, DomainAgentClient
from ui.components.auth import CustomerValidator
from ui.components.monitoring import check_service_health

# Use components
client = DomainAgentClient()
health = check_service_health()
```

### Import Everything
```python
from ui.components import *

# All components available
config = UIConfig.get_enabled_features()
```

### External Integration
```python
# From any Python file in the project
import sys
sys.path.append('path/to/ui')

from ui.components import render_chat_interface, UIConfig
```

## 🎨 UI Modes

### Simple Mode (`UI_MODE=simple`)
- Clean chat interface
- Basic authentication
- Quick action buttons
- Minimal resource usage

### Advanced Mode (`UI_MODE=advanced`)
- Multi-tab interface
- System health monitoring
- API call tracking
- LLM thinking steps visualization
- Agent orchestration view
- Performance metrics

## 📊 Component Details

### `config.py` - Configuration Management
- Central configuration class
- Environment variable handling
- Feature toggle logic
- Service endpoint definitions

### `auth.py` - Authentication
- Customer validation
- Demo customer database
- Session management
- Login/logout functionality

### `agent_client.py` - Domain Agent Communication
- Real domain agent integration
- Endpoint discovery
- API call logging
- Error handling and fallbacks

### `chat.py` - Chat Interface
- Conversation management
- Message processing
- Quick action buttons
- History tracking

### `monitoring.py` - System Monitoring
- Service health checks
- API call monitoring
- Performance metrics
- Real-time status updates

### `thinking.py` - AI Insights
- LLM thinking steps visualization
- Agent orchestration tracking
- Architecture flow diagrams
- Event logging

## 🔧 Deployment Configurations

### Docker Environment Variables
```dockerfile
ENV UI_MODE=advanced
ENV ENABLE_ADVANCED_FEATURES=true
ENV ENABLE_SYSTEM_MONITORING=true
ENV ENABLE_API_MONITORING=true
ENV ENABLE_THINKING_STEPS=true
ENV ENABLE_ORCHESTRATION_VIEW=true
```

### Kubernetes ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ui-config
data:
  UI_MODE: "advanced"
  ENABLE_ADVANCED_FEATURES: "true"
  # ... other features
```

### Local Development
```bash
# Simple mode
export UI_MODE=simple
streamlit run ui/streamlit_app.py

# Advanced mode with selective features
export UI_MODE=advanced
export ENABLE_THINKING_STEPS=false
streamlit run ui/streamlit_app.py
```

## 🧪 Testing

### Component Testing
```bash
# Test all components
python scripts/test_modular_ui.py

# Test in simple mode
UI_MODE=simple python scripts/test_modular_ui.py

# Test with specific features disabled
ENABLE_MONITORING=false python scripts/test_modular_ui.py
```

### Import Testing
```python
# Verify imports work from external files
from ui.components import UIConfig
print(UIConfig.get_enabled_features())
```

## 🎯 Architecture Flow

```
1. User Input → Chat Interface (chat.py)
2. Authentication → Customer Validation (auth.py)
3. Message Processing → Domain Agent Client (agent_client.py)
4. API Calls → Monitoring & Logging (monitoring.py)
5. LLM Response → Thinking Steps Capture (thinking.py)
6. UI Update → Feature-based Rendering (config.py)
```

## 📝 Key Features

### Modularity
- **Importable Components**: Use any component in external Python files
- **Clean Interfaces**: Well-defined APIs for each component
- **Separation of Concerns**: Each module has a single responsibility

### Flexibility
- **Runtime Configuration**: Change features without code changes
- **Progressive Enhancement**: Simple mode → Advanced mode
- **Selective Features**: Enable only needed monitoring

### Maintainability
- **Type Hints**: Full type annotations
- **Documentation**: Comprehensive docstrings
- **Error Handling**: Graceful fallbacks
- **Logging**: Structured logging throughout

### Performance
- **Conditional Imports**: Load only needed features
- **Resource Scaling**: Different resource requirements per mode
- **Efficient Caching**: Session state management

## 🔄 Switching Modes

### At Runtime (Kubernetes)
```bash
# Switch to simple mode
kubectl patch configmap ui-config -n cursor-insurance-ai-poc -p '{"data":{"UI_MODE":"simple"}}'
kubectl rollout restart deployment/streamlit-ui -n cursor-insurance-ai-poc

# Switch back to advanced mode
kubectl patch configmap ui-config -n cursor-insurance-ai-poc -p '{"data":{"UI_MODE":"advanced"}}'
kubectl rollout restart deployment/streamlit-ui -n cursor-insurance-ai-poc
```

### Development
```bash
# Simple mode for basic testing
UI_MODE=simple streamlit run ui/streamlit_app.py

# Advanced mode for full debugging
UI_MODE=advanced streamlit run ui/streamlit_app.py

# Custom feature mix
UI_MODE=advanced ENABLE_THINKING_STEPS=false ENABLE_API_MONITORING=true streamlit run ui/streamlit_app.py
```

## 📋 Best Practices

1. **Import Only What You Need**: Use specific imports for better performance
2. **Check Feature Flags**: Always check `UIConfig` before using optional features
3. **Handle Gracefully**: Ensure components work when features are disabled
4. **Use Type Hints**: Maintain type safety across components
5. **Test Both Modes**: Verify functionality in simple and advanced modes

## 🎮 Demo Usage

The UI includes demo customers for testing:
- `CUST-001` - John Smith (Premium)
- `CUST-002` - Jane Doe (Standard)
- `CUST-003` - Bob Johnson (Basic)
- `TEST-CUSTOMER` - Test User (Demo)

## 🌟 Benefits

### For Development
- **Fast Iteration**: Test with minimal features enabled
- **Debugging**: Advanced mode shows full system internals
- **Component Reuse**: Import components in tests and scripts

### For Production
- **Resource Optimization**: Simple mode uses fewer resources
- **User Experience**: Progressive disclosure of complexity
- **Operational Flexibility**: Toggle features based on needs

### For Testing
- **Isolated Testing**: Test individual components
- **Integration Testing**: Full end-to-end with all features
- **Performance Testing**: Compare simple vs advanced modes 