"""
Google ADK Integration for Insurance AI System
Using Official Google Agent Development Kit v1.0.0
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# Official Google ADK imports
from adk import Agent, Tool, Model, Workflow, WorkflowStep
from adk.models import LiteLLMModel
from adk.tools import FunctionTool
from adk.workflows import SequentialWorkflow, ParallelWorkflow

# LiteLLM for model integration
import litellm


class ADKModelConfig:
    """Configuration for ADK models with LiteLLM integration"""
    
    def __init__(self, primary_model: str, fallback_model: str = None, 
                 api_key: str = None, base_url: str = None, **kwargs):
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
        
    def create_model(self) -> LiteLLMModel:
        """Create ADK LiteLLM model instance"""
        return LiteLLMModel(
            model=self.primary_model,
            api_key=self.api_key,
            base_url=self.base_url,
            **self.config
        )


class InsuranceADKTool(Tool):
    """Base class for insurance-specific ADK tools"""
    
    def __init__(self, name: str, description: str, handler: Callable, **kwargs):
        super().__init__(name=name, description=description, **kwargs)
        self.handler = handler
        
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool using the handler"""
        try:
            return await self.handler(**kwargs)
        except Exception as e:
            logging.error(f"Tool {self.name} execution error: {str(e)}")
            return {"error": str(e), "tool": self.name}


class InsuranceADKWorkflow(Workflow):
    """Base class for insurance workflows using Google ADK"""
    
    def __init__(self, name: str, description: str, steps: List[WorkflowStep] = None, **kwargs):
        super().__init__(name=name, description=description, **kwargs)
        self.steps = steps or []
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow using ADK framework"""
        context = input_data.copy()
        results = []
        
        for step in self.steps:
            try:
                step_result = await step.execute(context)
                results.append({
                    "step": step.name,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update context with step results
                context.update(step_result)
                
            except Exception as e:
                error_result = {
                    "step": step.name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
                logging.error(f"Workflow step {step.name} failed: {str(e)}")
                break
        
        return {
            "workflow": self.name,
            "success": not any("error" in r for r in results),
            "results": results,
            "context": context,
            "completed_at": datetime.now().isoformat()
        }


class InsuranceADKAgent(Agent):
    """Base class for insurance agents using Google ADK"""
    
    def __init__(self, name: str, description: str, model_config: ADKModelConfig, 
                 tools: List[Tool] = None, workflows: List[Workflow] = None, **kwargs):
        
        # Create model
        model = model_config.create_model()
        
        # Initialize ADK agent
        super().__init__(
            name=name,
            description=description,
            model=model,
            tools=tools or [],
            **kwargs
        )
        
        # Store workflows
        self.workflows = {wf.name: wf for wf in (workflows or [])}
        self.logger = logging.getLogger(__name__)
        
    def get_workflow(self, workflow_name: str) -> Optional[Workflow]:
        """Get workflow by name"""
        return self.workflows.get(workflow_name)
    
    async def execute_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific workflow"""
        workflow = self.get_workflow(workflow_name)
        if not workflow:
            return {
                "success": False,
                "error": f"Workflow {workflow_name} not found",
                "available_workflows": list(self.workflows.keys())
            }
        
        return await workflow.execute(input_data)


def create_litellm_model(model_name: str, api_key: str = None, base_url: str = None, **kwargs) -> LiteLLMModel:
    """Factory function to create LiteLLM model for ADK"""
    return LiteLLMModel(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        **kwargs
    )


def create_function_tool(name: str, description: str, func: Callable, **kwargs) -> FunctionTool:
    """Factory function to create function tool for ADK"""
    return FunctionTool(
        name=name,
        description=description,
        func=func,
        **kwargs
    )


def create_sequential_workflow(name: str, description: str, steps: List[WorkflowStep], **kwargs) -> SequentialWorkflow:
    """Factory function to create sequential workflow"""
    return SequentialWorkflow(
        name=name,
        description=description,
        steps=steps,
        **kwargs
    )


def create_parallel_workflow(name: str, description: str, steps: List[WorkflowStep], **kwargs) -> ParallelWorkflow:
    """Factory function to create parallel workflow"""
    return ParallelWorkflow(
        name=name,
        description=description,
        steps=steps,
        **kwargs
    )