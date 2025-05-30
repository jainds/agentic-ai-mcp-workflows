"""
Data Agent - Technical agent providing MCP tools for data access and analytics.
Handles database queries, API calls, and data analysis for domain agents.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import random

from agents.shared.mcp_base import MCPServer, MCPToolDef, EnterpriseAPIWrapper
import structlog

logger = structlog.get_logger(__name__)


class DataAgent(MCPServer):
    """Technical agent providing data access and analysis tools via MCP"""
    
    def __init__(self, port: int = 8002):
        super().__init__(
            name="DataAgent",
            description="MCP server providing data access, analytics, and enterprise API integration",
            port=port
        )
        
        # Initialize enterprise API wrappers
        self.claims_api = EnterpriseAPIWrapper(
            os.getenv("CLAIMS_API_URL", "http://claims-service:8000")
        )
        self.user_api = EnterpriseAPIWrapper(
            os.getenv("USER_API_URL", "http://user-service:8000")
        )
        self.policy_api = EnterpriseAPIWrapper(
            os.getenv("POLICY_API_URL", "http://policy-service:8000")
        )
        self.analytics_api = EnterpriseAPIWrapper(
            os.getenv("ANALYTICS_API_URL", "http://analytics-service:8000")
        )
        
        # Data caches (in production, use proper caching like Redis)
        self.customer_cache: Dict[str, Dict[str, Any]] = {}
        self.policy_cache: Dict[str, Dict[str, Any]] = {}
        self.claims_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("Data Agent initialized", port=port)
    
    def setup_tools_and_resources(self):
        """Setup data access and analytics MCP tools"""
        
        # Customer data tools
        get_customer_tool = MCPToolDef(
            name="get_customer",
            description="Get customer information by customer ID",
            handler=self._get_customer,
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID to look up"}
                },
                "required": ["customer_id"]
            }
        )
        self.add_tool(get_customer_tool)
        
        # Policy data tools
        get_policy_tool = MCPToolDef(
            name="get_policy",
            description="Get policy information by policy number",
            handler=self._get_policy,
            parameters={
                "type": "object",
                "properties": {
                    "policy_number": {"type": "string", "description": "Policy number to look up"}
                },
                "required": ["policy_number"]
            }
        )
        self.add_tool(get_policy_tool)
        
        get_customer_policies_tool = MCPToolDef(
            name="get_customer_policies",
            description="Get all policies for a customer",
            handler=self._get_customer_policies,
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"}
                },
                "required": ["customer_id"]
            }
        )
        self.add_tool(get_customer_policies_tool)
        
        # Claims data tools
        get_customer_claims_tool = MCPToolDef(
            name="get_customer_claims",
            description="Get all claims for a customer",
            handler=self._get_customer_claims,
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"}
                },
                "required": ["customer_id"]
            }
        )
        self.add_tool(get_customer_claims_tool)
        
        create_claim_tool = MCPToolDef(
            name="create_claim",
            description="Create a new insurance claim",
            handler=self._create_claim,
            parameters={
                "type": "object",
                "properties": {
                    "claim_data": {
                        "type": "object",
                        "description": "Claim information",
                        "properties": {
                            "policy_number": {"type": "string"},
                            "customer_id": {"type": "string"},
                            "incident_date": {"type": "string"},
                            "description": {"type": "string"},
                            "amount": {"type": "number"},
                            "claim_type": {"type": "string"}
                        },
                        "required": ["customer_id", "description"]
                    }
                },
                "required": ["claim_data"]
            }
        )
        self.add_tool(create_claim_tool)
        
        # Fraud analysis tools
        analyze_fraud_tool = MCPToolDef(
            name="analyze_fraud",
            description="Analyze claim for fraud indicators",
            handler=self._analyze_fraud,
            parameters={
                "type": "object",
                "properties": {
                    "claim_data": {"type": "object", "description": "Claim information"},
                    "customer_data": {"type": "object", "description": "Customer information"}
                },
                "required": ["claim_data"]
            }
        )
        self.add_tool(analyze_fraud_tool)
        
        # Analytics tools
        get_claims_analytics_tool = MCPToolDef(
            name="get_claims_analytics",
            description="Get claims analytics and metrics",
            handler=self._get_claims_analytics,
            parameters={
                "type": "object",
                "properties": {
                    "time_period": {"type": "string", "enum": ["7d", "30d", "90d", "1y"], "default": "30d"},
                    "metric_type": {"type": "string", "enum": ["volume", "value", "fraud", "processing_time"], "default": "volume"}
                }
            }
        )
        self.add_tool(get_claims_analytics_tool)
        
        get_risk_profile_tool = MCPToolDef(
            name="get_risk_profile",
            description="Get risk profile for a customer",
            handler=self._get_risk_profile,
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"}
                },
                "required": ["customer_id"]
            }
        )
        self.add_tool(get_risk_profile_tool)
        
        # Search and query tools
        search_claims_tool = MCPToolDef(
            name="search_claims",
            description="Search claims by various criteria",
            handler=self._search_claims,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "filters": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "claim_type": {"type": "string"},
                            "date_from": {"type": "string"},
                            "date_to": {"type": "string"},
                            "amount_min": {"type": "number"},
                            "amount_max": {"type": "number"}
                        }
                    },
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        )
        self.add_tool(search_claims_tool)
    
    async def _get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer information"""
        try:
            # Check cache first
            if customer_id in self.customer_cache:
                logger.info("Customer data retrieved from cache", customer_id=customer_id)
                return self.customer_cache[customer_id]
            
            # Call User API
            customer_data = await self.user_api.get(f"/customers/{customer_id}")
            
            if not customer_data:
                # Generate mock customer data for demo
                customer_data = {
                    "customer_id": customer_id,
                    "name": f"Customer {customer_id}",
                    "email": f"customer{customer_id}@insurance.com",
                    "phone": "+1234567890",
                    "address": "123 Main St, Anytown, USA",
                    "risk_score": random.uniform(0.1, 0.8),
                    "created_at": "2023-01-01T00:00:00Z",
                    "status": "active"
                }
            
            # Cache the result
            self.customer_cache[customer_id] = customer_data
            
            logger.info("Customer data retrieved", customer_id=customer_id)
            return customer_data
            
        except Exception as e:
            logger.error("Failed to get customer", customer_id=customer_id, error=str(e))
            return {"error": f"Failed to retrieve customer {customer_id}: {str(e)}"}
    
    async def _get_policy(self, policy_number: str) -> Dict[str, Any]:
        """Get policy information"""
        try:
            # Check cache first
            if policy_number in self.policy_cache:
                logger.info("Policy data retrieved from cache", policy_number=policy_number)
                return self.policy_cache[policy_number]
            
            # Call Policy API
            policy_data = await self.policy_api.get(f"/policies/{policy_number}")
            
            if not policy_data:
                # Generate mock policy data for demo
                policy_data = {
                    "policy_number": policy_number,
                    "customer_id": f"cust_{policy_number.split('_')[0] if '_' in policy_number else '123'}",
                    "policy_type": random.choice(["auto", "home", "health", "life"]),
                    "coverage_limit": random.randint(10000, 1000000),
                    "deductible": random.randint(500, 5000),
                    "premium": random.randint(500, 5000),
                    "start_date": "2023-01-01T00:00:00Z",
                    "end_date": "2024-01-01T00:00:00Z",
                    "status": "active"
                }
            
            # Cache the result
            self.policy_cache[policy_number] = policy_data
            
            logger.info("Policy data retrieved", policy_number=policy_number)
            return policy_data
            
        except Exception as e:
            logger.error("Failed to get policy", policy_number=policy_number, error=str(e))
            return {"error": f"Failed to retrieve policy {policy_number}: {str(e)}"}
    
    async def _get_customer_policies(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all policies for a customer"""
        try:
            # Call Policy API
            policies = await self.policy_api.get(f"/policies", params={"customer_id": customer_id})
            
            if not policies:
                # Generate mock policies for demo
                policy_types = ["auto", "home", "health"]
                policies = []
                for i, policy_type in enumerate(policy_types):
                    policy = {
                        "policy_number": f"{customer_id}_{policy_type}_{i+1}",
                        "customer_id": customer_id,
                        "policy_type": policy_type,
                        "coverage_limit": random.randint(10000, 500000),
                        "deductible": random.randint(500, 5000),
                        "premium": random.randint(500, 3000),
                        "start_date": "2023-01-01T00:00:00Z",
                        "end_date": "2024-01-01T00:00:00Z",
                        "status": "active"
                    }
                    policies.append(policy)
                    # Cache individual policies
                    self.policy_cache[policy["policy_number"]] = policy
            
            logger.info("Customer policies retrieved", customer_id=customer_id, count=len(policies))
            return policies
            
        except Exception as e:
            logger.error("Failed to get customer policies", customer_id=customer_id, error=str(e))
            return []
    
    async def _get_customer_claims(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all claims for a customer"""
        try:
            # Check cache first
            if customer_id in self.claims_cache:
                logger.info("Claims data retrieved from cache", customer_id=customer_id)
                return self.claims_cache[customer_id]
            
            # Call Claims API
            claims = await self.claims_api.get(f"/claims", params={"customer_id": customer_id})
            
            if not claims:
                # Generate mock claims for demo
                claims = []
                for i in range(random.randint(0, 3)):
                    claim = {
                        "claim_id": f"CLM_{customer_id}_{i+1}",
                        "customer_id": customer_id,
                        "policy_number": f"{customer_id}_auto_1",
                        "claim_type": random.choice(["auto", "home", "health"]),
                        "status": random.choice(["pending", "processing", "approved", "rejected"]),
                        "amount": random.randint(1000, 50000),
                        "description": f"Sample claim {i+1} for customer {customer_id}",
                        "incident_date": (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
                        "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                        "fraud_score": random.uniform(0.0, 1.0)
                    }
                    claims.append(claim)
            
            # Cache the result
            self.claims_cache[customer_id] = claims
            
            logger.info("Customer claims retrieved", customer_id=customer_id, count=len(claims))
            return claims
            
        except Exception as e:
            logger.error("Failed to get customer claims", customer_id=customer_id, error=str(e))
            return []
    
    async def _create_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new claim"""
        try:
            # Generate claim ID
            claim_id = f"CLM_{datetime.utcnow().strftime('%Y%m%d')}_{random.randint(1000, 9999)}"
            
            # Enhance claim data
            enhanced_claim = {
                "claim_id": claim_id,
                "status": "processing",
                "created_at": datetime.utcnow().isoformat(),
                "fraud_score": 0.0,
                **claim_data
            }
            
            # Call Claims API to create claim
            result = await self.claims_api.post("/claims", enhanced_claim)
            
            if not result:
                # Mock successful creation
                result = enhanced_claim
            
            # Update cache
            customer_id = claim_data.get("customer_id")
            if customer_id and customer_id in self.claims_cache:
                self.claims_cache[customer_id].append(result)
            
            logger.info("Claim created successfully", claim_id=claim_id, customer_id=customer_id)
            return result
            
        except Exception as e:
            logger.error("Failed to create claim", error=str(e))
            return {"error": f"Failed to create claim: {str(e)}"}
    
    async def _analyze_fraud(self, claim_data: Dict[str, Any], customer_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze claim for fraud indicators"""
        try:
            fraud_score = 0.0
            indicators = []
            
            # Basic fraud analysis logic
            claim_amount = float(claim_data.get("amount", 0))
            
            # Check claim amount thresholds
            if claim_amount > 50000:
                fraud_score += 0.3
                indicators.append("High claim amount")
            elif claim_amount > 100000:
                fraud_score += 0.5
                indicators.append("Very high claim amount")
            
            # Check customer risk score if provided
            if customer_data:
                customer_risk = customer_data.get("risk_score", 0.0)
                fraud_score += customer_risk * 0.4
                if customer_risk > 0.7:
                    indicators.append("High-risk customer")
            
            # Check description for suspicious keywords
            description = claim_data.get("description", "").lower()
            suspicious_keywords = ["total loss", "stolen", "fire", "vandalism", "mysterious"]
            
            for keyword in suspicious_keywords:
                if keyword in description:
                    fraud_score += 0.2
                    indicators.append(f"Suspicious keyword: {keyword}")
            
            # Check incident date (claims too soon after policy start are suspicious)
            incident_date = claim_data.get("incident_date")
            if incident_date:
                incident_dt = datetime.fromisoformat(incident_date.replace('Z', '+00:00'))
                days_since_incident = (datetime.utcnow() - incident_dt.replace(tzinfo=None)).days
                
                if days_since_incident < 7:
                    fraud_score += 0.3
                    indicators.append("Claim filed very soon after incident")
            
            # Ensure fraud score is between 0 and 1
            fraud_score = min(fraud_score, 1.0)
            
            # Determine risk level
            if fraud_score > 0.7:
                risk_level = "high"
            elif fraud_score > 0.4:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            result = {
                "fraud_score": round(fraud_score, 3),
                "risk_level": risk_level,
                "indicators": indicators,
                "recommendation": self._get_fraud_recommendation(fraud_score),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Fraud analysis completed", 
                       claim_id=claim_data.get("claim_id"), 
                       fraud_score=fraud_score, 
                       risk_level=risk_level)
            
            return result
            
        except Exception as e:
            logger.error("Fraud analysis failed", error=str(e))
            return {
                "fraud_score": 0.5,
                "risk_level": "unknown",
                "indicators": [],
                "recommendation": "Manual review required due to analysis error",
                "error": str(e)
            }
    
    def _get_fraud_recommendation(self, fraud_score: float) -> str:
        """Get fraud recommendation based on score"""
        if fraud_score > 0.8:
            return "Immediate investigation required"
        elif fraud_score > 0.6:
            return "Detailed review recommended"
        elif fraud_score > 0.4:
            return "Standard verification process"
        else:
            return "Low risk - standard processing"
    
    async def _get_claims_analytics(self, time_period: str = "30d", metric_type: str = "volume") -> Dict[str, Any]:
        """Get claims analytics and metrics"""
        try:
            # Call Analytics API
            analytics = await self.analytics_api.get(f"/analytics/claims", params={
                "time_period": time_period,
                "metric_type": metric_type
            })
            
            if not analytics:
                # Generate mock analytics for demo
                days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[time_period]
                
                if metric_type == "volume":
                    analytics = {
                        "total_claims": random.randint(100, 1000) * (days // 30),
                        "time_period": time_period,
                        "metric_type": metric_type,
                        "trend": random.choice(["increasing", "decreasing", "stable"]),
                        "period_data": [
                            {
                                "date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"),
                                "value": random.randint(10, 50)
                            } for i in range(min(days, 30))
                        ]
                    }
                elif metric_type == "fraud":
                    analytics = {
                        "fraud_rate": round(random.uniform(0.02, 0.08), 3),
                        "total_fraud_cases": random.randint(5, 50),
                        "time_period": time_period,
                        "metric_type": metric_type,
                        "high_risk_claims": random.randint(1, 10)
                    }
            
            logger.info("Claims analytics retrieved", time_period=time_period, metric_type=metric_type)
            return analytics
            
        except Exception as e:
            logger.error("Failed to get claims analytics", error=str(e))
            return {"error": f"Failed to retrieve analytics: {str(e)}"}
    
    async def _get_risk_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get risk profile for a customer"""
        try:
            # Get customer data first
            customer_data = await self._get_customer(customer_id)
            if "error" in customer_data:
                return customer_data
            
            # Get customer's claims history
            claims = await self._get_customer_claims(customer_id)
            
            # Calculate risk metrics
            total_claims = len(claims)
            total_claim_amount = sum(claim.get("amount", 0) for claim in claims)
            avg_fraud_score = sum(claim.get("fraud_score", 0) for claim in claims) / max(total_claims, 1)
            
            # Recent claims (last 90 days)
            recent_claims = [
                claim for claim in claims 
                if (datetime.utcnow() - datetime.fromisoformat(claim.get("created_at", "2020-01-01T00:00:00"))).days <= 90
            ]
            
            # Calculate overall risk score
            risk_score = customer_data.get("risk_score", 0.0)
            
            # Adjust based on claims history
            if total_claims > 3:
                risk_score += 0.2
            if len(recent_claims) > 1:
                risk_score += 0.3
            if avg_fraud_score > 0.5:
                risk_score += 0.2
            
            risk_score = min(risk_score, 1.0)
            
            profile = {
                "customer_id": customer_id,
                "overall_risk_score": round(risk_score, 3),
                "risk_category": "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low",
                "total_claims": total_claims,
                "recent_claims_count": len(recent_claims),
                "total_claim_amount": total_claim_amount,
                "average_fraud_score": round(avg_fraud_score, 3),
                "last_claim_date": max((claim.get("created_at") for claim in claims), default=None),
                "risk_factors": self._identify_risk_factors(customer_data, claims, recent_claims),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            logger.info("Risk profile generated", customer_id=customer_id, risk_score=risk_score)
            return profile
            
        except Exception as e:
            logger.error("Failed to get risk profile", customer_id=customer_id, error=str(e))
            return {"error": f"Failed to generate risk profile: {str(e)}"}
    
    def _identify_risk_factors(self, customer_data: Dict[str, Any], claims: List[Dict[str, Any]], recent_claims: List[Dict[str, Any]]) -> List[str]:
        """Identify risk factors for a customer"""
        factors = []
        
        if len(claims) > 3:
            factors.append("Multiple claims history")
        
        if len(recent_claims) > 1:
            factors.append("Multiple recent claims")
        
        if customer_data.get("risk_score", 0) > 0.6:
            factors.append("High baseline risk score")
        
        high_fraud_claims = [claim for claim in claims if claim.get("fraud_score", 0) > 0.7]
        if high_fraud_claims:
            factors.append("Previous high-risk claims")
        
        return factors
    
    async def _search_claims(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search claims by various criteria"""
        try:
            # Call Claims API with search parameters
            params = {"q": query, "limit": limit}
            if filters:
                params.update(filters)
            
            results = await self.claims_api.get("/claims/search", params=params)
            
            if not results:
                # Generate mock search results for demo
                results = []
                for i in range(min(limit, 5)):
                    claim = {
                        "claim_id": f"CLM_SEARCH_{i+1}",
                        "customer_id": f"cust_{i+1}",
                        "policy_number": f"POL_{i+1}",
                        "claim_type": random.choice(["auto", "home", "health"]),
                        "status": random.choice(["pending", "processing", "approved"]),
                        "amount": random.randint(1000, 25000),
                        "description": f"Search result {i+1} matching '{query}'",
                        "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 100))).isoformat(),
                        "relevance_score": random.uniform(0.7, 1.0)
                    }
                    results.append(claim)
            
            logger.info("Claims search completed", query=query, results=len(results))
            return results
            
        except Exception as e:
            logger.error("Claims search failed", query=query, error=str(e))
            return []


# Main execution
if __name__ == "__main__":
    port = int(os.getenv("DATA_AGENT_PORT", "8002"))
    agent = DataAgent(port=port)
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        logger.info("Data Agent shutting down") 