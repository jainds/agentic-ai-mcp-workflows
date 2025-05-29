# 🛡️ Insurance AI PoC - A2A/MCP Architecture

## Intelligent Insurance Assistant with Proper Agent Orchestration

This project demonstrates a production-ready Insurance AI system using **A2A (Agent-to-Agent)** communication and **MCP (Model Context Protocol)** tools for enterprise integration.

## 🏗️ Architecture Overview

### Proper A2A/MCP Design
```
User → Single Chatbot → Domain Agent → Technical Agents → MCP Tools → Enterprise Systems
```

**Key Principles:**
- 🤖 **Single User Interface**: One chatbot handles all interactions
- 🧠 **Domain Agent Intelligence**: LLM-powered agent makes orchestration decisions
- 🔄 **A2A Communication**: Domain agents call Technical agents automatically
- 🛠️ **MCP Tool Integration**: Technical agents access enterprise systems via MCP
- ✅ **Comprehensive Responses**: Complete solutions, not manual actions

## 🚀 Quick Start

### 1. Access the System
```bash
# The system is deployed and ready
open http://localhost:8503
```

### 2. Chat Naturally
```
Try these conversations:
- "I was in an accident and need to file a claim"
- "What does my policy cover for flood damage?"
- "When is my next payment due?"
- "I want to update my contact information"
```

### 3. Observe AI Orchestration
- Watch the AI thinking process
- See automatic agent orchestration  
- Get comprehensive responses automatically

## 📊 System Status

```bash
# Check all services
kubectl get pods -n cursor-insurance-ai-poc

# Expected output:
NAME                                   READY   STATUS    RESTARTS   AGE
claims-agent-867fc6ff7c-ztntf          1/1     Running   0          98m
data-agent-7858df979f-fj4qn            1/1     Running   0          98m  
notification-agent-8489bf867d-l77jn    1/1     Running   0          98m
simple-insurance-ui-67b977455c-sqjz2   1/1     Running   0          5m
```

## 🔧 System Components

### Domain Agents (LLM-Powered)
- **Claims Agent**: Main orchestrator for insurance operations
  - Analyzes user requests using LLM
  - Creates orchestration plans
  - Calls Technical Agents via A2A protocol

### Technical Agents (MCP Tools)
- **Data Agent**: Enterprise system access via MCP tools
  - Claims Service MCP integration
  - Policy Service MCP integration  
  - Customer Service MCP integration
- **Notification Agent**: Communication via MCP tools
  - Email service integration
  - SMS service integration

### User Interface
- **Simple Chatbot**: Single conversation interface
  - Natural language input
  - Comprehensive AI responses
  - No manual action selection needed

## 💡 Usage Examples

### Claims Processing
```
You: "I was in an accident and need to file a claim"

AI: "I've processed your claim request:
- ✅ Policy validation successful (POL-AUTO-123456)
- ✅ Customer verification completed
- ✅ Fraud risk assessment: Low risk
- 📋 Claim #CLM-2024-001234 created
- 📧 Confirmation email sent
- 🔔 SMS notification sent

Next Steps:
1. Upload photos via our app
2. Schedule inspection appointment  
3. Processing time: 3-5 business days"
```

### Policy Inquiries
```
You: "What does my auto insurance cover?"

AI: "Your policy information:
- 📄 Policy: POL-AUTO-123456
- 🚗 Vehicle: 2022 Honda Accord
- ✅ Liability: $100,000/$300,000
- ✅ Collision: $50,000 deductible $500
- ✅ Comprehensive: $50,000 deductible $250

Would you like me to explain any coverage details?"
```

## 🏗️ Deployment Architecture

### Kubernetes Deployment
- **Namespace**: `cursor-insurance-ai-poc`
- **Services**: Claims Agent, Data Agent, Notification Agent, Simple UI
- **Access**: LoadBalancer services with port forwarding
- **Health Checks**: Configured for all components

### Docker Images
- `insurance-ai/claims-agent:latest` - Domain agent with LLM
- `insurance-ai/data-agent:latest` - Technical agent with MCP tools
- `insurance-ai/notification-agent:latest` - Communication agent
- `insurance-ai/simple-ui:latest` - Single chatbot interface

## 📚 Documentation

### Architecture Guides
- [`docs/PROPER_A2A_ARCHITECTURE_DEPLOYMENT.md`](docs/PROPER_A2A_ARCHITECTURE_DEPLOYMENT.md) - Complete architecture guide
- [`ui/DASHBOARD_README.md`](ui/DASHBOARD_README.md) - UI documentation

### Key Features
- ✅ Single chatbot interface (no manual actions)
- ✅ LLM-powered domain agent orchestration
- ✅ A2A protocol for agent communication
- ✅ MCP tools for enterprise system access
- ✅ Comprehensive automated responses
- ✅ Real-time thinking and orchestration visibility

## 🔧 Development

### Local Testing
```bash
# Check system health
curl http://localhost:8503
curl http://localhost:8000/health

# View logs
kubectl logs deployment/simple-insurance-ui -n cursor-insurance-ai-poc
kubectl logs deployment/claims-agent -n cursor-insurance-ai-poc
```

### Architecture Validation
- ✅ User sees only ONE chat interface
- ✅ No manual service selection required
- ✅ AI automatically determines required actions
- ✅ Domain agent orchestrates all technical agents
- ✅ Technical agents use MCP tools for enterprise access
- ✅ Single comprehensive response per user request

## 🎯 Key Differentiators

### ✅ Correct Implementation
- **User Experience**: Natural conversation with one AI
- **Architecture**: Proper A2A/MCP design patterns
- **Intelligence**: LLM makes orchestration decisions
- **Integration**: MCP tools for enterprise connectivity
- **Response**: Complete solutions automatically

### ❌ Anti-Patterns Avoided
- ❌ Manual action selection in UI
- ❌ Direct API calls from frontend
- ❌ Multi-service selection dropdowns
- ❌ Partial responses requiring manual steps
- ❌ Technical configuration exposed to users

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Main Chatbot** | **http://localhost:8503** | **Primary user interface** |
| Claims Agent API | http://localhost:8000 | Backend domain agent |

## 🎉 Success Metrics

✅ **Proper A2A/MCP Architecture**: Complete implementation  
✅ **Single User Interface**: One chatbot for all needs  
✅ **Intelligent Orchestration**: AI-driven agent coordination  
✅ **Enterprise Integration**: MCP tools for system access  
✅ **User Experience**: Natural language conversations  
✅ **Comprehensive Responses**: Complete solutions automatically  

---

**🚀 Experience intelligent insurance assistance with proper A2A/MCP architecture at http://localhost:8503** 