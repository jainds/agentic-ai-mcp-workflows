"""
ADK Orchestrator for Insurance AI System using Official Google ADK
Coordinates between domain and technical agents
"""
import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional

# Official Google ADK imports
from adk import Agent, Workflow, WorkflowStep
from adk.workflows import SequentialWorkflow

# Our ADK integration
from agents.base_adk import InsuranceADKAgent, ADKModelConfig, create_sequential_workflow
from agents.domain_agent import create_domain_agent
from agents.technical_agent import create_technical_agent
from tools.agent_definitions import OrchestratorDefinition


class InsuranceADKOrchestrator:
    """ADK orchestrator for insurance agent system"""
    
    def __init__(self):
        # Load configuration
        self.definition = OrchestratorDefinition()
        config = self.definition.get_agent_config()
        
        # Initialize agents
        self.domain_agent = create_domain_agent()
        self.technical_agent = create_technical_agent()
        
        # Create model configuration for orchestrator
        model_config_data = config['model_config']
        self.model_config = ADKModelConfig(
            primary_model=model_config_data['primary'],
            fallback_model=model_config_data.get('fallback'),
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url="https://openrouter.ai/api/v1",
            max_tokens=model_config_data.get('max_tokens', 4096),
            temperature=model_config_data.get('temperature', 0.2)
        )
        
        # Create workflows
        self.workflows = self._create_workflows()
        
        self.logger = logging.getLogger(__name__)
    
    def _create_workflows(self) -> Dict[str, SequentialWorkflow]:
        """Create ADK workflows for orchestration"""
        workflows = {}
        
        # Customer inquiry workflow
        customer_workflow_steps = [
            WorkflowStep(
                name="intent_analysis",
                agent=self.domain_agent,
                instruction="Analyze customer intent and determine required actions"
            ),
            WorkflowStep(
                name="authentication_check",
                agent=self.domain_agent,
                instruction="Verify customer authentication if required"
            ),
            WorkflowStep(
                name="data_retrieval",
                agent=self.technical_agent,
                instruction="Retrieve policy data using MCP tools"
            ),
            WorkflowStep(
                name="response_synthesis",
                agent=self.domain_agent,
                instruction="Create final customer response"
            )
        ]
        
        workflows["customer_inquiry"] = create_sequential_workflow(
            name="customer_inquiry_processing",
            description="Process customer inquiries through domain and technical agents",
            steps=customer_workflow_steps
        )
        
        # Technical data workflow
        technical_workflow_steps = [
            WorkflowStep(
                name="request_parsing",
                agent=self.technical_agent,
                instruction="Parse A2A request into structured format"
            ),
            WorkflowStep(
                name="mcp_data_retrieval", 
                agent=self.technical_agent,
                instruction="Retrieve data using MCP tools"
            ),
            WorkflowStep(
                name="response_formatting",
                agent=self.technical_agent,
                instruction="Format response for A2A protocol"
            )
        ]
        
        workflows["technical_data"] = create_sequential_workflow(
            name="technical_data_processing",
            description="A2A technical data processing workflow",
            steps=technical_workflow_steps
        )
        
        return workflows
    
    async def process_customer_inquiry(self, message: str, session_id: str, 
                                     customer_id: str = None) -> Dict[str, Any]:
        """Process customer inquiry using ADK workflow orchestration"""
        try:
            # Prepare workflow input
            workflow_input = {
                "message": message,
                "session_id": session_id,
                "customer_id": customer_id,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Execute customer inquiry workflow
            workflow = self.workflows.get("customer_inquiry")
            if not workflow:
                raise Exception("Customer inquiry workflow not found")
            
            result = await workflow.execute(workflow_input)
            
            # Extract final response
            if result.get("success", False):
                final_step = result.get("results", [])[-1] if result.get("results") else {}
                response = final_step.get("result", {}).get("formatted_response", "")
                
                return {
                    "success": True,
                    "response": response,
                    "session_id": session_id,
                    "workflow_results": result,
                    "orchestrated_by": "adk_orchestrator"
                }
            else:
                return {
                    "success": False,
                    "error": "Workflow execution failed",
                    "response": "I apologize, but I'm unable to process your request at this time.",
                    "workflow_results": result
                }
                
        except Exception as e:
            self.logger.error(f"Customer inquiry orchestration error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties.",
                "session_id": session_id
            }
    
    async def process_technical_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process technical A2A request using ADK workflow orchestration"""
        try:
            # Prepare workflow input
            workflow_input = {
                "request": request,
                "customer_id": request.get("customer_id", ""),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Execute technical data workflow
            workflow = self.workflows.get("technical_data")
            if not workflow:
                raise Exception("Technical data workflow not found")
            
            result = await workflow.execute(workflow_input)
            
            # Extract final response
            if result.get("success", False):
                final_step = result.get("results", [])[-1] if result.get("results") else {}
                response = final_step.get("result", {}).get("formatted_response", {})
                
                return {
                    "success": True,
                    "data": response,
                    "workflow_results": result,
                    "orchestrated_by": "adk_orchestrator"
                }
            else:
                return {
                    "success": False,
                    "error": "Technical workflow execution failed",
                    "workflow_results": result
                }
                
        except Exception as e:
            self.logger.error(f"Technical request orchestration error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def route_request(self, request_type: str, **kwargs) -> Dict[str, Any]:
        """Route requests to appropriate workflows"""
        try:
            if request_type == "customer_inquiry":
                return await self.process_customer_inquiry(
                    message=kwargs.get("message", ""),
                    session_id=kwargs.get("session_id", ""),
                    customer_id=kwargs.get("customer_id")
                )
            elif request_type == "technical_request":
                return await self.process_technical_request(
                    request=kwargs.get("request", {})
                )
            elif request_type == "health_check":
                return await self._health_check()
            else:
                return {
                    "success": False,
                    "error": f"Unknown request type: {request_type}",
                    "available_types": ["customer_inquiry", "technical_request", "health_check"]
                }
                
        except Exception as e:
            self.logger.error(f"Request routing error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _health_check(self) -> Dict[str, Any]:
        """Check health of all agents and systems"""
        try:
            health_status = {
                "orchestrator": "healthy",
                "domain_agent": "healthy",
                "technical_agent": "healthy",
                "workflows": list(self.workflows.keys()),
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Test MCP connection through technical agent
            try:
                test_result = await self.technical_agent.mcp_manager.execute_tool_call("health_check")
                health_status["mcp_server"] = "healthy" if test_result.get("success") else "unhealthy"
            except Exception:
                health_status["mcp_server"] = "unreachable"
            
            return {
                "success": True,
                "status": health_status,
                "orchestrated_by": "adk_orchestrator"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    async def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows"""
        return [
            {
                "name": name,
                "description": workflow.description,
                "type": "sequential"
            }
            for name, workflow in self.workflows.items()
        ]
    
    async def close(self):
        """Clean up orchestrator resources"""
        try:
            await self.technical_agent.close()
            # Domain agent doesn't need explicit closing
        except Exception as e:
            self.logger.error(f"Error closing orchestrator: {str(e)}")


# Factory function for creating orchestrator
def create_adk_orchestrator() -> InsuranceADKOrchestrator:
    """Create and return ADK orchestrator instance"""
    return InsuranceADKOrchestrator() 