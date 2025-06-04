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
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

import structlog
from python_a2a import A2AServer, AgentCard, skill, agent, run_server, TaskStatus, TaskState
from fastmcp import Client
from openai import OpenAI

from request_parser import RequestParser
from prompt_loader import PromptLoader
from service_discovery import ServiceDiscovery

# Import monitoring
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from monitoring.setup.monitoring_setup import get_monitoring_manager
    monitoring = get_monitoring_manager()
    MONITORING_ENABLED = monitoring.is_monitoring_enabled()
    if MONITORING_ENABLED:
        print("✅ Technical Agent: Monitoring enabled")
    else:
        print("⚠️  Technical Agent: Monitoring disabled (providers not available)")
except Exception as e:
    print(f"⚠️  Technical Agent: Monitoring not available: {e}")
    monitoring = None
    MONITORING_ENABLED = False

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
        
        # Load prompts using existing PromptLoader
        self.prompts = PromptLoader()
        
        # Environment and constants
        self.policy_server_url = os.getenv("POLICY_SERVICE_URL", "http://localhost:8001/mcp/")
        self.policy_client = None
        
        # Initialize Service Discovery with correct k8s service URL
        from technical_agent.service_discovery import ServiceEndpoint
        services_config = [
            ServiceEndpoint(
                name="policy_service",
                url=self.policy_server_url,  # Use k8s service URL instead of localhost
                description="Insurance policy management service",
                enabled=True
            )
        ]
        self.service_discovery = ServiceDiscovery(services_config)
        self.services_initialized = False
        
        # Initialize OpenAI client - required for LLM-only mode
        self.openai_client = None
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if api_key:
                self.openai_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key
                )
                logger.info("OpenAI client initialized for LLM-based parsing")
            else:
                raise ValueError("OPENROUTER_API_KEY environment variable is required for LLM-based operation")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise RuntimeError(f"Technical Agent requires OpenAI client for LLM-based operation: {e}")
        
        # Initialize request parser with OpenAI client
        try:
            self.request_parser = RequestParser(self.openai_client)
        except Exception as e:
            logger.error(f"Failed to initialize request parser: {e}")
            raise RuntimeError(f"Failed to initialize LLM-based request parser: {e}")
        
        logger.info("Enhanced Technical Agent initialized")
        logger.info(f"Will connect to Policy FastMCP Server at: {self.policy_server_url}")
        logger.info(f"Prompts loaded: {list(self.prompts.prompts.keys()) if self.prompts.prompts else 'No prompts loaded'}")
    
    async def _initialize_services(self):
        """Initialize service discovery and discover all available services"""
        if self.services_initialized:
            return
        
        try:
            logger.info("Initializing service discovery...")
            discovered_services = await self.service_discovery.discover_all_services()
            
            # Log discovery results
            summary = self.service_discovery.get_service_summary()
            logger.info(f"Service discovery complete: {summary['total_services']} services, {summary['total_tools']} tools")
            
            for service_name, service_info in summary['services'].items():
                logger.info(f"  - {service_name}: {service_info['tools']} tools, {service_info['resources']} resources")
            
            self.services_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            # Continue with limited functionality
            self.services_initialized = False
    
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
            
            # Get tool information from service discovery if available
            if self.services_initialized:
                discovered_tool = self.service_discovery.get_tool_by_name(tool_name)
                if discovered_tool:
                    # Validate against discovered tool parameters
                    if discovered_tool.parameters and 'required' in discovered_tool.parameters:
                        required_params = discovered_tool.parameters['required']
                        for required_param in required_params:
                            if required_param not in params or not params[required_param]:
                                logger.error(f"Missing required parameter {required_param} for tool {tool_name}")
                                return False
                else:
                    logger.warning(f"Tool {tool_name} not found in service discovery")
            
            # Legacy validation for known tools
            if tool_name in ["get_customer_policies", "get_policies", "get_agent", "get_policy_types", 
                           "get_policy_list", "get_payment_information", "get_coverage_information", 
                           "get_deductibles", "get_recommendations"]:
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
        start_time = time.time()
        last_error = None
        total_retries = 0
        
        for attempt in range(max_retries):
            try:
                # Validate request before sending
                if not self._validate_mcp_request(tool_name, params):
                    raise ValueError(f"Invalid MCP request: {tool_name} with params {params}")
                
                # Get service information for better routing
                service_name = "policy_service"  # Default service
                if self.services_initialized:
                    discovered_tool = self.service_discovery.get_tool_by_name(tool_name)
                    if discovered_tool:
                        service_name = discovered_tool.service
                        logger.info(f"Routing {tool_name} to service: {service_name}")
                
                # Get fresh client connection
                client = await self._get_policy_client()
                if not client:
                    raise ConnectionError("Unable to establish MCP connection")
                
                # Make the MCP call with proper context manager
                logger.info(f"Attempt {attempt + 1}: Calling MCP tool {tool_name} with params {params}")
                
                async with client:
                    result = await client.call_tool(tool_name, params)
                
                duration = time.time() - start_time
                
                # Record successful MCP call
                if MONITORING_ENABLED and monitoring:
                    monitoring.record_mcp_call(
                        tool_name=tool_name,
                        success=True,
                        duration_seconds=duration,
                        retry_count=total_retries
                    )
                
                logger.info(f"MCP call successful on attempt {attempt + 1}")
                return result
                
            except Exception as e:
                last_error = e
                total_retries += 1
                logger.warning(f"MCP call attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    
        duration = time.time() - start_time
        
        # Record failed MCP call
        if MONITORING_ENABLED and monitoring:
            monitoring.record_mcp_call(
                tool_name=tool_name,
                success=False,
                duration_seconds=duration,
                retry_count=total_retries,
                error=str(last_error)
            )
                    
        logger.error(f"All MCP call attempts failed. Last error: {last_error}")
        raise last_error
    
    @skill(
        name="Health Check",
        description="Check if the Technical Agent and connected services are healthy",
        tags=["health", "status"]
    )
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the technical agent and connected services"""
        # Ensure services are initialized
        await self._initialize_services()
        
        status = {
            "technical_agent": "healthy",
            "policy_server": "unknown",
            "llm_enabled": bool(self.openai_client),
            "service_discovery": "unknown",
            "discovered_services": {},
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
        
        # Service discovery status
        if self.services_initialized:
            status["service_discovery"] = "healthy"
            summary = self.service_discovery.get_service_summary()
            status["discovered_services"] = summary
        else:
            status["service_discovery"] = "not_initialized"
        
        import datetime
        status["timestamp"] = datetime.datetime.now().isoformat()
        
        return status
    
    @skill(
        name="Refresh Services",
        description="Refresh service discovery and update available tools",
        tags=["admin", "discovery", "refresh"]
    )
    async def refresh_services(self) -> Dict[str, Any]:
        """Manually refresh service discovery"""
        try:
            logger.info("Manual service refresh requested")
            self.services_initialized = False
            await self._initialize_services()
            
            summary = self.service_discovery.get_service_summary()
            
            return {
                "success": True,
                "message": "Service discovery refreshed successfully",
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh services: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Service refresh failed"
            }
    
    def handle_task(self, task):
        """Handle incoming A2A tasks with session-based customer identification"""
        logger.info(f"Received A2A task: {task}")
        
        # Enhanced session data extraction from A2A task
        session_data = self._extract_session_data_from_task(task)
        
        # Run the async handler
        return asyncio.run(self._handle_task_async(task, session_data))
    
    def _extract_session_data_from_task(self, task) -> dict:
        """Extract session data from A2A task using multiple approaches"""
        session_data = {}
        
        try:
            # Approach 1: Direct task session attribute
            if hasattr(task, 'session') and task.session:
                session_data = task.session
                logger.info(f"Found session data in task.session: {session_data}")
                return session_data
            
            # Approach 2: Session in task metadata
            if hasattr(task, 'metadata') and task.metadata and 'session' in task.metadata:
                session_data = task.metadata['session']
                logger.info(f"Found session data in task.metadata.session: {session_data}")
                return session_data
            
            # Approach 3: Check the raw task data (for debugging)
            task_dict = {}
            if hasattr(task, 'to_dict'):
                task_dict = task.to_dict()
            elif hasattr(task, '__dict__'):
                task_dict = task.__dict__
            
            logger.info(f"Task dict contents: {list(task_dict.keys()) if task_dict else 'No dict available'}")
            
            # Look for session data in task dict
            if task_dict and 'session' in task_dict:
                session_data = task_dict['session']
                logger.info(f"Found session data in task dict: {session_data}")
                return session_data
            
            # Approach 4: Check if session data is stored differently
            for attr_name in dir(task):
                if not attr_name.startswith('_'):
                    attr_value = getattr(task, attr_name, None)
                    if isinstance(attr_value, dict) and 'customer_id' in attr_value:
                        logger.info(f"Found potential session data in task.{attr_name}: {attr_value}")
                        session_data = attr_value
                        return session_data
                        
        except Exception as e:
            logger.warning(f"Error extracting session data: {e}")
        
        logger.warning("No session data found in task")
        return {}
    
    async def _handle_task_async(self, task, session_data=None):
        """Async task handler implementation"""
        try:
            # Ensure services are initialized
            await self._initialize_services()
            
            # Extract message content
            message_data = task.message or {}
            content = message_data.get("content", {})
            
            if isinstance(content, dict):
                text = content.get("text", "")
            else:
                text = str(content)
            
            logger.info(f"Processing task with text: {text}")
            
            # Use session data passed from handle_task, fallback to task attributes
            if not session_data:
                session_data = getattr(task, 'session', {}) or {}
            
            # Extract customer ID from session data (new structured approach)
            session_customer_id = session_data.get('customer_id')
            authenticated = session_data.get('authenticated', False)
            customer_data = session_data.get('customer_data', {})
            
            # Extract metadata if available
            metadata = getattr(task, 'metadata', {}) or {}
            ui_mode = metadata.get('ui_mode', 'unknown')
            message_id = metadata.get('message_id', 'unknown')
            
            # Debug logging to understand task structure
            logger.info(f"Task attributes: {[attr for attr in dir(task) if not attr.startswith('_')]}")
            logger.info(f"Task session_id: {getattr(task, 'session_id', 'None')}")
            logger.info(f"Task session attribute: {getattr(task, 'session', 'None')}")
            logger.info(f"Task metadata: {metadata}")
            logger.info(f"Received session_data: {session_data}")
            
            # Check if session data is in metadata (sent by domain agent)
            if not session_customer_id and 'session' in metadata:
                session_data = metadata['session']
                session_customer_id = session_data.get('customer_id')
                authenticated = session_data.get('authenticated', False)
                customer_data = session_data.get('customer_data', {})
                logger.info(f"Found session data in metadata: {session_data}")
            
            logger.info(f"Session-based identification - Customer ID: {session_customer_id}, Authenticated: {authenticated}, UI Mode: {ui_mode}")
            
            if session_customer_id:
                # Use session-based customer identification with LLM intent analysis
                logger.info(f"Using LLM for intent identification with session customer ID: {session_customer_id}")
                
                # Get available tools from service discovery for LLM context
                available_tools = {}
                if self.services_initialized:
                    available_tools = self.service_discovery.get_available_tools()
                    logger.info(f"Available MCP tools for LLM context: {list(available_tools.keys())}")
                
                # Use LLM to determine intent and tool mapping
                try:
                    parsed_request = await self._parse_request_with_llm_and_tools(text, session_customer_id, available_tools)
                    parsed_request["method"] = "session_llm"
                    parsed_request["reasoning"] = f"Customer ID from session, intent from LLM: {parsed_request.get('reasoning', '')}"
                    
                except Exception as e:
                    logger.error(f"LLM parsing failed for session request: {e}")
                    logger.error(f"Exception type: {type(e).__name__}")
                    logger.error(f"Exception args: {e.args}")
                    # # Fallback to basic classification
                    # parsed_request = {
                    #     "intent": "get_customer_policies",  # Default for authenticated users
                    #     "customer_id": session_customer_id,
                    #     "original_customer_mention": f"session:{session_customer_id}",
                    #     "confidence": 0.8,
                    #     "reasoning": "Session-based customer ID, fallback intent classification",
                    #     "method": "session_fallback"
                    # }
                    # Force failure to surface LLM issues
                    raise e
                
                logger.info(f"Session-based parsing: {parsed_request}")
                
            else:
                # Check if customer ID is embedded in the text from domain agent A2A call
                import re
                session_customer_match = re.search(r'\(session_customer_id:\s*([^)]+)\)', text)
                if session_customer_match:
                    embedded_customer_id = session_customer_match.group(1).strip()
                    logger.info(f"🔥 TECHNICAL AGENT: Found embedded customer ID from domain agent: {embedded_customer_id}")
                    
                    # Get available tools from service discovery for LLM context
                    available_tools = {}
                    if self.services_initialized:
                        available_tools = self.service_discovery.get_available_tools()
                        logger.info(f"Available MCP tools for LLM context: {list(available_tools.keys())}")
                    
                    # Use LLM to determine intent and tool mapping
                    try:
                        logger.info(f"Attempting LLM parsing for embedded customer ID: {embedded_customer_id}")
                        logger.info(f"Available tools for LLM context: {list(available_tools.keys())}")
                        
                        parsed_request = await self._parse_request_with_llm_and_tools(text, embedded_customer_id, available_tools)
                        parsed_request["method"] = "embedded_llm"
                        parsed_request["reasoning"] = f"Customer ID from domain agent, intent from LLM: {parsed_request.get('reasoning', '')}"
                        
                        logger.info(f"LLM parsing successful: {parsed_request}")
                        
                    except Exception as e:
                        logger.error(f"LLM parsing failed for embedded request: {e}")
                        logger.error(f"Exception type: {type(e).__name__}")
                        logger.error(f"Exception args: {e.args}")
                        # # Fallback to basic classification
                        # parsed_request = {
                        #     "intent": "get_customer_policies",  # Default for domain agent requests
                        #     "customer_id": embedded_customer_id,
                        #     "original_customer_mention": f"embedded:{embedded_customer_id}",
                        #     "confidence": 0.8,
                        #     "reasoning": "Domain agent customer ID, fallback intent classification",
                        #     "method": "embedded_fallback"
                        # }
                        # Force failure to surface LLM issues
                        raise e
                    
                    logger.info(f"Embedded parsing: {parsed_request}")
                
                elif not session_customer_id:
                    # No customer ID in session, use LLM-based message parsing
                    logger.info(f"No customer ID in session, using LLM-based message parsing")
                    
                    try:
                        # Use the enhanced request parser with LLM
                        parsed_request = self.request_parser.parse_request(text)
                        logger.info(f"LLM parsing result: {parsed_request}")
                        
                    except Exception as e:
                        logger.error(f"LLM-based parsing failed: {e}")
                        # Return error response instead of fallback
                        error_msg = f"Failed to parse request using LLM: {str(e)}"
                        task.artifacts = [{
                            "parts": [{"type": "text", "text": error_msg}]
                        }]
                        task.status = TaskStatus(state=TaskState.FAILED)
                        return task
            
            intent = parsed_request.get("intent", "general_inquiry")
            customer_id = parsed_request.get("customer_id")
            original_mention = parsed_request.get("original_customer_mention")
            confidence = parsed_request.get("confidence", 0.5)
            method = parsed_request.get("method", "unknown")
            reasoning = parsed_request.get("reasoning", "No reasoning provided")
            recommended_tool = parsed_request.get("recommended_tool")
            
            # Log the parsing details for better transparency
            logger.info(f"Intent: {intent}, Customer ID: {customer_id}, Confidence: {confidence:.1%}, Method: {method}")
            logger.info(f"Reasoning: {reasoning}")
            if recommended_tool:
                logger.info(f"LLM recommended tool: {recommended_tool}")
            
            # Smart tool mapping based on LLM analysis and available tools
            if customer_id and intent != "health_check":
                # Determine which tool to use based on LLM recommendation
                tool_to_use = recommended_tool if recommended_tool else intent
                
                # Validate that the tool exists in our available tools
                available_tools = {}
                if self.services_initialized:
                    available_tools = self.service_discovery.get_available_tools()
                
                if tool_to_use not in available_tools and tool_to_use != "get_customer_policies":
                    logger.warning(f"Recommended tool '{tool_to_use}' not available, falling back to get_customer_policies")
                    tool_to_use = "get_customer_policies"
                
                logger.info(f"Using MCP tool: {tool_to_use} for customer {customer_id}")
                
                # Execute the appropriate MCP tool
                try:
                    result = await self._generic_mcp_skill(tool_to_use, {"customer_id": customer_id}, self._get_result_key_for_tool(tool_to_use))
                    
                    # Process result with proper customer validation
                    if result["success"]:
                        response_text = await self._format_tool_response(result, customer_id, customer_data, authenticated, method, confidence, original_mention, tool_to_use, reasoning)
                    else:
                        # If the specific tool fails, try get_customer_policies as fallback
                        if tool_to_use != "get_customer_policies":
                            logger.warning(f"Tool {tool_to_use} failed, trying get_customer_policies as fallback")
                            fallback_result = await self._generic_mcp_skill("get_customer_policies", {"customer_id": customer_id}, "policies")
                            if fallback_result["success"]:
                                response_text = await self._format_tool_response(fallback_result, customer_id, customer_data, authenticated, method, confidence, original_mention, "get_customer_policies", f"Fallback after {tool_to_use} failed: {reasoning}")
                            else:
                                response_text = f"Customer {customer_id} not found in our system. Please verify the customer ID and try again."
                        else:
                            response_text = f"Customer {customer_id} not found in our system. Please verify the customer ID and try again."
                    
                    task.artifacts = [{
                        "parts": [{"type": "text", "text": response_text}]
                    }]
                    task.status = TaskStatus(state=TaskState.COMPLETED)
                    
                except Exception as e:
                    logger.error(f"Error executing tool {tool_to_use}: {e}")
                    task.artifacts = [{
                        "parts": [{"type": "text", "text": f"Error processing request: {str(e)}"}]
                    }]
                    task.status = TaskStatus(state=TaskState.FAILED)
            
            elif intent == "health_check":
                # Health check request
                health_result = await self.health_check()
                
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
            else:
                # General inquiry or unknown request
                response_text = "I can help with:\n"
                response_text += "- Looking up customer policies (customer ID from session or provide manually)\n"
                response_text += "- Health status checks\n"
                response_text += "- General insurance inquiries\n\n"
                
                # Add discovered tools if available
                if self.services_initialized:
                    available_tools = self.service_discovery.get_available_tools()
                    response_text += f"Available tools: {', '.join(available_tools.keys())}\n\n"
                
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

    # ============================================
    # INTELLIGENT LLM-POWERED SKILL
    # ============================================

    @skill(
        name="Intelligent Policy Assistant",
        description="AI-powered assistant that creates comprehensive execution plans for complex insurance requests",
        tags=["ai", "intelligent", "policy", "assistant", "planning"]
    )
    async def intelligent_policy_assistant(self, request: str, customer_id: str = None, **context) -> Dict[str, Any]:
        """
        Intelligent skill that analyzes requests and creates comprehensive execution plans
        
        Can handle both simple single-tool requests and complex multi-tool planning
        
        Args:
            request: Natural language request (e.g., "Give me a complete overview of customer CUST-001")
            customer_id: Optional customer ID if known from context
            **context: Additional context like session data, metadata, etc.
        """
        try:
            # Ensure services are initialized
            await self._initialize_services()
            
            logger.info(f"Processing intelligent request: {request}")
            
            # Use LLM to create an execution plan
            execution_plan = await self._create_execution_plan(request, customer_id, context)
            
            if not execution_plan.get("success"):
                return {
                    "success": False,
                    "error": execution_plan.get("error", "Failed to create execution plan"),
                    "request": request
                }
            
            plan_type = execution_plan.get("plan_type", "single_tool")
            tool_calls = execution_plan.get("tool_calls", [])
            execution_order = execution_plan.get("execution_order", "parallel")
            reasoning = execution_plan.get("reasoning", "")
            
            logger.info(f"Created {plan_type} plan with {len(tool_calls)} tool calls")
            logger.info(f"Execution order: {execution_order}")
            logger.info(f"Reasoning: {reasoning}")
            
            # Execute the plan
            if plan_type == "single_tool" and len(tool_calls) == 1:
                # Single tool execution
                tool_call = tool_calls[0]
                result = await self._generic_mcp_skill(
                    tool_call["tool_name"], 
                    tool_call["parameters"], 
                    tool_call["result_key"]
                )
                
                result["execution_plan"] = execution_plan
                result["original_request"] = request
                return result
                
            elif plan_type == "multi_tool":
                # Multi-tool execution
                return await self._execute_multi_tool_plan(tool_calls, execution_order, execution_plan, request)
            
            else:
                return {
                    "success": False,
                    "error": "Invalid execution plan format",
                    "request": request,
                    "plan": execution_plan
                }
                
        except Exception as e:
            logger.error(f"Error in intelligent policy assistant: {e}")
            return {
                "success": False,
                "error": str(e),
                "request": request
            }

    async def _create_execution_plan(self, request: str, customer_id: str = None, context: Dict = None) -> Dict[str, Any]:
        """Create an intelligent execution plan using LLM"""
        
        if not self.openai_client:
            logger.warning("No LLM available for planning")
            return {
                "success": False,
                "error": "LLM not available for intelligent planning"
            }
        
        try:
            # Get available tools from service discovery
            if self.services_initialized:
                available_tools = self.service_discovery.get_available_tools()
                tools_description = self.service_discovery.build_tools_description()
            else:
                # Fallback to hardcoded tools if discovery failed
                available_tools = {
                    "get_policies": "Get basic list of customer policies (limited info - use get_policy_list for complete data)",
                    "get_policy_list": "Get detailed policy list with billing cycles, dates, and deductibles (preferred for policy inquiries)",
                    "get_customer_policies": "Get comprehensive customer policies with all details",
                    "get_agent": "Get agent contact information for customer",
                    "get_policy_types": "Get list of policy types for customer", 
                    "get_payment_information": "Get payment schedules, due dates, and billing information",
                    "get_coverage_information": "Get coverage amounts, limits, and types",
                    "get_policy_details": "Get complete details for specific policy (requires policy_id)",
                    "get_deductibles": "Get deductible amounts for customer policies",
                    "get_recommendations": "Get policy recommendations for customer"
                }
                tools_description = "\n".join([f"- {name}: {desc}" for name, desc in available_tools.items()])
            
            # Get multi-tool planning prompt
            prompt = self.prompts.get_multi_tool_planning_prompt(request, customer_id, context, tools_description)
            
            if not prompt:
                logger.warning("No multi-tool planning prompt found")
                return {
                    "success": False,
                    "error": "No planning prompt configured"
                }

            response = self.openai_client.chat.completions.create(
                model="anthropic/claude-3-haiku",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse LLM response
            llm_content = response.choices[0].message.content.strip()
            logger.info(f"LLM planning response: {llm_content}")
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', llm_content, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                
                # Validate the execution plan
                if self._validate_execution_plan(plan, available_tools):
                    plan["success"] = True
                    plan["method"] = "llm_planning"
                    return plan
                else:
                    logger.warning("Execution plan validation failed")
                    return {
                        "success": False,
                        "error": "Execution plan validation failed"
                    }
            else:
                logger.warning("Could not extract JSON from LLM planning response")
                return {
                    "success": False,
                    "error": "Could not parse LLM planning response"
                }
                
        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            return {
                "success": False,
                "error": f"LLM planning failed: {str(e)}"
            }

    def _validate_execution_plan(self, plan: Dict, available_tools: Dict) -> bool:
        """Validate execution plan structure and tool names"""
        try:
            plan_type = plan.get("plan_type")
            tool_calls = plan.get("tool_calls", [])
            
            if plan_type not in ["single_tool", "multi_tool"]:
                logger.error(f"Invalid plan_type: {plan_type}")
                return False
                
            if not tool_calls or not isinstance(tool_calls, list):
                logger.error("No tool_calls in plan")
                return False
            
            # Validate each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.get("tool_name")
                parameters = tool_call.get("parameters", {})
                
                if tool_name not in available_tools:
                    logger.error(f"Invalid tool name in plan: {tool_name}")
                    return False
                
                # Get parameter requirements from service discovery if available
                if self.services_initialized:
                    discovered_tool = self.service_discovery.get_tool_by_name(tool_name)
                    if discovered_tool and discovered_tool.parameters:
                        required = discovered_tool.parameters.get('required', [])
                        for required_param in required:
                            if not parameters.get(required_param):
                                logger.error(f"Missing required parameter {required_param} for {tool_name}")
                                return False
                else:
                    # Legacy parameter validation
                    if tool_name in ["get_policies", "get_agent", "get_policy_types", "get_policy_list", 
                                    "get_payment_information", "get_coverage_information", "get_deductibles", 
                                    "get_recommendations", "get_customer_policies"]:
                        if not parameters.get("customer_id"):
                            logger.error(f"Missing customer_id for {tool_name}")
                            return False
                            
                    elif tool_name == "get_policy_details":
                        if not parameters.get("policy_id"):
                            logger.error(f"Missing policy_id for {tool_name}")
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Plan validation error: {e}")
            return False

    async def _execute_multi_tool_plan(self, tool_calls: List[Dict], execution_order: str, execution_plan: Dict, original_request: str) -> Dict[str, Any]:
        """Execute multiple tool calls according to the plan"""
        try:
            results = {}
            
            if execution_order == "parallel":
                # Execute all tools in parallel
                logger.info(f"Executing {len(tool_calls)} tools in parallel")
                tasks = []
                for i, tool_call in enumerate(tool_calls):
                    task = self._generic_mcp_skill(
                        tool_call["tool_name"],
                        tool_call["parameters"],
                        tool_call["result_key"]
                    )
                    tasks.append((f"tool_{i}_{tool_call['tool_name']}", task))
                
                # Wait for all tasks to complete
                for tool_id, task in tasks:
                    result = await task
                    results[tool_id] = result
                    
            else:  # sequential
                # Execute tools one by one
                logger.info(f"Executing {len(tool_calls)} tools sequentially")
                for i, tool_call in enumerate(tool_calls):
                    tool_id = f"tool_{i}_{tool_call['tool_name']}"
                    result = await self._generic_mcp_skill(
                        tool_call["tool_name"],
                        tool_call["parameters"],
                        tool_call["result_key"]
                    )
                    results[tool_id] = result
            
            # Combine all results
            return {
                "success": True,
                "plan_type": "multi_tool",
                "execution_order": execution_order,
                "tool_results": results,
                "execution_plan": execution_plan,
                "original_request": original_request,
                "summary": {
                    "total_tools": len(tool_calls),
                    "successful_tools": sum(1 for r in results.values() if r.get("success")),
                    "failed_tools": sum(1 for r in results.values() if not r.get("success"))
                }
            }
            
        except Exception as e:
            logger.error(f"Multi-tool execution failed: {e}")
            return {
                "success": False,
                "error": f"Multi-tool execution failed: {str(e)}",
                "partial_results": results,
                "execution_plan": execution_plan,
                "original_request": original_request
            }

    # ============================================
    # GENERIC MCP TOOL INFRASTRUCTURE (unchanged)
    # ============================================

    # ============================================
    # GENERIC MCP TOOL SKILL
    # ============================================

    async def _generic_mcp_skill(self, tool_name: str, params: Dict[str, Any], result_key: str = "data") -> Dict[str, Any]:
        """Generic method to handle any MCP tool call with consistent error handling and response formatting"""
        try:
            logger.info(f"Executing MCP tool: {tool_name} with params: {params}")
            
            result = await self._call_mcp_tool_with_retry(tool_name, params)
            
            processed_data = []
            if result:
                for content in result:
                    if hasattr(content, 'text'):
                        try:
                            data = json.loads(content.text)
                            # Handle both list and single object responses
                            if isinstance(data, list):
                                processed_data = data
                            elif isinstance(data, dict):
                                processed_data = [data] if tool_name != "get_agent" else data
                            else:
                                processed_data = [{"text": content.text}]
                            break
                        except json.JSONDecodeError:
                            processed_data = [{"text": content.text}]
            
            logger.info(f"Successfully executed {tool_name}")
            return {
                "success": True,
                "tool_name": tool_name,
                "params": params,
                result_key: processed_data
            }
            
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return {
                "success": False,
                "tool_name": tool_name,
                "params": params,
                "error": str(e)
            }

    async def _validate_customer_exists(self, customer_id: str) -> bool:
        """Validate if a customer exists in our system by checking multiple sources"""
        try:
            # Method 1: Try to get any customer-related information
            # Check if customer has any agent assigned (even if no policies)
            try:
                agent_result = await self._generic_mcp_skill("get_agent", {"customer_id": customer_id}, "agent")
                if agent_result.get("success") and not agent_result.get("agent", {}).get("error"):
                    return True
            except Exception:
                pass
            
            # Method 2: Check if customer ID follows known patterns from our data
            # Based on the mock data, valid customers are: CUST-001, user_003, etc.
            known_customer_patterns = [
                "CUST-001",  # From mock data
                "user_003"   # From mock data
            ]
            
            if customer_id in known_customer_patterns:
                return True
            
            # Method 3: Check if customer ID follows valid format patterns
            import re
            valid_patterns = [
                r'^CUST-\d{3}$',      # CUST-001, CUST-002, etc.
                r'^user_\d{3}$',      # user_001, user_002, etc.
                r'^customer-\d{3}$',  # customer-001, customer-002, etc.
                r'^Customer_\d{3}$'   # Customer_001, Customer_002, etc.
            ]
            
            for pattern in valid_patterns:
                if re.match(pattern, customer_id):
                    # For now, only validate known customers from our mock data
                    # In a real system, this would check against a customer database
                    if customer_id in ["CUST-001", "user_003"]:
                        return True
                    else:
                        # Customer ID format is valid but customer doesn't exist in our data
                        return False
            
            # Method 4: If none of the above methods confirm existence, customer doesn't exist
            return False
            
        except Exception as e:
            logger.error(f"Failed to validate customer existence: {e}")
            # If validation fails, assume customer doesn't exist to be safe
            return False

    async def _parse_request_with_llm_and_tools(self, text: str, customer_id: str, available_tools: Dict) -> Dict[str, Any]:
        """Parse a request using LLM with context of available MCP tools"""
        try:
            # Create enhanced prompt with available tools context
            tools_description = ""
            if available_tools:
                tools_description = "Available MCP tools:\n"
                for tool_name, tool_desc in available_tools.items():
                    tools_description += f"- {tool_name}: {tool_desc}\n"
            
            # Get prompt that includes tools context
            enhanced_prompt = f"""
            You are analyzing an insurance customer request to determine the intent and appropriate tool mapping.
            
            Request: "{text}"
            Customer ID: {customer_id}
            
            {tools_description}
            
            Based on the request and available tools, respond with JSON:
            {{
                "intent": "specific_tool_name_from_available_tools_or_general_category",
                "confidence": 0.0-1.0,
                "reasoning": "why this intent was chosen and which tool should be used",
                "recommended_tool": "exact_tool_name_if_specific_tool_identified"
            }}
            
            Examples:
            - "What is my deductible?" -> intent: "get_deductibles"
            - "When is payment due?" -> intent: "get_payment_information" 
            - "What policies do I have?" -> intent: "get_customer_policies"
            - "Who is my agent?" -> intent: "get_agent"
            """
            
            if not self.openai_client:
                raise ValueError("OpenAI client not available for LLM parsing")
            
            response = self.openai_client.chat.completions.create(
                model="anthropic/claude-3-haiku",
                messages=[{"role": "user", "content": enhanced_prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"LLM tool-aware parsing response: {result_text}")
            
            # Parse JSON response
            import json
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                
                return {
                    "intent": parsed_data.get("intent", "get_customer_policies"),
                    "customer_id": customer_id,
                    "original_customer_mention": f"llm_analyzed:{customer_id}",
                    "confidence": parsed_data.get("confidence", 0.8),
                    "reasoning": parsed_data.get("reasoning", "LLM analysis with available tools"),
                    "recommended_tool": parsed_data.get("recommended_tool"),
                    "available_tools": list(available_tools.keys()) if available_tools else []
                }
            else:
                raise ValueError("Could not parse LLM JSON response")
                
        except Exception as e:
            logger.error(f"LLM tool-aware parsing failed: {e}")
            raise

    def _get_result_key_for_tool(self, tool_name: str) -> str:
        """Get the appropriate result key for a given MCP tool"""
        # Map tools to their expected result keys
        tool_result_mapping = {
            "get_customer_policies": "policies",
            "get_policies": "policies", 
            "get_agent": "agent",
            "get_policy_types": "policy_types",
            "get_policy_list": "policies",
            "get_payment_information": "payment_info",
            "get_coverage_information": "coverage_info",
            "get_deductibles": "deductibles",
            "get_recommendations": "recommendations",
            "get_policy_details": "policy_details"
        }
        return tool_result_mapping.get(tool_name, "data")

    async def _format_tool_response(self, result: Dict[str, Any], customer_id: str, customer_data: Dict[str, Any], authenticated: bool, method: str, confidence: float, original_mention: str, tool_name: str, reasoning: str) -> str:
        """Format a tool response based on the result and customer data"""
        try:
            # Build customer greeting prefix
            customer_name = customer_data.get('name', customer_id) if customer_data else customer_id
            
            if authenticated and customer_name != customer_id:
                response_prefix = f"Hello {customer_name}! "
            else:
                response_prefix = ""
            
            if original_mention and original_mention != customer_id and not original_mention.startswith("session:"):
                response_prefix += f"(identified from: '{original_mention}') "
            
            # Get the data from the result
            result_key = self._get_result_key_for_tool(tool_name)
            data = result.get(result_key, [])
            
            # Helper function to format premium with billing cycle
            def format_premium_with_cycle(premium, billing_cycle):
                """Format premium amount with billing cycle if available"""
                if billing_cycle:
                    return f"${premium} ({billing_cycle})"
                else:
                    return f"${premium}"
            
            # Format based on tool type
            if tool_name == "get_customer_policies":
                if len(data) == 0:
                    return f"{response_prefix}Customer {customer_id} exists but has no active policies."
                else:
                    comprehensive_data = {
                        "customer_id": customer_id,
                        "total_policies": len(data),
                        "policies": data,
                        "response_prefix": response_prefix,
                        "method": method,
                        "confidence": confidence,
                        "tool_used": tool_name,
                        "llm_reasoning": reasoning
                    }
                    return json.dumps(comprehensive_data, indent=2)
            
            elif tool_name in ["get_policies", "get_policy_list"]:
                if len(data) == 0:
                    return f"{response_prefix}Customer {customer_id} exists but has no active policies."
                else:
                    policies_text = f"{response_prefix}Your insurance policies:\n\n"
                    for policy in data:
                        if isinstance(policy, dict):
                            policy_id = policy.get('id', 'Unknown')
                            policy_type = policy.get('type', 'Unknown').title()
                            premium = policy.get('premium', 'N/A')
                            billing_cycle = policy.get('billing_cycle', '')
                            coverage = policy.get('coverage_amount', 'N/A')
                            status = policy.get('status', 'Unknown')
                            
                            # Format premium with billing cycle
                            premium_display = format_premium_with_cycle(premium, billing_cycle)
                            
                            policies_text += f"🛡️ **{policy_type} Insurance ({policy_id})**\n"
                            policies_text += f"- Coverage: ${coverage:,}\n"
                            policies_text += f"- Premium: {premium_display}\n"
                            policies_text += f"- Status: {status}\n\n"
                    
                    policies_text += "If you need more details about any specific policy, just let me know!"
                    return policies_text
            
            elif tool_name == "get_deductibles":
                if isinstance(data, list) and len(data) > 0:
                    deductible_text = f"{response_prefix}Your deductible information:\n"
                    for item in data:
                        if isinstance(item, dict):
                            policy_id = item.get('policy_id', 'Unknown')
                            deductible = item.get('deductible', 'N/A')
                            policy_type = item.get('policy_type', 'Unknown')
                            deductible_text += f"- {policy_type} ({policy_id}): ${deductible}\n"
                    return deductible_text
                else:
                    return f"{response_prefix}No deductible information found for customer {customer_id}."
            
            elif tool_name == "get_payment_information":
                if isinstance(data, list) and len(data) > 0:
                    payment_text = f"{response_prefix}Your payment information:\n"
                    for item in data:
                        if isinstance(item, dict):
                            policy_id = item.get('policy_id', 'Unknown')
                            next_due = item.get('next_payment_due', 'N/A')
                            premium = item.get('premium', 'N/A')
                            billing_cycle = item.get('billing_cycle', '')
                            
                            # Format premium with billing cycle
                            premium_display = format_premium_with_cycle(premium, billing_cycle)
                            
                            payment_text += f"- Policy {policy_id}: {premium_display} due on {next_due}\n"
                    return payment_text
                else:
                    return f"{response_prefix}No payment information found for customer {customer_id}."
            
            elif tool_name == "get_agent":
                if isinstance(data, dict) and data:
                    agent_text = f"{response_prefix}Your agent information:\n"
                    agent_text += f"Name: {data.get('name', 'N/A')}\n"
                    agent_text += f"Email: {data.get('email', 'N/A')}\n" 
                    agent_text += f"Phone: {data.get('phone', 'N/A')}\n"
                    return agent_text
                else:
                    return f"{response_prefix}No agent information found for customer {customer_id}."
            
            elif tool_name == "get_coverage_information":
                if isinstance(data, list) and len(data) > 0:
                    coverage_text = f"{response_prefix}Your coverage information:\n"
                    for item in data:
                        if isinstance(item, dict):
                            policy_id = item.get('policy_id', 'Unknown')
                            coverage = item.get('coverage_amount', 'N/A')
                            policy_type = item.get('policy_type', 'Unknown')
                            coverage_text += f"- {policy_type} ({policy_id}): ${coverage} coverage\n"
                    return coverage_text
                else:
                    return f"{response_prefix}No coverage information found for customer {customer_id}."
            
            else:
                # Generic formatting for other tools
                if isinstance(data, list) and len(data) > 0:
                    return f"{response_prefix}Found {len(data)} result(s) for {tool_name}:\n" + json.dumps(data, indent=2)
                elif isinstance(data, dict) and data:
                    return f"{response_prefix}Result from {tool_name}:\n" + json.dumps(data, indent=2)
                else:
                    return f"{response_prefix}No data found using {tool_name} for customer {customer_id}."
            
        except Exception as e:
            logger.error(f"Error formatting response for tool {tool_name}: {e}")
            return f"Successfully retrieved data using {tool_name}, but encountered formatting error: {str(e)}"

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