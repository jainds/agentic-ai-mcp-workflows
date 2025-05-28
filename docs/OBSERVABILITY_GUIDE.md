# 🔍 Comprehensive Observability Guide
## Multi-Agent Insurance AI System Monitoring

### 🎯 **Observability Strategy Overview**

Our multi-layer observability approach provides complete visibility into:
- **🤖 Agent Interactions** - Inter-agent communication and workflows
- **🧠 LLM Performance** - Token usage, latency, costs, prompt effectiveness  
- **📊 System Health** - Infrastructure metrics, errors, performance
- **🔄 Business Metrics** - Claim processing success rates, customer satisfaction

---

## 🛠️ **Quick Setup**

### **1. Deploy Observability Stack**
```bash
cd scripts
./deploy_observability.sh
```

### **2. Access Dashboards**
- **📊 Grafana**: http://localhost:30030 (admin/admin123)
- **📈 Prometheus**: http://localhost:30090 
- **🔍 Jaeger**: http://localhost:30016

---

## 📊 **Monitoring Components**

### **🔍 Jaeger - Distributed Tracing**

**Purpose**: Track requests across multiple agents
**Use Cases**:
- Debug slow claim processing workflows
- Identify bottlenecks in multi-agent conversations
- Trace errors through the system

**Key Features**:
```
🌐 Request Flow Visualization
⏱️  End-to-end Latency Analysis  
❌ Error Propagation Tracking
🔗 Agent Communication Chains
```

**Example Traces**:
- `ClaimsDomainAgent` → `ClaimsDataAgent.GetClaimStatus`
- `HandleClaimInquiry` → Intent Detection → ID Extraction → Response Generation

### **📈 Prometheus - Metrics Collection**

**Purpose**: Collect and query time-series metrics
**Use Cases**:
- Monitor agent performance trends
- Track LLM usage and costs
- Set up alerts for system issues

**Key Metrics**:
```yaml
# Agent Communication
agent_requests_total{source_agent, target_agent, skill_name, status}
agent_request_duration_seconds{source_agent, target_agent, skill_name}

# LLM Usage  
llm_requests_total{model, task_type, status}
llm_request_duration_seconds{model, task_type}
llm_tokens_total{model, task_type, token_type}

# Workflow Performance
workflow_executions_total{workflow_type, status}
workflow_duration_seconds{workflow_type}

# System Health
agent_health_status{agent_name}
active_sessions_total
```

### **📊 Grafana - Visual Dashboards**

**Purpose**: Beautiful, interactive dashboards
**Use Cases**:
- Real-time monitoring of agent performance
- Historical analysis of system usage
- Business intelligence on claim processing

**Pre-built Dashboards**:
- **Insurance Agent Overview** - System health at a glance
- **LLM Performance** - Token usage, costs, model comparison
- **Workflow Analysis** - Success rates, processing times
- **Error Tracking** - Failed requests, error patterns

---

## 🧠 **LLM Observability with LangFuse** 

### **Setup (Optional but Recommended)**
1. **Sign up**: https://cloud.langfuse.com
2. **Get API keys** from your LangFuse dashboard
3. **Add to Kubernetes**:
```bash
kubectl create secret generic langfuse-keys -n insurance-poc \
  --from-literal=LANGFUSE_PUBLIC_KEY="pk-..." \
  --from-literal=LANGFUSE_SECRET_KEY="sk-..."
```

### **LangFuse Capabilities**
```
📝 Prompt Engineering Analysis
💰 Cost Tracking by Model
🎯 A/B Testing Different Prompts  
🔄 Conversation Flow Analysis
📊 Token Usage Optimization
⚡ Performance Benchmarking
```

### **Example LangFuse Traces**
- **Intent Detection**: User message → LLM call → Extracted intent
- **Response Generation**: Context + Data → LLM call → Customer response
- **ID Extraction**: Natural language → Structured IDs

---

## 🎯 **Key Metrics to Monitor**

### **🚀 Performance Metrics**
```
📊 Agent Response Time (95th percentile)
Target: < 5 seconds for claim status

🔄 Workflow Success Rate  
Target: > 95% for claim inquiries

⚡ LLM Response Time
Target: < 3 seconds per call

🎯 Intent Detection Accuracy
Target: > 90% correct classification
```

### **💰 Cost Metrics**
```
💵 LLM Token Usage per Day
📈 Cost per Claim Processed
📊 Token Efficiency by Model
🎯 Cost per Customer Interaction
```

### **🔧 Operational Metrics**
```
✅ Agent Health Status (all agents)
🔥 Error Rate by Agent/Skill
📈 Request Volume Trends
⚠️  System Resource Usage
```

---

## 🎯 **Use Case Examples**

### **🔍 Debugging Slow Claims**
1. **Grafana**: Check workflow duration dashboard
2. **Jaeger**: Find slow trace for specific claim
3. **Prometheus**: Query agent communication latency
4. **Root Cause**: Identify bottleneck (LLM, DB, network)

### **💰 LLM Cost Optimization**  
1. **LangFuse**: Analyze token usage by task type
2. **Prometheus**: Compare model performance vs cost
3. **Grafana**: Trend analysis of daily costs
4. **Action**: Switch expensive models for simple tasks

### **📊 Business Intelligence**
1. **Grafana**: Create claim processing KPI dashboard
2. **Prometheus**: Query success rates by workflow
3. **Analysis**: Peak usage times, common failure points
4. **Insights**: Optimize agent allocation, improve prompts

---

## 📝 **Prometheus Query Examples**

### **Agent Performance**
```promql
# Agent request rate (requests/second)
rate(agent_requests_total[5m])

# Average response time by agent
avg by (source_agent) (rate(agent_request_duration_seconds_sum[5m]) / rate(agent_request_duration_seconds_count[5m]))

# Error rate percentage
rate(agent_requests_total{status="error"}[5m]) / rate(agent_requests_total[5m]) * 100
```

### **LLM Usage**
```promql
# Total tokens used per hour
sum by (model) (rate(llm_tokens_total[1h]) * 3600)

# Average LLM response time
avg by (model) (rate(llm_request_duration_seconds_sum[5m]) / rate(llm_request_duration_seconds_count[5m]))

# LLM error rate
rate(llm_requests_total{status="error"}[5m]) / rate(llm_requests_total[5m]) * 100
```

### **Business Metrics**
```promql
# Claim processing success rate
rate(workflow_executions_total{workflow_type="claim_status", status="success"}[5m]) / rate(workflow_executions_total{workflow_type="claim_status"}[5m]) * 100

# Active user sessions
active_sessions_total

# System health score (percentage of healthy agents)
avg(agent_health_status) * 100
```

---

## 🚨 **Alerting Setup**

### **Critical Alerts**
```yaml
# High Error Rate
alert: HighErrorRate
expr: rate(agent_requests_total{status="error"}[5m]) / rate(agent_requests_total[5m]) > 0.05
for: 2m

# Agent Down
alert: AgentDown  
expr: agent_health_status == 0
for: 1m

# High LLM Latency
alert: HighLLMLatency
expr: histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m])) > 10
for: 5m
```

### **Business Alerts** 
```yaml
# Low Success Rate
alert: LowSuccessRate
expr: rate(workflow_executions_total{status="success"}[10m]) / rate(workflow_executions_total[10m]) < 0.90
for: 5m

# High Token Usage (Cost)
alert: HighTokenUsage
expr: rate(llm_tokens_total[1h]) > 100000
for: 10m
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**🔴 Metrics Not Appearing**
```bash
# Check if agents are exposing metrics
kubectl exec -it deployment/claims-agent -n insurance-poc -- curl localhost:9000/metrics

# Check Prometheus targets
curl http://localhost:30090/api/v1/targets
```

**🔴 Traces Not Showing**
```bash
# Check Jaeger connectivity
kubectl logs deployment/jaeger -n insurance-poc

# Verify OpenTelemetry configuration
kubectl exec -it deployment/claims-agent -n insurance-poc -- env | grep JAEGER
```

**🔴 Grafana Dashboard Issues**
```bash
# Check Grafana logs
kubectl logs deployment/grafana -n insurance-poc

# Verify data sources
curl -u admin:admin123 http://localhost:30030/api/datasources
```

### **Performance Tuning**
```bash
# Increase Prometheus retention
# Edit prometheus-config ConfigMap
retention.time=720h  # 30 days

# Scale Jaeger for high volume  
kubectl scale deployment jaeger --replicas=2 -n insurance-poc

# Optimize Grafana queries
# Use recording rules for complex queries
```

---

## 📈 **Advanced Features**

### **Custom Dashboards**
Create specialized dashboards for:
- **Customer Success Team**: Response times, resolution rates
- **DevOps Team**: System health, resource usage  
- **Product Team**: Feature usage, user journeys
- **Finance Team**: LLM costs, operational efficiency

### **Machine Learning Integration**
- **Anomaly Detection**: Use Prometheus data to detect unusual patterns
- **Predictive Scaling**: Forecast load based on historical metrics
- **Quality Scoring**: Track conversation quality over time

### **Integration with External Tools**
- **Slack Alerts**: Critical system notifications
- **PagerDuty**: Incident management integration
- **Jupyter Notebooks**: Advanced analytics and reporting

---

## 🎉 **Best Practices**

### **📊 Dashboard Design**
- ✅ **Focus on Business Metrics** first, technical metrics second
- ✅ **Use Consistent Time Ranges** across related panels
- ✅ **Color Code by Severity** (green=good, yellow=warning, red=critical)
- ✅ **Include Context** with annotations and descriptions

### **📈 Metrics Strategy**
- ✅ **Start Simple** - Monitor key workflows first
- ✅ **Add Labels Carefully** - Too many can impact performance
- ✅ **Use Recording Rules** for expensive queries
- ✅ **Set Meaningful Thresholds** based on business impact

### **🔍 Tracing Best Practices**
- ✅ **Sample Appropriately** - 100% for development, 1-10% for production
- ✅ **Add Business Context** to spans (customer_id, claim_id)
- ✅ **Instrument Key Operations** - LLM calls, database queries, external APIs
- ✅ **Use Structured Logging** with correlation IDs

---

## 🚀 **Getting Started Checklist**

- [ ] Deploy observability stack (`./deploy_observability.sh`)
- [ ] Access Grafana dashboard (http://localhost:30030)
- [ ] Generate test traffic to populate metrics
- [ ] Explore pre-built dashboards
- [ ] Set up LangFuse for LLM observability (optional)
- [ ] Configure alerts for critical metrics
- [ ] Create custom dashboards for your team
- [ ] Document runbooks for common issues

---

**🎯 Result**: Complete visibility into your multi-agent AI system with actionable insights for optimization, debugging, and business intelligence! 