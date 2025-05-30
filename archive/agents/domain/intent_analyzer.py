"""
Intent Analysis Module for Domain Agent
Handles intent understanding, entity extraction, and analysis
"""

import json
import re
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger(__name__)


class IntentAnalyzer:
    """
    Handles intent analysis and understanding for the domain agent
    """
    
    def __init__(self, llm_client, model_name: str):
        """
        Initialize the intent analyzer
        
        Args:
            llm_client: LLM client for intent analysis
            model_name: Name of the model to use
        """
        self.llm_client = llm_client
        self.model_name = model_name
    
    def understand_intent(self, user_text: str) -> Dict[str, Any]:
        """
        Role 1: Understand user intent and extract key information
        """
        if not self.llm_client:
            raise RuntimeError("LLM client required for intent understanding")
        
        prompt = f"""
        As an insurance domain expert, analyze this user request and extract:
        1. Primary intent - Choose ONE from: claim_filing, policy_inquiry, billing_question, claim_status, quote_request, general_inquiry
        2. Secondary intents (if any)
        3. Key entities (policy numbers, claim IDs, dates, amounts, etc.)
        4. Required information gathering
        5. Urgency level
        6. Complexity assessment
        
        IMPORTANT INTENT CLASSIFICATION RULES:
        - If user mentions "quote", "rate", "pricing", "cost", "estimate", "get a quote" → quote_request
        - If user wants to buy/purchase insurance or asks about insurance options → quote_request
        - If user mentions "claim" AND ("status", "check", "update", "progress", "recent") → claim_status
        - If user mentions claim ID (like CLM-123456) → claim_status  
        - If user asks about "claims" in plural → claim_status
        - If user wants to "file" or "submit" new claim → claim_filing
        - If user asks about "policy" or "policies" → policy_inquiry
        - If user asks about "billing", "payment", "premium" → billing_question
        - Otherwise → general_inquiry
        
        EXAMPLES:
        - "I'd like to get a quote for auto insurance" → quote_request
        - "What's the status of my claim?" → claim_status
        - "I need to file a claim" → claim_filing
        - "What's my policy details?" → policy_inquiry
        
        User Request: "{user_text}"
        
        Respond in JSON format:
        {{
            "primary_intent": "string",
            "secondary_intents": ["string"],
            "entities": {{"entity_type": "value"}},
            "required_info": ["info_needed"],
            "urgency": "low|medium|high",
            "complexity": "simple|moderate|complex",
            "confidence": 0.0-1.0
        }}
        """
        
        logger.info("Intent analysis starting", user_text=user_text, model=self.model_name)
        
        response = self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        intent_text = response.choices[0].message.content
        logger.info("LLM raw response", response_text=intent_text)
        
        # Parse the JSON response
        intent_analysis = self._parse_intent_response(intent_text)
        
        logger.info("Intent analysis completed", 
                   primary_intent=intent_analysis.get("primary_intent"),
                   confidence=intent_analysis.get("confidence"),
                   entities=intent_analysis.get("entities"))
        
        return intent_analysis
    
    def _parse_intent_response(self, intent_text: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract JSON intent analysis
        """
        # Handle markdown code blocks around JSON
        if intent_text.startswith("```json") and intent_text.endswith("```"):
            intent_text = intent_text[7:-3].strip()
        elif intent_text.startswith("```") and intent_text.endswith("```"):
            intent_text = intent_text[3:-3].strip()
        
        # Handle cases where LLM returns JSON followed by explanation text
        # Look for the first complete JSON object
        try:
            intent_analysis = json.loads(intent_text)
        except json.JSONDecodeError:
            # Look for JSON block in the response
            json_match = re.search(r'\{[^}]*\}', intent_text, re.DOTALL)
            if json_match:
                json_part = json_match.group(0)
                # Count braces to get complete JSON
                brace_count = 0
                end_pos = 0
                for i, char in enumerate(intent_text):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos > 0:
                    json_part = intent_text[:end_pos]
                    intent_analysis = json.loads(json_part)
                else:
                    raise ValueError("Could not extract valid JSON from LLM response")
            else:
                raise ValueError("No JSON found in LLM response")
        
        return intent_analysis
    
    def identify_missing_information(self, intent: str, entities: Dict[str, Any], customer_id: str = None) -> List[str]:
        """Identify what information is missing for the given intent"""
        missing = []
        
        # Critical information requirements by intent
        intent_requirements = {
            "claim_filing": ["customer_id", "incident_details"],
            "claim_status": ["customer_id"],  # claim_id is optional if we can find by customer
            "policy_inquiry": ["customer_id"],
            "billing_question": ["customer_id"],
            "quote_request": ["coverage_type"],  # customer_id not required for quotes
            "general_inquiry": []  # No specific requirements
        }
        
        required_info = intent_requirements.get(intent, [])
        
        # Check each requirement
        for requirement in required_info:
            if requirement == "customer_id" and not customer_id:
                missing.append("customer_id")
            elif requirement == "incident_details" and not any(
                key in entities for key in ["incident_date", "incident_type", "damage_description"]
            ):
                missing.append("incident_details")
            elif requirement == "coverage_type" and not any(
                key in entities for key in ["coverage_type", "vehicle_type", "property_type"]
            ):
                missing.append("coverage_type")
        
        return missing
    
    def generate_clarifying_questions(self, missing_info: List[str], intent: str) -> List[str]:
        """Generate clarifying questions for missing information"""
        questions = []
        
        question_templates = {
            "customer_id": "Could you please provide your customer ID or policy number so I can look up your account?",
            "incident_details": "To help you file your claim, could you provide details about the incident (date, type of damage, and description)?",
            "coverage_type": "What type of insurance coverage are you interested in? (auto, home, life, etc.)",
            "claim_id": "Do you have your claim number handy? If not, I can look it up using your customer information.",
            "policy_number": "Could you provide your policy number so I can access your specific coverage details?"
        }
        
        for info in missing_info:
            if info in question_templates:
                questions.append(question_templates[info])
            else:
                questions.append(f"I need additional information about {info.replace('_', ' ')} to help you better.")
        
        return questions 