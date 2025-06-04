# 📊 Monitoring Demo Reference Card

## 🔍 **Live Monitoring Commands**

### **Real-time Logs**
```bash
# Domain Agent monitoring
kubectl logs -n insurance-ai-agentic deployment/insurance-ai-poc-domain-agent --tail=10 -f

# Technical Agent monitoring  
kubectl logs -n insurance-ai-agentic deployment/insurance-ai-poc-technical-agent --tail=10 -f

# All pods status
kubectl get pods -n insurance-ai-agentic
```

### **What to Look For in Logs**

**Domain Agent Monitoring**:
- ✅ `INFO:httpx:HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"`
- ✅ `🔥 DOMAIN AGENT: Intent analysis result: {confidence: 0.9, method: "llm"}`
- ✅ `🔥 DOMAIN AGENT: Processing message: Customer ID CUST-001...`

**Technical Agent Monitoring**:
- ✅ `INFO:__main__:MCP call successful on attempt 1`
- ✅ `INFO:httpx:HTTP Request: POST http://insurance-ai-poc-policy-server:8001/mcp/ "HTTP/1.1 200 OK"`
- ✅ `INFO:__main__:Successfully retrieved 3 policies for customer CUST-001`

## 📈 **Monitoring Features Active**

| Feature | Status | What It Tracks |
|---------|--------|---------------|
| **Prometheus Metrics** | ✅ Active | System performance, request counts, duration |
| **Intent Analysis** | ✅ Active | Confidence scores, method comparison (LLM vs rules) |
| **LLM Call Tracking** | ✅ Active | Token usage, response times, success rates |
| **MCP Monitoring** | ✅ Active | Tool calls, retries, data retrieval performance |
| **Request Tracing** | ✅ Active | End-to-end request flow, timing |
| **Error Tracking** | ✅ Active | Failure patterns, retry logic |

## 🎯 **Demo Monitoring Scenarios**

### **Scenario 1: Show LLM Monitoring**
1. Send request: "Customer CUST-001, what are my policies?"
2. Show log output with LLM call tracking
3. Point out: Token usage, response time, success status

### **Scenario 2: Show MCP Monitoring**  
1. Send direct technical agent request
2. Show MCP connection logs
3. Point out: Session management, data retrieval, performance

### **Scenario 3: Show Intent Analysis**
1. Send different types of queries
2. Show confidence scores and methods
3. Compare LLM vs rule-based analysis

## 🚨 **Quick Monitoring Demo Commands**

```bash
# Show monitoring is active
kubectl exec -n insurance-ai-agentic deployment/insurance-ai-poc-domain-agent -- python -c "
from monitoring.setup.monitoring_setup import get_monitoring_manager
monitoring = get_monitoring_manager()
print(f'Monitoring enabled: {monitoring.is_monitoring_enabled()}')
status = monitoring.get_monitoring_status()
print(f'Active providers: {list(status[\"providers\"].keys())}')
"

# Test request with monitoring
curl -X POST http://localhost:8003/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"content": {"text": "Customer CUST-001 policies"}}}'

# Show the logs immediately after
kubectl logs -n insurance-ai-agentic deployment/insurance-ai-poc-domain-agent --tail=5
```

## 📊 **Grafana Dashboard Files**

Located in: `monitoring/dashboards/grafana/`
- `llm_dashboard.json` - LLM performance metrics
- `system_dashboard.json` - System performance metrics

**Demo Note**: "These JSON files can be imported directly into Grafana for production monitoring dashboards"

## 🔧 **Monitoring Architecture Highlights**

- **Zero-Impact Design**: Monitoring never affects core functionality
- **Multiple Providers**: Prometheus (metrics) + Langfuse (LLM observability)  
- **SOLID Principles**: Modular, extensible architecture
- **Production Ready**: Enterprise-grade monitoring capabilities
- **Real-time**: Live metrics collection on every request

## ⚡ **Quick Demo Tips**

1. **Start monitoring logs BEFORE making requests** for best effect
2. **Use multiple browser tabs** to show real-time log updates
3. **Point out specific log entries** that show monitoring data
4. **Explain that Langfuse would show even more detail** with API keys
5. **Mention production alerting capabilities** built on these metrics 