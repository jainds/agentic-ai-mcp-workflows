"""
Response formatting module for Domain Agent
Handles LLM-based response formatting
"""

import logging
from typing import Dict, Any
from prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Handles formatting of responses using LLM and templates"""
    
    def __init__(self, openai_client=None):
        """Initialize the response formatter"""
        self.openai_client = openai_client
        self.prompts = PromptLoader()
    
    def format_comprehensive_response(self, intent: str, customer_id: str, technical_response: str, user_question: str) -> str:
        """Format comprehensive response using LLM and templates"""
        return self._format_with_llm(intent, customer_id, technical_response, user_question)
    
    def _format_with_llm(self, intent: str, customer_id: str, technical_response: str, user_question: str) -> str:
        """Use LLM to format response with template structure"""
        try:
            # Select appropriate template based on intent
            template_key = self._get_template_key_for_intent(intent)
            response_template = self.prompts.prompts.get("response_formatting", {}).get(template_key, "")
            
            # Get enhanced prompt from YAML
            enhanced_prompt = self.prompts.get_llm_formatting_prompt(
                user_question, customer_id, intent, technical_response, response_template
            )

            response = self.openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            formatted_response = response.choices[0].message.content.strip()
            logger.info(f"🔥 DOMAIN AGENT: LLM formatted response using template: {template_key}")
            return formatted_response
            
        except Exception as e:
            logger.error(f"🔥 DOMAIN AGENT: LLM formatting failed: {e}")
            raise ValueError(f"Failed to format response with LLM: {e}")

    def _get_template_key_for_intent(self, intent: str) -> str:
        """Map intent to appropriate response template key"""
        template_mapping = {
            "payment_inquiry": "payment_due_template",
            "coverage_inquiry": "coverage_total_template", 
            "agent_contact": "agent_contact_template",
            "policy_inquiry": "policy_response_template",
            "policy_types": "policy_types_template"
        }
        
        return template_mapping.get(intent, "policy_response_template") 