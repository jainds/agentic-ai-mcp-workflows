"""
Policy Tools Module

FastMCP tools for policy management operations.
"""

from typing import Optional
from .base_tools import BaseTools
import structlog

logger = structlog.get_logger(__name__)


class PolicyTools(BaseTools):
    """Policy management tools for FastMCP"""
    
    def __init__(self, data_service):
        super().__init__(data_service)
        self.logger.info("Policy tools initialized")
    
    def get_policy(self, policy_id: str) -> str:
        """Get policy information by ID"""
        return self.handle_tool_execution(
            "get_policy",
            self.data_service.get_policy,
            policy_id=policy_id
        )
    
    def get_customer_policies(self, customer_id: str) -> str:
        """Get all policies for a customer"""
        return self.handle_tool_execution(
            "get_customer_policies",
            self.data_service.get_customer_policies,
            customer_id=customer_id
        )
    
    def create_policy(self, customer_id: str, policy_type: str, coverage_amount: int) -> str:
        """Create a new policy (mock write operation)"""
        policy_data = {
            "customer_id": customer_id,
            "type": policy_type,
            "coverage_amount": coverage_amount
        }
        return self.handle_tool_execution(
            "create_policy",
            self.data_service.create_policy,
            policy_data=policy_data
        )
    
    def register_tools(self, mcp_server):
        """Register all policy tools with the FastMCP server"""
        self.logger.info("Registering policy tools with FastMCP server")
        
        @mcp_server.tool()
        def get_policy(policy_id: str) -> str:
            """Get policy information by ID"""
            return self.get_policy(policy_id=policy_id)
        
        @mcp_server.tool()
        def get_customer_policies(customer_id: str) -> str:
            """Get all policies for a customer"""
            return self.get_customer_policies(customer_id=customer_id)
        
        @mcp_server.tool()
        def create_policy(customer_id: str, policy_type: str, coverage_amount: int) -> str:
            """Create a new policy (mock write operation)"""
            return self.create_policy(customer_id=customer_id, policy_type=policy_type, coverage_amount=coverage_amount)
        
        self.logger.info("Policy tools registered successfully", tools_count=3) 