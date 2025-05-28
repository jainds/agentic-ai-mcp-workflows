#!/usr/bin/env python3
"""
Comprehensive Observability Module for Multi-Agent System
Integrates LangFuse (LLM tracing), OpenTelemetry (distributed tracing), and Prometheus (metrics)
"""

import os
import time
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from functools import wraps
from contextlib import asynccontextmanager
import logging

# LangFuse for LLM observability
try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    print("⚠️  LangFuse not available. Install: pip install langfuse")

# OpenTelemetry for distributed tracing  
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    print("⚠️  OpenTelemetry not available. Install: pip install opentelemetry-*")

# Prometheus for metrics
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server, generate_latest
    from prometheus_fastapi_instrumentator import Instrumentator
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("⚠️  Prometheus not available. Install: pip install prometheus-client")


class MultiAgentObservability:
    """Central observability manager for the multi-agent system"""
    
    def __init__(self, 
                 service_name: str,
                 langfuse_public_key: Optional[str] = None,
                 langfuse_secret_key: Optional[str] = None,
                 jaeger_endpoint: Optional[str] = None,
                 prometheus_port: int = 8000):
        
        self.service_name = service_name
        self.logger = logging.getLogger(f"observability.{service_name}")
        
        # Initialize components
        self.langfuse = None
        self.tracer = None
        self.meter = None
        self.metrics = {}
        
        self._setup_langfuse(langfuse_public_key, langfuse_secret_key)
        self._setup_opentelemetry(jaeger_endpoint)
        self._setup_prometheus(prometheus_port)
        
    def _setup_langfuse(self, public_key: Optional[str], secret_key: Optional[str]):
        """Setup LangFuse for LLM observability"""
        if not LANGFUSE_AVAILABLE:
            return
            
        try:
            # Get keys from environment if not provided
            public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
            secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
            host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            
            if public_key and secret_key:
                self.langfuse = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host
                )
                self.logger.info("✅ LangFuse initialized successfully")
            else:
                self.logger.warning("⚠️  LangFuse keys not found in environment")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize LangFuse: {e}")
    
    def _setup_opentelemetry(self, jaeger_endpoint: Optional[str]):
        """Setup OpenTelemetry for distributed tracing"""
        if not OTEL_AVAILABLE:
            return
            
        try:
            # Setup tracer
            trace.set_tracer_provider(TracerProvider())
            self.tracer = trace.get_tracer(self.service_name)
            
            # Setup Jaeger exporter if endpoint provided
            jaeger_endpoint = jaeger_endpoint or os.getenv("JAEGER_ENDPOINT")
            if jaeger_endpoint:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_endpoint.split(":")[0],
                    agent_port=int(jaeger_endpoint.split(":")[1]) if ":" in jaeger_endpoint else 14268,
                )
                span_processor = BatchSpanProcessor(jaeger_exporter)
                trace.get_tracer_provider().add_span_processor(span_processor)
                
            # Setup metrics
            metrics.set_meter_provider(MeterProvider())
            self.meter = metrics.get_meter(self.service_name)
            
            self.logger.info("✅ OpenTelemetry initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize OpenTelemetry: {e}")
    
    def _setup_prometheus(self, port: int):
        """Setup Prometheus metrics"""
        if not PROMETHEUS_AVAILABLE:
            return
            
        try:
            # Define custom metrics for multi-agent system
            self.metrics = {
                # Agent communication metrics
                "agent_requests_total": Counter(
                    "agent_requests_total", 
                    "Total agent requests", 
                    ["source_agent", "target_agent", "skill_name", "status"]
                ),
                "agent_request_duration": Histogram(
                    "agent_request_duration_seconds",
                    "Agent request duration",
                    ["source_agent", "target_agent", "skill_name"]
                ),
                
                # LLM metrics
                "llm_requests_total": Counter(
                    "llm_requests_total",
                    "Total LLM requests", 
                    ["model", "task_type", "status"]
                ),
                "llm_request_duration": Histogram(
                    "llm_request_duration_seconds",
                    "LLM request duration",
                    ["model", "task_type"]
                ),
                "llm_tokens_total": Counter(
                    "llm_tokens_total",
                    "Total LLM tokens used",
                    ["model", "task_type", "token_type"]
                ),
                
                # Workflow metrics
                "workflow_executions_total": Counter(
                    "workflow_executions_total",
                    "Total workflow executions",
                    ["workflow_type", "status"]
                ),
                "workflow_duration": Histogram(
                    "workflow_duration_seconds", 
                    "Workflow execution duration",
                    ["workflow_type"]
                ),
                
                # System metrics
                "active_sessions": Gauge(
                    "active_sessions_total",
                    "Number of active user sessions"
                ),
                "agent_health": Gauge(
                    "agent_health_status",
                    "Agent health status (1=healthy, 0=unhealthy)",
                    ["agent_name"]
                )
            }
            
            # Start Prometheus HTTP server on different port for each agent
            try:
                start_http_server(port + hash(self.service_name) % 1000)
                self.logger.info(f"✅ Prometheus metrics server started on port {port + hash(self.service_name) % 1000}")
            except OSError:
                self.logger.warning(f"⚠️  Prometheus port {port} already in use")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Prometheus: {e}")
    
    @asynccontextmanager
    async def trace_agent_call(self, source_agent: str, target_agent: str, skill_name: str, parameters: Dict[str, Any]):
        """Context manager for tracing agent-to-agent calls"""
        start_time = time.time()
        status = "success"
        
        # OpenTelemetry span
        span = None
        if self.tracer:
            span = self.tracer.start_span(f"{source_agent} -> {target_agent}.{skill_name}")
            span.set_attributes({
                "source.agent": source_agent,
                "target.agent": target_agent,
                "skill.name": skill_name,
                "parameters.count": len(parameters)
            })
        
        # LangFuse trace
        langfuse_trace = None
        if self.langfuse:
            langfuse_trace = self.langfuse.trace(
                name=f"agent_call_{source_agent}_to_{target_agent}",
                metadata={
                    "source_agent": source_agent,
                    "target_agent": target_agent,
                    "skill_name": skill_name,
                    "parameters": parameters
                }
            )
        
        try:
            yield {
                "span": span,
                "trace": langfuse_trace,
                "start_time": start_time
            }
            
        except Exception as e:
            status = "error"
            if span:
                span.set_attribute("error", str(e))
            if langfuse_trace:
                langfuse_trace.update(metadata={"error": str(e)})
            raise
            
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            if PROMETHEUS_AVAILABLE and "agent_requests_total" in self.metrics:
                self.metrics["agent_requests_total"].labels(
                    source_agent=source_agent,
                    target_agent=target_agent, 
                    skill_name=skill_name,
                    status=status
                ).inc()
                
                self.metrics["agent_request_duration"].labels(
                    source_agent=source_agent,
                    target_agent=target_agent,
                    skill_name=skill_name
                ).observe(duration)
            
            # Finish spans
            if span:
                span.set_attribute("duration", duration)
                span.end()
                
            if langfuse_trace:
                langfuse_trace.update(
                    output={"status": status, "duration": duration}
                )
    
    @asynccontextmanager  
    async def trace_llm_call(self, model: str, task_type: str, prompt: str, **kwargs):
        """Context manager for tracing LLM calls"""
        start_time = time.time()
        status = "success"
        response_data = {}
        
        # LangFuse generation tracking
        generation = None
        if self.langfuse:
            generation = self.langfuse.generation(
                name=f"llm_{task_type}",
                model=model,
                input=prompt,
                metadata={
                    "task_type": task_type,
                    **kwargs
                }
            )
        
        # OpenTelemetry span
        span = None
        if self.tracer:
            span = self.tracer.start_span(f"llm_call_{task_type}")
            span.set_attributes({
                "llm.model": model,
                "llm.task_type": task_type,
                "llm.prompt_length": len(prompt)
            })
        
        try:
            yield {
                "generation": generation,
                "span": span,
                "start_time": start_time
            }
            
        except Exception as e:
            status = "error"
            if span:
                span.set_attribute("error", str(e))
            if generation:
                generation.update(metadata={"error": str(e)})
            raise
            
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            if PROMETHEUS_AVAILABLE and "llm_requests_total" in self.metrics:
                self.metrics["llm_requests_total"].labels(
                    model=model,
                    task_type=task_type,
                    status=status
                ).inc()
                
                self.metrics["llm_request_duration"].labels(
                    model=model,
                    task_type=task_type
                ).observe(duration)
            
            # Finish spans
            if span:
                span.set_attribute("duration", duration)
                span.end()
    
    def record_workflow_execution(self, workflow_type: str, duration: float, status: str = "success"):
        """Record workflow execution metrics"""
        if PROMETHEUS_AVAILABLE and "workflow_executions_total" in self.metrics:
            self.metrics["workflow_executions_total"].labels(
                workflow_type=workflow_type,
                status=status
            ).inc()
            
            self.metrics["workflow_duration"].labels(
                workflow_type=workflow_type
            ).observe(duration)
    
    def update_agent_health(self, agent_name: str, is_healthy: bool):
        """Update agent health status"""
        if PROMETHEUS_AVAILABLE and "agent_health" in self.metrics:
            self.metrics["agent_health"].labels(agent_name=agent_name).set(1 if is_healthy else 0)
    
    def record_token_usage(self, model: str, task_type: str, prompt_tokens: int, completion_tokens: int):
        """Record LLM token usage"""
        if PROMETHEUS_AVAILABLE and "llm_tokens_total" in self.metrics:
            self.metrics["llm_tokens_total"].labels(
                model=model, 
                task_type=task_type,
                token_type="prompt"
            ).inc(prompt_tokens)
            
            self.metrics["llm_tokens_total"].labels(
                model=model,
                task_type=task_type, 
                token_type="completion"
            ).inc(completion_tokens)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        summary = {
            "service": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "langfuse": self.langfuse is not None,
                "opentelemetry": self.tracer is not None,
                "prometheus": bool(self.metrics)
            }
        }
        
        # Add current metric values if available
        if PROMETHEUS_AVAILABLE and self.metrics:
            try:
                # This would require prometheus_client registry access
                # For now, just indicate metrics are available
                summary["metrics_available"] = list(self.metrics.keys())
            except Exception:
                pass
                
        return summary


# Global observability instance
_observability: Optional[MultiAgentObservability] = None

def init_observability(service_name: str, **kwargs) -> MultiAgentObservability:
    """Initialize global observability instance"""
    global _observability
    _observability = MultiAgentObservability(service_name, **kwargs)
    return _observability

def get_observability() -> Optional[MultiAgentObservability]:
    """Get global observability instance"""
    return _observability

# Decorators for easy integration
def trace_agent_method(skill_name: str):
    """Decorator to trace agent methods"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            obs = get_observability()
            if obs:
                agent_name = getattr(self, 'name', self.__class__.__name__)
                async with obs.trace_agent_call(agent_name, agent_name, skill_name, kwargs):
                    return await func(self, *args, **kwargs)
            else:
                return await func(self, *args, **kwargs)
        return wrapper
    return decorator

def trace_llm_method(task_type: str):
    """Decorator to trace LLM methods"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            obs = get_observability()
            if obs:
                model = getattr(self, 'primary_model', 'unknown')
                prompt = str(args[0]) if args else str(kwargs.get('prompt', ''))
                async with obs.trace_llm_call(model, task_type, prompt):
                    return await func(self, *args, **kwargs)
            else:
                return await func(self, *args, **kwargs)
        return wrapper
    return decorator 