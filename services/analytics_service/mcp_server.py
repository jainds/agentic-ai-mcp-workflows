"""
FastMCP Server for Analytics Service
Integrates with the existing FastAPI analytics service to provide MCP tools
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
import structlog

logger = structlog.get_logger(__name__)

class AnalyticsMCPServer:
    """FastMCP server for analytics operations"""
    
    def __init__(self, fastapi_app: FastAPI):
        self.app = fastapi_app
        
        # Initialize FastMCP server
        self.mcp = FastMCP(
            name="analytics-service",
            dependencies=["fastapi", "structlog", "pydantic"]
        )
        
        self._setup_tools()
        self._setup_resources()
        self._integrate_with_fastapi()
    
    def _setup_tools(self):
        """Setup MCP tools for analytics operations"""
        
        # Tool: Generate report
        @self.mcp.tool()
        def generate_report(report_type: str, customer_id: Optional[str] = None, 
                           start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
            """Generate analytics report"""
            try:
                from datetime import datetime, timedelta
                import random
                
                # Mock data generation for different report types
                if report_type.lower() == "customer":
                    if not customer_id:
                        return {"success": False, "error": "customer_id required for customer report"}
                    
                    report = {
                        "report_type": "customer",
                        "customer_id": customer_id,
                        "total_policies": random.randint(1, 5),
                        "total_claims": random.randint(0, 3),
                        "total_premium": round(random.uniform(500, 5000), 2),
                        "risk_score": round(random.uniform(0.1, 1.0), 2),
                        "claim_ratio": round(random.uniform(0.0, 0.3), 2),
                        "customer_since": (datetime.utcnow() - timedelta(days=random.randint(30, 1095))).isoformat()
                    }
                
                elif report_type.lower() == "claims":
                    report = {
                        "report_type": "claims",
                        "total_claims": random.randint(50, 200),
                        "approved_claims": random.randint(30, 150),
                        "rejected_claims": random.randint(5, 30),
                        "average_claim_amount": round(random.uniform(1000, 10000), 2),
                        "total_claim_amount": round(random.uniform(50000, 500000), 2),
                        "processing_time_avg": round(random.uniform(5, 15), 1)
                    }
                
                elif report_type.lower() == "policies":
                    report = {
                        "report_type": "policies",
                        "total_policies": random.randint(100, 500),
                        "active_policies": random.randint(80, 400),
                        "cancelled_policies": random.randint(5, 50),
                        "average_premium": round(random.uniform(200, 800), 2),
                        "total_coverage": round(random.uniform(1000000, 10000000), 2),
                        "policy_types": {
                            "auto": random.randint(20, 100),
                            "home": random.randint(15, 80),
                            "life": random.randint(10, 60),
                            "health": random.randint(25, 120)
                        }
                    }
                
                else:
                    return {"success": False, "error": f"Unknown report type: {report_type}"}
                
                report.update({
                    "generated_at": datetime.utcnow().isoformat(),
                    "period": {"start": start_date, "end": end_date} if start_date and end_date else None
                })
                
                return {
                    "success": True,
                    "report": report
                }
                
            except Exception as e:
                logger.error("Error generating report", report_type=report_type, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "report_type": report_type
                }
        
        # Tool: Get customer metrics
        @self.mcp.tool()
        def get_customer_metrics(customer_id: str) -> Dict[str, Any]:
            """Get analytics metrics for a specific customer"""
            try:
                import random
                from datetime import datetime, timedelta
                
                # Mock customer metrics
                metrics = {
                    "customer_id": customer_id,
                    "risk_score": round(random.uniform(0.1, 1.0), 2),
                    "lifetime_value": round(random.uniform(1000, 20000), 2),
                    "total_policies": random.randint(1, 8),
                    "active_policies": random.randint(1, 6),
                    "total_claims": random.randint(0, 5),
                    "claim_frequency": round(random.uniform(0.0, 0.5), 2),
                    "average_claim_amount": round(random.uniform(500, 8000), 2),
                    "payment_history": {
                        "on_time_payments": random.randint(10, 50),
                        "late_payments": random.randint(0, 5),
                        "missed_payments": random.randint(0, 2)
                    },
                    "customer_since": (datetime.utcnow() - timedelta(days=random.randint(30, 2000))).isoformat(),
                    "last_interaction": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
                    "satisfaction_score": round(random.uniform(3.0, 5.0), 1)
                }
                
                return {
                    "success": True,
                    "metrics": metrics
                }
                
            except Exception as e:
                logger.error("Error getting customer metrics", customer_id=customer_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "customer_id": customer_id
                }
        
        # Tool: Calculate risk score
        @self.mcp.tool()
        def calculate_risk_score(customer_id: str, factors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Calculate risk score for a customer based on various factors"""
            try:
                import random
                from datetime import datetime
                
                # Base risk score
                base_risk = 0.5
                
                # Adjust based on factors if provided
                if factors:
                    # Age factor (younger = higher risk)
                    age = factors.get('age', 35)
                    if age < 25:
                        base_risk += 0.2
                    elif age > 50:
                        base_risk -= 0.1
                    
                    # Driving history for auto insurance
                    accidents = factors.get('accidents', 0)
                    base_risk += accidents * 0.15
                    
                    # Credit score factor
                    credit_score = factors.get('credit_score', 700)
                    if credit_score > 750:
                        base_risk -= 0.1
                    elif credit_score < 600:
                        base_risk += 0.2
                    
                    # Location factor
                    location_risk = factors.get('location_risk', 'medium')
                    risk_multipliers = {'low': -0.05, 'medium': 0.0, 'high': 0.15}
                    base_risk += risk_multipliers.get(location_risk, 0.0)
                
                # Ensure risk score is within bounds
                risk_score = max(0.1, min(1.0, base_risk + random.uniform(-0.05, 0.05)))
                
                # Determine risk category
                if risk_score < 0.3:
                    risk_category = "Low"
                elif risk_score < 0.7:
                    risk_category = "Medium"
                else:
                    risk_category = "High"
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "risk_score": round(risk_score, 3),
                    "risk_category": risk_category,
                    "factors_considered": list(factors.keys()) if factors else [],
                    "calculated_at": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error("Error calculating risk score", customer_id=customer_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "customer_id": customer_id
                }
    
    def _setup_resources(self):
        """Setup MCP resources for analytics data"""
        
        # Resource: Get customer analytics
        @self.mcp.resource("analytics://customer/{customer_id}")
        def get_customer_analytics_resource(customer_id: str) -> Dict[str, Any]:
            """Provides customer analytics as a resource"""
            try:
                # This would call the actual analytics logic
                return self._tool_get_customer_metrics(customer_id)
            except Exception as e:
                logger.error("Error getting customer analytics resource", customer_id=customer_id, error=str(e))
                return {"error": str(e), "customer_id": customer_id}
        
        # Resource: Get dashboard metrics
        @self.mcp.resource("analytics://dashboard")
        def get_dashboard_metrics_resource() -> Dict[str, Any]:
            """Provides dashboard metrics as a resource"""
            try:
                import random
                from datetime import datetime
                
                return {
                    "total_customers": random.randint(1000, 5000),
                    "total_policies": random.randint(1200, 6000),
                    "total_claims": random.randint(100, 800),
                    "total_revenue": round(random.uniform(100000, 1000000), 2),
                    "average_risk_score": round(random.uniform(0.3, 0.7), 2),
                    "generated_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error("Error getting dashboard metrics resource", error=str(e))
                return {"error": str(e)}
    
    def _integrate_with_fastapi(self):
        """Integrate FastMCP with FastAPI by adding endpoints"""
        
        # Add FastMCP endpoints to the existing FastAPI app
        @self.app.get("/mcp/tools")
        async def mcp_list_tools():
            """List available MCP tools"""
            try:
                tools = []
                for tool_name in ['generate_report', 'get_customer_metrics', 'calculate_risk_score']:
                    tools.append({
                        "name": tool_name,
                        "description": f"MCP tool: {tool_name}",
                        "inputSchema": {"type": "object", "properties": {}}
                    })
                
                return {"tools": tools}
            except Exception as e:
                logger.error("Error listing MCP tools", error=str(e))
                return {"error": str(e), "tools": []}
        
        @self.app.post("/mcp/call")
        async def mcp_call_tool(request: Dict[str, Any]):
            """Call an MCP tool"""
            try:
                method = request.get("method", "")
                params = request.get("params", {})
                
                if method != "tools/call":
                    return {"error": f"Unsupported method: {method}"}
                
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Route to the appropriate tool function
                if tool_name == "generate_report":
                    result = self._tool_generate_report(**arguments)
                elif tool_name == "get_customer_metrics":
                    result = self._tool_get_customer_metrics(**arguments)
                elif tool_name == "calculate_risk_score":
                    result = self._tool_calculate_risk_score(**arguments)
                else:
                    return {"error": f"Tool '{tool_name}' not found"}
                
                return {
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result)
                            }
                        ]
                    }
                }
            except Exception as e:
                logger.error("Error calling MCP tool", error=str(e))
                return {"error": str(e)}
        
        @self.app.get("/mcp/resources")
        async def mcp_list_resources():
            """List available MCP resources"""
            try:
                resources = [
                    {
                        "uri": "analytics://customer/{customer_id}",
                        "name": "customer_analytics",
                        "description": "Get analytics data for a specific customer"
                    },
                    {
                        "uri": "analytics://dashboard",
                        "name": "dashboard_metrics", 
                        "description": "Get overall dashboard metrics"
                    }
                ]
                
                return {"resources": resources}
            except Exception as e:
                logger.error("Error listing MCP resources", error=str(e))
                return {"error": str(e), "resources": []}
    
    # Helper methods for tool calls (to avoid relying on FastMCP internals)
    def _tool_generate_report(self, report_type: str, customer_id: Optional[str] = None, 
                             start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Internal method for generate_report tool"""
        try:
            from datetime import datetime, timedelta
            import random
            
            # Mock data generation for different report types
            if report_type.lower() == "customer":
                if not customer_id:
                    return {"success": False, "error": "customer_id required for customer report"}
                
                report = {
                    "report_type": "customer",
                    "customer_id": customer_id,
                    "total_policies": random.randint(1, 5),
                    "total_claims": random.randint(0, 3),
                    "total_premium": round(random.uniform(500, 5000), 2),
                    "risk_score": round(random.uniform(0.1, 1.0), 2),
                    "claim_ratio": round(random.uniform(0.0, 0.3), 2),
                    "customer_since": (datetime.utcnow() - timedelta(days=random.randint(30, 1095))).isoformat()
                }
            
            elif report_type.lower() == "claims":
                report = {
                    "report_type": "claims",
                    "total_claims": random.randint(50, 200),
                    "approved_claims": random.randint(30, 150),
                    "rejected_claims": random.randint(5, 30),
                    "average_claim_amount": round(random.uniform(1000, 10000), 2),
                    "total_claim_amount": round(random.uniform(50000, 500000), 2),
                    "processing_time_avg": round(random.uniform(5, 15), 1)
                }
            
            elif report_type.lower() == "policies":
                report = {
                    "report_type": "policies",
                    "total_policies": random.randint(100, 500),
                    "active_policies": random.randint(80, 400),
                    "cancelled_policies": random.randint(5, 50),
                    "average_premium": round(random.uniform(200, 800), 2),
                    "total_coverage": round(random.uniform(1000000, 10000000), 2),
                    "policy_types": {
                        "auto": random.randint(20, 100),
                        "home": random.randint(15, 80),
                        "life": random.randint(10, 60),
                        "health": random.randint(25, 120)
                    }
                }
            
            else:
                return {"success": False, "error": f"Unknown report type: {report_type}"}
            
            report.update({
                "generated_at": datetime.utcnow().isoformat(),
                "period": {"start": start_date, "end": end_date} if start_date and end_date else None
            })
            
            return {
                "success": True,
                "report": report
            }
            
        except Exception as e:
            logger.error("Error generating report", report_type=report_type, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "report_type": report_type
            }
    
    def _tool_get_customer_metrics(self, customer_id: str) -> Dict[str, Any]:
        """Internal method for get_customer_metrics tool"""
        try:
            import random
            from datetime import datetime, timedelta
            
            # Mock customer metrics
            metrics = {
                "customer_id": customer_id,
                "risk_score": round(random.uniform(0.1, 1.0), 2),
                "lifetime_value": round(random.uniform(1000, 20000), 2),
                "total_policies": random.randint(1, 8),
                "active_policies": random.randint(1, 6),
                "total_claims": random.randint(0, 5),
                "claim_frequency": round(random.uniform(0.0, 0.5), 2),
                "average_claim_amount": round(random.uniform(500, 8000), 2),
                "payment_history": {
                    "on_time_payments": random.randint(10, 50),
                    "late_payments": random.randint(0, 5),
                    "missed_payments": random.randint(0, 2)
                },
                "customer_since": (datetime.utcnow() - timedelta(days=random.randint(30, 2000))).isoformat(),
                "last_interaction": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
                "satisfaction_score": round(random.uniform(3.0, 5.0), 1)
            }
            
            return {
                "success": True,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error("Error getting customer metrics", customer_id=customer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            }
    
    def _tool_calculate_risk_score(self, customer_id: str, factors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Internal method for calculate_risk_score tool"""
        try:
            import random
            from datetime import datetime
            
            # Base risk score
            base_risk = 0.5
            
            # Adjust based on factors if provided
            if factors:
                # Age factor (younger = higher risk)
                age = factors.get('age', 35)
                if age < 25:
                    base_risk += 0.2
                elif age > 50:
                    base_risk -= 0.1
                
                # Driving history for auto insurance
                accidents = factors.get('accidents', 0)
                base_risk += accidents * 0.15
                
                # Credit score factor
                credit_score = factors.get('credit_score', 700)
                if credit_score > 750:
                    base_risk -= 0.1
                elif credit_score < 600:
                    base_risk += 0.2
                
                # Location factor
                location_risk = factors.get('location_risk', 'medium')
                risk_multipliers = {'low': -0.05, 'medium': 0.0, 'high': 0.15}
                base_risk += risk_multipliers.get(location_risk, 0.0)
            
            # Ensure risk score is within bounds
            risk_score = max(0.1, min(1.0, base_risk + random.uniform(-0.05, 0.05)))
            
            # Determine risk category
            if risk_score < 0.3:
                risk_category = "Low"
            elif risk_score < 0.7:
                risk_category = "Medium"
            else:
                risk_category = "High"
            
            return {
                "success": True,
                "customer_id": customer_id,
                "risk_score": round(risk_score, 3),
                "risk_category": risk_category,
                "factors_considered": list(factors.keys()) if factors else [],
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Error calculating risk score", customer_id=customer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            } 