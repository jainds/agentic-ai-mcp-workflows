"""
Pure ADK Agent Definitions for Insurance AI System
"""
from typing import Dict, Any, List
import yaml
import os


class ADKAgentDefinition:
    """Base class for pure ADK agent definitions"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.prompts = self._load_prompts()
        self.models = self._load_models()
        self.workflows = self._load_workflows()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompts from YAML files"""
        prompts = {}
        prompt_files = [
            'domain_agent.yaml',
            'technical_agent.yaml'
        ]
        
        for file in prompt_files:
            try:
                with open(f'config/prompts/{file}', 'r') as f:
                    prompts.update(yaml.safe_load(f))
            except FileNotFoundError:
                print(f"Warning: Prompt file {file} not found")
                continue
        
        return prompts
    
    def _load_models(self) -> Dict[str, Any]:
        """Load model configuration"""
        try:
            with open('config/models.yaml', 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print("Warning: models.yaml not found, using defaults")
            return {
                'models': {
                    'domain_agent': {
                        'primary': 'openrouter/anthropic/claude-3.5-sonnet',
                        'fallback': 'openrouter/openai/gpt-4o-mini'
                    },
                    'technical_agent': {
                        'primary': 'openrouter/meta-llama/llama-3.1-70b-instruct',
                        'fallback': 'openrouter/openai/gpt-4o-mini'
                    }
                }
            }
    
    def _load_workflows(self) -> Dict[str, Any]:
        """Load workflow configurations"""
        workflows = {}
        workflow_files = ['customer_workflow.yaml', 'technical_workflow.yaml']
        
        for file in workflow_files:
            try:
                with open(f'config/workflows/{file}', 'r') as f:
                    workflows.update(yaml.safe_load(f))
            except FileNotFoundError:
                print(f"Warning: Workflow file {file} not found")
                continue
        
        return workflows


class PureDomainAgentDefinition(ADKAgentDefinition):
    """Pure ADK domain agent definition"""
    
    def __init__(self):
        super().__init__('config/prompts/domain_agent.yaml')
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration for ADK"""
        model_config = self.models['models']['domain_agent']
        
        return {
            'name': 'insurance_domain_agent',
            'description': 'Pure ADK insurance domain agent for customer service',
            'instruction': self.prompts.get('system_prompt', ''),
            'model_config': model_config,
            'workflows': self._get_domain_workflows(),
            'tools': self._get_domain_tools()
        }
    
    def _get_domain_workflows(self) -> List[str]:
        """Get workflows for domain agent"""
        return ['customer_inquiry_processing']
    
    def _get_domain_tools(self) -> List[str]:
        """Get tools for domain agent"""
        return ['session_manager', 'intent_analyzer', 'response_formatter']
    
    def get_prompts(self) -> Dict[str, str]:
        """Get domain agent prompts"""
        return {
            'intent_analysis': self.prompts.get('intent_analysis_prompt', ''),
            'response_formatting': self.prompts.get('response_formatting_prompt', ''),
            'conversation_planning': self.prompts.get('conversation_planning_prompt', '')
        }


class PureTechnicalAgentDefinition(ADKAgentDefinition):
    """Pure ADK technical agent definition"""
    
    def __init__(self):
        super().__init__('config/prompts/technical_agent.yaml')
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration for ADK"""
        model_config = self.models['models']['technical_agent']
        
        return {
            'name': 'insurance_technical_agent',
            'description': 'Pure ADK technical agent for A2A operations and MCP integration',
            'instruction': self.prompts.get('system_prompt', ''),
            'model_config': model_config,
            'workflows': self._get_technical_workflows(),
            'tools': self._get_technical_tools()
        }
    
    def _get_technical_workflows(self) -> List[str]:
        """Get workflows for technical agent"""
        return ['technical_data_processing']
    
    def _get_technical_tools(self) -> List[str]:
        """Get tools for technical agent"""
        return ['mcp_policy_tool', 'request_parser', 'response_formatter']
    
    def get_prompts(self) -> Dict[str, str]:
        """Get technical agent prompts"""
        return {
            'request_parsing': self.prompts.get('request_parsing_prompt', ''),
            'tool_selection': self.prompts.get('tool_selection_prompt', ''),
            'error_handling': self.prompts.get('error_handling_prompt', ''),
            'response_formatting': self.prompts.get('response_formatting_prompt', '')
        }


class OrchestratorDefinition(ADKAgentDefinition):
    """ADK orchestrator definition"""
    
    def __init__(self):
        super().__init__('config/prompts/orchestrator.yaml')
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get orchestrator configuration for ADK"""
        model_config = self.models['models'].get('orchestrator', 
                                                  self.models['models']['domain_agent'])
        
        return {
            'name': 'insurance_orchestrator',
            'description': 'ADK orchestrator for insurance agent system',
            'instruction': 'Coordinate between domain and technical agents to provide comprehensive insurance services',
            'model_config': model_config,
            'workflows': self._get_orchestrator_workflows(),
            'agents': ['insurance_domain_agent', 'insurance_technical_agent']
        }
    
    def _get_orchestrator_workflows(self) -> List[str]:
        """Get workflows managed by orchestrator"""
        return ['customer_inquiry_processing', 'technical_data_processing'] 