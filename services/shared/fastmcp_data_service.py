"""
FastMCP Data Service - Comprehensive insurance data service using FastMCP
Reads actual data from JSON file, provides MCP tools for all insurance operations
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid
import copy
from datetime import timedelta

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

import structlog

logger = structlog.get_logger(__name__)


class FastMCPDataService:
    """FastMCP service for comprehensive insurance data operations"""
    
    def __init__(self, data_file_path: Optional[str] = None):
        self.data_file_path = data_file_path or self._get_default_data_path()
        self.data = {}
        self.mcp_server = None
        self._load_data()
        
        if FASTMCP_AVAILABLE:
            self._initialize_mcp_server()
        else:
            logger.warning("FastMCP not available, running without MCP support")
    
    def _get_default_data_path(self) -> str:
        """Get default path to mock data JSON file"""
        current_dir = Path(__file__).parent
        return str(current_dir / "mock_data.json")
    
    def _load_data(self):
        """Load data from JSON file"""
        try:
            with open(self.data_file_path, 'r') as f:
                self.data = json.load(f)
            logger.info("Mock data loaded successfully", 
                       users=len(self.data.get('users', [])),
                       policies=len(self.data.get('policies', [])),
                       claims=len(self.data.get('claims', [])))
        except FileNotFoundError:
            logger.error(f"Mock data file not found: {self.data_file_path}")
            self.data = self._get_empty_data_structure()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in data file: {e}")
            self.data = self._get_empty_data_structure()
    
    def _get_empty_data_structure(self) -> Dict[str, Any]:
        """Return empty data structure"""
        return {
            "users": [],
            "policies": [],
            "claims": [],
            "analytics": {
                "customer_risk_profiles": [],
                "market_trends": {},
                "fraud_indicators": []
            },
            "quotes": []
        }
    
    def _initialize_mcp_server(self):
        """Initialize FastMCP server with all tools"""
        self.mcp_server = FastMCP("Insurance Data Service")
        
        # User management tools
        self.mcp_server.tool(
            name="get_user",
            description="Get user information by ID or email"
        )(self.get_user)
        
        self.mcp_server.tool(
            name="list_users", 
            description="List all users with optional filtering"
        )(self.list_users)
        
        self.mcp_server.tool(
            name="create_user",
            description="Create a new user (mock write operation)"
        )(self.create_user)
        
        # Policy management tools
        self.mcp_server.tool(
            name="get_policy",
            description="Get policy information by ID"
        )(self.get_policy)
        
        self.mcp_server.tool(
            name="get_customer_policies",
            description="Get all policies for a customer"
        )(self.get_customer_policies)
        
        self.mcp_server.tool(
            name="create_policy",
            description="Create a new policy (mock write operation)"
        )(self.create_policy)
        
        # Claims management tools
        self.mcp_server.tool(
            name="get_claim",
            description="Get claim information by ID"
        )(self.get_claim)
        
        self.mcp_server.tool(
            name="get_customer_claims",
            description="Get all claims for a customer"
        )(self.get_customer_claims)
        
        self.mcp_server.tool(
            name="create_claim",
            description="Create a new claim (mock write operation)"
        )(self.create_claim)
        
        self.mcp_server.tool(
            name="update_claim_status",
            description="Update claim status (mock write operation)"
        )(self.update_claim_status)
        
        # Analytics tools
        self.mcp_server.tool(
            name="get_customer_risk_profile",
            description="Get risk profile for a customer"
        )(self.get_customer_risk_profile)
        
        self.mcp_server.tool(
            name="calculate_fraud_score",
            description="Calculate fraud score for a claim"
        )(self.calculate_fraud_score)
        
        self.mcp_server.tool(
            name="get_market_trends",
            description="Get market trends and analytics"
        )(self.get_market_trends)
        
        # Quote tools
        self.mcp_server.tool(
            name="generate_quote",
            description="Generate insurance quote (mock calculation)"
        )(self.generate_quote)
        
        self.mcp_server.tool(
            name="get_quote",
            description="Get existing quote by ID"
        )(self.get_quote)
        
        logger.info("FastMCP server initialized with all insurance tools")
    
    # User operations (actual reads from JSON)
    def get_user(self, user_id: str = None, email: str = None) -> Dict[str, Any]:
        """Get user by ID or email"""
        users = self.data.get('users', [])
        
        if user_id:
            user = next((u for u in users if u['id'] == user_id), None)
        elif email:
            user = next((u for u in users if u['email'] == email), None)
        else:
            return {"success": False, "error": "Either user_id or email must be provided"}
        
        if user:
            return {"success": True, "data": user}
        else:
            return {"success": False, "error": "User not found"}
    
    def list_users(self, role: str = None, status: str = None) -> Dict[str, Any]:
        """List users with optional filtering"""
        users = self.data.get('users', [])
        
        if role:
            users = [u for u in users if u.get('role') == role]
        if status:
            users = [u for u in users if u.get('status') == status]
        
        return {"success": True, "data": users, "count": len(users)}
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user (mock write operation)"""
        new_user = {
            "id": f"user_{uuid.uuid4().hex[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            **user_data
        }
        
        # This is a mock write - in reality would persist to storage
        logger.info("Mock user creation", user_id=new_user["id"], email=user_data.get("email"))
        
        return {"success": True, "data": new_user, "message": "User created (mock operation)"}
    
    # Policy operations (actual reads from JSON)
    def get_policy(self, policy_id: str) -> Dict[str, Any]:
        """Get policy by ID"""
        policies = self.data.get('policies', [])
        policy = next((p for p in policies if p['id'] == policy_id), None)
        
        if policy:
            return {"success": True, "data": policy}
        else:
            return {"success": False, "error": "Policy not found"}
    
    def get_customer_policies(self, customer_id: str) -> Dict[str, Any]:
        """Get all policies for a customer"""
        policies = self.data.get('policies', [])
        customer_policies = [p for p in policies if p.get('customer_id') == customer_id]
        
        return {
            "success": True, 
            "data": customer_policies, 
            "count": len(customer_policies),
            "customer_id": customer_id
        }
    
    def create_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create policy (mock write operation)"""
        new_policy = {
            "id": f"POL-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}",
            "start_date": datetime.now(timezone.utc).isoformat(),
            **policy_data
        }
        
        # Mock write operation
        logger.info("Mock policy creation", policy_id=new_policy["id"], 
                   customer_id=policy_data.get("customer_id"))
        
        return {"success": True, "data": new_policy, "message": "Policy created (mock operation)"}
    
    # Claims operations (actual reads from JSON)
    def get_claim(self, claim_id: str) -> Dict[str, Any]:
        """Get claim by ID"""
        claims = self.data.get('claims', [])
        claim = next((c for c in claims if c['id'] == claim_id), None)
        
        if claim:
            return {"success": True, "data": claim}
        else:
            return {"success": False, "error": "Claim not found"}
    
    def get_customer_claims(self, customer_id: str) -> Dict[str, Any]:
        """Get all claims for a customer"""
        claims = self.data.get('claims', [])
        customer_claims = [c for c in claims if c.get('customer_id') == customer_id]
        
        return {
            "success": True,
            "data": customer_claims,
            "count": len(customer_claims),
            "customer_id": customer_id
        }
    
    def create_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create claim (mock write operation)"""
        new_claim = {
            "id": f"CLM-{datetime.now().year}-{uuid.uuid4().hex[:3].upper()}",
            "filed_date": datetime.now(timezone.utc).isoformat(),
            "status": "processing",
            "fraud_score": 0.1,  # Default low fraud score
            "risk_assessment": "pending",
            **claim_data
        }
        
        # Mock write operation
        logger.info("Mock claim creation", claim_id=new_claim["id"],
                   customer_id=claim_data.get("customer_id"))
        
        return {"success": True, "data": new_claim, "message": "Claim created (mock operation)"}
    
    def update_claim_status(self, claim_id: str, status: str, notes: str = None) -> Dict[str, Any]:
        """Update claim status (mock write operation)"""
        # Mock update operation
        update_data = {
            "claim_id": claim_id,
            "new_status": status,
            "update_date": datetime.now(timezone.utc).isoformat(),
            "notes": notes
        }
        
        logger.info("Mock claim status update", claim_id=claim_id, status=status)
        
        return {"success": True, "data": update_data, "message": "Claim status updated (mock operation)"}
    
    # Analytics operations (actual reads from JSON)
    def get_customer_risk_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get customer risk profile"""
        analytics = self.data.get('analytics', {})
        risk_profiles = analytics.get('customer_risk_profiles', [])
        
        profile = next((p for p in risk_profiles if p['customer_id'] == customer_id), None)
        
        if profile:
            return {"success": True, "data": profile}
        else:
            # Generate default risk profile
            default_profile = {
                "customer_id": customer_id,
                "overall_risk_score": "medium", 
                "fraud_probability": 0.1,
                "credit_score": 700,
                "claims_history_score": "average",
                "payment_history_score": "good",
                "recommendations": ["Review coverage options", "Consider safe driver course"],
                "factors": {
                    "positive": ["Timely payments"],
                    "negative": ["Limited history"]
                }
            }
            return {"success": True, "data": default_profile, "note": "Default profile generated"}
    
    def calculate_fraud_score(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate fraud score for claim"""
        fraud_indicators = self.data.get('analytics', {}).get('fraud_indicators', [])
        
        # Simple fraud score calculation based on indicators
        base_score = 0.05
        risk_factors = []
        
        # Check for high claim amount
        if claim_data.get('amount_claimed', 0) > 5000:
            base_score += 0.2
            risk_factors.append("High claim amount")
        
        # Check for recent claims (mock check)
        if claim_data.get('recent_claims_count', 0) > 1:
            base_score += 0.3
            risk_factors.append("Multiple recent claims")
        
        fraud_score = min(base_score, 1.0)  # Cap at 1.0
        
        result = {
            "fraud_score": fraud_score,
            "risk_level": "low" if fraud_score < 0.3 else "medium" if fraud_score < 0.7 else "high",
            "risk_factors": risk_factors,
            "indicators_used": [ind['indicator'] for ind in fraud_indicators]
        }
        
        return {"success": True, "data": result}
    
    def get_market_trends(self) -> Dict[str, Any]:
        """Get market trends"""
        market_trends = self.data.get('analytics', {}).get('market_trends', {})
        
        if market_trends:
            return {"success": True, "data": market_trends}
        else:
            # Return default trends
            default_trends = {
                "auto_insurance": {"avg_premium_change": 0.02, "claim_frequency_trend": 0.01},
                "home_insurance": {"avg_premium_change": 0.04, "claim_frequency_trend": 0.02}
            }
            return {"success": True, "data": default_trends, "note": "Default trends provided"}
    
    # Quote operations
    def generate_quote(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insurance quote (mock calculation)"""
        coverage_type = quote_data.get('type', 'auto')
        coverage_amount = quote_data.get('coverage_amount', 100000)
        
        # Simple premium calculation
        base_rate = 0.001 if coverage_type == 'auto' else 0.0005
        calculated_premium = coverage_amount * base_rate
        
        # Apply discounts
        discount = 0.1 if quote_data.get('bundle_discount') else 0
        final_premium = calculated_premium * (1 - discount)
        
        # Calculate expiry date (30 days from now)
        expiry_date = datetime.now(timezone.utc) + timedelta(days=30)
        
        new_quote = {
            "id": f"QTE-{datetime.now().year}-{uuid.uuid4().hex[:3].upper()}",
            "customer_id": quote_data.get('customer_id'),
            "type": coverage_type,
            "status": "pending",
            "requested_coverage": quote_data,
            "calculated_premium": round(calculated_premium, 2),
            "discount_applied": round(calculated_premium * discount, 2),
            "final_premium": round(final_premium, 2),
            "quote_date": datetime.now(timezone.utc).isoformat(),
            "expires_date": expiry_date.isoformat()
        }
        
        logger.info("Quote generated", quote_id=new_quote["id"], 
                   premium=final_premium, type=coverage_type)
        
        return {"success": True, "data": new_quote, "message": "Quote generated"}
    
    def get_quote(self, quote_id: str) -> Dict[str, Any]:
        """Get quote by ID"""
        quotes = self.data.get('quotes', [])
        quote = next((q for q in quotes if q['id'] == quote_id), None)
        
        if quote:
            return {"success": True, "data": quote}
        else:
            return {"success": False, "error": "Quote not found"}
    
    def get_server(self):
        """Get the FastMCP server instance"""
        return self.mcp_server
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools"""
        if not self.mcp_server:
            return []
        
        # Return tool schemas from FastMCP server
        tools = []
        
        # User tools
        tools.extend([
            {"name": "get_user", "description": "Get user information by ID or email"},
            {"name": "list_users", "description": "List all users with optional filtering"},
            {"name": "create_user", "description": "Create a new user (mock write operation)"}
        ])
        
        # Policy tools
        tools.extend([
            {"name": "get_policy", "description": "Get policy information by ID"},
            {"name": "get_customer_policies", "description": "Get all policies for a customer"},
            {"name": "create_policy", "description": "Create a new policy (mock write operation)"}
        ])
        
        # Claims tools
        tools.extend([
            {"name": "get_claim", "description": "Get claim information by ID"},
            {"name": "get_customer_claims", "description": "Get all claims for a customer"},
            {"name": "create_claim", "description": "Create a new claim (mock write operation)"},
            {"name": "update_claim_status", "description": "Update claim status (mock write operation)"}
        ])
        
        # Analytics tools
        tools.extend([
            {"name": "get_customer_risk_profile", "description": "Get risk profile for a customer"},
            {"name": "calculate_fraud_score", "description": "Calculate fraud score for a claim"},
            {"name": "get_market_trends", "description": "Get market trends and analytics"}
        ])
        
        # Quote tools
        tools.extend([
            {"name": "generate_quote", "description": "Generate insurance quote (mock calculation)"},
            {"name": "get_quote", "description": "Get existing quote by ID"}
        ])
        
        return tools


# Singleton instance for easy import
_data_service_instance = None

def get_data_service() -> FastMCPDataService:
    """Get singleton data service instance"""
    global _data_service_instance
    if _data_service_instance is None:
        _data_service_instance = FastMCPDataService()
    return _data_service_instance 