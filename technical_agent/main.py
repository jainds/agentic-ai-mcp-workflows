#!/usr/bin/env python3
"""
Enhanced Technical Agent
A2A-enabled agent with LLM intelligence that integrates with Policy FastMCP server
"""

import asyncio
import json
import os
import re
import sys
from typing import Dict, Any, List, Optional

import structlog
from python_a2a import A2AServer, AgentCard, skill, agent, run_server, TaskStatus, TaskState
from fastmcp import Client

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
        
        # Policy FastMCP Server configuration
        self.policy_server_url = "http://insurance-ai-poc-policy-server:8001/mcp"
        self.policy_client = None
        
        # Initialize OpenAI client if API key is available
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                logger.info("OpenAI client initialized for LLM intelligence")
            except ImportError:
                logger.warning("OpenAI library not available - using rule-based parsing")
        else:
            logger.warning("No OpenAI API key found - using rule-based parsing")
        
        logger.info("Enhanced Technical Agent initialized")
        logger.info(f"Will connect to Policy FastMCP Server at: {self.policy_server_url}")
    
    async def _get_policy_client(self):
        """Get or create FastMCP client connection with proper configuration"""
        try:
            # Always create a fresh client to avoid session issues
            client = Client(self.policy_server_url)
            logger.info("FastMCP client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create FastMCP client: {e}")
            raise
    
    async def _call_mcp_tool_with_retry(self, tool_name: str, params: Dict[str, Any], max_retries: int = 3) -> Any:
        """Call MCP tool with retry logic and better error handling"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"MCP call attempt {attempt + 1}/{max_retries}: {tool_name} with {params}")
                
                client = await self._get_policy_client()
                async with client:
                    # Try to list tools first to verify connection
                    try:
                        tools = await client.list_tools()
                        logger.info(f"Available MCP tools: {[tool.name for tool in tools]}")
                    except Exception as e:
                        logger.warning(f"Could not list tools: {e}")
                    
                    # Call the actual tool
                    result = await client.call_tool(tool_name, params)
                    logger.info(f"MCP tool call successful on attempt {attempt + 1}")
                    return result
                    
            except Exception as e:
                last_error = e
                logger.warning(f"MCP call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
                    
        logger.error(f"All MCP call attempts failed. Last error: {last_error}")
        raise last_error
    
    def _parse_request_with_llm(self, text: str) -> Dict[str, Any]:
        """Use LLM to intelligently parse the request and extract customer IDs"""
        if not self.openai_client:
            return self._parse_request_with_rules(text)
        
        try:
            prompt = f"""
            You are an intelligent insurance technical agent parser. Analyze this request and extract the intent and customer information.
            
            IMPORTANT: Customer IDs can appear in many formats:
            - Standard formats: user_003, CUST-001, customer-123, cust001, USER001
            - Casual mentions: "customer john", "user named Sarah", "client ID ABC123"
            - Mixed case: User_003, CUSTOMER_001, Cust-ABC
            - With prefixes: "for customer user_003", "check user CUST-001"
            - Natural language: "policies for user 003", "customer with ID 001"
            
            Possible intents:
            - get_customer_policies: User wants to retrieve/view/check policies for a customer
            - health_check: User wants to check system/service health status
            - general_inquiry: General questions or unclear intent
            
            Request: "{text}"
            
            Instructions:
            1. Extract any customer identifier mentioned in ANY format (be very flexible)
            2. Normalize customer IDs to a consistent format when possible
            3. Determine the most likely intent based on context
            4. Provide high confidence only when very certain
            
            Respond ONLY with valid JSON:
            {{
                "intent": "get_customer_policies|health_check|general_inquiry",
                "customer_id": "normalized_customer_id_or_null", 
                "original_customer_mention": "exact_text_where_customer_was_mentioned_or_null",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation of your analysis"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Lower temperature for more consistent parsing
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
                        # Apply same validation as above
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
    
    @skill(
        name="Get Customer Policies",
        description="Get all policies for a specific customer via Policy FastMCP server",
        tags=["policy", "customer", "fastmcp"]
    )
    async def get_customer_policies_skill(self, customer_id: str) -> Dict[str, Any]:
        """Get policies for a customer using the Policy FastMCP server"""
        try:
            logger.info(f"Fetching policies for customer: {customer_id}")
            
            # Use the retry mechanism for MCP calls
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
                parsed_request = self._parse_request_with_llm(text)
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
                
                # Format response with enhanced context
                if result["success"]:
                    customer_name = customer_data.get('name', customer_id) if customer_data else customer_id
                    response_text = f"Found {result['count']} policies for customer {customer_id}"
                    
                    # Add personalized greeting if we have customer name from session
                    if authenticated and customer_name != customer_id:
                        response_text = f"Hello {customer_name}! " + response_text
                    
                    if original_mention and original_mention != customer_id and not original_mention.startswith("session:"):
                        response_text += f" (identified from: '{original_mention}')"
                    
                    if result["count"] > 0:
                        response_text += f":\n\n"
                        for i, policy in enumerate(result["policies"], 1):
                            response_text += f"{i}. Policy {policy.get('id', 'Unknown')} ({policy.get('type', 'Unknown')} policy)\n"
                            response_text += f"   Status: {policy.get('status', 'Unknown')}\n"
                            response_text += f"   Premium: ${policy.get('premium', 'Unknown')}\n\n"
                    
                    # Add session/parsing info if not from authenticated session
                    if method == "session":
                        response_text += f"\n(Information retrieved for authenticated customer)"
                    elif method == "llm" and confidence < 0.8:
                        response_text += f"\n(Note: Parsed with {confidence:.1%} confidence using {method} method)"
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