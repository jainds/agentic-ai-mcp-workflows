"""
Monitoring Setup Manager

Central manager for initializing and coordinating all monitoring components.
Follows Dependency Inversion principle by depending on abstractions.
"""

import os
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

from ..interfaces.metrics_collector import MetricsCollector, LLMMetricsCollector, APIMetricsCollector
from ..interfaces.trace_provider import TraceProvider, LLMTraceProvider, MCPTraceProvider
from ..interfaces.health_checker import HealthChecker, LLMHealthChecker, MCPHealthChecker, APIHealthChecker
from ..providers.langfuse_provider import LangfuseProvider
from ..providers.prometheus_provider import PrometheusProvider


class MonitoringManager:
    """
    Central monitoring manager that coordinates all monitoring components.
    
    Follows Single Responsibility principle by managing only monitoring setup.
    Follows Open/Closed principle by allowing easy addition of new providers.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize monitoring manager with optional configuration.
        
        Args:
            config: Optional configuration dict, defaults to environment variables
        """
        self.config = config or {}
        self._providers = {}
        self._initialized = False
        
        # Initialize providers based on configuration
        self._setup_providers()

    def _setup_providers(self) -> None:
        """Set up monitoring providers based on configuration."""
        # Setup Langfuse for LLM observability
        if self._is_langfuse_enabled():
            langfuse = LangfuseProvider()
            if langfuse.is_enabled():
                self._providers['langfuse'] = langfuse
                print("✅ Langfuse LLM observability enabled")
            else:
                print("⚠️  Langfuse configured but failed to initialize")
        else:
            print("ℹ️  Langfuse disabled (missing LANGFUSE_SECRET_KEY or LANGFUSE_PUBLIC_KEY)")

        # Setup Prometheus for metrics
        prometheus = PrometheusProvider()
        if prometheus.is_enabled():
            self._providers['prometheus'] = prometheus
            print("✅ Prometheus metrics collection enabled")
        else:
            print("⚠️  Prometheus failed to initialize")

        self._initialized = True

    def _is_langfuse_enabled(self) -> bool:
        """Check if Langfuse is configured via environment variables."""
        return bool(
            os.getenv("LANGFUSE_SECRET_KEY") and 
            os.getenv("LANGFUSE_PUBLIC_KEY")
        )

    def get_metrics_collector(self) -> Optional[MetricsCollector]:
        """Get the primary metrics collector (Prometheus)."""
        return self._providers.get('prometheus')

    def get_llm_metrics_collector(self) -> Optional[LLMMetricsCollector]:
        """Get LLM-specific metrics collector."""
        # Langfuse provides LLM metrics, Prometheus can supplement
        return self._providers.get('langfuse')

    def get_api_metrics_collector(self) -> Optional[APIMetricsCollector]:
        """Get API-specific metrics collector."""
        return self._providers.get('prometheus')

    def get_llm_trace_provider(self) -> Optional[LLMTraceProvider]:
        """Get LLM-specific trace provider."""
        return self._providers.get('langfuse')

    def get_trace_provider(self) -> Optional[TraceProvider]:
        """Get general trace provider."""
        # Could return OpenTelemetry provider when implemented
        return self._providers.get('langfuse')

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        duration_seconds: float,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record LLM call metrics across all enabled providers.
        
        This is a convenience method that calls all relevant providers.
        """
        # Record in Langfuse for detailed LLM observability
        langfuse = self._providers.get('langfuse')
        if langfuse:
            langfuse.record_llm_call(
                model, prompt_tokens, completion_tokens, total_tokens,
                duration_seconds, success, error, metadata
            )

        # Record in Prometheus for system metrics
        prometheus = self._providers.get('prometheus')
        if prometheus and hasattr(prometheus, 'record_llm_metrics'):
            prometheus.record_llm_metrics(
                model, prompt_tokens, completion_tokens, total_tokens,
                duration_seconds, success
            )

    def record_intent_analysis(
        self,
        intent: str,
        confidence: float,
        method: str,
        success: bool,
        duration_seconds: float
    ) -> None:
        """Record intent analysis metrics across all enabled providers."""
        # Record in Langfuse
        langfuse = self._providers.get('langfuse')
        if langfuse:
            langfuse.record_intent_analysis(intent, confidence, method, success, duration_seconds)

        # Record in Prometheus
        prometheus = self._providers.get('prometheus')
        if prometheus and hasattr(prometheus, 'record_intent_metrics'):
            prometheus.record_intent_metrics(intent, confidence, method, success, duration_seconds)

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
        prometheus = self._providers.get('prometheus')
        if prometheus:
            prometheus.record_http_request(
                method, endpoint, status_code, duration_seconds,
                request_size_bytes, response_size_bytes
            )

    def record_mcp_call(
        self,
        tool_name: str,
        success: bool,
        duration_seconds: float,
        retry_count: int = 0,
        error: Optional[str] = None
    ) -> None:
        """Record MCP tool call metrics."""
        prometheus = self._providers.get('prometheus')
        if prometheus:
            prometheus.record_mcp_call(tool_name, success, duration_seconds, retry_count, error)

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric across all enabled providers."""
        prometheus = self._providers.get('prometheus')
        if prometheus:
            prometheus.increment_counter(name, value, labels)

    def record_duration(
        self,
        name: str,
        duration_seconds: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a duration metric across all enabled providers."""
        prometheus = self._providers.get('prometheus')
        if prometheus:
            prometheus.record_duration(name, duration_seconds, labels)

    @contextmanager
    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        completion: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracing LLM calls.
        
        Usage:
            with monitoring.trace_llm_call(model, prompt, response) as span:
                span.set_attribute("custom_attr", "value")
        """
        langfuse = self._providers.get('langfuse')
        if langfuse:
            with langfuse.trace_llm_call(model, prompt, completion, metadata) as span:
                yield span
        else:
            # Return a dummy context if no trace provider
            from ..providers.langfuse_provider import DummySpanContext
            yield DummySpanContext()

    @contextmanager
    def trace_intent_analysis(
        self,
        input_text: str,
        detected_intent: str,
        confidence: float,
        method: str
    ):
        """Context manager for tracing intent analysis."""
        langfuse = self._providers.get('langfuse')
        if langfuse:
            with langfuse.trace_intent_analysis(input_text, detected_intent, confidence, method) as span:
                yield span
        else:
            from ..providers.langfuse_provider import DummySpanContext
            yield DummySpanContext()

    def flush_metrics(self) -> None:
        """Flush all metrics to their respective backends."""
        for provider in self._providers.values():
            if hasattr(provider, 'flush'):
                try:
                    provider.flush()
                except Exception as e:
                    print(f"Warning: Failed to flush metrics for {type(provider).__name__}: {e}")

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get the status of all monitoring providers."""
        status = {
            "initialized": self._initialized,
            "providers": {}
        }
        
        for name, provider in self._providers.items():
            status["providers"][name] = {
                "enabled": hasattr(provider, 'is_enabled') and provider.is_enabled(),
                "type": type(provider).__name__
            }
            
        return status

    def is_monitoring_enabled(self) -> bool:
        """Check if any monitoring providers are enabled."""
        return self._initialized and len(self._providers) > 0


# Global instance for easy access
_global_monitoring_manager = None


def get_monitoring_manager() -> MonitoringManager:
    """Get or create the global monitoring manager instance."""
    global _global_monitoring_manager
    if _global_monitoring_manager is None:
        _global_monitoring_manager = MonitoringManager()
    return _global_monitoring_manager


def init_monitoring(config: Optional[Dict[str, Any]] = None) -> MonitoringManager:
    """Initialize monitoring with optional configuration."""
    global _global_monitoring_manager
    _global_monitoring_manager = MonitoringManager(config)
    return _global_monitoring_manager 