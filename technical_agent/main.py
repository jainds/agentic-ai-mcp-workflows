#!/usr/bin/env python3
"""
Enhanced Technical Agent
A2A-enabled agent with LLM intelligence that integrates with Policy FastMCP server
"""

import sys
import os
import json
import re
import logging
import asyncio
from typing import Dict, Any, List, Optional

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

import structlog
from python_a2a import A2AServer, AgentCard, skill, agent, run_server, TaskStatus, TaskState
from fastmcp import Client
from openai import OpenAI

from request_parser import RequestParser

# Setup logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

@agent(
    name="Enhanced Technical Agent", 
    description="LLM-powered technical agent that bridges Policy FastMCP server with domain agents via A2A",
    version="2.0.0"
)
class TechnicalAgent(A2AServer):
    
    def __init__(self):
        # Initialize with agent card
        super().__init__()
        
        # Policy FastMCP Server configuration - Use trailing slash to avoid 307 redirects
        self.policy_server_url = "http://insurance-ai-poc-policy-server:8001/mcp/"
        self.policy_client = None
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                self.openai_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key
                )
                logger.info("OpenAI client initialized for enhanced parsing")
            else:
                logger.warning("No OpenAI API key found, using rule-based parsing only")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Initialize request parser with OpenAI client
        self.request_parser = RequestParser(self.openai_client)
        
        logger.info("Enhanced Technical Agent initialized")
        logger.info(f"Will connect to Policy FastMCP Server at: {self.policy_server_url}")
    
    async def _get_policy_client(self):
        """Get or create FastMCP client connection with enhanced session management"""
        try:
            # Create client with explicit configuration
            client = Client(self.policy_server_url)
            logger.info("FastMCP client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create FastMCP client: {e}")
            raise
    
    def _validate_mcp_request(self, tool_name: str, params: Dict[str, Any]) -> bool:
        """Validate MCP request parameters to prevent 400 Bad Request errors"""
        try:
            # Validate tool name
            if not tool_name or not isinstance(tool_name, str):
                logger.error(f"Invalid tool name: {tool_name}")
                return False
            
            # Validate parameters
            if not isinstance(params, dict):
                logger.error(f"Invalid parameters type: {type(params)}")
                return False
            
            # Specific validation for get_customer_policies
            if tool_name == "get_customer_policies":
                customer_id = params.get("customer_id")
                if not customer_id or not isinstance(customer_id, str) or len(customer_id.strip()) == 0:
                    logger.error(f"Invalid customer_id: {customer_id}")
                    return False
                
                # Clean and validate customer ID format
                clean_customer_id = customer_id.strip()
                if len(clean_customer_id) < 2:
                    logger.error(f"Customer ID too short: {clean_customer_id}")
                    return False
                
                # Update params with cleaned customer ID
                params["customer_id"] = clean_customer_id
            
            logger.info(f"MCP request validation passed for {tool_name} with {params}")
            return True
            
        except Exception as e:
            logger.error(f"MCP request validation failed: {e}")
            return False
    
    async def _call_mcp_tool_with_retry(self, tool_name: str, params: Dict[str, Any], max_retries: int = 3) -> Any:
        """Call MCP tool with retry logic and better error handling"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Validate request before sending
                if not self._validate_mcp_request(tool_name, params):
                    raise ValueError(f"Invalid MCP request: {tool_name} with params {params}")
                
                # Get fresh client connection
                client = await self._get_policy_client()
                if not client:
                    raise ConnectionError("Unable to establish MCP connection")
                
                # Make the MCP call with proper context manager
                logger.info(f"Attempt {attempt + 1}: Calling MCP tool {tool_name} with params {params}")
                
                async with client:
                    if tool_name == "get_customer_policies":
                        result = await client.call_tool("get_customer_policies", params)
                    elif tool_name == "health_check":
                        result = await client.call_tool("health_check", params or {})
                    else:
                        raise ValueError(f"Unknown tool: {tool_name}")
                
                logger.info(f"MCP call successful on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"MCP call attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    
        logger.error(f"All MCP call attempts failed. Last error: {last_error}")
        raise last_error
    
    @skill(
        name="Get Customer Policies",
        description="Get all policies for a specific customer via Policy FastMCP server",
        tags=["policy", "customer", "fastmcp"]
    )
    async def get_customer_policies_skill(self, customer_id: str) -> Dict[str, Any]:
        """Get policies for a customer using the Policy FastMCP server"""
        try:
            logger.info(f"Fetching policies for customer: {customer_id}")
            
            # Use the enhanced retry mechanism for MCP calls
            result = await self._call_mcp_tool_with_retry("get_customer_policies", {"customer_id": customer_id})
                
            # Process the result properly
            policies_data = []
            if result:
                logger.info(f"Raw MCP result: {result}")
                for content in result:
                    if hasattr(content, 'text'):
                        try:
                            # Try to parse as JSON first
                            data = json.loads(content.text)
                            if isinstance(data, list):
                                policies_data = data
                            else:
                                policies_data = [data]
                            logger.info(f"Parsed JSON data: {policies_data}")
                            break
                        except json.JSONDecodeError:
                            # If not JSON, treat as text
                            logger.warning(f"Could not parse as JSON: {content.text}")
                            policies_data.append({"text": content.text})
                    elif hasattr(content, 'content'):
                        policies_data.append(content.content)
                    else:
                        logger.info(f"Unknown content type: {type(content)} - {content}")
            else:
                logger.warning("No result returned from MCP call")
                
            logger.info(f"Successfully retrieved {len(policies_data)} policies for customer {customer_id}")
            
            return {
                "success": True,
                "customer_id": customer_id,
                "policies": policies_data,
                "count": len(policies_data)
            }
                
        except Exception as e:
            logger.error(f"Error fetching policies for customer {customer_id}: {e}")
            return {
                "success": False,
                "customer_id": customer_id,
                "error": str(e),
                "policies": []
            }
    
    @skill(
        name="Health Check",
        description="Check if the Technical Agent and connected services are healthy",
        tags=["health", "status"]
    )
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the technical agent and connected services"""
        status = {
            "technical_agent": "healthy",
            "policy_server": "unknown",
            "llm_enabled": bool(self.openai_client),
            "timestamp": None
        }
        
        try:
            # Test connection to Policy FastMCP server
            client = await self._get_policy_client()
            async with client:
                # Try to list available tools
                tools = await client.list_tools()
                status["policy_server"] = "healthy"
                status["available_tools"] = [tool.name for tool in tools]
                logger.info("Policy FastMCP server is healthy")
                
        except Exception as e:
            status["policy_server"] = f"unhealthy: {str(e)}"
            logger.warning(f"Policy FastMCP server health check failed: {e}")
        
        import datetime
        status["timestamp"] = datetime.datetime.now().isoformat()
        
        return status
    
    def handle_task(self, task):
        """Handle incoming A2A tasks with session-based customer identification"""
        logger.info(f"Received A2A task: {task}")
        
        try:
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})
            
            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)
            
            logger.info(f"Processing task with text: {text}")
            
            # Extract customer ID from session data (new structured approach)
            session_data = getattr(task, 'session', {}) or {}
            session_customer_id = session_data.get('customer_id')
            authenticated = session_data.get('authenticated', False)
            customer_data = session_data.get('customer_data', {})
            
            # Extract metadata if available
            metadata = getattr(task, 'metadata', {}) or {}
            ui_mode = metadata.get('ui_mode', 'unknown')
            message_id = metadata.get('message_id', 'unknown')
            
            logger.info(f"Session-based identification - Customer ID: {session_customer_id}, Authenticated: {authenticated}, UI Mode: {ui_mode}")
            
            if session_customer_id:
                # Use session-based customer identification - no parsing needed!
                parsed_request = {
                    "intent": "get_customer_policies" if any(word in text.lower() for word in ["policy", "policies", "coverage"]) else 
                             "health_check" if any(word in text.lower() for word in ["health", "status", "check"]) else 
                             "general_inquiry",
                    "customer_id": session_customer_id,
                    "original_customer_mention": f"session:{session_customer_id}",
                    "confidence": 1.0,  # 100% confidence since it's from authenticated session
                    "reasoning": "Customer ID retrieved from authenticated session",
                    "method": "session"
                }
                
                logger.info(f"Session-based parsing: {parsed_request}")
            else:
                # Fallback to LLM/rule-based parsing if no session data (for backwards compatibility)
                logger.info("No customer ID in session, falling back to message parsing")
                parsed_request = self.request_parser.parse_request(text)
                logger.info(f"Fallback parsing result: {parsed_request}")
            
            intent = parsed_request.get("intent", "general_inquiry")
            customer_id = parsed_request.get("customer_id")
            original_mention = parsed_request.get("original_customer_mention")
            confidence = parsed_request.get("confidence", 0.5)
            method = parsed_request.get("method", "unknown")
            reasoning = parsed_request.get("reasoning", "No reasoning provided")
            
            # Log the parsing details for better transparency
            logger.info(f"Intent: {intent}, Customer ID: {customer_id}, Confidence: {confidence:.1%}, Method: {method}")
            logger.info(f"Reasoning: {reasoning}")
            
            # Handle different intents with session context
            if intent == "get_customer_policies" and customer_id:
                # Call our skill asynchronously
                result = asyncio.run(self.get_customer_policies_skill(customer_id))
                
                # Send comprehensive JSON data directly to domain agent
                if result["success"]:
                    customer_name = customer_data.get('name', customer_id) if customer_data else customer_id
                    
                    # Add personalized greeting if we have customer name from session
                    if authenticated and customer_name != customer_id:
                        response_prefix = f"Hello {customer_name}! "
                    else:
                        response_prefix = ""
                    
                    if original_mention and original_mention != customer_id and not original_mention.startswith("session:"):
                        response_prefix += f"(identified from: '{original_mention}') "
                    
                    if result["count"] > 0:
                        # Send the comprehensive JSON data directly to domain agent
                        # This preserves all payment info, agent details, vehicle info, coverage limits, etc.
                        comprehensive_data = {
                            "customer_id": customer_id,
                            "total_policies": result["count"],
                            "policies": result["policies"],
                            "response_prefix": response_prefix,
                            "method": method,
                            "confidence": confidence if method != "session" else 1.0
                        }
                        
                        # Convert to JSON string for domain agent processing
                        response_text = json.dumps(comprehensive_data, indent=2)
                    else:
                        response_text = f"{response_prefix}Found {result['count']} policies for customer {customer_id}"
                    
                    # Add session/parsing info if not from authenticated session
                    if method == "session":
                        logger.info("Information retrieved for authenticated customer")
                    elif method == "llm" and confidence < 0.8:
                        logger.info(f"Parsed with {confidence:.1%} confidence using {method} method")
                else:
                    response_text = f"Error retrieving policies for customer {customer_id}: {result['error']}"
                    if original_mention and original_mention != customer_id and not original_mention.startswith("session:"):
                        response_text += f" (identified from: '{original_mention}')"
                
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response_text}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            
            elif intent == "health_check":
                # Health check request
                health_result = asyncio.run(self.health_check())
                
                response_text = "Technical Agent Health Status:\n"
                for service, status in health_result.items():
                    response_text += f"- {service}: {status}\n"
                
                # Add session/parsing method info for transparency
                if method == "session":
                    response_text += f"\n(Request processed for authenticated session)"
                else:
                    response_text += f"\n(Request parsed using {method} method with {confidence:.1%} confidence)"
                
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response_text}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            
            elif intent == "get_customer_policies" and not customer_id:
                # Customer policies requested but no ID found
                response_text = "I understand you want to look up customer policies, but I couldn't identify a specific customer ID.\n\n"
                
                if authenticated:
                    response_text += "Please make sure your session includes your customer ID, or log in again.\n\n"
                else:
                    response_text += "Please specify a customer ID in one of these formats:\n"
                    response_text += "- user_003\n- CUST-001\n- customer ABC123\n- client 001\n\n"
                
                if original_mention and not original_mention.startswith("session:"):
                    response_text += f"(I found '{original_mention}' but couldn't parse it as a valid customer ID)"
                
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response_text}]
                }]
                task.status = TaskStatus(state=TaskState.INPUT_REQUIRED)
                
            else:
                # General inquiry or unknown request
                response_text = "I can help with:\n"
                response_text += "- Looking up customer policies (customer ID from session or provide manually)\n"
                response_text += "- Health status checks\n"
                response_text += "- General insurance inquiries\n\n"
                response_text += "What would you like assistance with?"
                
                # Include session/parsing details if confidence is low
                if method != "session" and confidence < 0.6:
                    response_text += f"\n\n(Note: I wasn't very confident about interpreting your request - {confidence:.1%} confidence)"
                
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response_text}]
                }]
                task.status = TaskStatus(state=TaskState.INPUT_REQUIRED)
        
        except Exception as e:
            logger.error(f"Error handling task: {e}")
            task.artifacts = [{
                "parts": [{"type": "text", "text": f"Error processing request: {str(e)}"}]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
        
        return task

if __name__ == "__main__":
    # Check command line arguments for port
    port = 8002
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    
    logger.info(f"Starting Enhanced Technical Agent on port {port}")
    logger.info("Technical Agent provides intelligent A2A interface for Policy FastMCP server")
    
    # Create and run the agent
    agent = TechnicalAgent()
    run_server(agent, port=port) 