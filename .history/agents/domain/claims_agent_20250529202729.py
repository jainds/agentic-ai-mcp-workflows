"""
Claims Agent - Domain agent for processing insurance claims.
Uses A2A protocol for communication and MCP tools for data access.
"""

import os
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from agents.shared.a2a_base import A2AAgent, TaskRequest, TaskResponse
from agents.shared.mcp_base import MCPAgentMixin
from agents.shared.auth import service_auth
import structlog

logger = structlog.get_logger(__name__)


class ClaimsAgent(A2AAgent, MCPAgentMixin):
    """Domain agent for insurance claims processing"""
    
    def __init__(self, port: int = 8000):
        capabilities = {
            "streaming": False,
            "pushNotifications": True,
            "fileUpload": True,
            "messageHistory": True,
            "claimsProcessing": True,
            "documentAnalysis": True
        }
        
        # Initialize A2A agent
        A2AAgent.__init__(
            self,
            name="ClaimsAgent",
            description="Processes insurance claims with AI analysis and fraud detection",
            port=port,
            capabilities=capabilities
        )
        
        # Initialize MCP capabilities
        MCPAgentMixin.__init__(self)
        
        # Setup MCP connections
        self._setup_mcp_connections()
        
        # Claims processing state
        self.active_claims: Dict[str, Dict[str, Any]] = {}
        self.fraud_threshold = 0.7
        
        logger.info("Claims Agent initialized", port=port)
    
    def _setup_mcp_connections(self):
        """Setup MCP server connections"""
        # Connect to data MCP server for claims data access
        data_server_url = os.getenv("DATA_MCP_SERVER_URL", "http://data-agent:8001")
        self.add_mcp_server("data", data_server_url)
        
        # Connect to integration MCP server for external APIs
        integration_server_url = os.getenv("INTEGRATION_MCP_SERVER_URL", "http://integration-agent:8001")
        self.add_mcp_server("integration", integration_server_url)
        
        # Add enterprise API wrappers
        claims_api_url = os.getenv("CLAIMS_API_URL", "http://claims-service:8000")
        self.add_api_wrapper("claims_api", claims_api_url)
        
        user_api_url = os.getenv("USER_API_URL", "http://user-service:8000")
        self.add_api_wrapper("user_api", user_api_url)
    
    async def process_task(self, task: TaskRequest) -> TaskResponse:
        """Process incoming A2A tasks"""
        user_data = task.user
        task_type = user_data.get("type", "process_claim")
        
        logger.info("Processing claims task", task_id=task.taskId, type=task_type)
        
        try:
            if task_type == "process_claim":
                result = await self._process_claim(user_data)
            elif task_type == "analyze_claim":
                result = await self._analyze_claim(user_data)
            elif task_type == "fraud_detection":
                result = await self._detect_fraud(user_data)
            elif task_type == "claim_status":
                result = await self._get_claim_status(user_data)
            elif task_type == "approve_claim":
                result = await self._approve_claim(user_data)
            elif task_type == "reject_claim":
                result = await self._reject_claim(user_data)
            else:
                result = {"error": f"Unknown task type: {task_type}"}
            
            return TaskResponse(
                taskId=task.taskId,
                parts=[{"text": str(result), "type": "claims_response"}],
                status="completed",
                metadata={"agent": "ClaimsAgent", "task_type": task_type}
            )
            
        except Exception as e:
            logger.error("Task processing failed", task_id=task.taskId, error=str(e))
            return TaskResponse(
                taskId=task.taskId,
                parts=[{"text": f"Error: {str(e)}", "type": "error"}],
                status="failed",
                metadata={"agent": "ClaimsAgent", "error": str(e)}
            )
    
    async def _process_claim(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a new insurance claim"""
        claim_data = data.get("claim", {})
        claim_id = claim_data.get("claim_id")
        policy_number = claim_data.get("policy_number")
        incident_description = claim_data.get("description", "")
        
        if not claim_id or not policy_number:
            return {"error": "Missing required claim data: claim_id and policy_number"}
        
        logger.info("Processing new claim", claim_id=claim_id, policy=policy_number)
        
        # Store active claim
        self.active_claims[claim_id] = {
            "claim_id": claim_id,
            "policy_number": policy_number,
            "description": incident_description,
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
            "processing_steps": []
        }
        
        try:
            # Step 1: Validate policy via Data Agent MCP
            policy_data = await self.call_mcp_tool(
                "data", 
                "get_policy", 
                policy_number=policy_number
            )
            
            if not policy_data:
                return {"error": f"Policy {policy_number} not found"}
            
            self.active_claims[claim_id]["policy_data"] = policy_data
            self.active_claims[claim_id]["processing_steps"].append("policy_validated")
            
            # Step 2: Get customer information
            customer_id = policy_data.get("customer_id")
            customer_data = await self.call_enterprise_api(
                "user_api",
                "GET",
                f"/customers/{customer_id}"
            )
            
            self.active_claims[claim_id]["customer_data"] = customer_data
            self.active_claims[claim_id]["processing_steps"].append("customer_validated")
            
            # Step 3: Analyze claim for fraud indicators
            fraud_score = await self._analyze_fraud_indicators(claim_data, policy_data, customer_data)
            self.active_claims[claim_id]["fraud_score"] = fraud_score
            self.active_claims[claim_id]["processing_steps"].append("fraud_analyzed")
            
            # Step 4: Determine processing path
            if fraud_score > self.fraud_threshold:
                # High fraud risk - require manual review
                self.active_claims[claim_id]["status"] = "manual_review"
                self.active_claims[claim_id]["processing_steps"].append("flagged_for_review")
                
                # Notify fraud investigation team via Notification Agent
                await self._notify_fraud_team(claim_id, fraud_score)
                
                return {
                    "claim_id": claim_id,
                    "status": "manual_review",
                    "fraud_score": fraud_score,
                    "message": "Claim flagged for manual review due to fraud indicators"
                }
            else:
                # Low fraud risk - auto-process
                approval_result = await self._auto_process_claim(claim_id)
                return approval_result
                
        except Exception as e:
            self.active_claims[claim_id]["status"] = "error"
            self.active_claims[claim_id]["error"] = str(e)
            logger.error("Claim processing failed", claim_id=claim_id, error=str(e))
            raise
    
    async def _analyze_fraud_indicators(
        self, 
        claim_data: Dict[str, Any], 
        policy_data: Dict[str, Any], 
        customer_data: Dict[str, Any]
    ) -> float:
        """Analyze claim for fraud indicators using AI"""
        
        # Basic fraud detection logic (in production, use ML models)
        fraud_score = 0.0
        
        # Check claim amount vs policy limits
        claim_amount = float(claim_data.get("amount", 0))
        policy_limit = float(policy_data.get("coverage_limit", 0))
        
        if claim_amount > policy_limit * 0.8:
            fraud_score += 0.3
        
        # Check recent claims frequency
        recent_claims = await self.call_mcp_tool(
            "data",
            "get_recent_claims",
            customer_id=customer_data.get("id"),
            days=90
        )
        
        if recent_claims and len(recent_claims) > 2:
            fraud_score += 0.4
        
        # Check for suspicious patterns in description
        suspicious_keywords = ["total loss", "stolen", "vandalism", "fire"]
        description = claim_data.get("description", "").lower()
        
        if any(keyword in description for keyword in suspicious_keywords):
            fraud_score += 0.2
        
        # Check customer risk profile
        customer_risk = customer_data.get("risk_score", 0.0)
        fraud_score += customer_risk * 0.3
        
        return min(fraud_score, 1.0)  # Cap at 1.0
    
    async def _auto_process_claim(self, claim_id: str) -> Dict[str, Any]:
        """Auto-process low-risk claims"""
        claim = self.active_claims[claim_id]
        
        # Simple auto-approval logic
        claim_amount = float(claim.get("claim_data", {}).get("amount", 0))
        policy_limit = float(claim.get("policy_data", {}).get("coverage_limit", 0))
        
        if claim_amount <= policy_limit * 0.5:  # Auto-approve if <= 50% of policy limit
            claim["status"] = "approved"
            claim["processing_steps"].append("auto_approved")
            
            # Create payment record via Claims API
            payment_result = await self.call_enterprise_api(
                "claims_api",
                "POST",
                "/payments",
                data={
                    "claim_id": claim_id,
                    "amount": claim_amount,
                    "status": "approved"
                }
            )
            
            return {
                "claim_id": claim_id,
                "status": "approved",
                "amount": claim_amount,
                "payment_id": payment_result.get("payment_id") if payment_result else None,
                "message": "Claim auto-approved and payment processed"
            }
        else:
            # Require manual approval for larger amounts
            claim["status"] = "pending_approval"
            claim["processing_steps"].append("pending_manual_approval")
            
            return {
                "claim_id": claim_id,
                "status": "pending_approval",
                "message": "Claim requires manual approval due to amount"
            }
    
    async def _notify_fraud_team(self, claim_id: str, fraud_score: float):
        """Notify fraud investigation team"""
        try:
            # Send notification via Notification Agent A2A call
            notification_data = {
                "type": "fraud_alert",
                "claim_id": claim_id,
                "fraud_score": fraud_score,
                "priority": "high" if fraud_score > 0.8 else "medium",
                "message": f"Claim {claim_id} flagged for fraud review (score: {fraud_score:.2f})"
            }
            
            # Get service token for A2A communication
            token = service_auth.get_service_token("claims-agent")
            
            await self.send_task_to_agent(
                "NotificationAgent",
                notification_data,
                token
            )
            
            logger.info("Fraud team notified", claim_id=claim_id, fraud_score=fraud_score)
            
        except Exception as e:
            logger.error("Failed to notify fraud team", claim_id=claim_id, error=str(e))
    
    async def _analyze_claim(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze claim details and provide insights"""
        claim_id = data.get("claim_id")
        
        if claim_id not in self.active_claims:
            return {"error": f"Claim {claim_id} not found"}
        
        claim = self.active_claims[claim_id]
        
        analysis = {
            "claim_id": claim_id,
            "status": claim["status"],
            "fraud_score": claim.get("fraud_score", 0.0),
            "processing_steps": claim["processing_steps"],
            "recommendation": self._get_processing_recommendation(claim)
        }
        
        return analysis
    
    def _get_processing_recommendation(self, claim: Dict[str, Any]) -> str:
        """Get processing recommendation based on claim analysis"""
        fraud_score = claim.get("fraud_score", 0.0)
        status = claim.get("status")
        
        if fraud_score > 0.8:
            return "Recommend detailed fraud investigation"
        elif fraud_score > 0.5:
            return "Recommend additional documentation review"
        elif status == "approved":
            return "Claim processed successfully"
        else:
            return "Standard processing recommended"
    
    async def _detect_fraud(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run fraud detection on specific claim"""
        claim_id = data.get("claim_id")
        
        if claim_id not in self.active_claims:
            return {"error": f"Claim {claim_id} not found"}
        
        claim = self.active_claims[claim_id]
        fraud_score = claim.get("fraud_score", 0.0)
        
        return {
            "claim_id": claim_id,
            "fraud_score": fraud_score,
            "risk_level": "high" if fraud_score > 0.7 else "medium" if fraud_score > 0.4 else "low",
            "indicators": self._get_fraud_indicators(claim)
        }
    
    def _get_fraud_indicators(self, claim: Dict[str, Any]) -> List[str]:
        """Get list of fraud indicators for a claim"""
        indicators = []
        fraud_score = claim.get("fraud_score", 0.0)
        
        if fraud_score > 0.7:
            indicators.append("High fraud score")
        if "recent_claims" in claim.get("processing_steps", []):
            indicators.append("Multiple recent claims")
        
        return indicators
    
    async def _get_claim_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a specific claim"""
        claim_id = data.get("claim_id")
        
        if claim_id not in self.active_claims:
            return {"error": f"Claim {claim_id} not found"}
        
        claim = self.active_claims[claim_id]
        
        return {
            "claim_id": claim_id,
            "status": claim["status"],
            "created_at": claim["created_at"],
            "processing_steps": claim["processing_steps"],
            "fraud_score": claim.get("fraud_score"),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def _approve_claim(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manually approve a claim"""
        claim_id = data.get("claim_id")
        approver = data.get("approver", "system")
        
        if claim_id not in self.active_claims:
            return {"error": f"Claim {claim_id} not found"}
        
        claim = self.active_claims[claim_id]
        claim["status"] = "approved"
        claim["approver"] = approver
        claim["approved_at"] = datetime.utcnow().isoformat()
        claim["processing_steps"].append("manually_approved")
        
        # Process payment
        claim_amount = float(claim.get("claim_data", {}).get("amount", 0))
        payment_result = await self.call_enterprise_api(
            "claims_api",
            "POST",
            "/payments",
            data={
                "claim_id": claim_id,
                "amount": claim_amount,
                "status": "approved",
                "approver": approver
            }
        )
        
        return {
            "claim_id": claim_id,
            "status": "approved",
            "approver": approver,
            "payment_id": payment_result.get("payment_id") if payment_result else None
        }
    
    async def _reject_claim(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manually reject a claim"""
        claim_id = data.get("claim_id")
        reason = data.get("reason", "No reason provided")
        approver = data.get("approver", "system")
        
        if claim_id not in self.active_claims:
            return {"error": f"Claim {claim_id} not found"}
        
        claim = self.active_claims[claim_id]
        claim["status"] = "rejected"
        claim["rejection_reason"] = reason
        claim["rejected_by"] = approver
        claim["rejected_at"] = datetime.utcnow().isoformat()
        claim["processing_steps"].append("manually_rejected")
        
        return {
            "claim_id": claim_id,
            "status": "rejected",
            "reason": reason,
            "rejected_by": approver
        }


# Main execution
if __name__ == "__main__":
    port = int(os.getenv("CLAIMS_AGENT_PORT", "8000"))
    agent = ClaimsAgent(port=port)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("Claims Agent shutting down")
    finally:
        # Cleanup MCP connections
        asyncio.run(agent.cleanup_mcp_connections()) 