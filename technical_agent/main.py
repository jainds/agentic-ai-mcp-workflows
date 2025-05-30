#!/usr/bin/env python3
"""
Minimal Technical Agent
A2A-enabled agent that integrates with Policy FastMCP server
"""

import asyncio
import sys
from typing import Dict, Any, List

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
    name="Technical Agent", 
    description="Technical agent that bridges Policy FastMCP server with domain agents via A2A",
    version="1.0.0"
)
class TechnicalAgent(A2AServer):
    
    def __init__(self):
        # Initialize with agent card
        super().__init__()
        
        # Policy FastMCP Server configuration
        self.policy_server_url = "http://localhost:8001/mcp"
        self.policy_client = None
        
        logger.info("Technical Agent initialized")
        logger.info(f"Will connect to Policy FastMCP Server at: {self.policy_server_url}")
    
    async def _get_policy_client(self):
        """Get or create FastMCP client connection"""
        if self.policy_client is None:
            self.policy_client = Client(self.policy_server_url)
        return self.policy_client
    
    @skill(
        name="Get Customer Policies",
        description="Get all policies for a specific customer via Policy FastMCP server",
        tags=["policy", "customer", "fastmcp"]
    )
    async def get_customer_policies_skill(self, customer_id: str) -> Dict[str, Any]:
        """Get policies for a customer using the Policy FastMCP server"""
        try:
            logger.info(f"Fetching policies for customer: {customer_id}")
            
            client = await self._get_policy_client()
            async with client:
                # Call the Policy FastMCP server tool
                result = await client.call_tool("get_customer_policies", {"customer_id": customer_id})
                
                # Extract the text content from the result
                policies_data = []
                for content in result:
                    if hasattr(content, 'text'):
                        import json
                        try:
                            policies_data = json.loads(content.text)
                            break
                        except json.JSONDecodeError:
                            policies_data.append(content.text)
                
                logger.info(f"Successfully retrieved {len(policies_data)} policies for customer {customer_id}")
                
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "policies": policies_data,
                    "count": len(policies_data) if isinstance(policies_data, list) else 1
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
            "timestamp": None
        }
        
        try:
            # Test connection to Policy FastMCP server
            client = await self._get_policy_client()
            async with client:
                # Try to ping the server
                await client.ping()
                status["policy_server"] = "healthy"
                logger.info("Policy FastMCP server is healthy")
                
        except Exception as e:
            status["policy_server"] = f"unhealthy: {str(e)}"
            logger.warning(f"Policy FastMCP server health check failed: {e}")
        
        import datetime
        status["timestamp"] = datetime.datetime.now().isoformat()
        
        return status
    
    def handle_task(self, task):
        """Handle incoming A2A tasks from domain agents"""
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
            
            # Handle different types of requests
            if "policies" in text.lower() and "customer" in text.lower():
                # Extract customer ID from the text
                # Simple parsing - in a real system you'd use more sophisticated NLP
                import re
                customer_match = re.search(r'customer[_\s]+([a-zA-Z0-9_]+)', text, re.IGNORECASE)
                
                if customer_match:
                    customer_id = customer_match.group(1)
                    
                    # Call our skill asynchronously
                    result = asyncio.run(self.get_customer_policies_skill(customer_id))
                    
                    # Format response
                    if result["success"]:
                        response_text = f"Found {result['count']} policies for customer {customer_id}"
                        if result["count"] > 0:
                            response_text += f":\n\n"
                            for i, policy in enumerate(result["policies"], 1):
                                response_text += f"{i}. Policy {policy.get('id', 'Unknown')} ({policy.get('type', 'Unknown')} policy)\n"
                                response_text += f"   Status: {policy.get('status', 'Unknown')}\n"
                                response_text += f"   Premium: ${policy.get('premium', 'Unknown')}\n\n"
                    else:
                        response_text = f"Error retrieving policies for customer {customer_id}: {result['error']}"
                    
                    task.artifacts = [{
                        "parts": [{"type": "text", "text": response_text}]
                    }]
                    task.status = TaskStatus(state=TaskState.COMPLETED)
                else:
                    task.artifacts = [{
                        "parts": [{"type": "text", "text": "Please specify a customer ID to look up policies"}]
                    }]
                    task.status = TaskStatus(state=TaskState.INPUT_REQUIRED)
            
            elif "health" in text.lower() or "status" in text.lower():
                # Health check request
                health_result = asyncio.run(self.health_check())
                
                response_text = "Technical Agent Health Status:\n"
                for service, status in health_result.items():
                    response_text += f"- {service}: {status}\n"
                
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response_text}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            
            else:
                # Unknown request
                task.artifacts = [{
                    "parts": [{"type": "text", "text": "I can help with:\n- Looking up customer policies\n- Health status checks\n\nPlease specify what you need help with."}]
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
    
    logger.info(f"Starting Technical Agent on port {port}")
    logger.info("Technical Agent provides A2A interface for Policy FastMCP server")
    
    # Create and run the agent
    agent = TechnicalAgent()
    run_server(agent, port=port) 