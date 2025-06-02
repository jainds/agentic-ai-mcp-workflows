"""
FastAPI Monitoring Middleware

Automatically instruments FastAPI applications with monitoring.
Records HTTP request metrics and distributed traces.
"""

import time
from typing import Callable, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..setup.monitoring_setup import get_monitoring_manager


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic HTTP request monitoring.
    
    Automatically records:
    - HTTP request count and duration
    - Request/response sizes
    - Status codes and error rates
    - Request paths and methods
    """

    def __init__(self, app, exclude_paths: list = None):
        """
        Initialize monitoring middleware.
        
        Args:
            app: FastAPI application instance
            exclude_paths: List of paths to exclude from monitoring (e.g., ["/health", "/metrics"])
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.monitoring = get_monitoring_manager()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request with monitoring.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
            
        Returns:
            HTTP response
        """
        # Check if path should be excluded from monitoring
        if self._should_exclude_path(request.url.path):
            return await call_next(request)

        # Extract request information
        method = request.method
        path = self._normalize_path(request.url.path)
        
        # Get request size if available
        request_size = None
        if hasattr(request, "headers") and "content-length" in request.headers:
            try:
                request_size = int(request.headers["content-length"])
            except ValueError:
                pass

        # Record request start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get response size if available
        response_size = None
        if hasattr(response, "headers") and "content-length" in response.headers:
            try:
                response_size = int(response.headers["content-length"])
            except ValueError:
                pass

        # Record metrics
        if self.monitoring.is_monitoring_enabled():
            self.monitoring.record_http_request(
                method=method,
                endpoint=path,
                status_code=response.status_code,
                duration_seconds=duration,
                request_size_bytes=request_size,
                response_size_bytes=response_size
            )

        return response

    def _should_exclude_path(self, path: str) -> bool:
        """Check if a path should be excluded from monitoring."""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for consistent metrics.
        
        Replaces dynamic segments with placeholders to avoid cardinality explosion.
        """
        # Basic normalization - could be enhanced with more sophisticated patterns
        normalized = path
        
        # Replace common dynamic segments
        # Replace UUIDs and IDs with placeholders
        import re
        
        # Replace UUID patterns
        uuid_pattern = r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        normalized = re.sub(uuid_pattern, '/{uuid}', normalized, flags=re.IGNORECASE)
        
        # Replace numeric IDs
        id_pattern = r'/\d+'
        normalized = re.sub(id_pattern, '/{id}', normalized)
        
        # Replace customer IDs (CUST-XXX pattern)
        customer_pattern = r'/CUST-[A-Z0-9]+'
        normalized = re.sub(customer_pattern, '/{customer_id}', normalized)
        
        return normalized


def add_monitoring_middleware(app, exclude_paths: list = None):
    """
    Convenience function to add monitoring middleware to FastAPI app.
    
    Args:
        app: FastAPI application instance
        exclude_paths: List of paths to exclude from monitoring
    """
    app.add_middleware(MonitoringMiddleware, exclude_paths=exclude_paths)
    return app 