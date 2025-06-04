"""
Langfuse Provider Implementation

Implements LLM observability and tracing using Langfuse.
Provides comprehensive LLM call tracking, token usage, and performance metrics.
"""

import os
import time
from typing import Dict, Any, Optional, ContextManager
from contextlib import contextmanager
from datetime import datetime

from ..interfaces.metrics_collector import LLMMetricsCollector
from ..interfaces.trace_provider import LLMTraceProvider, SpanContext


class LangfuseProvider(LLMMetricsCollector, LLMTraceProvider):
    """
    Langfuse implementation for LLM observability.
    
    Requires environment variables:
    - LANGFUSE_SECRET_KEY: Langfuse secret key
    - LANGFUSE_PUBLIC_KEY: Langfuse public key  
    - LANGFUSE_HOST: Langfuse host (optional, defaults to cloud)
    """

    def __init__(self):
        """Initialize Langfuse provider with environment configuration."""
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        
        self._client = None
        self._initialized = False
        
        if self.secret_key and self.public_key:
            self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Langfuse client."""
        try:
            # Import langfuse only when needed to avoid dependency issues
            from langfuse import Langfuse
            
            self._client = Langfuse(
                secret_key=self.secret_key,
                public_key=self.public_key,
                host=self.host
            )
            self._initialized = True
        except ImportError:
            print("Warning: langfuse package not installed. LLM tracing will be disabled.")
        except Exception as e:
            print(f"Warning: Failed to initialize Langfuse client: {e}")

    def is_enabled(self) -> bool:
        """Check if Langfuse is properly configured and enabled."""
        return self._initialized and self._client is not None

    # LLMMetricsCollector implementation
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
        """Record LLM call metrics in Langfuse."""
        if not self.is_enabled():
            return

        try:
            # Create a generation in Langfuse
            generation = self._client.generation(
                name=f"llm_call_{model}",
                model=model,
                start_time=datetime.now(),
                end_time=datetime.now(),
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                metadata={
                    "duration_seconds": duration_seconds,
                    "success": success,
                    "error": error,
                    **(metadata or {})
                }
            )
            
            if not success and error:
                generation.level = "ERROR"
                
        except Exception as e:
            print(f"Warning: Failed to record LLM call in Langfuse: {e}")

    def record_intent_analysis(
        self,
        intent: str,
        confidence: float,
        method: str,
        success: bool,
        duration_seconds: float
    ) -> None:
        """Record intent analysis metrics in Langfuse."""
        if not self.is_enabled():
            return

        try:
            self._client.trace(
                name="intent_analysis",
                metadata={
                    "intent": intent,
                    "confidence": confidence,
                    "method": method,
                    "success": success,
                    "duration_seconds": duration_seconds
                }
            )
        except Exception as e:
            print(f"Warning: Failed to record intent analysis in Langfuse: {e}")

    # LLMTraceProvider implementation
    @contextmanager
    def trace_llm_call(
        self,
        model: str,
        prompt: str,
        completion: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextManager[SpanContext]:
        """Trace an LLM call with full context."""
        if not self.is_enabled():
            yield DummySpanContext()
            return

        start_time = time.time()
        generation = None
        
        try:
            generation = self._client.generation(
                name=f"llm_call_{model}",
                model=model,
                input=prompt,
                start_time=datetime.now(),
                metadata=metadata or {}
            )
            
            span_context = LangfuseSpanContext(generation)
            yield span_context
            
        except Exception as e:
            print(f"Warning: Failed to start LLM trace in Langfuse: {e}")
            yield DummySpanContext()
        finally:
            if generation:
                try:
                    duration = time.time() - start_time
                    generation.end(
                        output=completion,
                        end_time=datetime.now(),
                        metadata={
                            "duration_seconds": duration,
                            **(metadata or {})
                        }
                    )
                except Exception as e:
                    print(f"Warning: Failed to end LLM trace in Langfuse: {e}")

    @contextmanager
    def trace_intent_analysis(
        self,
        input_text: str,
        detected_intent: str,
        confidence: float,
        method: str
    ) -> ContextManager[SpanContext]:
        """Trace intent analysis operation."""
        if not self.is_enabled():
            yield DummySpanContext()
            return

        try:
            span = self._client.span(
                name="intent_analysis",
                input=input_text,
                metadata={
                    "detected_intent": detected_intent,
                    "confidence": confidence,
                    "method": method
                }
            )
            
            span_context = LangfuseSpanContext(span)
            yield span_context
            
        except Exception as e:
            print(f"Warning: Failed to trace intent analysis in Langfuse: {e}")
            yield DummySpanContext()

    @contextmanager  
    def trace_response_formatting(
        self,
        raw_data: str,
        formatted_response: str,
        template_used: Optional[str] = None
    ) -> ContextManager[SpanContext]:
        """Trace response formatting operation."""
        if not self.is_enabled():
            yield DummySpanContext()
            return

        try:
            span = self._client.span(
                name="response_formatting",
                input=raw_data,
                output=formatted_response,
                metadata={
                    "template_used": template_used
                }
            )
            
            span_context = LangfuseSpanContext(span)
            yield span_context
            
        except Exception as e:
            print(f"Warning: Failed to trace response formatting in Langfuse: {e}")
            yield DummySpanContext()


class LangfuseSpanContext(SpanContext):
    """Langfuse-specific span context implementation."""

    def __init__(self, langfuse_span):
        self._span = langfuse_span

    def __enter__(self) -> "LangfuseSpanContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            self.record_exception(exc_val)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the Langfuse span."""
        try:
            if hasattr(self._span, 'metadata'):
                if not self._span.metadata:
                    self._span.metadata = {}
                self._span.metadata[key] = value
        except Exception as e:
            print(f"Warning: Failed to set attribute in Langfuse span: {e}")

    def set_status(self, status: str, description: Optional[str] = None) -> None:
        """Set the status of the Langfuse span."""
        try:
            self.set_attribute("status", status)
            if description:
                self.set_attribute("status_description", description)
        except Exception as e:
            print(f"Warning: Failed to set status in Langfuse span: {e}")

    def record_exception(self, exception: Exception) -> None:
        """Record an exception on the Langfuse span."""
        try:
            self.set_attribute("error", str(exception))
            self.set_attribute("error_type", type(exception).__name__)
            if hasattr(self._span, 'level'):
                self._span.level = "ERROR"
        except Exception as e:
            print(f"Warning: Failed to record exception in Langfuse span: {e}")


class DummySpanContext(SpanContext):
    """Dummy span context for when Langfuse is not available."""

    def __enter__(self) -> "DummySpanContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: str, description: Optional[str] = None) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass 