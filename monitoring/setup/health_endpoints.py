"""
Health Check Endpoints

FastAPI endpoints for system health monitoring.
Provides REST API access to health check functionality.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .monitoring_setup import get_monitoring_manager


def create_health_router() -> APIRouter:
    """
    Create FastAPI router with health check endpoints.
    
    Returns:
        Configured router with health endpoints
    """
    router = APIRouter(prefix="/health", tags=["health"])
    monitoring = get_monitoring_manager()

    @router.get("/")
    async def health_check() -> Dict[str, Any]:
        """
        Basic health check endpoint.
        
        Returns:
            System health status
        """
        try:
            status = monitoring.get_monitoring_status()
            
            # Determine overall health
            is_healthy = status.get("initialized", False) and len(status.get("providers", {})) > 0
            
            return {
                "status": "healthy" if is_healthy else "degraded",
                "timestamp": "2024-01-01T00:00:00Z",  # Should use datetime.utcnow()
                "monitoring": status,
                "version": "1.0.0"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }

    @router.get("/detailed")
    async def detailed_health_check() -> Dict[str, Any]:
        """
        Detailed health check with component status.
        
        Returns:
            Comprehensive system health information
        """
        try:
            monitoring_status = monitoring.get_monitoring_status()
            
            # Basic component checks
            components = {}
            
            # Check monitoring providers
            for provider_name, provider_info in monitoring_status.get("providers", {}).items():
                components[f"monitoring_{provider_name}"] = {
                    "status": "healthy" if provider_info.get("enabled") else "unhealthy",
                    "type": provider_info.get("type"),
                    "enabled": provider_info.get("enabled")
                }
            
            # Overall status
            healthy_components = sum(1 for comp in components.values() if comp["status"] == "healthy")
            total_components = len(components)
            
            overall_status = "healthy" if healthy_components == total_components else "degraded"
            if healthy_components == 0:
                overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "timestamp": "2024-01-01T00:00:00Z",
                "components": components,
                "summary": {
                    "total_components": total_components,
                    "healthy_components": healthy_components,
                    "unhealthy_components": total_components - healthy_components
                },
                "monitoring": monitoring_status
            }
            
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

    @router.get("/monitoring")
    async def monitoring_status() -> Dict[str, Any]:
        """
        Get monitoring system status.
        
        Returns:
            Monitoring providers status and configuration
        """
        try:
            status = monitoring.get_monitoring_status()
            return {
                "monitoring_enabled": monitoring.is_monitoring_enabled(),
                "status": status
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")

    @router.get("/metrics/summary")
    async def metrics_summary() -> Dict[str, Any]:
        """
        Get basic metrics summary.
        
        Returns:
            Summary of key system metrics
        """
        try:
            # This would typically query the metrics backend
            # For now, return placeholder data
            return {
                "timestamp": "2024-01-01T00:00:00Z",
                "summary": {
                    "requests_per_minute": 0,
                    "average_response_time": 0.0,
                    "error_rate": 0.0,
                    "llm_calls_per_minute": 0,
                    "successful_llm_calls": 0
                },
                "note": "Metrics integration would require Prometheus query API"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {str(e)}")

    return router


class HealthEndpoints:
    """
    Health endpoints manager for easy integration.
    """

    def __init__(self):
        """Initialize health endpoints manager."""
        self.router = create_health_router()

    def add_to_app(self, app):
        """
        Add health endpoints to FastAPI app.
        
        Args:
            app: FastAPI application instance
        """
        app.include_router(self.router)
        return app


def add_health_endpoints(app):
    """
    Convenience function to add health endpoints to FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    health = HealthEndpoints()
    return health.add_to_app(app) 