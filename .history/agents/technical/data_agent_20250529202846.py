"""
Data Agent - Technical agent providing data access via MCP tools.
Serves as MCP server for claims data, policy information, and analytics.
"""

import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

from agents.shared.a2a_base import A2AAgent, TaskRequest, TaskResponse
from agents.shared.mcp_base import MCPServer, MCPTool, MCPResource, EnterpriseAPIWrapper
from agents.shared.auth import service_auth
import structlog

logger = structlog.get_logger(__name__)


class DataMCPServer(MCPServer):
    """MCP Server for data access and analytics"""
    
    def __init__(self):
        super().__init__(
            name="DataMCPServer",
            description="Provides data access tools for claims, policies, customers, and analytics",
            port=8001
        )
        
        # Initialize API wrappers for enterprise services
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
        
        # Mock data cache for demo purposes
        self.data_cache: Dict[str, Any] = {}
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize mock data for demonstration"""
        # Mock policies
        self.data_cache["policies"] = {
            "POL-001": {
                "policy_number": "POL-001",
                "customer_id": "CUST-001",
                "coverage_limit": 100000,
                "premium": 1200,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "type": "auto",
                "status": "active"
            },
            "POL-002": {
                "policy_number": "POL-002",
                "customer_id": "CUST-002", 
                "coverage_limit": 250000,
                "premium": 2400,
                "start_date": "2024-01-15",
                "end_date": "2024-12-31",
                "type": "home",
                "status": "active"
            }
        }
        
        # Mock customers
        self.data_cache["customers"] = {
            "CUST-001": {
                "id": "CUST-001",
                "name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "555-0123",
                "risk_score": 0.2,
                "claims_history": ["CLM-001", "CLM-002"]
            },
            "CUST-002": {
                "id": "CUST-002",
                "name": "Jane Doe",
                "email": "jane.doe@email.com",
                "phone": "555-0456",
                "risk_score": 0.1,
                "claims_history": []
            }
        }
        
        # Mock claims
        self.data_cache["claims"] = {
            "CLM-001": {
                "claim_id": "CLM-001",
                "policy_number": "POL-001",
                "customer_id": "CUST-001",
                "amount": 5000,
                "status": "approved",
                "created_date": "2024-01-15",
                "description": "Minor accident damage"
            },
            "CLM-002": {
                "claim_id": "CLM-002",
                "policy_number": "POL-001",
                "customer_id": "CUST-001",
                "amount": 12000,
                "status": "processing",
                "created_date": "2024-03-10",
                "description": "Collision repair"
            }
        }
    
    def setup_tools_and_resources(self):
        """Setup MCP tools and resources"""
        
        # Policy tools
        policy_tools = [
            MCPTool(
                name="get_policy",
                description="Get policy information by policy number",
                handler=self._get_policy,
                parameters={
                    "policy_number": {"type": "string", "description": "Policy number to lookup"}
                }
            ),
            MCPTool(
                name="search_policies",
                description="Search policies by customer ID or other criteria",
                handler=self._search_policies,
                parameters={
                    "customer_id": {"type": "string", "description": "Customer ID to search"},
                    "status": {"type": "string", "description": "Policy status filter"}
                }
            ),
            MCPTool(
                name="validate_policy",
                description="Validate if a policy is active and covers specific claim type",
                handler=self._validate_policy,
                parameters={
                    "policy_number": {"type": "string", "description": "Policy number"},
                    "claim_type": {"type": "string", "description": "Type of claim"}
                }
            )
        ]
        
        # Customer tools
        customer_tools = [
            MCPTool(
                name="get_customer",
                description="Get customer information by customer ID",
                handler=self._get_customer,
                parameters={
                    "customer_id": {"type": "string", "description": "Customer ID to lookup"}
                }
            ),
            MCPTool(
                name="get_customer_risk_profile",
                description="Get customer risk assessment and scoring",
                handler=self._get_customer_risk_profile,
                parameters={
                    "customer_id": {"type": "string", "description": "Customer ID"}
                }
            )
        ]
        
        # Claims tools
        claims_tools = [
            MCPTool(
                name="get_recent_claims",
                description="Get recent claims for a customer within specified days",
                handler=self._get_recent_claims,
                parameters={
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "days": {"type": "integer", "description": "Number of days to look back"}
                }
            ),
            MCPTool(
                name="get_claim_history",
                description="Get complete claim history for a customer",
                handler=self._get_claim_history,
                parameters={
                    "customer_id": {"type": "string", "description": "Customer ID"}
                }
            ),
            MCPTool(
                name="calculate_claim_statistics",
                description="Calculate claim statistics and patterns",
                handler=self._calculate_claim_statistics,
                parameters={
                    "period": {"type": "string", "description": "Time period (month, quarter, year)"}
                }
            )
        ]
        
        # Analytics tools
        analytics_tools = [
            MCPTool(
                name="fraud_risk_analysis",
                description="Analyze fraud risk for a claim or customer",
                handler=self._fraud_risk_analysis,
                parameters={
                    "data": {"type": "object", "description": "Claim or customer data"},
                    "analysis_type": {"type": "string", "description": "Type of analysis"}
                }
            ),
            MCPTool(
                name="generate_report",
                description="Generate analytics report",
                handler=self._generate_report,
                parameters={
                    "report_type": {"type": "string", "description": "Type of report"},
                    "filters": {"type": "object", "description": "Report filters"}
                }
            )
        ]
        
        # Add all tools
        for tool in policy_tools + customer_tools + claims_tools + analytics_tools:
            self.add_tool(tool)
        
        # Resources
        resources = [
            MCPResource(
                uri_template="policy://{policy_number}",
                description="Policy data resource",
                handler=self._get_policy_resource
            ),
            MCPResource(
                uri_template="customer://{customer_id}",
                description="Customer data resource", 
                handler=self._get_customer_resource
            ),
            MCPResource(
                uri_template="claims://{customer_id}",
                description="Claims data resource",
                handler=self._get_claims_resource
            )
        ]
        
        for resource in resources:
            self.add_resource(resource)
    
    # Tool implementations
    def _get_policy(self, policy_number: str) -> Dict[str, Any]:
        """Get policy by number"""
        policy = self.data_cache["policies"].get(policy_number)
        if policy:
            logger.info("Policy retrieved", policy_number=policy_number)
            return policy
        else:
            logger.warning("Policy not found", policy_number=policy_number)
            return {"error": f"Policy {policy_number} not found"}
    
    def _search_policies(self, customer_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Search policies by criteria"""
        policies = list(self.data_cache["policies"].values())
        
        if customer_id:
            policies = [p for p in policies if p.get("customer_id") == customer_id]
        
        if status:
            policies = [p for p in policies if p.get("status") == status]
        
        logger.info("Policies searched", customer_id=customer_id, status=status, count=len(policies))
        return policies
    
    def _validate_policy(self, policy_number: str, claim_type: str) -> Dict[str, Any]:
        """Validate policy for claim type"""
        policy = self.data_cache["policies"].get(policy_number)
        
        if not policy:
            return {"valid": False, "reason": "Policy not found"}
        
        if policy.get("status") != "active":
            return {"valid": False, "reason": "Policy not active"}
        
        # Check if policy type covers claim type
        policy_type = policy.get("type")
        coverage_map = {
            "auto": ["collision", "comprehensive", "liability"],
            "home": ["fire", "theft", "water_damage", "liability"],
            "health": ["medical", "dental", "vision"]
        }
        
        covered_types = coverage_map.get(policy_type, [])
        is_covered = claim_type.lower() in covered_types
        
        return {
            "valid": is_covered,
            "policy_type": policy_type,
            "claim_type": claim_type,
            "covered": is_covered
        }
    
    def _get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer by ID"""
        customer = self.data_cache["customers"].get(customer_id)
        if customer:
            logger.info("Customer retrieved", customer_id=customer_id)
            return customer
        else:
            logger.warning("Customer not found", customer_id=customer_id)
            return {"error": f"Customer {customer_id} not found"}
    
    def _get_customer_risk_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get customer risk assessment"""
        customer = self.data_cache["customers"].get(customer_id)
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
        
        # Calculate comprehensive risk profile
        risk_factors = {
            "base_risk_score": customer.get("risk_score", 0.0),
            "claims_frequency": len(customer.get("claims_history", [])),
            "policy_violations": 0,  # Would check violation history
            "payment_history": "good"  # Would check payment patterns
        }
        
        # Calculate composite risk score
        composite_score = risk_factors["base_risk_score"]
        if risk_factors["claims_frequency"] > 3:
            composite_score += 0.2
        
        risk_level = "low" if composite_score < 0.3 else "medium" if composite_score < 0.7 else "high"
        
        return {
            "customer_id": customer_id,
            "risk_level": risk_level,
            "risk_score": composite_score,
            "risk_factors": risk_factors,
            "recommendations": self._get_risk_recommendations(risk_level)
        }
    
    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """Get recommendations based on risk level"""
        recommendations = {
            "low": ["Standard processing", "Automated approval eligible"],
            "medium": ["Additional documentation review", "Supervisor approval required"],
            "high": ["Manual review required", "Fraud investigation recommended", "Additional verification needed"]
        }
        return recommendations.get(risk_level, [])
    
    def _get_recent_claims(self, customer_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Get recent claims for customer"""
        customer = self.data_cache["customers"].get(customer_id)
        if not customer:
            return []
        
        claim_ids = customer.get("claims_history", [])
        claims = []
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for claim_id in claim_ids:
            claim = self.data_cache["claims"].get(claim_id)
            if claim:
                claim_date = datetime.strptime(claim["created_date"], "%Y-%m-%d")
                if claim_date >= cutoff_date:
                    claims.append(claim)
        
        logger.info("Recent claims retrieved", customer_id=customer_id, days=days, count=len(claims))
        return claims
    
    def _get_claim_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get complete claim history"""
        customer = self.data_cache["customers"].get(customer_id)
        if not customer:
            return []
        
        claim_ids = customer.get("claims_history", [])
        claims = []
        
        for claim_id in claim_ids:
            claim = self.data_cache["claims"].get(claim_id)
            if claim:
                claims.append(claim)
        
        # Sort by date descending
        claims.sort(key=lambda x: x["created_date"], reverse=True)
        
        logger.info("Claim history retrieved", customer_id=customer_id, count=len(claims))
        return claims
    
    def _calculate_claim_statistics(self, period: str = "month") -> Dict[str, Any]:
        """Calculate claim statistics"""
        claims = list(self.data_cache["claims"].values())
        
        stats = {
            "total_claims": len(claims),
            "total_amount": sum(claim.get("amount", 0) for claim in claims),
            "average_amount": 0,
            "status_breakdown": {},
            "period": period
        }
        
        if stats["total_claims"] > 0:
            stats["average_amount"] = stats["total_amount"] / stats["total_claims"]
        
        # Status breakdown
        for claim in claims:
            status = claim.get("status", "unknown")
            stats["status_breakdown"][status] = stats["status_breakdown"].get(status, 0) + 1
        
        logger.info("Claim statistics calculated", period=period, total_claims=stats["total_claims"])
        return stats
    
    def _fraud_risk_analysis(self, data: Dict[str, Any], analysis_type: str = "claim") -> Dict[str, Any]:
        """Analyze fraud risk"""
        risk_score = 0.0
        risk_indicators = []
        
        if analysis_type == "claim":
            # Analyze claim data for fraud indicators
            amount = data.get("amount", 0)
            if amount > 50000:
                risk_score += 0.3
                risk_indicators.append("High claim amount")
            
            description = data.get("description", "").lower()
            suspicious_keywords = ["total loss", "stolen", "fire", "vandalism"]
            if any(keyword in description for keyword in suspicious_keywords):
                risk_score += 0.2
                risk_indicators.append("Suspicious keywords in description")
            
        elif analysis_type == "customer":
            # Analyze customer data
            claims_count = len(data.get("claims_history", []))
            if claims_count > 5:
                risk_score += 0.4
                risk_indicators.append("High claims frequency")
            
            base_risk = data.get("risk_score", 0.0)
            risk_score += base_risk * 0.5
        
        risk_level = "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low"
        
        return {
            "risk_score": min(risk_score, 1.0),
            "risk_level": risk_level,
            "risk_indicators": risk_indicators,
            "analysis_type": analysis_type,
            "recommendations": self._get_fraud_recommendations(risk_level)
        }
    
    def _get_fraud_recommendations(self, risk_level: str) -> List[str]:
        """Get fraud prevention recommendations"""
        recommendations = {
            "low": ["Standard processing"],
            "medium": ["Additional verification", "Document review"],
            "high": ["Detailed investigation", "Expert review", "Additional documentation required"]
        }
        return recommendations.get(risk_level, [])
    
    def _generate_report(self, report_type: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate analytics report"""
        if filters is None:
            filters = {}
        
        if report_type == "claims_summary":
            return self._generate_claims_summary_report(filters)
        elif report_type == "fraud_analysis":
            return self._generate_fraud_analysis_report(filters)
        elif report_type == "customer_risk":
            return self._generate_customer_risk_report(filters)
        else:
            return {"error": f"Unknown report type: {report_type}"}
    
    def _generate_claims_summary_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate claims summary report"""
        claims = list(self.data_cache["claims"].values())
        
        # Apply filters
        if filters.get("status"):
            claims = [c for c in claims if c.get("status") == filters["status"]]
        
        report = {
            "report_type": "claims_summary",
            "generated_at": datetime.utcnow().isoformat(),
            "filters": filters,
            "summary": {
                "total_claims": len(claims),
                "total_amount": sum(c.get("amount", 0) for c in claims),
                "average_amount": 0,
                "status_distribution": {}
            },
            "claims": claims
        }
        
        if report["summary"]["total_claims"] > 0:
            report["summary"]["average_amount"] = (
                report["summary"]["total_amount"] / report["summary"]["total_claims"]
            )
        
        # Status distribution
        for claim in claims:
            status = claim.get("status", "unknown")
            report["summary"]["status_distribution"][status] = (
                report["summary"]["status_distribution"].get(status, 0) + 1
            )
        
        return report
    
    def _generate_fraud_analysis_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fraud analysis report"""
        claims = list(self.data_cache["claims"].values())
        customers = list(self.data_cache["customers"].values())
        
        high_risk_claims = []
        high_risk_customers = []
        
        # Analyze claims for fraud risk
        for claim in claims:
            fraud_analysis = self._fraud_risk_analysis(claim, "claim")
            if fraud_analysis["risk_level"] == "high":
                high_risk_claims.append({
                    "claim_id": claim["claim_id"],
                    "risk_score": fraud_analysis["risk_score"],
                    "indicators": fraud_analysis["risk_indicators"]
                })
        
        # Analyze customers for fraud risk
        for customer in customers:
            risk_analysis = self._fraud_risk_analysis(customer, "customer")
            if risk_analysis["risk_level"] == "high":
                high_risk_customers.append({
                    "customer_id": customer["id"],
                    "risk_score": risk_analysis["risk_score"],
                    "indicators": risk_analysis["risk_indicators"]
                })
        
        return {
            "report_type": "fraud_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_claims_analyzed": len(claims),
                "high_risk_claims": len(high_risk_claims),
                "total_customers_analyzed": len(customers),
                "high_risk_customers": len(high_risk_customers)
            },
            "high_risk_claims": high_risk_claims,
            "high_risk_customers": high_risk_customers
        }
    
    def _generate_customer_risk_report(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customer risk assessment report"""
        customers = list(self.data_cache["customers"].values())
        
        risk_distribution = {"low": 0, "medium": 0, "high": 0}
        customer_risks = []
        
        for customer in customers:
            risk_profile = self._get_customer_risk_profile(customer["id"])
            risk_level = risk_profile["risk_level"]
            risk_distribution[risk_level] += 1
            
            customer_risks.append({
                "customer_id": customer["id"],
                "name": customer["name"],
                "risk_level": risk_level,
                "risk_score": risk_profile["risk_score"]
            })
        
        # Sort by risk score descending
        customer_risks.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return {
            "report_type": "customer_risk",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_customers": len(customers),
                "risk_distribution": risk_distribution
            },
            "customer_risks": customer_risks
        }
    
    # Resource implementations
    def _get_policy_resource(self, policy_number: str) -> Dict[str, Any]:
        """Policy resource handler"""
        return self._get_policy(policy_number)
    
    def _get_customer_resource(self, customer_id: str) -> Dict[str, Any]:
        """Customer resource handler"""
        return self._get_customer(customer_id)
    
    def _get_claims_resource(self, customer_id: str) -> List[Dict[str, Any]]:
        """Claims resource handler"""
        return self._get_claim_history(customer_id)


class DataAgent(A2AAgent):
    """Data Agent - provides A2A interface to data MCP server"""
    
    def __init__(self, port: int = 8002):
        capabilities = {
            "streaming": False,
            "pushNotifications": False,
            "fileUpload": False,
            "messageHistory": True,
            "dataAccess": True,
            "analytics": True
        }
        
        super().__init__(
            name="DataAgent",
            description="Provides data access and analytics via MCP tools",
            port=port,
            capabilities=capabilities
        )
        
        # Initialize MCP server
        self.mcp_server = DataMCPServer()
        
        logger.info("Data Agent initialized", port=port)
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process A2A tasks by delegating to MCP server"""
        user_data = task.user
        task_type = user_data.get("type", "data_query")
        
        logger.info("Processing data task", task_id=task.taskId, type=task_type)
        
        try:
            if task_type == "data_query":
                result = await self._handle_data_query(user_data)
            elif task_type == "analytics":
                result = await self._handle_analytics(user_data)
            elif task_type == "report":
                result = await self._handle_report(user_data)
            else:
                result = {"error": f"Unknown task type: {task_type}"}
            
            return TaskResponse(
                taskId=task.taskId,
                parts=[{"text": str(result), "type": "data_response"}],
                status="completed",
                metadata={"agent": "DataAgent", "task_type": task_type}
            )
            
        except Exception as e:
            logger.error("Data task failed", task_id=task.taskId, error=str(e))
            return TaskResponse(
                taskId=task.taskId,
                parts=[{"text": f"Error: {str(e)}", "type": "error"}],
                status="failed",
                metadata={"agent": "DataAgent", "error": str(e)}
            )
    
    async def _handle_data_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data query requests"""
        query_type = data.get("query_type")
        params = data.get("params", {})
        
        # Route to appropriate MCP tool
        if query_type == "get_policy":
            return self.mcp_server._get_policy(**params)
        elif query_type == "get_customer":
            return self.mcp_server._get_customer(**params)
        elif query_type == "get_recent_claims":
            return self.mcp_server._get_recent_claims(**params)
        else:
            return {"error": f"Unknown query type: {query_type}"}
    
    async def _handle_analytics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics requests"""
        analysis_type = data.get("analysis_type")
        params = data.get("params", {})
        
        if analysis_type == "fraud_risk":
            return self.mcp_server._fraud_risk_analysis(**params)
        elif analysis_type == "claim_statistics":
            return self.mcp_server._calculate_claim_statistics(**params)
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}
    
    async def _handle_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generation requests"""
        report_type = data.get("report_type")
        filters = data.get("filters", {})
        
        return self.mcp_server._generate_report(report_type, filters)
    
    def run_mcp_server(self):
        """Run the MCP server"""
        self.mcp_server.run()


# Main execution
if __name__ == "__main__":
    import threading
    
    # Parse command line arguments for which component to run
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        # Run MCP server only
        mcp_server = DataMCPServer()
        mcp_server.run()
    else:
        # Run A2A agent with embedded MCP server
        agent_port = int(os.getenv("DATA_AGENT_PORT", "8002"))
        mcp_port = int(os.getenv("DATA_MCP_PORT", "8001"))
        
        agent = DataAgent(port=agent_port)
        
        # Run MCP server in separate thread
        mcp_thread = threading.Thread(target=agent.run_mcp_server)
        mcp_thread.daemon = True
        mcp_thread.start()
        
        try:
            # Run A2A agent
            agent.run()
        except KeyboardInterrupt:
            logger.info("Data Agent shutting down")
        finally:
            logger.info("Data Agent stopped") 