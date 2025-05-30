"""
FastMCP Server for Policy Service
Integrates with the existing FastAPI policy service to provide MCP tools
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP
import structlog

logger = structlog.get_logger(__name__)

class PolicyMCPServer:
    """FastMCP server for policy operations"""
    
    def __init__(self, fastapi_app: FastAPI, policies_db: Dict[str, Any]):
        self.app = fastapi_app
        self.policies_db = policies_db
        
        # Initialize FastMCP server
        self.mcp = FastMCP(
            name="policy-service",
            dependencies=["fastapi", "structlog", "pydantic"]
        )
        
        self._setup_tools()
        self._setup_resources()
        self._integrate_with_fastapi()
    
    def _setup_tools(self):
        """Setup MCP tools for policy operations"""
        
        # Tool: Get policy details
        @self.mcp.tool()
        def get_policy(policy_id: str, customer_id: str) -> Dict[str, Any]:
            """Get detailed information about a specific policy"""
            try:
                if policy_id not in self.policies_db:
                    return {
                        "success": False,
                        "error": f"Policy {policy_id} not found",
                        "policy_id": policy_id
                    }
                
                policy = self.policies_db[policy_id]
                
                # Verify customer ownership
                if policy.get('customer_id') != customer_id:
                    return {
                        "success": False,
                        "error": "Unauthorized access to policy",
                        "policy_id": policy_id
                    }
                
                return {
                    "success": True,
                    "policy": policy
                }
            except Exception as e:
                logger.error("Error getting policy details", policy_id=policy_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "policy_id": policy_id
                }
        
        # Tool: Calculate quote
        @self.mcp.tool()
        def calculate_quote(customer_id: str, policy_type: str, coverage_amount: float, 
                           vehicle_year: Optional[int] = None, vehicle_make: Optional[str] = None,
                           vehicle_model: Optional[str] = None) -> Dict[str, Any]:
            """Calculate insurance quote for a customer"""
            try:
                import uuid
                from datetime import datetime, timedelta
                
                # Base premium calculation (simplified algorithm)
                base_premium = coverage_amount * 0.05  # 5% of coverage amount
                
                # Risk adjustments based on policy type
                risk_multiplier = {
                    "auto": 1.0,
                    "home": 0.8,
                    "life": 1.2,
                    "health": 1.1
                }.get(policy_type.lower(), 1.0)
                
                # Vehicle-specific adjustments for auto policies
                if policy_type.lower() == "auto" and vehicle_year:
                    if vehicle_year >= 2020:
                        risk_multiplier *= 0.9  # Newer cars are safer
                    elif vehicle_year < 2010:
                        risk_multiplier *= 1.2  # Older cars are riskier
                
                monthly_premium = base_premium * risk_multiplier / 12
                annual_premium = base_premium * risk_multiplier
                
                quote_id = f"QTE-{str(uuid.uuid4())[:8].upper()}"
                
                quote = {
                    "quote_id": quote_id,
                    "customer_id": customer_id,
                    "policy_type": policy_type,
                    "coverage_amount": coverage_amount,
                    "monthly_premium": round(monthly_premium, 2),
                    "annual_premium": round(annual_premium, 2),
                    "risk_score": risk_multiplier,
                    "valid_until": (datetime.utcnow().replace(day=1) + 
                                  timedelta(days=32)).replace(day=1),
                    "created_at": datetime.utcnow().isoformat(),
                    "vehicle_details": {
                        "year": vehicle_year,
                        "make": vehicle_make,
                        "model": vehicle_model
                    } if policy_type.lower() == "auto" else None
                }
                
                return {
                    "success": True,
                    "quote": quote
                }
                
            except Exception as e:
                logger.error("Error calculating quote", customer_id=customer_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "customer_id": customer_id
                }
        
        # Tool: List policies for customer
        @self.mcp.tool()
        def list_policies(customer_id: str, status: Optional[str] = None) -> Dict[str, Any]:
            """List all policies for a specific customer"""
            try:
                customer_policies = []
                for policy in self.policies_db.values():
                    if policy.get('customer_id') == customer_id:
                        if status is None or policy.get('status') == status:
                            customer_policies.append(policy)
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "policies": customer_policies,
                    "total_policies": len(customer_policies),
                    "filter_status": status
                }
            except Exception as e:
                logger.error("Error listing policies", customer_id=customer_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "customer_id": customer_id
                }
        
        # Tool: Update policy
        @self.mcp.tool()
        def update_policy(policy_id: str, customer_id: str, 
                         coverage_amount: Optional[float] = None,
                         status: Optional[str] = None,
                         beneficiaries: Optional[List[str]] = None) -> Dict[str, Any]:
            """Update an existing policy"""
            try:
                if policy_id not in self.policies_db:
                    return {
                        "success": False,
                        "error": f"Policy {policy_id} not found",
                        "policy_id": policy_id
                    }
                
                policy = self.policies_db[policy_id]
                
                # Verify customer ownership
                if policy.get('customer_id') != customer_id:
                    return {
                        "success": False,
                        "error": "Unauthorized access to policy",
                        "policy_id": policy_id
                    }
                
                # Update fields
                updates = {}
                if coverage_amount is not None:
                    old_amount = policy.get('coverage_amount')
                    policy['coverage_amount'] = coverage_amount
                    updates['coverage_amount'] = {'old': old_amount, 'new': coverage_amount}
                    
                    # Recalculate premium based on new coverage
                    if 'monthly_premium' in policy:
                        ratio = coverage_amount / old_amount if old_amount else 1
                        policy['monthly_premium'] = round(policy['monthly_premium'] * ratio, 2)
                        policy['annual_premium'] = round(policy['annual_premium'] * ratio, 2)
                
                if status is not None:
                    old_status = policy.get('status')
                    policy['status'] = status
                    updates['status'] = {'old': old_status, 'new': status}
                
                if beneficiaries is not None:
                    old_beneficiaries = policy.get('beneficiaries', [])
                    policy['beneficiaries'] = beneficiaries
                    updates['beneficiaries'] = {'old': old_beneficiaries, 'new': beneficiaries}
                
                from datetime import datetime
                policy['updated_at'] = datetime.utcnow().isoformat()
                
                logger.info("Policy updated", policy_id=policy_id, updates=list(updates.keys()))
                
                return {
                    "success": True,
                    "policy_id": policy_id,
                    "policy": policy,
                    "updates": updates
                }
                
            except Exception as e:
                logger.error("Error updating policy", policy_id=policy_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "policy_id": policy_id
                }
        
        # Tool: Validate coverage
        @self.mcp.tool()
        def validate_coverage(policy_id: str, customer_id: str, claim_amount: float) -> Dict[str, Any]:
            """Validate if a claim amount is covered by the policy"""
            try:
                if policy_id not in self.policies_db:
                    return {
                        "success": False,
                        "error": f"Policy {policy_id} not found",
                        "policy_id": policy_id
                    }
                
                policy = self.policies_db[policy_id]
                
                # Verify customer ownership
                if policy.get('customer_id') != customer_id:
                    return {
                        "success": False,
                        "error": "Unauthorized access to policy",
                        "policy_id": policy_id
                    }
                
                # Check policy status
                if policy.get('status') != 'active':
                    return {
                        "success": True,
                        "covered": False,
                        "reason": f"Policy is not active (status: {policy.get('status')})",
                        "policy_id": policy_id,
                        "claim_amount": claim_amount
                    }
                
                # Check coverage limits
                coverage_amount = policy.get('coverage_amount', 0)
                deductible = policy.get('deductible', 0)
                
                # Calculate covered amount
                if claim_amount <= deductible:
                    covered_amount = 0
                    reason = f"Claim amount (${claim_amount}) is below deductible (${deductible})"
                elif claim_amount > coverage_amount:
                    covered_amount = coverage_amount - deductible
                    reason = f"Claim amount exceeds coverage limit. Max coverage: ${coverage_amount - deductible}"
                else:
                    covered_amount = claim_amount - deductible
                    reason = "Claim is fully covered"
                
                is_covered = covered_amount > 0
                
                return {
                    "success": True,
                    "covered": is_covered,
                    "covered_amount": covered_amount,
                    "claim_amount": claim_amount,
                    "deductible": deductible,
                    "coverage_limit": coverage_amount,
                    "reason": reason,
                    "policy_id": policy_id
                }
                
            except Exception as e:
                logger.error("Error validating coverage", policy_id=policy_id, error=str(e))
                return {
                    "success": False,
                    "error": str(e),
                    "policy_id": policy_id
                }
    
    def _setup_resources(self):
        """Setup MCP resources for policy data"""
        
        # Resource: Get customer policies
        @self.mcp.resource("policies://customer/{customer_id}")
        def get_customer_policies_resource(customer_id: str) -> Dict[str, Any]:
            """Provides all policies for a specific customer as a resource"""
            try:
                customer_policies = [
                    policy for policy in self.policies_db.values()
                    if policy.get('customer_id') == customer_id
                ]
                return {
                    "customer_id": customer_id,
                    "policies": customer_policies,
                    "total_policies": len(customer_policies)
                }
            except Exception as e:
                logger.error("Error getting customer policies resource", customer_id=customer_id, error=str(e))
                return {"error": str(e), "customer_id": customer_id}
        
        # Resource: Get specific policy
        @self.mcp.resource("policies://policy/{policy_id}")
        def get_policy_resource(policy_id: str) -> Dict[str, Any]:
            """Provides detailed information about a specific policy as a resource"""
            try:
                if policy_id not in self.policies_db:
                    return {"error": f"Policy {policy_id} not found", "policy_id": policy_id}
                
                policy = self.policies_db[policy_id]
                return policy
            except Exception as e:
                logger.error("Error getting policy resource", policy_id=policy_id, error=str(e))
                return {"error": str(e), "policy_id": policy_id}
    
    def _integrate_with_fastapi(self):
        """Integrate FastMCP with FastAPI by adding endpoints"""
        
        # Add FastMCP endpoints to the existing FastAPI app
        @self.app.get("/mcp/tools")
        async def mcp_list_tools():
            """List available MCP tools"""
            try:
                tools = []
                for tool_name in ['get_policy', 'calculate_quote', 'list_policies', 'update_policy', 'validate_coverage']:
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
                if tool_name == "get_policy":
                    result = self._tool_get_policy(**arguments)
                elif tool_name == "calculate_quote":
                    result = self._tool_calculate_quote(**arguments)
                elif tool_name == "list_policies":
                    result = self._tool_list_policies(**arguments)
                elif tool_name == "update_policy":
                    result = self._tool_update_policy(**arguments)
                elif tool_name == "validate_coverage":
                    result = self._tool_validate_coverage(**arguments)
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
                        "uri": "policies://customer/{customer_id}",
                        "name": "customer_policies",
                        "description": "Get all policies for a specific customer"
                    },
                    {
                        "uri": "policies://policy/{policy_id}",
                        "name": "policy_details", 
                        "description": "Get details for a specific policy"
                    }
                ]
                
                return {"resources": resources}
            except Exception as e:
                logger.error("Error listing MCP resources", error=str(e))
                return {"error": str(e), "resources": []}
    
    # Helper methods for tool calls (to avoid relying on FastMCP internals)
    def _tool_get_policy(self, policy_id: str, customer_id: str) -> Dict[str, Any]:
        """Internal method for get_policy tool"""
        try:
            if policy_id not in self.policies_db:
                return {
                    "success": False,
                    "error": f"Policy {policy_id} not found",
                    "policy_id": policy_id
                }
            
            policy = self.policies_db[policy_id]
            
            # Verify customer ownership
            if policy.get('customer_id') != customer_id:
                return {
                    "success": False,
                    "error": "Unauthorized access to policy",
                    "policy_id": policy_id
                }
            
            return {
                "success": True,
                "policy": policy
            }
        except Exception as e:
            logger.error("Error getting policy details", policy_id=policy_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "policy_id": policy_id
            }
    
    def _tool_calculate_quote(self, customer_id: str, policy_type: str, coverage_amount: float, 
                             vehicle_year: Optional[int] = None, vehicle_make: Optional[str] = None,
                             vehicle_model: Optional[str] = None) -> Dict[str, Any]:
        """Internal method for calculate_quote tool"""
        try:
            import uuid
            from datetime import datetime, timedelta
            
            # Base premium calculation (simplified algorithm)
            base_premium = coverage_amount * 0.05  # 5% of coverage amount
            
            # Risk adjustments based on policy type
            risk_multiplier = {
                "auto": 1.0,
                "home": 0.8,
                "life": 1.2,
                "health": 1.1
            }.get(policy_type.lower(), 1.0)
            
            # Vehicle-specific adjustments for auto policies
            if policy_type.lower() == "auto" and vehicle_year:
                if vehicle_year >= 2020:
                    risk_multiplier *= 0.9  # Newer cars are safer
                elif vehicle_year < 2010:
                    risk_multiplier *= 1.2  # Older cars are riskier
            
            monthly_premium = base_premium * risk_multiplier / 12
            annual_premium = base_premium * risk_multiplier
            
            quote_id = f"QTE-{str(uuid.uuid4())[:8].upper()}"
            
            quote = {
                "quote_id": quote_id,
                "customer_id": customer_id,
                "policy_type": policy_type,
                "coverage_amount": coverage_amount,
                "monthly_premium": round(monthly_premium, 2),
                "annual_premium": round(annual_premium, 2),
                "risk_score": risk_multiplier,
                "valid_until": (datetime.utcnow().replace(day=1) + 
                              timedelta(days=32)).replace(day=1),
                "created_at": datetime.utcnow().isoformat(),
                "vehicle_details": {
                    "year": vehicle_year,
                    "make": vehicle_make,
                    "model": vehicle_model
                } if policy_type.lower() == "auto" else None
            }
            
            return {
                "success": True,
                "quote": quote
            }
            
        except Exception as e:
            logger.error("Error calculating quote", customer_id=customer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            }
    
    def _tool_list_policies(self, customer_id: str, status: Optional[str] = None) -> Dict[str, Any]:
        """Internal method for list_policies tool"""
        try:
            customer_policies = []
            for policy in self.policies_db.values():
                if policy.get('customer_id') == customer_id:
                    if status is None or policy.get('status') == status:
                        customer_policies.append(policy)
            
            return {
                "success": True,
                "customer_id": customer_id,
                "policies": customer_policies,
                "total_policies": len(customer_policies),
                "filter_status": status
            }
        except Exception as e:
            logger.error("Error listing policies", customer_id=customer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id
            }
    
    def _tool_update_policy(self, policy_id: str, customer_id: str, 
                           coverage_amount: Optional[float] = None,
                           status: Optional[str] = None,
                           beneficiaries: Optional[List[str]] = None) -> Dict[str, Any]:
        """Internal method for update_policy tool"""
        try:
            if policy_id not in self.policies_db:
                return {
                    "success": False,
                    "error": f"Policy {policy_id} not found",
                    "policy_id": policy_id
                }
            
            policy = self.policies_db[policy_id]
            
            # Verify customer ownership
            if policy.get('customer_id') != customer_id:
                return {
                    "success": False,
                    "error": "Unauthorized access to policy",
                    "policy_id": policy_id
                }
            
            # Update fields
            updates = {}
            if coverage_amount is not None:
                old_amount = policy.get('coverage_amount')
                policy['coverage_amount'] = coverage_amount
                updates['coverage_amount'] = {'old': old_amount, 'new': coverage_amount}
                
                # Recalculate premium based on new coverage
                if 'monthly_premium' in policy:
                    ratio = coverage_amount / old_amount if old_amount else 1
                    policy['monthly_premium'] = round(policy['monthly_premium'] * ratio, 2)
                    policy['annual_premium'] = round(policy['annual_premium'] * ratio, 2)
            
            if status is not None:
                old_status = policy.get('status')
                policy['status'] = status
                updates['status'] = {'old': old_status, 'new': status}
            
            if beneficiaries is not None:
                old_beneficiaries = policy.get('beneficiaries', [])
                policy['beneficiaries'] = beneficiaries
                updates['beneficiaries'] = {'old': old_beneficiaries, 'new': beneficiaries}
            
            from datetime import datetime
            policy['updated_at'] = datetime.utcnow().isoformat()
            
            logger.info("Policy updated", policy_id=policy_id, updates=list(updates.keys()))
            
            return {
                "success": True,
                "policy_id": policy_id,
                "policy": policy,
                "updates": updates
            }
            
        except Exception as e:
            logger.error("Error updating policy", policy_id=policy_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "policy_id": policy_id
            }
    
    def _tool_validate_coverage(self, policy_id: str, customer_id: str, claim_amount: float) -> Dict[str, Any]:
        """Internal method for validate_coverage tool"""
        try:
            if policy_id not in self.policies_db:
                return {
                    "success": False,
                    "error": f"Policy {policy_id} not found",
                    "policy_id": policy_id
                }
            
            policy = self.policies_db[policy_id]
            
            # Verify customer ownership
            if policy.get('customer_id') != customer_id:
                return {
                    "success": False,
                    "error": "Unauthorized access to policy",
                    "policy_id": policy_id
                }
            
            # Check policy status
            if policy.get('status') != 'active':
                return {
                    "success": True,
                    "covered": False,
                    "reason": f"Policy is not active (status: {policy.get('status')})",
                    "policy_id": policy_id,
                    "claim_amount": claim_amount
                }
            
            # Check coverage limits
            coverage_amount = policy.get('coverage_amount', 0)
            deductible = policy.get('deductible', 0)
            
            # Calculate covered amount
            if claim_amount <= deductible:
                covered_amount = 0
                reason = f"Claim amount (${claim_amount}) is below deductible (${deductible})"
            elif claim_amount > coverage_amount:
                covered_amount = coverage_amount - deductible
                reason = f"Claim amount exceeds coverage limit. Max coverage: ${coverage_amount - deductible}"
            else:
                covered_amount = claim_amount - deductible
                reason = "Claim is fully covered"
            
            is_covered = covered_amount > 0
            
            return {
                "success": True,
                "covered": is_covered,
                "covered_amount": covered_amount,
                "claim_amount": claim_amount,
                "deductible": deductible,
                "coverage_limit": coverage_amount,
                "reason": reason,
                "policy_id": policy_id
            }
            
        except Exception as e:
            logger.error("Error validating coverage", policy_id=policy_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "policy_id": policy_id
            } 