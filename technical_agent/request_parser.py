"""
Request parsing module for Technical Agent
Handles LLM and rule-based request parsing
"""

import json
import re
import logging
from typing import Dict, Any, Optional
from prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class RequestParser:
    """Handles parsing of incoming requests to extract intent and customer information"""
    
    def __init__(self, openai_client=None):
        """Initialize the request parser"""
        self.openai_client = openai_client
        self.prompts = PromptLoader()
    
    def parse_request(self, text: str) -> Dict[str, Any]:
        """Parse request using LLM if available, otherwise use rules"""
        if self.openai_client:
            return self._parse_request_with_llm(text)
        else:
            return self._parse_request_with_rules(text)
    
    def _parse_request_with_llm(self, text: str) -> Dict[str, Any]:
        """Use LLM to intelligently parse the request and extract customer IDs"""
        try:
            prompt = self.prompts.get_llm_parsing_prompt(text)
            
            response = self.openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"LLM parsing response: {result_text}")
            
            # Parse JSON response with better error handling
            try:
                parsed_result = json.loads(result_text)
                
                # Validate required fields
                if not isinstance(parsed_result, dict):
                    raise ValueError("Response is not a JSON object")
                
                # Ensure required fields exist with defaults
                result = {
                    "intent": parsed_result.get("intent", "general_inquiry"),
                    "customer_id": parsed_result.get("customer_id"),
                    "original_customer_mention": parsed_result.get("original_customer_mention"),
                    "confidence": float(parsed_result.get("confidence", 0.5)),
                    "reasoning": parsed_result.get("reasoning", "LLM analysis"),
                    "method": "llm"
                }
                
                # Additional validation for customer_id
                if result["customer_id"] and result["customer_id"].lower() in ["null", "none", ""]:
                    result["customer_id"] = None
                
                logger.info(f"Successfully parsed with LLM: {result}")
                return result
                
            except (json.JSONDecodeError, ValueError) as json_error:
                # Try to extract JSON from response if wrapped in other text
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_result = json.loads(json_match.group(0))
                        result = {
                            "intent": parsed_result.get("intent", "general_inquiry"),
                            "customer_id": parsed_result.get("customer_id"),
                            "original_customer_mention": parsed_result.get("original_customer_mention"),
                            "confidence": float(parsed_result.get("confidence", 0.5)),
                            "reasoning": parsed_result.get("reasoning", "LLM analysis (extracted)"),
                            "method": "llm"
                        }
                        
                        if result["customer_id"] and result["customer_id"].lower() in ["null", "none", ""]:
                            result["customer_id"] = None
                            
                        logger.info(f"Extracted JSON from LLM response: {result}")
                        return result
                    except json.JSONDecodeError:
                        pass
                
                logger.warning(f"Could not parse LLM JSON response: {json_error}, falling back to rules")
                return self._parse_request_with_rules(text)
                    
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}, falling back to rules")
            return self._parse_request_with_rules(text)
    
    def _parse_request_with_rules(self, text: str) -> Dict[str, Any]:
        """Enhanced rule-based request parsing as fallback"""
        text_lower = text.lower()
        
        # Enhanced customer ID extraction patterns
        customer_id = None
        original_mention = None
        patterns = [
            # Standard ID formats
            (r'user_\w+', None),                         # user_003, user_001
            (r'CUST-\d+', None),                         # CUST-001, CUST-002  
            (r'cust-\d+', None),                         # cust-001 (lowercase)
            (r'customer[_\s-]+([A-Za-z0-9_-]+)', 1),    # customer CUST-001, customer_001
            (r'user[_\s]+([A-Za-z0-9_-]+)', 1),         # user 003, user ABC
            (r'client[_\s]+([A-Za-z0-9_-]+)', 1),       # client 001, client ABC
            # More flexible patterns
            (r'id[_\s]*([A-Za-z0-9_-]+)', 1),           # id 003, id_ABC
            (r'([A-Z]{3,}-\d+)', None),                  # Any 3+ letter prefix with dash and numbers
            (r'([A-Za-z]+\d+)', None),                   # Any letters followed by numbers
        ]
        
        for pattern, group_index in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if group_index is not None:
                    customer_id = match.group(group_index)
                    original_mention = match.group(0)
                else:
                    customer_id = match.group(0)
                    original_mention = match.group(0)
                break
        
        # Determine intent with better keyword matching
        intent = "general_inquiry"  # default
        
        # Policy-related keywords
        policy_keywords = ["policy", "policies", "coverage", "claim", "claims", "premium", "deductible"]
        if any(word in text_lower for word in policy_keywords):
            intent = "get_customer_policies"
        
        # Health check keywords
        health_keywords = ["health", "status", "check", "ping", "alive", "working"]
        if any(word in text_lower for word in health_keywords):
            intent = "health_check"
        
        # If we found a customer ID, it's likely a policy request
        if customer_id and intent == "general_inquiry":
            intent = "get_customer_policies"
        
        # Calculate confidence based on pattern strength
        confidence = 0.6  # base confidence for rule-based
        if customer_id:
            confidence += 0.2  # boost if we found a customer ID
        if intent != "general_inquiry":
            confidence += 0.1  # boost if we determined specific intent
        
        result = {
            "intent": intent,
            "customer_id": customer_id,
            "original_customer_mention": original_mention,
            "confidence": min(confidence, 0.9),  # cap at 0.9 for rule-based
            "reasoning": f"Rule-based pattern matching (found: {original_mention})" if original_mention else "Rule-based pattern matching",
            "method": "rules"
        }
        
        logger.info(f"Rule-based parsing result: {result}")
        return result 