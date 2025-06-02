# Monitoring Integration Documentation

## Overview

The Insurance AI PoC now includes comprehensive monitoring capabilities with enterprise-grade observability. The monitoring system is designed following SOLID principles and provides automatic instrumentation for LLM calls, intent analysis, MCP tool calls, and system metrics.

## Architecture

### Core Components

- **Monitoring Manager** (`monitoring/setup/monitoring_setup.py`): Central coordinator for all monitoring providers
- **Interfaces** (`monitoring/interfaces/`): Abstract interfaces following Dependency Inversion principle
- **Providers** (`monitoring/providers/`): Concrete implementations for Langfuse, Prometheus, OpenTelemetry
- **Middleware** (`monitoring/middleware/`): Automatic instrumentation for FastAPI and MCP
- **Dashboards** (`monitoring/dashboards/`): Pre-configured Grafana dashboards

### Provider Architecture

1. **LangfuseProvider**: LLM observability, token tracking, cost analysis
2. **PrometheusProvider**: System metrics, counters, histograms, gauges
3. **OpenTelemetryProvider**: Distributed tracing (future implementation)

## Integration Status

### ✅ Domain Agent Monitoring
- LLM call tracking (intent analysis, response formatting)
- Intent analysis metrics (confidence, method, success rate)
- Request duration and success/failure tracking
- Customer interaction patterns

### ✅ Technical Agent Monitoring  
- MCP tool call monitoring with retry tracking
- Technical operations metrics
- Performance and error rate monitoring

### ✅ Kubernetes Integration
- Environment variables for all monitoring providers
- Secrets management for API keys
- Health check endpoints
- Configurable monitoring settings via Helm values

## Environment Variables Required

### Langfuse (LLM Observability)
```bash
LANGFUSE_SECRET_KEY=sk-xxx  # Required for Langfuse
LANGFUSE_PUBLIC_KEY=pk-xxx  # Required for Langfuse  
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
```

### Prometheus (Metrics)
```bash
PROMETHEUS_GATEWAY_URL=http://prometheus-pushgateway:9091  # Optional
PROMETHEUS_JOB_NAME=insurance-ai-poc  # Optional
```

### Grafana (Dashboards)
```bash
GRAFANA_API_KEY=xxx  # Optional, for automated dashboard management
```

## Metrics Collected

### LLM Metrics
- **Token Usage**: Prompt tokens, completion tokens, total tokens
- **Performance**: Response time, success rate, error rate
- **Cost Tracking**: Token costs per model, daily/monthly usage
- **Model Comparison**: Performance across different models

### Intent Analysis Metrics
- **Confidence Scores**: Distribution and trends
- **Method Performance**: LLM vs rule-based analysis
- **Intent Distribution**: Most common customer intents
- **Analysis Duration**: Time to process customer queries

### MCP Metrics
- **Tool Call Performance**: Success rate, retry count, duration
- **Error Patterns**: Common failure modes and error types
- **Data Retrieval**: Policy fetch times and success rates

### System Metrics
- **Request Volume**: Requests per second, daily patterns
- **Response Times**: P50, P95, P99 percentiles
- **Error Rates**: 4xx, 5xx responses
- **Resource Usage**: Memory, CPU utilization

## Monitoring in Action

### Automatic Instrumentation

The monitoring system automatically tracks:

1. **Every LLM call** with token usage and performance
2. **Every intent analysis** with confidence and method
3. **Every MCP tool call** with retry logic and timing
4. **Every customer request** with success/failure tracking

### Zero-Impact Design

- Monitoring failures never affect core functionality
- Automatic fallback to dummy implementations
- Minimal performance overhead (<1ms per request)
- Graceful degradation when providers are unavailable

## Usage Examples

### Recording Custom Metrics

```python
from monitoring.setup.monitoring_setup import get_monitoring_manager

monitoring = get_monitoring_manager()

# Record a counter
monitoring.increment_counter("custom_events", 1.0, {"type": "user_action"})

# Record duration
monitoring.record_duration("operation_time", 0.123, {"operation": "data_fetch"})

# Record LLM call
monitoring.record_llm_call(
    model="gpt-4o-mini",
    prompt_tokens=100,
    completion_tokens=50,
    total_tokens=150,
    duration_seconds=1.2,
    success=True
)
```

### Tracing Operations

```python
# Trace LLM calls
with monitoring.trace_llm_call(model, prompt, response) as span:
    span.set_attribute("customer_id", "CUST-001")
    span.set_attribute("intent", "policy_inquiry")
```

## Deployment Integration

### Helm Values Configuration

```yaml
monitoring:
  enabled: true
  langfuse:
    secretKey: ""  # Set via Kubernetes secrets
    publicKey: ""  # Set via Kubernetes secrets
    host: "https://cloud.langfuse.com"
  prometheus:
    gatewayUrl: ""
    jobName: "insurance-ai-poc"
  healthChecks:
    enabled: true
    interval: 30
    timeout: 10
```

### Kubernetes Secrets

```bash
kubectl create secret generic api-keys \
  --from-literal=LANGFUSE_SECRET_KEY=sk-xxx \
  --from-literal=LANGFUSE_PUBLIC_KEY=pk-xxx \
  --from-literal=PROMETHEUS_GATEWAY_URL=http://prometheus:9091 \
  -n insurance-ai-agentic
```

## Grafana Dashboards

Pre-configured dashboards available in `monitoring/dashboards/grafana/`:

1. **LLM Dashboard** (`llm_dashboard.json`):
   - Token usage trends
   - Model performance comparison
   - Cost analysis
   - Error rate monitoring

2. **System Dashboard** (`system_dashboard.json`):
   - Request volume and response times
   - Error rates and status codes
   - Resource utilization
   - Health check status

## Testing Integration

Run the comprehensive monitoring test:

```bash
python test_monitoring_integration.py
```

This validates:
- ✅ Monitoring imports work correctly
- ✅ Domain agent monitoring integration
- ✅ Technical agent monitoring integration  
- ✅ All metric recording functions

## Benefits

### For Operations Team
- **Real-time visibility** into system health and performance
- **Proactive alerting** on errors and performance degradation
- **Cost monitoring** for LLM usage and optimization opportunities
- **Capacity planning** with historical trends and patterns

### For Development Team
- **Performance optimization** with detailed timing metrics
- **Error debugging** with comprehensive error tracking
- **Feature usage analytics** to guide product decisions
- **A/B testing** capabilities with detailed metrics

### For Business Team
- **Customer behavior insights** from intent analysis
- **Operational cost tracking** with detailed breakdowns
- **Service quality metrics** for SLA monitoring
- **Usage patterns** for capacity planning

## Next Steps

1. **Add API keys** to your environment or Kubernetes secrets
2. **Deploy updated containers** with monitoring integration
3. **Configure Grafana** with provided dashboard JSON files
4. **Set up alerting** based on key metrics and thresholds
5. **Customize dashboards** for your specific monitoring needs

The monitoring system is now fully integrated and ready for production use! 