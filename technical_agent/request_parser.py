"""
Request parsing module for Technical Agent
Handles LLM-based request parsing only
"""

import json
import re
import logging
from typing import Dict, Any, Optional
from prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class RequestParser:
    """Handles parsing of incoming requests using LLM only"""
    
    def __init__(self, openai_client=None):
        """Initialize the request parser"""
        if not openai_client:
            raise ValueError("OpenAI client is required for LLM-based request parsing. No fallback to rules.")
        
        self.openai_client = openai_client
        self.prompts = PromptLoader()
    
    def parse_request(self, text: str) -> Dict[str, Any]:
        """Parse request using LLM only"""
        return self._parse_request_with_llm(text)
    
    def _parse_request_with_llm(self, text: str) -> Dict[str, Any]:
        """Use LLM to intelligently parse the request and extract intent only"""
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
                    "customer_id": None,  # Customer ID comes from session, not LLM
                    "original_customer_mention": None,  # Not extracted by LLM anymore
                    "confidence": float(parsed_result.get("confidence", 0.5)),
                    "reasoning": parsed_result.get("reasoning", "LLM analysis"),
                    "method": "llm"
                }
                
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
                            "customer_id": None,  # Customer ID comes from session, not LLM
                            "original_customer_mention": None,  # Not extracted by LLM anymore
                            "confidence": float(parsed_result.get("confidence", 0.5)),
                            "reasoning": parsed_result.get("reasoning", "LLM analysis (extracted)"),
                            "method": "llm"
                        }
                        
                        logger.info(f"Extracted JSON from LLM response: {result}")
                        return result
                    except json.JSONDecodeError:
                        pass
                
                logger.error(f"Could not parse LLM JSON response: {json_error}")
                raise RuntimeError(f"Failed to parse LLM response as JSON: {json_error}. No fallback available.")
                    
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            raise RuntimeError(f"LLM-based request parsing failed: {e}. No fallback available.") 