"""
ADK-Compatible MCP Tools for Policy Operations
Migrated from existing MCP integration
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime


class ADKMCPTool:
    """Base class for ADK-compatible MCP tools"""
    
    def __init__(self, name: str, description: str, server_url: str = "http://localhost:8001/mcp"):
        self.name = name
        self.description = description
        self.server_url = server_url
        self.logger = logging.getLogger(__name__)
        self.http_client = None
    
    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the MCP tool - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    async def close(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()


class MCPPolicyTool(ADKMCPTool):
    """Primary MCP tool for policy operations"""
    
    def __init__(self, server_url: str = "http://localhost:8001/mcp"):
        super().__init__(
            name="mcp_policy_tool",
            description="Retrieve policy information using MCP protocol - migrated from current system",
            server_url=server_url
        )
    
    async def execute(self, customer_id: str, operation: str = "get_customer_policies") -> Dict[str, Any]:
        """Execute MCP call - same logic as current system"""
        try:
            client = await self.get_http_client()
            
            # Map operations to MCP tool calls
            operation_mapping = {
                "get_customer_policies": "get_customer_policies",
                "get_policy_details": "get_policy_info", 
                "get_coverage_info": "get_policy_coverages",
                "get_payment_info": "get_payment_information",
                "get_agent_info": "get_agent",
                "get_deductibles": "get_deductibles"
            }
            
            mcp_tool_name = operation_mapping.get(operation, "get_customer_policies")
            
            response = await client.post(
                f"{self.server_url}/tools/call",
                json={
                    "name": mcp_tool_name,
                    "arguments": {"customer_id": customer_id}
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result,
                    "operation": operation,
                    "customer_id": customer_id
                }
            else:
                return {
                    "success": False,
                    "error": f"MCP call failed: {response.status_code}",
                    "operation": operation,
                    "customer_id": customer_id
                }
                
        except Exception as e:
            self.logger.error(f"MCP connection error: {str(e)}")
            return {
                "success": False,
                "error": f"MCP connection error: {str(e)}",
                "operation": operation,
                "customer_id": customer_id
            }
    
    async def get_customer_policies(self, customer_id: str) -> Dict[str, Any]:
        """Get customer policies - current system method"""
        return await self.execute(customer_id, "get_customer_policies")
    
    async def get_policy_details(self, policy_id: str) -> Dict[str, Any]:
        """Get policy details - current system method"""
        return await self.execute(policy_id, "get_policy_details")
    
    async def get_coverage_information(self, customer_id: str) -> Dict[str, Any]:
        """Get coverage information"""
        return await self.execute(customer_id, "get_coverage_info")
    
    async def get_payment_information(self, customer_id: str) -> Dict[str, Any]:
        """Get payment information"""
        return await self.execute(customer_id, "get_payment_info")
    
    async def get_agent_information(self, customer_id: str) -> Dict[str, Any]:
        """Get agent contact information"""
        return await self.execute(customer_id, "get_agent_info")
    
    async def get_deductibles(self, customer_id: str) -> Dict[str, Any]:
        """Get deductible information"""
        return await self.execute(customer_id, "get_deductibles")


class MCPHealthTool(ADKMCPTool):
    """Health check tool for MCP server"""
    
    def __init__(self, server_url: str = "http://localhost:8001"):
        super().__init__(
            name="mcp_health_tool",
            description="Check MCP server health status",
            server_url=server_url
        )
    
    async def execute(self) -> Dict[str, Any]:
        """Check MCP server health"""
        try:
            client = await self.get_http_client()
            response = await client.get(f"{self.server_url}/health", timeout=10.0)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": "healthy",
                    "server_url": self.server_url,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": f"Health check failed: {response.status_code}",
                    "server_url": self.server_url
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "unreachable",
                "error": f"Connection error: {str(e)}",
                "server_url": self.server_url
            }


class MCPToolManager:
    """Manager for all MCP tools in ADK system"""
    
    def __init__(self, server_url: str = "http://localhost:8001/mcp"):
        self.server_url = server_url
        self.policy_tool = MCPPolicyTool(server_url)
        self.health_tool = MCPHealthTool(server_url.replace('/mcp', ''))
        self.logger = logging.getLogger(__name__)
    
    async def execute_tool_call(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool call by name"""
        
        tool_mapping = {
            "get_customer_policies": self.policy_tool.get_customer_policies,
            "get_policy_details": self.policy_tool.get_policy_details,
            "get_coverage_information": self.policy_tool.get_coverage_information,
            "get_payment_information": self.policy_tool.get_payment_information,
            "get_agent_information": self.policy_tool.get_agent_information,
            "get_deductibles": self.policy_tool.get_deductibles,
            "health_check": self.health_tool.execute
        }
        
        if tool_name not in tool_mapping:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(tool_mapping.keys())
            }
        
        try:
            tool_func = tool_mapping[tool_name]
            
            # Handle health check differently (no parameters)
            if tool_name == "health_check":
                result = await tool_func()
            else:
                result = await tool_func(**kwargs)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}",
                "tool_name": tool_name
            }
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools"""
        return [
            {
                "name": "get_customer_policies",
                "description": "Retrieve comprehensive customer policy information",
                "parameters": ["customer_id"]
            },
            {
                "name": "get_policy_details",
                "description": "Get detailed information for a specific policy",
                "parameters": ["policy_id"]
            },
            {
                "name": "get_coverage_information",
                "description": "Get coverage amounts and limits",
                "parameters": ["customer_id"]
            },
            {
                "name": "get_payment_information",
                "description": "Get payment schedules and billing information",
                "parameters": ["customer_id"]
            },
            {
                "name": "get_agent_information",
                "description": "Get agent contact information",
                "parameters": ["customer_id"]
            },
            {
                "name": "get_deductibles",
                "description": "Get deductible information",
                "parameters": ["customer_id"]
            },
            {
                "name": "health_check",
                "description": "Check MCP server health status",
                "parameters": []
            }
        ]
    
    async def close(self):
        """Close all tool connections"""
        await self.policy_tool.close()
        await self.health_tool.close()


# Factory function for creating MCP tool manager
def create_mcp_tool_manager(server_url: str = "http://localhost:8001/mcp") -> MCPToolManager:
    """Create and return MCP tool manager instance"""
    return MCPToolManager(server_url) 