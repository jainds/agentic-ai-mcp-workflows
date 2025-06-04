"""
MCP Monitoring Middleware

Wrapper for MCP client calls to add monitoring and observability.
Automatically tracks MCP tool calls, performance, and errors.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from functools import wraps

from ..setup.monitoring_setup import get_monitoring_manager


class MCPMonitoringWrapper:
    """
    Wrapper for MCP client to add monitoring capabilities.
    
    Automatically tracks:
    - MCP tool call success/failure rates
    - Call duration and performance
    - Retry attempts and patterns
    - Error types and frequencies
    """

    def __init__(self, mcp_client, tool_prefix: str = ""):
        """
        Initialize MCP monitoring wrapper.
        
        Args:
            mcp_client: Original MCP client instance
            tool_prefix: Optional prefix for tool names in metrics
        """
        self.mcp_client = mcp_client
        self.tool_prefix = tool_prefix
        self.monitoring = get_monitoring_manager()

    async def call_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        timeout: Optional[float] = None
    ) -> Any:
        """
        Call MCP tool with monitoring.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            timeout: Optional timeout for the call
            
        Returns:
            Tool call result
        """
        prefixed_tool_name = f"{self.tool_prefix}{tool_name}" if self.tool_prefix else tool_name
        start_time = time.time()
        retry_count = 0
        
        try:
            # Call the original MCP tool
            if timeout:
                result = await asyncio.wait_for(
                    self.mcp_client.call_tool(tool_name, parameters),
                    timeout=timeout
                )
            else:
                result = await self.mcp_client.call_tool(tool_name, parameters)
            
            duration = time.time() - start_time
            
            # Record successful call
            if self.monitoring.is_monitoring_enabled():
                self.monitoring.record_mcp_call(
                    tool_name=prefixed_tool_name,
                    success=True,
                    duration_seconds=duration,
                    retry_count=retry_count
                )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record failed call
            if self.monitoring.is_monitoring_enabled():
                self.monitoring.record_mcp_call(
                    tool_name=prefixed_tool_name,
                    success=False,
                    duration_seconds=duration,
                    retry_count=retry_count,
                    error=type(e).__name__
                )
            
            raise

    async def call_tool_with_retry(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Call MCP tool with retry logic and monitoring.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Optional timeout for each call
            
        Returns:
            Tool call result
        """
        prefixed_tool_name = f"{self.tool_prefix}{tool_name}" if self.tool_prefix else tool_name
        start_time = time.time()
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if timeout:
                    result = await asyncio.wait_for(
                        self.mcp_client.call_tool(tool_name, parameters),
                        timeout=timeout
                    )
                else:
                    result = await self.mcp_client.call_tool(tool_name, parameters)
                
                duration = time.time() - start_time
                
                # Record successful call with retry count
                if self.monitoring.is_monitoring_enabled():
                    self.monitoring.record_mcp_call(
                        tool_name=prefixed_tool_name,
                        success=True,
                        duration_seconds=duration,
                        retry_count=attempt
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # If this was the last attempt, record failure
                if attempt == max_retries:
                    duration = time.time() - start_time
                    
                    if self.monitoring.is_monitoring_enabled():
                        self.monitoring.record_mcp_call(
                            tool_name=prefixed_tool_name,
                            success=False,
                            duration_seconds=duration,
                            retry_count=attempt,
                            error=type(e).__name__
                        )
                    
                    raise
                
                # Wait before retrying
                if retry_delay > 0:
                    await asyncio.sleep(retry_delay)

    def __getattr__(self, name):
        """
        Forward other attributes to the original MCP client.
        
        This allows the wrapper to be used as a drop-in replacement.
        """
        return getattr(self.mcp_client, name)


def monitor_mcp_calls(tool_prefix: str = ""):
    """
    Decorator to add monitoring to MCP call functions.
    
    Args:
        tool_prefix: Optional prefix for tool names in metrics
        
    Returns:
        Decorated function with monitoring
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitoring = get_monitoring_manager()
            
            # Extract tool name from function name or arguments
            tool_name = tool_prefix + (kwargs.get('tool_name') or func.__name__)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record successful call
                if monitoring.is_monitoring_enabled():
                    monitoring.record_mcp_call(
                        tool_name=tool_name,
                        success=True,
                        duration_seconds=duration
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Record failed call
                if monitoring.is_monitoring_enabled():
                    monitoring.record_mcp_call(
                        tool_name=tool_name,
                        success=False,
                        duration_seconds=duration,
                        error=type(e).__name__
                    )
                
                raise
        
        return wrapper
    return decorator


# Context manager for MCP call monitoring
class MCPCallContext:
    """
    Context manager for monitoring individual MCP calls.
    
    Usage:
        async with MCPCallContext("get_policy_details") as ctx:
            result = await some_mcp_call()
            ctx.set_metadata("customer_id", "CUST-001")
    """

    def __init__(self, tool_name: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize MCP call context.
        
        Args:
            tool_name: Name of the MCP tool being called
            parameters: Optional tool parameters
        """
        self.tool_name = tool_name
        self.parameters = parameters or {}
        self.monitoring = get_monitoring_manager()
        self.start_time = None
        self.metadata = {}

    async def __aenter__(self):
        """Enter the context."""
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and record metrics."""
        if self.start_time is None:
            return

        duration = time.time() - self.start_time
        success = exc_type is None
        error = type(exc_val).__name__ if exc_val else None

        if self.monitoring.is_monitoring_enabled():
            self.monitoring.record_mcp_call(
                tool_name=self.tool_name,
                success=success,
                duration_seconds=duration,
                error=error
            )

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata for the MCP call.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value


def create_monitored_mcp_client(original_client, tool_prefix: str = ""):
    """
    Create a monitored version of an MCP client.
    
    Args:
        original_client: Original MCP client instance
        tool_prefix: Optional prefix for tool names
        
    Returns:
        Monitored MCP client wrapper
    """
    return MCPMonitoringWrapper(original_client, tool_prefix) 