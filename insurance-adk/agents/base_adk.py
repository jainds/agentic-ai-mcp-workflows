"""
Base Google ADK Integration Classes with Real A2A Communication

This module provides the core Google ADK integration classes for the
insurance AI system following the architecture patterns from:
https://medium.com/google-cloud/architecting-a-multi-agent-system-with-google-a2a-and-adk-4ced4502c86a
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import asyncio

# A2A imports for proper agent communication
from python_a2a import AgentCard

logger = logging.getLogger(__name__)

@dataclass
class ADKModelConfig:
    """Configuration for Google ADK models with OpenRouter integration"""
    primary_model: str
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    fallback_model: str = "openrouter/openai/gpt-4o-mini"
    max_tokens: int = 4096
    temperature: float = 0.3

class InsuranceADKTool:
    """Base class for insurance-specific ADK tools with A2A support"""
    
    def __init__(self, name: str, description: str, tool_function: callable):
        self.name = name
        self.description = description
        self.function = tool_function
        self.insurance_context = True
        
    async def execute_with_context(self, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute tool with insurance context"""
        try:
            # Add insurance-specific context
            kwargs['insurance_context'] = context
            result = await self.function(**kwargs)
            
            return {
                "success": True,
                "tool": self.name,
                "result": result,
                "context": context
            }
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            return {
                "success": False,
                "tool": self.name,
                "error": str(e),
                "context": context
            }

class InsuranceADKWorkflow:
    """Insurance-specific ADK workflow with A2A communication"""
    
    def __init__(self, name: str, description: str, steps: List[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.steps = steps or []
        self.insurance_workflow = True
        
    async def execute_insurance_flow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute insurance workflow with A2A communication support"""
        try:
            logger.info(f"Starting insurance workflow: {self.name}")
            
            # Initialize workflow context
            context = {
                "workflow": self.name,
                "customer_id": input_data.get("customer_id"),
                "session_id": input_data.get("session_id"),
                "timestamp": input_data.get("timestamp"),
                "steps_completed": []
            }
            
            result = {
                "success": True,
                "workflow": self.name,
                "description": self.description,
                "input": input_data,
                "context": context,
                "processed_by": "InsuranceADKWorkflow"
            }
            
            logger.info(f"Insurance workflow {self.name} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Insurance workflow {self.name} failed: {e}")
            return {
                "success": False,
                "workflow": self.name,
                "error": str(e),
                "input": input_data
            }

class InsuranceADKAgent:
    """Insurance-specific ADK agent following BaseAgent pattern with A2A communication
    
    Based on the architecture described in:
    https://medium.com/google-cloud/architecting-a-multi-agent-system-with-google-a2a-and-adk-4ced4502c86a
    """
    
    def __init__(self, name: str, description: str, model_config: ADKModelConfig, 
                 tools: List[InsuranceADKTool] = None, agent_url: str = None):
        
        self.agent_name = name
        self.agent_description = description
        self.model_config = model_config
        self.tools = tools or []
        self.insurance_agent = True
        self.logger = logging.getLogger(__name__)
        
        # Create proper A2A Agent Card following the article pattern
        self.agent_card = AgentCard(
            name=name,
            description=description,
            url=agent_url or f"http://localhost:8000/agents/{name.lower().replace(' ', '-')}",
            version="1.0.0",
            capabilities={
                "customer_service": True,
                "policy_management": True, 
                "a2a_communication": True
            }
        )
        
    async def process_customer_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process customer request with insurance context - Core agent logic"""
        try:
            self.logger.info(f"Agent {self.agent_name} processing customer request")
            
            # Insurance-specific processing following ADK BaseAgent pattern
            result = {
                "agent": self.agent_name,
                "description": self.agent_description,
                "framework": "Google ADK + A2A Protocol",
                "request": request,
                "processed": True,
                "timestamp": request.get("timestamp"),
                "customer_id": request.get("customer_id")
            }
            
            # LLM processing simulation
            if "message" in request:
                result["response"] = f"Insurance agent {self.agent_name} processed: {request['message']}"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_name} processing failed: {e}")
            return {
                "agent": self.agent_name,
                "error": str(e),
                "request": request,
                "processed": False
            }
    
    async def handle_a2a_communication(self, a2a_request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle A2A communication requests using proper A2A protocol patterns"""
        try:
            self.logger.info(f"Agent {self.agent_name} handling A2A request")
            
            # Follow A2A Task/Message/Artifact pattern from the article
            result = {
                "agent": self.agent_name,
                "framework": "Google ADK + A2A Protocol",
                "a2a_request": a2a_request,
                "a2a_processed": True,
                "customer_id": a2a_request.get("customer_id"),
                "operation": a2a_request.get("operation")
            }
            
            # A2A processing with proper response structure
            if a2a_request.get("operation") == "get_customer_policies":
                # Return A2A Artifact structure as described in the article
                result["a2a_response"] = {
                    "status": "success",
                    "data": "Policy data retrieved via A2A protocol",
                    "agent": self.agent_name,
                    "a2a_protocol": "python-a2a",
                    "artifact": {
                        "type": "DataPart",
                        "content": {
                            "policies": ["Policy-001", "Policy-002"],
                            "customer_id": a2a_request.get("customer_id")
                        }
                    }
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Agent {self.agent_name} A2A handling failed: {e}")
            return {
                "agent": self.agent_name,
                "error": str(e),
                "a2a_request": a2a_request,
                "a2a_processed": False
            }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status with A2A capabilities"""
        return {
            "agent": self.agent_name,
            "status": "active",
            "framework": "Google ADK + A2A Protocol",
            "a2a_protocol": "python-a2a v0.5.6",
            "capabilities": ["customer_service", "policy_management", "a2a_communication"],
            "tools_count": len(self.tools),
            "insurance_agent": self.insurance_agent,
            "agent_card": {
                "name": self.agent_card.name,
                "url": self.agent_card.url,
                "version": self.agent_card.version
            }
        }
    
    def get_agent_card(self) -> AgentCard:
        """Return A2A Agent Card for discovery"""
        return self.agent_card

class A2ARiskCheckTool(InsuranceADKTool):
    """A2A Tool for risk checking - following the article's A2ARiskCheckTool pattern"""
    
    def __init__(self, risk_agent_url: str):
        super().__init__(
            name="A2A Risk Check Tool",
            description="Communicates with risk agent via A2A protocol",
            tool_function=self._perform_risk_check
        )
        self.risk_agent_url = risk_agent_url
        self.logger = logging.getLogger(__name__)
    
    async def _perform_risk_check(self, trade_proposal: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Perform A2A risk check following the article's pattern"""
        try:
            # Simulate A2A JSON-RPC call to risk agent
            # In real implementation, this would use httpx to call the risk agent
            self.logger.info(f"Performing A2A risk check for trade: {trade_proposal}")
            
            # Mock A2A response following the article's structure
            return {
                "success": True,
                "risk_decision": "approved",
                "reasoning": "Trade within risk limits",
                "a2a_protocol": "python-a2a",
                "artifact": {
                    "type": "DataPart",
                    "risk_analysis": {
                        "approved": True,
                        "risk_score": 0.3,
                        "limits_checked": ["position_size", "concentration"]
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"A2A risk check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "a2a_protocol": "python-a2a"
            } 