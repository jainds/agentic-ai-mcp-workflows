"""
Prompt loader for Technical Agent
Reads prompts from YAML file and provides easy access
"""

import yaml
import os
from typing import Dict, Any


class PromptLoader:
    """Load and format prompts from YAML for Technical Agent"""
    
    def __init__(self, prompts_file: str = "prompts.yaml"):
        """Load prompts from YAML file"""
        self.prompts_file = prompts_file
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from YAML file"""
        prompts_path = os.path.join(os.path.dirname(__file__), self.prompts_file)
        
        try:
            with open(prompts_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: Prompts file {prompts_path} not found. Using defaults.")
            return {}
        except yaml.YAMLError as e:
            print(f"Warning: Error loading prompts file: {e}. Using defaults.")
            return {}
    
    def get_llm_parsing_prompt(self, text: str) -> str:
        """Get the LLM request parsing prompt"""
        template = self.prompts.get("request_parsing", {}).get("llm_parsing_prompt", "")
        return template.format(text=text)
    
    def get_error_response(self, error_type: str) -> str:
        """Get error response template"""
        templates = self.prompts.get("error_responses", {})
        return templates.get(error_type, "An error occurred while processing your request.") 