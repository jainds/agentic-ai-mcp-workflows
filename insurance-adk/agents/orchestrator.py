"""
Google ADK Orchestrator

This module provides orchestration capabilities for coordinating
multiple Google ADK agents with A2A communication support.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_adk import (
    ADKModelConfig, 
    InsuranceADKAgent, 
    InsuranceADKWorkflow,
    InsuranceADKTool
)

logger = logging.getLogger(__name__)

class InsuranceADKOrchestrator:
    """Orchestrator for managing multiple Google ADK agents with A2A communication"""
    
    def __init__(self, domain_agent: InsuranceADKAgent, technical_agent: InsuranceADKAgent):
        self.domain_agent = domain_agent
        self.technical_agent = technical_agent
        self.logger = logging.getLogger(__name__)
        
        # A2A communication endpoints
        self.agents = {
            "domain": domain_agent,
            "technical": technical_agent
        }
        
    async def route_customer_inquiry(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route customer inquiry through appropriate agent workflow"""
        try:
            self.logger.info("Orchestrator routing customer inquiry")
            
            # Determine if technical data is needed
            message = request.get("message", "").lower()
            needs_technical = any(keyword in message for keyword in [
                "policy", "claim", "coverage", "premium", "details", "information"
            ])
            
            if needs_technical:
                # Process through both agents with A2A communication
                return await self._process_with_a2a_communication(request)
            else:
                # Process with domain agent only
                return await self.domain_agent.process_customer_request(request)
                
        except Exception as e:
            self.logger.error(f"Orchestrator routing failed: {e}")
            return {
                "success": False,
                "error": f"Orchestration failed: {str(e)}",
                "request": request
            }
    
    async def _process_with_a2a_communication(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request using A2A communication between agents"""
        try:
            self.logger.info("Processing with A2A communication")
            
            # Step 1: Domain agent processes the inquiry
            domain_result = await self.domain_agent.process_customer_request(request)
            
            # Step 2: If technical data is needed, make A2A call to technical agent
            if domain_result.get("processed"):
                a2a_request = {
                    "customer_id": request.get("customer_id"),
                    "operation": "get_customer_policies",
                    "parameters": {
                        "request_type": "policy_inquiry",
                        "original_message": request.get("message")
                    },
                    "source_agent": "domain",
                    "timestamp": datetime.now().isoformat()
                }
                
                technical_result = await self.technical_agent.handle_a2a_communication(a2a_request)
                
                # Step 3: Combine results
                combined_result = {
                    "success": True,
                    "orchestrator": "InsuranceADKOrchestrator",
                    "framework": "Google ADK v1.0.0",
                    "domain_response": domain_result,
                    "technical_response": technical_result,
                    "a2a_communication": True,
                    "customer_id": request.get("customer_id"),
                    "final_response": self._combine_agent_responses(domain_result, technical_result, request)
                }
                
                return combined_result
            else:
                return domain_result
                
        except Exception as e:
            self.logger.error(f"A2A communication processing failed: {e}")
            return {
                "success": False,
                "error": f"A2A communication failed: {str(e)}",
                "request": request
            }
    
    def _combine_agent_responses(self, domain_result: Dict[str, Any], 
                               technical_result: Dict[str, Any], 
                               original_request: Dict[str, Any]) -> str:
        """Combine responses from both agents into a coherent response"""
        try:
            message = original_request.get("message", "")
            customer_id = original_request.get("customer_id", "Unknown")
            
            # Mock intelligent response combination
            if "policy" in message.lower():
                return f"Based on your inquiry about policies, I found information for customer {customer_id}. The domain agent processed your request and the technical agent retrieved relevant policy data through our A2A communication system."
            elif "claim" in message.lower():
                return f"Regarding your claim inquiry for customer {customer_id}, our agents have coordinated to provide you with comprehensive information through our A2A communication protocol."
            else:
                return f"I've processed your request for customer {customer_id} using our coordinated agent system with A2A communication to ensure accurate and complete information."
                
        except Exception as e:
            self.logger.error(f"Response combination failed: {e}")
            return "I've processed your request using our agent coordination system."
    
    async def process_technical_data_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process technical data request directly through technical agent"""
        try:
            self.logger.info("Processing technical data request")
            return await self.technical_agent.handle_a2a_communication(request)
            
        except Exception as e:
            self.logger.error(f"Technical data processing failed: {e}")
            return {
                "success": False,
                "error": f"Technical processing failed: {str(e)}",
                "request": request
            }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all managed agents"""
        try:
            return {
                "orchestrator": "InsuranceADKOrchestrator",
                "framework": "Google ADK v1.0.0",
                "agents": {
                    "domain_agent": {
                        "name": self.domain_agent.name,
                        "description": self.domain_agent.description,
                        "status": "active",
                        "a2a_capable": True
                    },
                    "technical_agent": {
                        "name": self.technical_agent.name,
                        "description": self.technical_agent.description,
                        "status": "active",
                        "a2a_capable": True
                    }
                },
                "a2a_communication": "enabled",
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Agent status check failed: {e}")
            return {
                "error": f"Status check failed: {str(e)}",
                "orchestrator": "InsuranceADKOrchestrator"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        try:
            health_status = {
                "orchestrator": "healthy",
                "framework": "Google ADK v1.0.0",
                "agents": {},
                "a2a_communication": "functional",
                "timestamp": datetime.now().isoformat()
            }
            
            # Check each agent
            for agent_name, agent in self.agents.items():
                try:
                    test_request = {"test": True, "timestamp": datetime.now().isoformat()}
                    if hasattr(agent, 'process_customer_request'):
                        await agent.process_customer_request(test_request)
                    health_status["agents"][agent_name] = "healthy"
                except Exception as e:
                    health_status["agents"][agent_name] = f"unhealthy: {str(e)}"
            
            # Overall health
            all_healthy = all(status == "healthy" for status in health_status["agents"].values())
            health_status["overall"] = "healthy" if all_healthy else "degraded"
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "orchestrator": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def create_adk_orchestrator() -> InsuranceADKOrchestrator:
    """Factory function to create ADK orchestrator with configured agents"""
    try:
        # Create model configurations
        domain_model_config = ADKModelConfig(
            primary_model="anthropic/claude-3.5-sonnet",
            api_key="mock-api-key",  # This would come from environment
            base_url="https://openrouter.ai/api/v1",
            max_tokens=4096,
            temperature=0.3
        )
        
        technical_model_config = ADKModelConfig(
            primary_model="meta-llama/llama-3.1-70b-instruct",
            api_key="mock-api-key",  # This would come from environment
            base_url="https://openrouter.ai/api/v1",
            max_tokens=2048,
            temperature=0.1
        )
        
        # Create agents
        domain_agent = InsuranceADKAgent(
            name="Insurance Domain Agent",
            description="Customer-facing agent for insurance inquiries with A2A communication",
            model_config=domain_model_config
        )
        
        technical_agent = InsuranceADKAgent(
            name="Insurance Technical Agent", 
            description="Technical agent for policy data and A2A operations",
            model_config=technical_model_config
        )
        
        # Create orchestrator
        orchestrator = InsuranceADKOrchestrator(domain_agent, technical_agent)
        
        logger.info("ADK Orchestrator created successfully with A2A communication")
        return orchestrator
        
    except Exception as e:
        logger.error(f"Failed to create ADK orchestrator: {e}")
        raise 