# 🎯 Insurance AI PoC - Comprehensive Demo Guide

## 🚀 **Demo Access Links**

### **Core Components**
| Component | URL | Description |
|-----------|-----|-------------|
| **Streamlit UI** | http://localhost:8501 | 🎨 Interactive web interface for customer interactions |
| **Domain Agent** | http://localhost:8003 | 🤖 Conversational AI agent (A2A protocol) |
| **Technical Agent** | http://localhost:8002 | ⚙️ Backend data retrieval agent (MCP integration) |
| **Policy Server** | http://localhost:8001 | 📊 FastMCP policy data server |

### **Agent Domain Cards**
| Agent | Agent Card JSON | Interactive Interface |
|-------|----------------|----------------------|
| **Domain Agent** | http://localhost:8003/a2a/agent.json | http://localhost:8003/ |
| **Technical Agent** | http://localhost:8002/a2a/agent.json | http://localhost:8002/ |

### **Monitoring Components**
| System | URL/Status | Functionality |
|--------|------------|---------------|
| **Prometheus Metrics** | ✅ Active | Real-time system metrics collection |
| **Langfuse LLM Observability** | ⚠️ Disabled (needs API keys) | LLM call tracking, token usage, costs |
| **Health Monitoring** | http://localhost:8080 | System health checks |
| **Grafana Dashboards** | 📊 JSON configs available | Pre-built visualization templates |

## 🎭 **Demo Scenarios**

### **Scenario 1: Customer Policy Inquiry via Streamlit UI**

**URL**: http://localhost:8501

**Demo Flow**:
1. Open Streamlit interface
2. Enter customer query: "Customer ID CUST-001, show me my policies"
3. Show real-time response with complete policy details
4. Highlight: Auto insurance, Life insurance, payment schedules, agent contact

**What to Highlight**:
- ✅ Beautiful, modern UI
- ✅ Real-time policy data retrieval
- ✅ Comprehensive insurance information
- ✅ Agent contact details

---

### **Scenario 2: Direct Agent Interaction (A2A Protocol)**

**URL**: http://localhost:8003

**Demo Flow**:
1. Show Agent Card: http://localhost:8003/a2a/agent.json
2. Navigate to: http://localhost:8003/tasks/send
3. Send task:
   ```json
   {
     "message": {
       "content": {
         "text": "Customer CUST-001, what's my coverage amount?"
       }
     }
   }
   ```
4. Show structured response with detailed breakdown

**What to Highlight**:
- ✅ Google A2A protocol compliance
- ✅ Structured agent capabilities
- ✅ Direct API integration
- ✅ Enterprise-ready communication

---

### **Scenario 3: Technical Agent MCP Integration**

**URL**: http://localhost:8002

**Demo Flow**:
1. Show Technical Agent capabilities: http://localhost:8002/
2. Send direct MCP request:
   ```json
   {
     "message": {
       "content": {
         "text": "Get comprehensive policies for customer CUST-001"
       }
     }
   }
   ```
3. Show raw JSON policy data retrieval
4. Demonstrate MCP FastAPI integration

**What to Highlight**:
- ✅ Model Context Protocol (MCP) integration
- ✅ FastAPI backend connectivity
- ✅ Structured data retrieval
- ✅ Real policy database access

---

### **Scenario 4: Intent Analysis & LLM Intelligence**

**Test Queries** (via any interface):
```
1. "What are my premium amounts?"
2. "When is my next payment due?"  
3. "Who is my assigned agent?"
4. "Show me coverage details for auto insurance"
5. "What's the total value of my policies?"
```

**What to Highlight**:
- ✅ Intelligent intent classification
- ✅ Customer ID extraction
- ✅ Context-aware responses
- ✅ Multi-intent handling

---

### **Scenario 5: Monitoring in Action**

**How to Show**:
1. Make several requests through any interface
2. Check logs for monitoring output:
   ```bash
   kubectl logs -n insurance-ai-agentic deployment/insurance-ai-poc-domain-agent --tail=20
   ```

**What to Highlight**:
- ✅ Real-time LLM call tracking
- ✅ Intent analysis monitoring  
- ✅ Request/response timing
- ✅ Success/failure tracking
- ✅ MCP tool call monitoring

## 📊 **Sample Customer Data for Demo**

### **Customer CUST-001 (Primary Demo Customer)**
- **Auto Insurance**: $75,000 coverage, $95 quarterly premium
- **Life Insurance**: $250,000 coverage, $45 monthly premium
- **Agent**: Michael Brown (+1-555-0103)
- **Next Payments**: Auto (Sept 1), Life (June 15)

### **Customer CUST-002** 
- **Home Insurance**: $350,000 coverage
- **Agent**: Sarah Johnson
- **Premium**: $150/month

### **Customer CUST-003**
- **Health Insurance**: $50,000 coverage
- **Agent**: David Wilson  
- **Premium**: $200/month

## 🎯 **Demo Talking Points**

### **Technical Architecture**
- ✅ **Microservices**: Separate domain, technical, and policy components
- ✅ **Kubernetes Native**: Cloud-ready deployment with Helm
- ✅ **Protocol Standards**: Google A2A + Model Context Protocol (MCP)
- ✅ **Enterprise Monitoring**: Prometheus + Langfuse integration
- ✅ **LLM Integration**: OpenRouter with GPT-4o-mini

### **Business Value**
- ✅ **24/7 Availability**: Automated customer service
- ✅ **Real-time Data**: Live policy information
- ✅ **Cost Reduction**: Reduced support ticket volume
- ✅ **Customer Experience**: Instant, accurate responses
- ✅ **Scalability**: Handle thousands of concurrent users

### **Innovation Highlights**
- ✅ **Intent Recognition**: Advanced NLP for customer queries
- ✅ **Multi-Modal**: Web UI + API + Agent protocols
- ✅ **Observability**: Complete monitoring and analytics
- ✅ **Extensibility**: Easy to add new insurance products/features

## 🔧 **Advanced Demo Features**

### **API Testing with cURL**
```bash
# Domain Agent Task
curl -X POST http://localhost:8003/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "Customer CUST-001 premium amounts"}}}'

# Technical Agent Direct Call  
curl -X POST http://localhost:8002/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "Get policies for CUST-001"}}}'
```

### **Agent Card Examination**
```bash
# View agent capabilities
curl http://localhost:8003/a2a/agent.json | jq '.'
curl http://localhost:8002/a2a/agent.json | jq '.'
```

### **Health Check Monitoring**
```bash
# Check system health
kubectl get pods -n insurance-ai-agentic
kubectl logs -n insurance-ai-agentic deployment/insurance-ai-poc-domain-agent --tail=10
```

## 🎬 **Demo Flow Recommendations**

### **5-Minute Demo**
1. **Streamlit UI** - Customer interaction (2 min)
2. **Agent Cards** - Show A2A capabilities (1 min)  
3. **Monitoring** - Live metrics in logs (1 min)
4. **Architecture** - Quick overview (1 min)

### **15-Minute Demo**
1. **Business Context** - Insurance challenges (3 min)
2. **Streamlit Demo** - Multiple customer scenarios (5 min)
3. **Technical Deep Dive** - Agent cards, APIs, MCP (4 min)
4. **Monitoring & Operations** - Enterprise features (2 min)
5. **Q&A** - Technical questions (1 min)

### **30-Minute Demo**
- Include all scenarios above
- Live coding/configuration changes
- Performance testing with multiple requests
- Detailed monitoring dashboard walk-through
- Integration possibilities discussion

## 📝 **Demo Preparation Checklist**

- [ ] All port forwards active (8501, 8003, 8002, 8001)
- [ ] Test each URL accessibility  
- [ ] Prepare sample customer queries
- [ ] Have monitoring logs ready to show
- [ ] Browser tabs open for all components
- [ ] Backup demo data ready
- [ ] Network connectivity confirmed

## 🚨 **Troubleshooting During Demo**

**If Streamlit is slow**: Use direct agent URLs for faster response
**If port forwards fail**: Use `kubectl get svc` and NodePort access
**If monitoring doesn't show**: Explain the architecture instead
**If agents don't respond**: Show the agent cards and capabilities

The system is fully functional and ready for a comprehensive demonstration! 🎉 