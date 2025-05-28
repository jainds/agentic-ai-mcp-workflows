import asyncio
import os
import json
from typing import Dict, Any, List, Optional, Union
import httpx
import logging
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"


@dataclass
class LLMMessage:
    role: str
    content: str
    name: Optional[str] = None


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    provider: str


class OpenRouterClient:
    """Client for OpenRouter API with fallback models"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        self.http_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://insurance-ai-poc.local",
                "X-Title": "Insurance AI PoC"
            }
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Default models with fallbacks
        self.models = {
            "primary": os.getenv("PRIMARY_MODEL", "openai/gpt-4o"),
            "fallback": os.getenv("FALLBACK_MODEL", "anthropic/claude-3-haiku"),
            "embedding": os.getenv("EMBEDDING_MODEL", "openai/text-embedding-ada-002")
        }

    async def chat_completion(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        use_fallback: bool = True,
        **kwargs
    ) -> LLMResponse:
        """Generate chat completion using OpenRouter"""
        
        # Convert messages to dict format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, LLMMessage):
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                    **({"name": msg.name} if msg.name else {})
                })
            else:
                formatted_messages.append(msg)
        
        # Use primary model if not specified
        target_model = model or self.models["primary"]
        
        payload = {
            "model": target_model,
            "messages": formatted_messages,
            "temperature": temperature,
            **kwargs
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            response = await self._make_request("/chat/completions", payload)
            
            choice = response["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                model=response["model"],
                usage=response.get("usage", {}),
                finish_reason=choice.get("finish_reason", "unknown"),
                provider=self._get_provider_from_model(response["model"])
            )
            
        except Exception as e:
            self.logger.error(f"Error with model {target_model}: {str(e)}")
            
            if use_fallback and target_model != self.models["fallback"]:
                self.logger.info(f"Falling back to {self.models['fallback']}")
                return await self.chat_completion(
                    messages, 
                    model=self.models["fallback"],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    use_fallback=False,
                    **kwargs
                )
            else:
                raise

    async def embedding(
        self,
        text: Union[str, List[str]],
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate embeddings using OpenRouter"""
        
        target_model = model or self.models["embedding"]
        
        payload = {
            "model": target_model,
            "input": text
        }
        
        try:
            response = await self._make_request("/embeddings", payload)
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            raise

    async def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to OpenRouter API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            self.logger.error(f"HTTP {e.response.status_code} error: {error_detail}")
            raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error: {str(e)}")
            raise

    def _get_provider_from_model(self, model: str) -> str:
        """Extract provider name from model string"""
        if "/" in model:
            return model.split("/")[0]
        return "unknown"

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


class LLMTemplates:
    """Common prompt templates for insurance domain"""
    
    SYSTEM_PROMPTS = {
        "customer_support": """You are an AI assistant for an insurance company's customer support team. 
You help customers with policy inquiries, claim status checks, and general insurance questions.
Be helpful, professional, and empathetic. Always verify customer information before providing sensitive details.
If you need to perform actions or access data, clearly state what you need to do.""",
        
        "claims_processor": """You are an AI assistant specialized in insurance claims processing.
You help customers file new claims, check claim status, and understand the claims process.
Be thorough in gathering incident details and guide customers through required documentation.
Always maintain a professional and supportive tone during potentially stressful situations.""",
        
        "policy_advisor": """You are an AI assistant focused on insurance policy guidance.
You help customers understand their coverage, policy terms, renewal options, and policy changes.
Explain complex insurance concepts in simple terms and always encourage customers to review policy documents.
Be accurate and conservative in policy interpretations."""
    }
    
    TASK_TEMPLATES = {
        "extract_customer_intent": """Analyze the following customer message and determine their intent:

Customer Message: "{message}"

Classify the intent as one of:
- policy_inquiry: Questions about policy status, coverage, or details
- claim_filing: Want to file a new claim
- claim_status: Check on existing claim status
- billing_inquiry: Questions about payments, billing, or premiums
- general_support: General questions or need assistance
- complaint: Has a complaint or issue to resolve

Respond with just the classification and a brief explanation.""",
        
        "extract_claim_details": """Extract claim information from the customer's description:

Customer Message: "{message}"

Extract and structure the following information if available:
- incident_date: When did the incident occur?
- incident_type: What type of incident (auto accident, theft, fire, etc.)?
- location: Where did it happen?
- description: Brief description of what happened
- estimated_damage: Any mention of damage amount
- police_report: Was police involved?
- injuries: Any injuries mentioned?

Format as JSON object with null for missing information.""",
        
        "generate_response": """Based on the context and information gathered, generate a helpful response to the customer.

Context: {context}
Customer Message: "{message}"
Available Information: {information}

Generate a professional, helpful response that:
1. Acknowledges the customer's request
2. Provides relevant information or next steps
3. Asks clarifying questions if needed
4. Maintains a supportive tone

Response:"""
    }


class LLMSkillMixin:
    """Mixin class to add LLM capabilities to agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_client = OpenRouterClient()
    
    async def llm_chat(
        self,
        messages: List[Union[Dict[str, str], LLMMessage]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Simple chat completion wrapper"""
        
        if system_prompt:
            full_messages = [{"role": "system", "content": system_prompt}] + list(messages)
        else:
            full_messages = list(messages)
        
        response = await self.llm_client.chat_completion(
            full_messages,
            temperature=temperature,
            **kwargs
        )
        
        return response.content
    
    async def extract_intent(self, user_message: str) -> Dict[str, Any]:
        """Extract user intent from message"""
        try:
            prompt = LLMTemplates.TASK_TEMPLATES["extract_customer_intent"].format(
                message=user_message
            )
            
            response = await self.llm_chat([
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            # Parse the response to extract intent
            lines = response.strip().split('\n')
            intent_line = lines[0].lower()
            
            intent_mapping = {
                "policy_inquiry": "policy_inquiry",
                "claim_filing": "claim_filing", 
                "claim_status": "claim_status",
                "billing_inquiry": "billing_inquiry",
                "general_support": "general_support",
                "complaint": "complaint"
            }
            
            detected_intent = "general_support"  # default
            for key in intent_mapping:
                if key in intent_line:
                    detected_intent = intent_mapping[key]
                    break
            
            return {
                "intent": detected_intent,
                "confidence": 0.8,  # Simple confidence score
                "explanation": response
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting intent: {str(e)}")
            return {
                "intent": "general_support",
                "confidence": 0.1,
                "explanation": "Error in intent extraction"
            }
    
    async def extract_claim_details(self, user_message: str) -> Dict[str, Any]:
        """Extract claim details from user message"""
        try:
            prompt = LLMTemplates.TASK_TEMPLATES["extract_claim_details"].format(
                message=user_message
            )
            
            response = await self.llm_chat([
                {"role": "user", "content": prompt}
            ], temperature=0.2)
            
            # Try to parse as JSON, fallback to empty dict
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                self.logger.warning(f"Could not parse claim details as JSON: {response}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error extracting claim details: {str(e)}")
            return {}
    
    async def generate_response(
        self,
        user_message: str,
        context: str = "",
        information: Dict[str, Any] = None
    ) -> str:
        """Generate a contextual response to user"""
        try:
            prompt = LLMTemplates.TASK_TEMPLATES["generate_response"].format(
                context=context,
                message=user_message,
                information=json.dumps(information or {}, indent=2)
            )
            
            return await self.llm_chat([
                {"role": "user", "content": prompt}
            ], temperature=0.7)
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again or contact customer service for assistance."
    
    async def close_llm_client(self):
        """Close LLM client connection"""
        if hasattr(self, 'llm_client'):
            await self.llm_client.close()