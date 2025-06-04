# Insurance AI Monitoring Suite

A comprehensive monitoring solution for the Insurance AI POC system, providing observability for LLM calls, API performance, MCP connections, and business metrics.

## Overview

The monitoring system follows SOLID principles and provides:

- **LLM Observability**: Track LLM calls, token usage, and performance with Langfuse
- **System Metrics**: Monitor API performance, system health with Prometheus
- **Distributed Tracing**: Trace requests across services with OpenTelemetry
- **Visualization**: Grafana dashboards for comprehensive insights
- **Health Monitoring**: Automated health checks for all components

## Architecture

```
monitoring/
├── interfaces/          # Abstract interfaces (SOLID compliance)
├── providers/           # Concrete implementations
├── middleware/          # Automatic instrumentation
├── setup/              # Configuration and initialization
├── dashboards/         # Grafana dashboard configurations
└── collectors/         # Specialized metric collectors
```

## Supported Tools

### Primary Tools
- **Langfuse**: LLM observability and tracing
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards

### Additional Tools
- **OpenTelemetry**: Distributed tracing
- **Jaeger**: Trace visualization

## Environment Variables

Add these environment variables to your `.env` file:

### Required for Langfuse
```bash
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
```

### Optional for Prometheus
```bash
PROMETHEUS_GATEWAY_URL=http://localhost:9091  # Push gateway URL
PROMETHEUS_JOB_NAME=insurance-ai-poc          # Job name for metrics
```

### Optional for Grafana
```bash
GRAFANA_API_KEY=your_grafana_api_key          # For automated dashboard setup
```

## Quick Start

### 1. Install Dependencies

```bash
pip install langfuse prometheus-client opentelemetry-api opentelemetry-sdk
```

### 2. Initialize Monitoring

```python
from monitoring import MonitoringManager
from monitoring.middleware import add_monitoring_middleware

# Initialize monitoring
monitoring = MonitoringManager()

# Add to FastAPI app
add_monitoring_middleware(app)
```

### 3. Manual Instrumentation

```python
from monitoring.setup.monitoring_setup import get_monitoring_manager

monitoring = get_monitoring_manager()

# Record LLM call
monitoring.record_llm_call(
    model="gpt-4",
    prompt_tokens=100,
    completion_tokens=50,
    total_tokens=150,
    duration_seconds=2.5,
    success=True,
    metadata={"customer_id": "CUST-001", "intent": "policy_inquiry"}
)

# Trace LLM call with context
with monitoring.trace_llm_call("gpt-4", prompt, response) as span:
    span.set_attribute("customer_id", "CUST-001")
    span.set_attribute("intent", "policy_inquiry")
```

## Integration Examples

### Domain Agent Integration

```python
# domain_agent/main.py
from monitoring.setup.monitoring_setup import get_monitoring_manager
import time

monitoring = get_monitoring_manager()

# In your LLM call function
async def analyze_intent_with_llm(text: str) -> dict:
    start_time = time.time()
    
    try:
        # Trace the LLM call
        with monitoring.trace_intent_analysis(text, "", 0.0, "llm") as span:
            response = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            duration = time.time() - start_time
            
            # Record metrics
            monitoring.record_llm_call(
                model="gpt-4",
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                duration_seconds=duration,
                success=True,
                metadata={"function": "intent_analysis", "customer_id": session.get("customer_id")}
            )
            
            # Update span
            span.set_attribute("prompt_tokens", response.usage.prompt_tokens)
            span.set_attribute("completion_tokens", response.usage.completion_tokens)
            
            return parse_intent_response(response.choices[0].message.content)
            
    except Exception as e:
        duration = time.time() - start_time
        monitoring.record_llm_call(
            model="gpt-4",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            duration_seconds=duration,
            success=False,
            error=str(e)
        )
        raise
```

### Technical Agent Integration

```python
# technical_agent/main.py
from monitoring.setup.monitoring_setup import get_monitoring_manager
import time

monitoring = get_monitoring_manager()

# In your MCP call function
async def call_mcp_tool_with_monitoring(tool_name: str, parameters: dict):
    start_time = time.time()
    
    try:
        result = await client.call_tool(tool_name, parameters)
        duration = time.time() - start_time
        
        # Record successful MCP call
        monitoring.record_mcp_call(
            tool_name=tool_name,
            success=True,
            duration_seconds=duration,
            retry_count=0
        )
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        monitoring.record_mcp_call(
            tool_name=tool_name,
            success=False,
            duration_seconds=duration,
            error=str(e)
        )
        raise
```

### FastAPI Middleware (Automatic)

```python
# main.py
from fastapi import FastAPI
from monitoring.middleware import add_monitoring_middleware

app = FastAPI()

# Add monitoring middleware (automatic instrumentation)
add_monitoring_middleware(app, exclude_paths=["/health", "/metrics"])
```

## Metrics Available

### LLM Metrics
- `llm_calls_total`: Total LLM API calls by model and success status
- `llm_tokens_total`: Total tokens used by model and type (prompt/completion/total)
- `llm_call_duration_seconds`: LLM call duration histogram
- `intent_analysis_total`: Intent analysis attempts by intent, method, and success
- `intent_confidence_score`: Intent analysis confidence score distribution

### API Metrics
- `http_requests_total`: Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: HTTP request duration histogram
- `http_request_size_bytes`: HTTP request payload size
- `http_response_size_bytes`: HTTP response payload size

### MCP Metrics
- `mcp_calls_total`: Total MCP tool calls by tool name and success
- `mcp_call_duration_seconds`: MCP call duration histogram
- `mcp_retry_count`: MCP retry attempts
- `mcp_errors_total`: MCP errors by tool name and error type

## Dashboards

### LLM Observability Dashboard
- LLM calls per minute
- Success rates by model
- Token usage trends
- Response time percentiles
- Intent analysis performance

Location: `monitoring/dashboards/grafana/llm_dashboard.json`

### System Dashboard
- API request rates and latencies
- Error rates and status codes
- MCP performance metrics
- System resource usage

### Business Dashboard
- Customer interaction patterns
- Query type distribution
- Resolution rates
- Customer satisfaction metrics

## Health Checks

The monitoring system includes health checks for:

- LLM service availability and performance
- MCP server connectivity and tool availability
- API endpoint health
- Database connectivity
- External dependencies

```python
from monitoring.interfaces.health_checker import HealthChecker

# Check overall system health
health_status = monitoring.check_all_health()
print(f"System Status: {health_status.overall_status}")
```

## Extending the System

### Adding New Providers

1. Implement the relevant interface:
```python
from monitoring.interfaces.metrics_collector import MetricsCollector

class CustomProvider(MetricsCollector):
    def increment_counter(self, name: str, value: float = 1.0, labels: dict = None):
        # Implementation
        pass
```

2. Register in MonitoringManager:
```python
# In monitoring_setup.py
custom_provider = CustomProvider()
self._providers['custom'] = custom_provider
```

### Adding New Metrics

```python
# Custom business metrics
monitoring.record_custom_metric(
    name="customer_satisfaction_score",
    metric_type=MetricType.GAUGE,
    value=4.5,
    labels={"agent": "domain", "customer_type": "premium"}
)
```

## Troubleshooting

### Common Issues

1. **Langfuse not working**: Check environment variables and network connectivity
2. **Prometheus metrics not appearing**: Verify prometheus-client installation
3. **High cardinality warnings**: Review label usage and normalize dynamic values

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("monitoring").setLevel(logging.DEBUG)
```

### Monitoring Status

Check monitoring system status:
```python
status = monitoring.get_monitoring_status()
print(f"Monitoring enabled: {status['initialized']}")
for provider, details in status['providers'].items():
    print(f"{provider}: {'✅' if details['enabled'] else '❌'}")
```

## Performance Considerations

- Monitoring adds minimal overhead (< 1ms per request)
- Metrics are buffered and sent asynchronously
- Failed monitoring calls don't affect application functionality
- Automatic fallback to dummy implementations when providers unavailable

## Security

- API keys stored in environment variables only
- No sensitive data logged in metrics
- Configurable data retention policies
- Optional anonymization of customer data in traces 