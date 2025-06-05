"""
Pure ADK Domain Agent Implementation using Official Google ADK
Migrated from existing FastAPI domain agent
"""
import json
import logging
import os
from typing import Dict, Any, Optional

# Official Google ADK imports
from adk import Agent
from adk.tools import FunctionTool

# Our ADK integration classes
from agents.base_adk import InsuranceADKAgent, ADKModelConfig, create_function_tool
from tools.agent_definitions import PureDomainAgentDefinition
from tools.session_tools import SessionManager, AuthenticationManager


class InsuranceDomainAgent(InsuranceADKAgent):
    """Pure ADK domain agent using official Google ADK v1.0.0"""
    
    def __init__(self):
        # Load configuration
        self.definition = PureDomainAgentDefinition()
        agent_config = self.definition.get_agent_config()
        prompts = self.definition.get_prompts()
        
        # Create model configuration
        model_config_data = agent_config['model_config']
        model_config = ADKModelConfig(
            primary_model=model_config_data['primary'],
            fallback_model=model_config_data.get('fallback'),
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url="https://openrouter.ai/api/v1",
            max_tokens=model_config_data.get('max_tokens', 4096),
            temperature=model_config_data.get('temperature', 0.3)
        )
        
        # Create ADK function tools
        tools = [
            create_function_tool(
                name="session_manager",
                description="Manage customer sessions",
                func=self._session_tool_handler
            ),
            create_function_tool(
                name="auth_manager", 
                description="Handle customer authentication",
                func=self._auth_tool_handler
            ),
            create_function_tool(
                name="intent_analyzer",
                description="Analyze customer intent from messages", 
                func=self._intent_analyzer_handler
            ),
            create_function_tool(
                name="response_formatter",
                description="Format responses for customers",
                func=self._response_formatter_handler
            )
        ]
        
        # Initialize with Google ADK
        super().__init__(
            name=agent_config['name'],
            description=agent_config['description'],
            model_config=model_config,
            tools=tools,
            instruction=agent_config.get('instruction', '')
        )
        
        # Store components
        self.prompts = prompts
        self.session_manager = SessionManager()
        self.auth_manager = AuthenticationManager()
        
        self.logger = logging.getLogger(__name__)
    
    async def handle_customer_inquiry(self, message: str, session_id: str, 
                                    customer_id: str = None) -> Dict[str, Any]:
        """Handle customer inquiry using ADK workflow"""
        try:
            # Prepare input for ADK agent
            agent_input = {
                "message": message,
                "session_id": session_id,
                "customer_id": customer_id,
                "task": "customer_inquiry"
            }
            
            # Use ADK's run_async method
            result = await self.run_async(
                input_data=agent_input,
                context={"session_data": self.session_manager.get_session_data(session_id)},
                tools=["intent_analyzer", "session_manager", "response_formatter"]
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Customer inquiry handling error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again."
            }
    
    async def analyze_intent(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze customer intent using Google ADK"""
        try:
            # Use ADK's built-in instruction processing
            prompt = self.prompts['intent_analysis'].format(message=message)
            
            # Use ADK agent processing
            result = await self.run_async(
                input_data={"prompt": prompt, "message": message},
                context=context or {},
                tools=["intent_analyzer"]
            )
            
            # Extract and format result
            if result.get("success", True):
                response_text = result.get("response", "{}")
                try:
                    intent_result = json.loads(response_text)
                    return {
                        "success": True,
                        "intent": intent_result.get("primary_intents", ["general_inquiry"])[0],
                        "intents": intent_result.get("primary_intents", []),
                        "confidence": intent_result.get("confidence", 0.0),
                        "requires_auth": intent_result.get("requires_auth", False),
                        "requires_technical": intent_result.get("requires_technical", False)
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "intent": "general_inquiry",
                        "intents": ["general_inquiry"],
                        "confidence": 0.5,
                        "requires_auth": True,
                        "requires_technical": False
                    }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Intent analysis failed"),
                    "intent": "general_inquiry",
                    "confidence": 0.0
                }
                
        except Exception as e:
            self.logger.error(f"Intent analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "intent": "general_inquiry",
                "confidence": 0.0
            }
    
    async def format_response(self, intent: str, data: Dict[str, Any], 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Format response using Google ADK"""
        try:
            # Prepare prompt
            customer_context = context.get("session_data", {})
            customer_id = customer_context.get("customer_id", "")
            
            prompt = self.prompts['response_formatting'].format(
                customer_message=context.get("customer_message", ""),
                customer_id=customer_id,
                intent=intent,
                technical_data=json.dumps(data),
                customer_context=json.dumps(customer_context)
            )
            
            # Use ADK for response generation
            result = await self.run_async(
                input_data={"prompt": prompt, "intent": intent, "data": data},
                context=context,
                tools=["response_formatter"]
            )
            
            if result.get("success", True):
                return {
                    "success": True,
                    "formatted_response": result.get("response", ""),
                    "intent": intent,
                    "customer_id": customer_id
                }
            else:
                return {
                    "success": False,
                    "formatted_response": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                    "error": result.get("error", "Response formatting failed")
                }
                
        except Exception as e:
            self.logger.error(f"Response formatting error: {str(e)}")
            return {
                "success": False,
                "formatted_response": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                "error": str(e)
            }
    
    # ADK Function Tool Handlers
    async def _session_tool_handler(self, operation: str = "get_session", 
                                  session_id: str = None, **kwargs) -> Dict[str, Any]:
        """Handle session management operations"""
        try:
            if operation == "get_session":
                return self.session_manager.get_session_data(session_id)
            elif operation == "update_session":
                updates = kwargs.get("updates", {})
                success = self.session_manager.update_session(session_id, updates)
                return {"success": success}
            elif operation == "create_session":
                customer_id = kwargs.get("customer_id")
                session_id = self.session_manager.create_session(customer_id)
                return {"success": True, "session_id": session_id}
            else:
                return {"error": f"Unknown session operation: {operation}"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _auth_tool_handler(self, customer_id: str = None, 
                               session_id: str = None, **kwargs) -> Dict[str, Any]:
        """Handle authentication operations"""
        try:
            # Verify customer
            auth_result = await self.auth_manager.verify_customer(customer_id)
            
            if auth_result.get("authenticated") and session_id:
                # Update session
                self.session_manager.authenticate_customer(session_id, customer_id)
            
            return auth_result
        except Exception as e:
            return {"error": str(e), "authenticated": False}
    
    async def _intent_analyzer_handler(self, message: str = "", 
                                     context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Handle intent analysis operations"""
        try:
            return await self.analyze_intent(message, context or {})
        except Exception as e:
            return {"error": str(e), "intent": "general_inquiry"}
    
    async def _response_formatter_handler(self, intent: str = "", 
                                        data: Dict[str, Any] = None,
                                        context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Handle response formatting operations"""
        try:
            return await self.format_response(intent, data or {}, context or {})
        except Exception as e:
            return {"error": str(e), "formatted_response": "Error formatting response"}


# Factory function for creating domain agent
def create_domain_agent() -> InsuranceDomainAgent:
    """Create and return domain agent instance"""
    return InsuranceDomainAgent()