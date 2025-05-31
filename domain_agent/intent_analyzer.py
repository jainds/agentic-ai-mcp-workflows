"""
Intent analysis module for Domain Agent
Handles LLM and rule-based intent analysis
"""

import json
import re
import logging
from typing import Dict, Any
from prompt_loader import PromptLoader

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
        rule_result = self._analyze_with_rules(user_text)
        logger.info(f"🔥 DOMAIN AGENT: Rule-based intent analysis result: {rule_result}")
        return rule_result
    
    def _analyze_with_llm(self, user_text: str) -> Dict[str, Any]:
        """Use LLM to understand customer intent"""
        try:
            prompt = self.prompts.get_intent_analysis_prompt(user_text)
            
            response = self.openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200
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
            logger.error(f"🔥 DOMAIN AGENT: LLM analysis failed: {e}")
            raise ValueError(f"LLM analysis failed: {e}")
    
    def _analyze_with_rules(self, user_text: str) -> Dict[str, Any]:
        """Fallback rule-based intent analysis"""
        text_lower = user_text.lower()
        
        # Extract customer ID using patterns
        customer_id = None
        patterns = [
            r'(?:customer|user|client|id)[:\s]+([A-Za-z0-9_-]+)',
            r'([A-Z]{3,}-\d+)',  # CUST-001, USER-123
            r'(user_\w+)',       # user_003
            r'(\w+\d+)',         # cust001, user123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                customer_id = match.group(1) if '(' in pattern else match.group(0)
                break
        
        # Determine intent based on keywords
        intent = "general_inquiry"  # default
        
        # Coverage/total amount queries
        if any(word in text_lower for word in ["total coverage", "coverage amount", "total amount", "how much coverage"]):
            intent = "coverage_inquiry"
        # Payment queries (including premium and billing)
        elif any(word in text_lower for word in ["payment", "due", "billing", "pay", "premium", "premiums", "deductible", "deductibles"]):
            intent = "payment_inquiry"
        # Agent contact queries
        elif any(word in text_lower for word in ["agent", "contact", "who is my", "representative"]):
            intent = "agent_contact"
        # Policy type queries  
        elif any(word in text_lower for word in ["policy", "policies", "types", "what do i have", "what policies"]):
            intent = "policy_inquiry"
        # Claims queries
        elif any(word in text_lower for word in ["claim", "claims", "claim status"]):
            intent = "claim_status"
        
        # Calculate confidence
        confidence = 0.7  # Base confidence for rule-based
        if customer_id:
            confidence += 0.2  # Higher confidence if customer ID found
        if intent != "general_inquiry":
            confidence += 0.1  # Higher confidence if specific intent detected
        
        return {
            "primary_intent": intent,
            "customer_id": customer_id,
            "confidence": min(confidence, 0.9),  # Cap at 0.9 for rule-based
            "method": "rules",
            "text_analyzed": user_text
        } 