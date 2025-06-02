"""
Metrics Collector Interface

Defines the contract for collecting and emitting metrics across the system.
Follows Single Responsibility and Interface Segregation principles.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class MetricType(Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"
    GAUGE = "gauge" 
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricsCollector(ABC):
    """
    Abstract interface for metrics collection.
    
    Implementations can include Prometheus, StatsD, CloudWatch, etc.
    """

    @abstractmethod
    def increment_counter(
        self, 
        name: str, 
        value: float = 1.0, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Amount to increment by (default 1.0)
            labels: Optional labels/tags for the metric
        """
        pass

    @abstractmethod
    def set_gauge(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels/tags for the metric
        """
        pass

    @abstractmethod
    def record_histogram(
        self, 
        name: str, 
        value: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a value in a histogram metric.
        
        Args:
            name: Metric name
            value: Value to record
            labels: Optional labels/tags for the metric
        """
        pass

    @abstractmethod
    def record_duration(
        self, 
        name: str, 
        duration_seconds: float, 
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a duration metric.
        
        Args:
            name: Metric name
            duration_seconds: Duration in seconds
            labels: Optional labels/tags for the metric
        """
        pass

    @abstractmethod
    def record_custom_metric(
        self, 
        name: str, 
        metric_type: MetricType, 
        value: float, 
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a custom metric with specific type.
        
        Args:
            name: Metric name
            metric_type: Type of metric to record
            value: Metric value
            labels: Optional labels/tags for the metric
            metadata: Additional metadata for the metric
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """
        Flush any buffered metrics to the backend.
        """
        pass


class LLMMetricsCollector(ABC):
    """
    Specialized interface for LLM-specific metrics.
    Follows Interface Segregation principle.
    """

    @abstractmethod
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
        Record metrics for an LLM API call.
        
        Args:
            model: LLM model name
            prompt_tokens: Number of tokens in prompt
            completion_tokens: Number of tokens in completion
            total_tokens: Total tokens used
            duration_seconds: Call duration in seconds
            success: Whether the call was successful
            error: Error message if call failed
            metadata: Additional metadata (intent, customer_id, etc.)
        """
        pass

    @abstractmethod
    def record_intent_analysis(
        self,
        intent: str,
        confidence: float,
        method: str,  # "llm" or "rules"
        success: bool,
        duration_seconds: float
    ) -> None:
        """
        Record intent analysis metrics.
        
        Args:
            intent: Detected intent
            confidence: Confidence score (0.0-1.0)
            method: Analysis method used
            success: Whether analysis was successful
            duration_seconds: Analysis duration
        """
        pass


class APIMetricsCollector(ABC):
    """
    Specialized interface for API metrics.
    Follows Interface Segregation principle.
    """

    @abstractmethod
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
        request_size_bytes: Optional[int] = None,
        response_size_bytes: Optional[int] = None
    ) -> None:
        """
        Record HTTP request metrics.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            status_code: HTTP status code
            duration_seconds: Request duration
            request_size_bytes: Request payload size
            response_size_bytes: Response payload size
        """
        pass

    @abstractmethod
    def record_mcp_call(
        self,
        tool_name: str,
        success: bool,
        duration_seconds: float,
        retry_count: int = 0,
        error: Optional[str] = None
    ) -> None:
        """
        Record MCP tool call metrics.
        
        Args:
            tool_name: Name of MCP tool called
            success: Whether call was successful
            duration_seconds: Call duration
            retry_count: Number of retries attempted
            error: Error message if call failed
        """
        pass 