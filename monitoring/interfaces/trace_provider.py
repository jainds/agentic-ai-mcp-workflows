"""
Trace Provider Interface

Defines the contract for distributed tracing across the system.
Supports OpenTelemetry, Jaeger, and Langfuse tracing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, ContextManager
from contextlib import contextmanager


class TraceProvider(ABC):
    """
    Abstract interface for distributed tracing.
    
    Implementations can include OpenTelemetry, Jaeger, Langfuse, etc.
    """

    @abstractmethod
    def start_trace(
        self, 
        name: str, 
        attributes: Optional[Dict[str, Any]] = None
    ) -> "TraceContext":
        """
        Start a new trace with the given name.
        
        Args:
            name: Name of the trace
            attributes: Optional attributes/tags for the trace
            
        Returns:
            TraceContext that can be used to manage the trace
        """
        pass

    @abstractmethod
    def start_span(
        self, 
        name: str, 
        parent_context: Optional["TraceContext"] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> "SpanContext":
        """
        Start a new span within a trace.
        
        Args:
            name: Name of the span
            parent_context: Parent trace context
            attributes: Optional attributes/tags for the span
            
        Returns:
            SpanContext that can be used to manage the span
        """
        pass

    @abstractmethod
    def get_current_trace_id(self) -> Optional[str]:
        """
        Get the current trace ID if available.
        
        Returns:
            Current trace ID or None if no active trace
        """
        pass

    @abstractmethod
    def set_trace_attribute(
        self, 
        key: str, 
        value: Any, 
        context: Optional["TraceContext"] = None
    ) -> None:
        """
        Set an attribute on the current or specified trace.
        
        Args:
            key: Attribute key
            value: Attribute value
            context: Optional trace context, uses current if None
        """
        pass

    @abstractmethod
    def record_exception(
        self, 
        exception: Exception, 
        context: Optional["TraceContext"] = None
    ) -> None:
        """
        Record an exception in the current or specified trace.
        
        Args:
            exception: Exception to record
            context: Optional trace context, uses current if None
        """
        pass


class TraceContext(ABC):
    """
    Abstract context for managing a trace lifecycle.
    """

    @abstractmethod
    def __enter__(self) -> "TraceContext":
        """Enter the trace context."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the trace context."""
        pass

    @abstractmethod
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on this trace."""
        pass

    @abstractmethod
    def set_status(self, status: str, description: Optional[str] = None) -> None:
        """Set the status of this trace."""
        pass

    @abstractmethod
    def get_trace_id(self) -> str:
        """Get the trace ID."""
        pass


class SpanContext(ABC):
    """
    Abstract context for managing a span lifecycle.
    """

    @abstractmethod
    def __enter__(self) -> "SpanContext":
        """Enter the span context."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the span context."""
        pass

    @abstractmethod
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on this span."""
        pass

    @abstractmethod
    def set_status(self, status: str, description: Optional[str] = None) -> None:
        """Set the status of this span."""
        pass

    @abstractmethod
    def record_exception(self, exception: Exception) -> None:
        """Record an exception on this span."""
        pass


class LLMTraceProvider(ABC):
    """
    Specialized interface for LLM tracing.
    Follows Interface Segregation principle.
    """

    @abstractmethod
    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        completion: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextManager["SpanContext"]:
        """
        Trace an LLM API call with prompt and completion.
        
        Args:
            model: LLM model name
            prompt: Input prompt
            completion: LLM completion
            metadata: Additional metadata
            
        Returns:
            Context manager for the LLM call span
        """
        pass

    @abstractmethod
    def trace_intent_analysis(
        self,
        input_text: str,
        detected_intent: str,
        confidence: float,
        method: str
    ) -> ContextManager["SpanContext"]:
        """
        Trace intent analysis operation.
        
        Args:
            input_text: Input text to analyze
            detected_intent: Detected intent
            confidence: Confidence score
            method: Analysis method used
            
        Returns:
            Context manager for the intent analysis span
        """
        pass

    @abstractmethod
    def trace_response_formatting(
        self,
        raw_data: str,
        formatted_response: str,
        template_used: Optional[str] = None
    ) -> ContextManager["SpanContext"]:
        """
        Trace response formatting operation.
        
        Args:
            raw_data: Raw input data
            formatted_response: Formatted response
            template_used: Template or prompt used
            
        Returns:
            Context manager for the formatting span
        """
        pass


class MCPTraceProvider(ABC):
    """
    Specialized interface for MCP operation tracing.
    Follows Interface Segregation principle.
    """

    @abstractmethod
    def trace_mcp_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        customer_id: Optional[str] = None
    ) -> ContextManager["SpanContext"]:
        """
        Trace an MCP tool call.
        
        Args:
            tool_name: Name of MCP tool
            parameters: Tool parameters
            customer_id: Customer ID if available
            
        Returns:
            Context manager for the MCP call span
        """
        pass

    @abstractmethod
    def trace_policy_retrieval(
        self,
        customer_id: str,
        policy_types: Optional[list] = None
    ) -> ContextManager["SpanContext"]:
        """
        Trace policy data retrieval.
        
        Args:
            customer_id: Customer ID
            policy_types: Types of policies retrieved
            
        Returns:
            Context manager for the policy retrieval span
        """
        pass 