"""
Health Checker Interface

Defines the contract for system health monitoring and status checking.
Provides health checks for all system components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """Overall system health summary"""
    overall_status: HealthStatus
    components: List[HealthCheckResult]
    timestamp: datetime
    total_checks: int
    healthy_checks: int
    degraded_checks: int
    unhealthy_checks: int


class HealthChecker(ABC):
    """
    Abstract interface for health checking.
    
    Implementations can check various system components.
    """

    @abstractmethod
    def check_component_health(self, component_name: str) -> HealthCheckResult:
        """
        Check the health of a specific component.
        
        Args:
            component_name: Name of component to check
            
        Returns:
            HealthCheckResult with status and details
        """
        pass

    @abstractmethod
    def check_all_health(self) -> SystemHealth:
        """
        Check the health of all registered components.
        
        Returns:
            SystemHealth with overall status and component details
        """
        pass

    @abstractmethod
    def register_health_check(
        self, 
        component_name: str, 
        check_function: callable,
        critical: bool = True
    ) -> None:
        """
        Register a health check for a component.
        
        Args:
            component_name: Name of the component
            check_function: Function that performs the health check
            critical: Whether this component is critical for overall health
        """
        pass

    @abstractmethod
    def get_health_history(
        self, 
        component_name: Optional[str] = None,
        hours: int = 24
    ) -> List[HealthCheckResult]:
        """
        Get health check history.
        
        Args:
            component_name: Specific component or None for all
            hours: Number of hours of history to retrieve
            
        Returns:
            List of health check results
        """
        pass


class LLMHealthChecker(ABC):
    """
    Specialized interface for LLM service health checking.
    Follows Interface Segregation principle.
    """

    @abstractmethod
    def check_llm_availability(self, model: str) -> HealthCheckResult:
        """
        Check if an LLM model is available and responding.
        
        Args:
            model: LLM model name to check
            
        Returns:
            HealthCheckResult with availability status
        """
        pass

    @abstractmethod
    def check_llm_performance(self, model: str) -> HealthCheckResult:
        """
        Check LLM performance metrics (latency, error rate).
        
        Args:
            model: LLM model name to check
            
        Returns:
            HealthCheckResult with performance metrics
        """
        pass

    @abstractmethod
    def check_token_limits(self, model: str) -> HealthCheckResult:
        """
        Check token usage against limits.
        
        Args:
            model: LLM model name to check
            
        Returns:
            HealthCheckResult with token usage status
        """
        pass


class MCPHealthChecker(ABC):
    """
    Specialized interface for MCP service health checking.
    Follows Interface Segregation principle.
    """

    @abstractmethod
    def check_mcp_server_connectivity(self) -> HealthCheckResult:
        """
        Check if MCP server is reachable and responding.
        
        Returns:
            HealthCheckResult with connectivity status
        """
        pass

    @abstractmethod
    def check_mcp_tools_availability(self) -> List[HealthCheckResult]:
        """
        Check availability of all MCP tools.
        
        Returns:
            List of HealthCheckResult for each tool
        """
        pass

    @abstractmethod
    def check_policy_data_consistency(self) -> HealthCheckResult:
        """
        Check policy data consistency and integrity.
        
        Returns:
            HealthCheckResult with data consistency status
        """
        pass


class APIHealthChecker(ABC):
    """
    Specialized interface for API health checking.
    Follows Interface Segregation principle.
    """

    @abstractmethod
    def check_endpoint_health(self, endpoint: str) -> HealthCheckResult:
        """
        Check health of a specific API endpoint.
        
        Args:
            endpoint: API endpoint to check
            
        Returns:
            HealthCheckResult with endpoint status
        """
        pass

    @abstractmethod
    def check_database_connectivity(self) -> HealthCheckResult:
        """
        Check database connectivity and performance.
        
        Returns:
            HealthCheckResult with database status
        """
        pass

    @abstractmethod
    def check_external_dependencies(self) -> List[HealthCheckResult]:
        """
        Check all external service dependencies.
        
        Returns:
            List of HealthCheckResult for each dependency
        """
        pass

    @abstractmethod
    def check_resource_usage(self) -> HealthCheckResult:
        """
        Check system resource usage (CPU, memory, disk).
        
        Returns:
            HealthCheckResult with resource usage status
        """
        pass 