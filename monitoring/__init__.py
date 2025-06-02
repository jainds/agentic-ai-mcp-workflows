"""
Insurance AI Monitoring Suite

A comprehensive monitoring solution for the Insurance AI POC system.
Provides observability for LLM calls, API performance, MCP connections, and business metrics.

Supported providers:
- Langfuse: LLM observability and tracing
- Prometheus: Metrics collection
- OpenTelemetry: Distributed tracing
- Grafana: Visualization dashboards
"""

from .setup.monitoring_setup import MonitoringManager
from .interfaces.metrics_collector import MetricsCollector
from .interfaces.trace_provider import TraceProvider
from .interfaces.health_checker import HealthChecker

__version__ = "1.0.0"

# Public API
__all__ = [
    "MonitoringManager",
    "MetricsCollector", 
    "TraceProvider",
    "HealthChecker"
] 