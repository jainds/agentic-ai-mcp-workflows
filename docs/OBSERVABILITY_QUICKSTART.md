# Insurance AI Observability - Quick Start Guide

## 🚀 **What You Have Now**

Your insurance AI system now has **production-ready observability** with:

- ✅ **Jaeger** - Distributed tracing (20+ traces captured)
- ✅ **Prometheus** - Metrics collection from 7 services  
- ✅ **Grafana** - Custom insurance dashboards
- ✅ **AlertManager** - Insurance-specific alerts
- ✅ **Custom Metrics** - Agent, LLM, and business KPIs

## 📊 **Access Your Dashboards**

| Service | URL | Login | Purpose |
|---------|-----|-------|---------|
| **Grafana** | http://localhost:30030 | admin/admin123 | Main dashboards |
| **Prometheus** | http://localhost:30090 | None | Raw metrics & queries |
| **Jaeger** | http://localhost:30016 | None | Request tracing |
| **AlertManager** | http://localhost:30093 | None | Alert management |

## 🎯 **Import Your Custom Dashboards**

We created **3 specialized dashboards** for you:

### 1. **Import Business Operations Dashboard**
```bash
# Copy dashboard files to a convenient location
cp /tmp/insurance_business_dashboard.json .
cp /tmp/insurance_technical_dashboard.json .
cp /tmp/insurance_alerts_dashboard.json .
```

### 2. **In Grafana (http://localhost:30030):**
1. Login with **admin/admin123**
2. Click **"+"** → **"Import"**
3. Upload each JSON file:
   - `insurance_business_dashboard.json` - Claims volume, success rates, response times
   - `insurance_technical_dashboard.json` - Service health, performance metrics
   - `insurance_alerts_dashboard.json` - System alerts and monitoring

## 📈 **Key Metrics to Monitor**

### **Business Metrics**
- **Claims Processing Volume**: `rate(workflow_executions_total{workflow_type=~".*claim.*"}[5m])`
- **Success Rate**: `rate(workflow_executions_total{status="success"}[5m]) / rate(workflow_executions_total[5m]) * 100`
- **Response Time**: `histogram_quantile(0.95, rate(workflow_execution_duration_seconds_bucket[5m]))`

### **Technical Metrics**
- **Service Health**: `up{job="insurance-agents"}`
- **HTTP Error Rate**: `rate(http_requests_total{status=~"4..|5.."}[5m])`
- **Memory Usage**: `process_resident_memory_bytes / 1024 / 1024`

### **Agent Communication**
- **Agent Requests**: `rate(agent_requests_total[5m])`
- **LLM Token Usage**: `rate(llm_token_usage_total[5m])`

## 🚨 **Alerts Configured**

Your system will alert on:

| Alert | Threshold | Severity | Action |
|-------|-----------|----------|--------|
| **High Claims Failure Rate** | >0.1/sec for 2m | Critical | Check agent services |
| **Slow Response Time** | >15s (95th %) for 3m | Warning | Scale resources |
| **Service Down** | Any service down 1m | Critical | Restart service |
| **High Error Rate** | >5% HTTP errors for 2m | Warning | Check logs |

## 🧪 **Generate Test Data**

To populate your dashboards with data:

```bash
# Quick test traffic (requires requests module)
curl -X POST http://localhost:30007/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of claim 12345?", "customer_id": 1001}'

# Or use our traffic generator (if requests available)
python3 scripts/generate_test_traffic.py
```

## 🔍 **Useful Prometheus Queries**

Copy these into Prometheus (http://localhost:30090):

```promql
# Service availability
up

# Request rate by agent
rate(agent_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"4..|5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Memory usage in MB
process_resident_memory_bytes / 1024 / 1024

# LLM response times
histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m]))
```

## 📋 **Dashboard Overview**

### **Business Operations Dashboard**
- **Claims Volume**: Real-time claims processing rate
- **Success Rate**: Customer inquiry success percentage  
- **Response Times**: Average and 95th percentile response times
- **Agent Communication**: Flow between different agents
- **Token Usage**: LLM consumption patterns

### **Technical Performance Dashboard**
- **Service Health**: Up/down status of all agents
- **HTTP Metrics**: Request rates, response times, error rates
- **Resource Usage**: Memory, CPU, active connections
- **Error Tracking**: Failed requests and timeouts

### **Alerts Dashboard**
- **Active Alerts**: Current system alerts
- **Failed Claims**: Claims processing failures over time
- **SLA Monitoring**: Response time SLA compliance

## 🔧 **Troubleshooting**

### **No Data in Dashboards?**
1. Check Prometheus targets: http://localhost:30090/targets
2. Verify agent metrics endpoints: `curl http://localhost:8010/metrics`
3. Generate test traffic to create data

### **Services Not Showing Up?**
```bash
# Check service status
kubectl get pods -n insurance-poc

# Restart agents to get metrics endpoints
kubectl rollout restart deployment/customer-agent -n insurance-poc
```

### **Custom Metrics Missing?**
The observability module needs proper initialization. Check agent logs:
```bash
kubectl logs deployment/customer-agent -n insurance-poc
```

## 🚀 **Next Steps**

1. **Configure Slack/Email Alerts**: Update AlertManager config with your webhooks
2. **Set Up LangFuse**: Add your LangFuse API keys for LLM observability
3. **Create Custom Dashboards**: Build specific views for your business needs
4. **Set SLA Targets**: Define your response time and availability goals
5. **Add Business Metrics**: Track claim approval rates, customer satisfaction

## 📚 **Learn More**

- **Full Documentation**: `docs/OBSERVABILITY_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md` 
- **Deployment**: `scripts/deploy_observability.sh`
- **Alert Rules**: `k8s/manifests/alert-rules.yaml`

---

## ✨ **You're All Set!**

Your insurance AI system now has **enterprise-grade observability**. You can:

- 👀 **Monitor** real-time performance
- 📊 **Analyze** business metrics and trends  
- 🚨 **Alert** on critical issues
- 🔍 **Trace** complex workflows
- 📈 **Optimize** based on data

**Happy monitoring!** 🎉 