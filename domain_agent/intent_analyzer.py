"""
Intent analysis module for Domain Agent
Handles LLM and rule-based intent analysis
"""

import json
import re
import logging
import time
from typing import Dict, Any
from prompt_loader import PromptLoader

# Import monitoring
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from monitoring.setup.monitoring_setup import get_monitoring_manager
    monitoring = get_monitoring_manager()
    MONITORING_ENABLED = monitoring.is_monitoring_enabled()
except Exception:
    monitoring = None
    MONITORING_ENABLED = False

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """Handles customer intent analysis using LLM and rules"""
    
    def __init__(self, openai_client=None):
        """Initialize the intent analyzer"""
        self.openai_client = openai_client
        self.prompts = PromptLoader()
    
    def analyze_customer_intent(self, user_text: str) -> Dict[str, Any]:
        """Analyze customer intent and extract information"""
        logger.info(f"🔥 DOMAIN AGENT: Analyzing intent for: {user_text}")
        
        # Try LLM analysis first if available
        if self.openai_client:
            try:
                llm_result = self._analyze_with_llm(user_text)
                logger.info(f"🔥 DOMAIN AGENT: LLM intent analysis result: {llm_result}")
                return llm_result
            except Exception as e:
                logger.warning(f"🔥 DOMAIN AGENT: LLM analysis failed: {e}, falling back to rules")
        
        # Fallback to rule-based analysis
        else:
            return None
    
    def _analyze_with_llm(self, user_text: str) -> Dict[str, Any]:
        """Use LLM to understand customer intent"""
        start_time = time.time()
        
        try:
            prompt = self.prompts.get_intent_analysis_prompt(user_text)
            
            # Track LLM call with monitoring
            response = self.openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200
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
                        "function": "intent_analysis",
                        "input_length": len(user_text)
                    }
                )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"🔥 DOMAIN AGENT: LLM raw response: {result_text}")
            
            # Try to parse JSON, handling common formatting issues
            try:
                result = json.loads(result_text)
                if "customer_id" in result and result["customer_id"] in ["null", "none", "", None]:
                    result["customer_id"] = None
                result["method"] = "llm"
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from markdown or other formatting
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    if "customer_id" in result and result["customer_id"] in ["null", "none", "", None]:
                        result["customer_id"] = None
                    result["method"] = "llm"
                    return result
                else:
                    raise ValueError(f"Could not extract JSON from LLM response: {result_text}")
                    
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
                        "function": "intent_analysis",
                        "input_length": len(user_text)
                    }
                )
            
            logger.error(f"🔥 DOMAIN AGENT: LLM analysis failed: {e}")
            raise ValueError(f"LLM analysis failed: {e}")