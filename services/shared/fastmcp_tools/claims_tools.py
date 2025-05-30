"""
Claims Tools Module

FastMCP tools for claims management operations.
"""

from typing import Optional
from .base_tools import BaseTools
import structlog

logger = structlog.get_logger(__name__)


class ClaimsTools(BaseTools):
    """Claims management tools for FastMCP"""
    
    def __init__(self, data_service):
        super().__init__(data_service)
        self.logger.info("Claims tools initialized")
    
    def get_claim(self, claim_id: str) -> str:
        """Get claim information by ID"""
        return self.handle_tool_execution(
            "get_claim",
            self.data_service.get_claim,
            claim_id=claim_id
        )
    
    def get_customer_claims(self, customer_id: str) -> str:
        """Get all claims for a customer"""
        return self.handle_tool_execution(
            "get_customer_claims",
            self.data_service.get_customer_claims,
            customer_id=customer_id
        )
    
    def create_claim(self, customer_id: str, policy_id: str, claim_type: str, amount: float) -> str:
        """Create a new claim (mock write operation)"""
        claim_data = {
            "customer_id": customer_id,
            "policy_id": policy_id,
            "type": claim_type,
            "amount": amount
        }
        return self.handle_tool_execution(
            "create_claim",
            self.data_service.create_claim,
            claim_data=claim_data
        )
    
    def update_claim_status(self, claim_id: str, status: str, notes: Optional[str] = None) -> str:
        """Update claim status (mock write operation)"""
        return self.handle_tool_execution(
            "update_claim_status",
            self.data_service.update_claim_status,
            claim_id=claim_id,
            status=status,
            notes=notes
        )
    
    def register_tools(self, mcp_server):
        """Register all claims tools with the FastMCP server"""
        self.logger.info("Registering claims tools with FastMCP server")
        
        @mcp_server.tool()
        def get_claim(claim_id: str) -> str:
            """Get claim information by ID"""
            return self.get_claim(claim_id=claim_id)
        
        @mcp_server.tool()
        def get_customer_claims(customer_id: str) -> str:
            """Get all claims for a customer"""
            return self.get_customer_claims(customer_id=customer_id)
        
        @mcp_server.tool()
        def create_claim(customer_id: str, policy_id: str, claim_type: str, amount: float) -> str:
            """Create a new claim (mock write operation)"""
            return self.create_claim(customer_id=customer_id, policy_id=policy_id, claim_type=claim_type, amount=amount)
        
        @mcp_server.tool()
        def update_claim_status(claim_id: str, status: str, notes: Optional[str] = None) -> str:
            """Update claim status (mock write operation)"""
            return self.update_claim_status(claim_id=claim_id, status=status, notes=notes)
        
        self.logger.info("Claims tools registered successfully", tools_count=4) 