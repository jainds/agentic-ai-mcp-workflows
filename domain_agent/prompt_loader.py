"""
Simple prompt loader for Domain Agent
Reads prompts from YAML file and provides easy access
"""

import yaml
import os
from typing import Dict, Any


class PromptLoader:
    """Simple class to load and format prompts from YAML"""
    
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
    
    def get_intent_analysis_prompt(self, user_text: str) -> str:
        """Get the LLM intent analysis prompt"""
        template = self.prompts.get("intent_analysis", {}).get("llm_intent_analysis_prompt", "")
        return template.format(user_text=user_text)
    
    def get_response_template(self, intent: str) -> str:
        """Get response template for specific intent"""
        templates = self.prompts.get("response_formatting", {})
        
        if intent == "policy_inquiry":
            return templates.get("policy_inquiry_response", "")
        elif intent == "claim_status":
            return templates.get("claim_status_response", "")
        else:
            return templates.get("general_inquiry_response", "")
    
    def get_error_response(self, error_type: str) -> str:
        """Get error response template"""
        templates = self.prompts.get("error_handling", {})
        return templates.get(f"{error_type}_response", "I apologize for the error.")
    
    def get_context_message(self, context_type: str) -> str:
        """Get context message template"""
        templates = self.prompts.get("conversation_context", {})
        return templates.get(context_type, "") 