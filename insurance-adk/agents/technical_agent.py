"""
Pure ADK Technical Agent Implementation using Official Google ADK
Migrated from existing Flask A2A technical agent
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional

# Official Google ADK imports
from adk import Agent
from adk.tools import FunctionTool

# Our ADK integration classes
from agents.base_adk import InsuranceADKAgent, ADKModelConfig, create_function_tool
from tools.agent_definitions import PureTechnicalAgentDefinition
from tools.policy_tools import MCPToolManager


class InsuranceTechnicalAgent(InsuranceADKAgent):
    """Pure ADK technical agent using official Google ADK v1.0.0"""
    
    def __init__(self):
        # Load configuration
        self.definition = PureTechnicalAgentDefinition()
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
            temperature=model_config_data.get('temperature', 0.1)
        )
        
        # Create ADK function tools
        tools = [
            create_function_tool(
                name="mcp_policy_tool",
                description="Retrieve policy data using MCP protocol",
                func=self._mcp_tool_handler
            ),
            create_function_tool(
                name="request_parser",
                description="Parse A2A requests into structured format",
                func=self._request_parser_handler
            ),
            create_function_tool(
                name="response_formatter",
                description="Format responses for A2A protocol",
                func=self._response_formatter_handler
            ),
            create_function_tool(
                name="error_handler",
                description="Handle technical errors gracefully",
                func=self._error_handler
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
        self.mcp_manager = MCPToolManager()
        
        self.logger = logging.getLogger(__name__)
    
    async def handle_a2a_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle A2A request using ADK workflow"""
        try:
            # Extract customer ID and request details
            customer_id = request.get("customer_id", "")
            request_type = request.get("type", "get_customer_policies")
            
            # Use ADK agent processing
            result = await self.run_async(
                input_data={
                    "request": request,
                    "customer_id": customer_id,
                    "type": request_type,
                    "task": "a2a_processing"
                },
                context={"request_context": request},
                tools=["request_parser", "mcp_policy_tool", "response_formatter"]
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"A2A request handling error: {str(e)}")
            return await self._error_handler(
                error=str(e),
                context={"request": request}
            )
    
    async def parse_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Parse A2A request using Google ADK"""
        try:
            # Format request for analysis
            request_str = json.dumps(request)
            customer_id = request.get("customer_id", "")
            
            # Use prompt template
            prompt = self.prompts['request_parsing'].format(
                request=request_str,
                customer_id=customer_id
            )
            
            # Use ADK for request parsing
            result = await self.run_async(
                input_data={"prompt": prompt, "request": request},
                context={"customer_id": customer_id},
                tools=["request_parser"]
            )
            
            # Extract parsing result
            if result.get("success", True):
                response_text = result.get("response", "{}")
                try:
                    parsed_result = json.loads(response_text)
                    return {
                        "success": True,
                        "intent": parsed_result.get("intent", "general_inquiry"),
                        "confidence": parsed_result.get("confidence", 0.0),
                        "mcp_calls": parsed_result.get("mcp_calls", []),
                        "reasoning": parsed_result.get("reasoning", "")
                    }
                except json.JSONDecodeError:
                    # Fallback parsing
                    return {
                        "success": True,
                        "intent": "get_customer_policies",
                        "confidence": 0.5,
                        "mcp_calls": [{
                            "tool_name": "get_customer_policies",
                            "parameters": {"customer_id": customer_id},
                            "purpose": "retrieve policy information"
                        }],
                        "reasoning": "Fallback to default policy retrieval"
                    }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Request parsing failed"),
                    "intent": "general_inquiry"
                }
                
        except Exception as e:
            self.logger.error(f"Request parsing error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "intent": "general_inquiry"
            }
    
    async def retrieve_policy_data(self, customer_id: str, operations: List[str] = None) -> Dict[str, Any]:
        """Retrieve policy data using MCP tools"""
        try:
            if not operations:
                operations = ["get_customer_policies"]
            
            results = {}
            
            for operation in operations:
                try:
                    # Execute MCP operation
                    mcp_result = await self.mcp_manager.execute_tool_call(
                        tool_name=operation,
                        customer_id=customer_id
                    )
                    
                    results[operation] = mcp_result
                    
                except Exception as op_error:
                    self.logger.error(f"MCP operation {operation} failed: {str(op_error)}")
                    results[operation] = {
                        "success": False,
                        "error": str(op_error)
                    }
            
            # Determine overall success
            successful_ops = [op for op, result in results.items() if result.get("success", False)]
            
            return {
                "success": len(successful_ops) > 0,
                "customer_id": customer_id,
                "operations": operations,
                "results": results,
                "successful_operations": successful_ops
            }
            
        except Exception as e:
            self.logger.error(f"Policy data retrieval error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id,
                "operations": operations or []
            }
    
    async def format_a2a_response(self, data: Dict[str, Any], 
                                context: Dict[str, Any]) -> Dict[str, Any]:
        """Format response for A2A protocol using Google ADK"""
        try:
            # Prepare formatting prompt
            request = context.get("request", {})
            customer_id = request.get("customer_id", "")
            
            prompt = self.prompts['response_formatting'].format(
                request=json.dumps(request),
                customer_id=customer_id,
                mcp_data=json.dumps(data)
            )
            
            # Use ADK for response formatting
            result = await self.run_async(
                input_data={"prompt": prompt, "data": data, "request": request},
                context=context,
                tools=["response_formatter"]
            )
            
            if result.get("success", True):
                return {
                    "success": True,
                    "formatted_response": result.get("response", data),
                    "customer_id": customer_id,
                    "timestamp": result.get("timestamp")
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Response formatting failed"),
                    "raw_data": data
                }
                
        except Exception as e:
            self.logger.error(f"A2A response formatting error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "raw_data": data
            }
    
    # ADK Function Tool Handlers
    async def _mcp_tool_handler(self, customer_id: str = None, operation: str = "get_customer_policies", 
                              **kwargs) -> Dict[str, Any]:
        """Handle MCP tool operations"""
        try:
            if not customer_id:
                return {"error": "Customer ID required for MCP operations"}
            
            return await self.mcp_manager.execute_tool_call(
                tool_name=operation,
                customer_id=customer_id,
                **kwargs
            )
        except Exception as e:
            return {"error": str(e), "tool": "mcp_policy_tool"}
    
    async def _request_parser_handler(self, request: Dict[str, Any] = None, 
                                    **kwargs) -> Dict[str, Any]:
        """Handle request parsing operations"""
        try:
            if not request:
                return {"error": "Request data required for parsing"}
            
            return await self.parse_request(request)
        except Exception as e:
            return {"error": str(e), "tool": "request_parser"}
    
    async def _response_formatter_handler(self, data: Dict[str, Any] = None,
                                        context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Handle response formatting operations"""
        try:
            return await self.format_a2a_response(data or {}, context or {})
        except Exception as e:
            return {"error": str(e), "tool": "response_formatter"}
    
    async def _error_handler(self, error: str = "", context: Dict[str, Any] = None, 
                           **kwargs) -> Dict[str, Any]:
        """Handle technical errors gracefully"""
        try:
            customer_id = context.get("customer_id", "") if context else ""
            
            # Use error handling prompt
            prompt = self.prompts['error_handling'].format(
                error=error,
                context=json.dumps(context or {}),
                customer_id=customer_id
            )
            
            # Generate customer-friendly error message
            result = await self.run_async(
                input_data={"prompt": prompt, "error": error},
                context=context or {},
                tools=["error_handler"]
            )
            
            if result.get("success", True):
                response_text = result.get("response", "{}")
                try:
                    error_result = json.loads(response_text)
                    return {
                        "success": False,
                        "error": error,
                        "customer_message": error_result.get("customer_message", "Technical error occurred"),
                        "suggested_action": error_result.get("suggested_action", "Please try again"),
                        "retry_possible": error_result.get("retry_possible", True),
                        "escalation_needed": error_result.get("escalation_needed", False)
                    }
                except json.JSONDecodeError:
                    pass
            
            # Fallback error response
            return {
                "success": False,
                "error": error,
                "customer_message": "We're experiencing technical difficulties. Please try again.",
                "suggested_action": "Retry your request",
                "retry_possible": True,
                "escalation_needed": False
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error handler failed: {str(e)}",
                "customer_message": "Technical error occurred",
                "retry_possible": True
            }
    
    async def close(self):
        """Clean up resources"""
        try:
            await self.mcp_manager.close()
        except Exception as e:
            self.logger.error(f"Error closing technical agent: {str(e)}")


# Factory function for creating technical agent
def create_technical_agent() -> InsuranceTechnicalAgent:
    """Create and return technical agent instance"""
    return InsuranceTechnicalAgent() 