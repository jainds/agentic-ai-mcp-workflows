"""
Quote Tools Module

FastMCP tools for insurance quote generation and management.
"""

from typing import Dict, Any
from .base_tools import BaseTools
import structlog

logger = structlog.get_logger(__name__)


class QuoteTools(BaseTools):
    """Quote generation and management tools for FastMCP"""
    
    def __init__(self, data_service):
        super().__init__(data_service)
        self.logger.info("Quote tools initialized")
    
    def generate_quote(self, customer_id: str, quote_type: str, coverage_amount: int) -> str:
        """Generate insurance quote (mock calculation)"""
        quote_data = {
            "customer_id": customer_id,
            "type": quote_type,
            "coverage_amount": coverage_amount
        }
        return self.handle_tool_execution(
            "generate_quote",
            self.data_service.generate_quote,
            quote_data=quote_data
        )
    
    def get_quote(self, quote_id: str) -> str:
        """Get existing quote by ID"""
        return self.handle_tool_execution(
            "get_quote",
            self.data_service.get_quote,
            quote_id=quote_id
        )
    
    def register_tools(self, mcp_server):
        """Register all quote tools with the FastMCP server"""
        self.logger.info("Registering quote tools with FastMCP server")
        
        @mcp_server.tool()
        def generate_quote(customer_id: str, quote_type: str, coverage_amount: int) -> str:
            """Generate insurance quote (mock calculation)"""
            return self.generate_quote(customer_id=customer_id, quote_type=quote_type, coverage_amount=coverage_amount)
        
        @mcp_server.tool()
        def get_quote(quote_id: str) -> str:
            """Get existing quote by ID"""
            return self.get_quote(quote_id=quote_id)
        
        self.logger.info("Quote tools registered successfully", tools_count=2) 