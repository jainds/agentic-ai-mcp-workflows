"""
Response formatting module for Domain Agent
Handles LLM-based response formatting using examples instead of rigid templates
"""

import sys
import os
import logging
import time
from typing import Dict, Any
from prompt_loader import PromptLoader

# Import monitoring
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from monitoring.setup.monitoring_setup import get_monitoring_manager
    monitoring = get_monitoring_manager()
    MONITORING_ENABLED = monitoring.is_monitoring_enabled()
except Exception:
    monitoring = None
    MONITORING_ENABLED = False

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Handles formatting of responses using LLM and templates"""
    
    def __init__(self, openai_client=None):
        """Initialize the response formatter"""
        self.openai_client = openai_client
        self.prompts = PromptLoader()
    
    def format_comprehensive_response(self, intent: str, customer_id: str, technical_response: str, user_question: str) -> str:
        """Format comprehensive response using LLM with examples instead of rigid templates"""
        start_time = time.time()
        
        try:
            # Get the LLM formatting prompt (no longer needs response_template parameter)
            prompt = self.prompts.get_llm_formatting_prompt(
                user_question=user_question,
                customer_id=customer_id,
                intent=intent,
                technical_response=technical_response
            )
            
            # Call LLM to format the response intelligently based on examples
            response = self.openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Slightly higher for more natural language
                max_tokens=800    # Allow for longer, more natural responses
            )
            
            duration = time.time() - start_time
            
            # Record LLM call metrics
            if MONITORING_ENABLED and monitoring:
                monitoring.record_llm_call(
                    model="gpt-4o-mini",
                    prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                    completion_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_tokens=response.usage.total_tokens if response.usage else 0,
                    duration_seconds=duration,
                    success=True,
                    metadata={
                        "function": "response_formatting",
                        "intent": intent,
                        "customer_id": customer_id
                    }
                )
            
            formatted_response = response.choices[0].message.content.strip()
            logger.info(f"🔥 DOMAIN AGENT: LLM formatted response successfully (intent: {intent})")
            
            return formatted_response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record failed LLM call
            if MONITORING_ENABLED and monitoring:
                monitoring.record_llm_call(
                    model="gpt-4o-mini",
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    duration_seconds=duration,
                    success=False,
                    error=str(e),
                    metadata={
                        "function": "response_formatting",
                        "intent": intent,
                        "customer_id": customer_id
                    }
                )
            
            logger.error(f"🔥 DOMAIN AGENT: LLM formatting failed: {e}")
            
            # Fallback to basic formatting if LLM fails
            return f"I found your policy information:\n\n{technical_response}\n\nLet me know if you need help with anything else!"

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