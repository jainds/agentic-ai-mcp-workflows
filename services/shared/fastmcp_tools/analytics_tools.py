"""
Analytics Tools Module

FastMCP tools for analytics and risk assessment operations.
"""

from typing import Dict, Any
from .base_tools import BaseTools
import structlog

logger = structlog.get_logger(__name__)


class AnalyticsTools(BaseTools):
    """Analytics and risk assessment tools for FastMCP"""
    
    def __init__(self, data_service):
        super().__init__(data_service)
        self.logger.info("Analytics tools initialized")
    
    def get_customer_risk_profile(self, customer_id: str) -> str:
        """Get risk profile for a customer"""
        return self.handle_tool_execution(
            "get_customer_risk_profile",
            self.data_service.get_customer_risk_profile,
            customer_id=customer_id
        )
    
    def calculate_fraud_score(self, amount: float, claim_type: str) -> str:
        """Calculate fraud score for a claim"""
        claim_data = {"amount": amount, "type": claim_type}
        return self.handle_tool_execution(
            "calculate_fraud_score",
            self.data_service.calculate_fraud_score,
            claim_data=claim_data
        )
    
    def get_market_trends(self) -> str:
        """Get market trends and analytics"""
        return self.handle_tool_execution(
            "get_market_trends",
            self.data_service.get_market_trends
        )
    
    def register_tools(self, mcp_server):
        """Register all analytics tools with the FastMCP server"""
        self.logger.info("Registering analytics tools with FastMCP server")
        
        @mcp_server.tool()
        def get_customer_risk_profile(customer_id: str) -> str:
            """Get risk profile for a customer"""
            return self.get_customer_risk_profile(customer_id=customer_id)
        
        @mcp_server.tool()
        def calculate_fraud_score(amount: float, claim_type: str) -> str:
            """Calculate fraud score for a claim"""
            return self.calculate_fraud_score(amount=amount, claim_type=claim_type)
        
        @mcp_server.tool()
        def get_market_trends() -> str:
            """Get market trends and analytics"""
            return self.get_market_trends()
        
        self.logger.info("Analytics tools registered successfully", tools_count=3) 