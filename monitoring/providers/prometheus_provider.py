"""
Prometheus Provider Implementation

Implements metrics collection using Prometheus.
Provides comprehensive system and business metrics.
"""

import os
import time
from typing import Dict, Any, Optional
from collections import defaultdict

from ..interfaces.metrics_collector import MetricsCollector, MetricType, APIMetricsCollector


class PrometheusProvider(MetricsCollector, APIMetricsCollector):
    """
    Prometheus implementation for metrics collection.
    
    Optional environment variables:
    - PROMETHEUS_GATEWAY_URL: Push gateway URL for batch metrics
    - PROMETHEUS_JOB_NAME: Job name for metrics (default: insurance-ai-poc)
    """

    def __init__(self):
        """Initialize Prometheus provider."""
        self.gateway_url = os.getenv("PROMETHEUS_GATEWAY_URL")
        self.job_name = os.getenv("PROMETHEUS_JOB_NAME", "insurance-ai-poc")
        
        self._metrics = {}
        self._initialized = False
        
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Prometheus client libraries."""
        try:
            # Import prometheus_client only when needed
            from prometheus_client import Counter, Gauge, Histogram, Summary
            from prometheus_client import CollectorRegistry, push_to_gateway
            
            self._Counter = Counter
            self._Gauge = Gauge  
            self._Histogram = Histogram
            self._Summary = Summary
            self._push_to_gateway = push_to_gateway
            
            self._registry = CollectorRegistry()
            self._initialized = True
            
            # Initialize common metrics
            self._init_common_metrics()
            
        except ImportError:
            print("Warning: prometheus_client package not installed. Metrics collection will be disabled.")
        except Exception as e:
            print(f"Warning: Failed to initialize Prometheus client: {e}")

    def _init_common_metrics(self) -> None:
        """Initialize commonly used metrics."""
        # HTTP request metrics
        self._http_requests_total = self._Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self._registry
        )
        
        self._http_request_duration = self._Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self._registry
        )
        
        # LLM metrics
        self._llm_calls_total = self._Counter(
            'llm_calls_total',
            'Total LLM API calls',
            ['model', 'success'],
            registry=self._registry
        )
        
        self._llm_tokens_total = self._Counter(
            'llm_tokens_total',
            'Total LLM tokens used',
            ['model', 'type'],  # type: prompt, completion, total
            registry=self._registry
        )
        
        self._llm_call_duration = self._Histogram(
            'llm_call_duration_seconds',
            'LLM call duration in seconds',
            ['model'],
            registry=self._registry
        )
        
        # MCP metrics
        self._mcp_calls_total = self._Counter(
            'mcp_calls_total',
            'Total MCP tool calls',
            ['tool_name', 'success'],
            registry=self._registry
        )
        
        self._mcp_call_duration = self._Histogram(
            'mcp_call_duration_seconds',
            'MCP call duration in seconds',
            ['tool_name'],
            registry=self._registry
        )
        
        # Intent analysis metrics
        self._intent_analysis_total = self._Counter(
            'intent_analysis_total',
            'Total intent analyses',
            ['intent', 'method', 'success'],
            registry=self._registry
        )
        
        self._intent_confidence = self._Histogram(
            'intent_confidence_score',
            'Intent analysis confidence scores',
            ['intent', 'method'],
            registry=self._registry
        )

    def is_enabled(self) -> bool:
        """Check if Prometheus is properly configured."""
        return self._initialized

    # MetricsCollector implementation
    def increment_counter(
        self, 
        name: str, 
        value: float = 1.0, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        if not self.is_enabled():
            return

        try:
            if name not in self._metrics:
                self._metrics[name] = self._Counter(
                    name, 
                    f'Custom counter metric: {name}',
                    list(labels.keys()) if labels else [],
                    registry=self._registry
                )
            
            if labels:
                self._metrics[name].labels(**labels).inc(value)
            else:
                self._metrics[name].inc(value)
                
        except Exception as e:
            print(f"Warning: Failed to increment counter {name}: {e}")

    def set_gauge(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric value."""
        if not self.is_enabled():
            return

        try:
            if name not in self._metrics:
                self._metrics[name] = self._Gauge(
                    name,
                    f'Custom gauge metric: {name}',
                    list(labels.keys()) if labels else [],
                    registry=self._registry
                )
            
            if labels:
                self._metrics[name].labels(**labels).set(value)
            else:
                self._metrics[name].set(value)
                
        except Exception as e:
            print(f"Warning: Failed to set gauge {name}: {e}")

    def record_histogram(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a value in a histogram metric."""
        if not self.is_enabled():
            return

        try:
            if name not in self._metrics:
                self._metrics[name] = self._Histogram(
                    name,
                    f'Custom histogram metric: {name}',
                    list(labels.keys()) if labels else [],
                    registry=self._registry
                )
            
            if labels:
                self._metrics[name].labels(**labels).observe(value)
            else:
                self._metrics[name].observe(value)
                
        except Exception as e:
            print(f"Warning: Failed to record histogram {name}: {e}")

    def record_duration(
        self, 
        name: str, 
        duration_seconds: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a duration metric."""
        self.record_histogram(f"{name}_duration_seconds", duration_seconds, labels)

    def record_custom_metric(
        self, 
        name: str, 
        metric_type: MetricType, 
        value: float, 
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a custom metric with specific type."""
        if metric_type == MetricType.COUNTER:
            self.increment_counter(name, value, labels)
        elif metric_type == MetricType.GAUGE:
            self.set_gauge(name, value, labels)
        elif metric_type == MetricType.HISTOGRAM:
            self.record_histogram(name, value, labels)
        # Summary type would require different implementation

    def flush(self) -> None:
        """Push metrics to gateway if configured."""
        if not self.is_enabled() or not self.gateway_url:
            return

        try:
            self._push_to_gateway(
                self.gateway_url, 
                job=self.job_name, 
                registry=self._registry
            )
        except Exception as e:
            print(f"Warning: Failed to push metrics to Prometheus gateway: {e}")

    # APIMetricsCollector implementation
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None
    ) -> None:
        """Record HTTP request metrics."""
        if not self.is_enabled():
            return

        try:
            # Record request count
            self._http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            
            # Record request duration
            self._http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration_seconds)
            
            # Record request/response sizes if provided
            if request_size_bytes is not None:
                self.record_histogram(
                    'http_request_size_bytes',
                    request_size_bytes,
                    {'method': method, 'endpoint': endpoint}
                )
                
            if response_size_bytes is not None:
                self.record_histogram(
                    'http_response_size_bytes',
                    response_size_bytes,
                    {'method': method, 'endpoint': endpoint}
                )
                
        except Exception as e:
            print(f"Warning: Failed to record HTTP request metrics: {e}")

    def record_mcp_call(
        self,
        tool_name: str,
        success: bool,
        duration_seconds: float,
        retry_count: int = 0,
        error: Optional[str] = None
    ) -> None:
        """Record MCP tool call metrics."""
        if not self.is_enabled():
            return

        try:
            # Record call count
            self._mcp_calls_total.labels(
                tool_name=tool_name,
                success=str(success)
            ).inc()
            
            # Record call duration
            self._mcp_call_duration.labels(
                tool_name=tool_name
            ).observe(duration_seconds)
            
            # Record retry count if any
            if retry_count > 0:
                self.record_histogram(
                    'mcp_retry_count',
                    retry_count,
                    {'tool_name': tool_name}
                )
                
            # Record error if present
            if error:
                self.increment_counter(
                    'mcp_errors_total',
                    labels={'tool_name': tool_name, 'error_type': error}
                )
                
        except Exception as e:
            print(f"Warning: Failed to record MCP call metrics: {e}")

    # LLM-specific methods (not in interface but useful)
    def record_llm_metrics(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        duration_seconds: float,
        success: bool
    ) -> None:
        """Record comprehensive LLM metrics."""
        if not self.is_enabled():
            return

        try:
            # Record call count
            self._llm_calls_total.labels(
                model=model,
                success=str(success)
            ).inc()
            
            # Record token usage
            self._llm_tokens_total.labels(model=model, type='prompt').inc(prompt_tokens)
            self._llm_tokens_total.labels(model=model, type='completion').inc(completion_tokens)
            self._llm_tokens_total.labels(model=model, type='total').inc(total_tokens)
            
            # Record call duration
            self._llm_call_duration.labels(model=model).observe(duration_seconds)
            
        except Exception as e:
            print(f"Warning: Failed to record LLM metrics: {e}")

    def record_intent_metrics(
        self,
        intent: str,
        confidence: float,
        method: str,
        success: bool,
        duration_seconds: float
    ) -> None:
        """Record intent analysis metrics."""
        if not self.is_enabled():
            return

        try:
            # Record analysis count
            self._intent_analysis_total.labels(
                intent=intent,
                method=method,
                success=str(success)
            ).inc()
            
            # Record confidence score
            self._intent_confidence.labels(
                intent=intent,
                method=method
            ).observe(confidence)
            
            # Record analysis duration
            self.record_duration(
                'intent_analysis',
                duration_seconds,
                {'intent': intent, 'method': method}
            )
            
        except Exception as e:
            print(f"Warning: Failed to record intent metrics: {e}") 