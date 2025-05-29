"""
Base MCP (Model Context Protocol) implementation using Anthropic's FastMCP.
Provides tools and resources that agents can use to interact with external services.
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx
import structlog
from fastmcp import FastMCP
from fastmcp.types import Tool, Resource

logger = structlog.get_logger(__name__)


@dataclass
class MCPTool:
    """MCP Tool definition"""
    name: str
    description: str
    handler: Callable
    parameters: Dict[str, Any]


@dataclass
class MCPResource:
    """MCP Resource definition"""
    uri_template: str
    description: str
    handler: Callable


class MCPServer(ABC):
    """Base MCP Server implementation"""
    
    def __init__(self, name: str, description: str, port: int = 8001):
        self.name = name
        self.description = description
        self.port = port
        self.mcp = FastMCP(name=name, description=description)
        
        # Tool and resource registries
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        
        self._setup_base_tools()
    
    def _setup_base_tools(self):
        """Setup common MCP tools"""
        
        @self.mcp.tool()
        def get_server_info() -> Dict[str, Any]:
            """Get information about this MCP server"""
            return {
                "name": self.name,
                "description": self.description,
                "tools": list(self.tools.keys()),
                "resources": list(self.resources.keys()),
                "capabilities": {
                    "resources": True,
                    "tools": True,
                    "prompts": False
                }
            }
        
        @self.mcp.tool()
        def health_check() -> Dict[str, Any]:
            """Health check for the MCP server"""
            return {
                "status": "healthy",
                "server": self.name,
                "timestamp": asyncio.get_event_loop().time()
            }
    
    def add_tool(self, tool: MCPTool):
        """Add a tool to the MCP server"""
        self.tools[tool.name] = tool
        
        # Register with FastMCP
        @self.mcp.tool(name=tool.name, description=tool.description)
        def tool_wrapper(**kwargs):
            return tool.handler(**kwargs)
    
    def add_resource(self, resource: MCPResource):
        """Add a resource to the MCP server"""
        self.resources[resource.uri_template] = resource
        
        # Register with FastMCP
        @self.mcp.resource(uri_template=resource.uri_template)
        def resource_wrapper(**kwargs):
            return resource.handler(**kwargs)
    
    @abstractmethod
    def setup_tools_and_resources(self):
        """Setup domain-specific tools and resources - must be implemented by subclasses"""
        pass
    
    def run(self):
        """Run the MCP server"""
        self.setup_tools_and_resources()
        logger.info(f"Starting MCP server {self.name} on port {self.port}")
        self.mcp.run(port=self.port)


class MCPClient:
    """Client for connecting to MCP servers"""
    
    def __init__(self, server_url: str, auth_token: Optional[str] = None):
        self.server_url = server_url
        self.auth_token = auth_token
        self.client = httpx.AsyncClient()
        
        # Headers for authentication
        self.headers = {}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the MCP server"""
        try:
            response = await self.client.post(
                f"{self.server_url}/tools/list",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json().get("tools", [])
            else:
                logger.error("Failed to list tools", status=response.status_code)
                return []
        except Exception as e:
            logger.error("Error listing tools", error=str(e))
            return []
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a tool on the MCP server"""
        try:
            payload = {
                "name": tool_name,
                "arguments": kwargs
            }
            
            response = await self.client.post(
                f"{self.server_url}/tools/call",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("content", [])
            else:
                logger.error("Tool call failed", tool=tool_name, status=response.status_code)
                return None
                
        except Exception as e:
            logger.error("Error calling tool", tool=tool_name, error=str(e))
            return None
    
    async def get_resource(self, uri: str) -> Any:
        """Get a resource from the MCP server"""
        try:
            payload = {"uri": uri}
            
            response = await self.client.post(
                f"{self.server_url}/resources/read",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("contents", [])
            else:
                logger.error("Resource read failed", uri=uri, status=response.status_code)
                return None
                
        except Exception as e:
            logger.error("Error reading resource", uri=uri, error=str(e))
            return None
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources on the MCP server"""
        try:
            response = await self.client.post(
                f"{self.server_url}/resources/list",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json().get("resources", [])
            else:
                logger.error("Failed to list resources", status=response.status_code)
                return []
        except Exception as e:
            logger.error("Error listing resources", error=str(e))
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


class EnterpriseAPIWrapper:
    """Wrapper for enterprise APIs to expose them as MCP tools"""
    
    def __init__(self, api_base_url: str, auth_token: Optional[str] = None):
        self.api_base_url = api_base_url
        self.auth_token = auth_token
        self.client = httpx.AsyncClient()
        
        self.headers = {"Content-Type": "application/json"}
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make GET request to enterprise API"""
        url = f"{self.api_base_url}{endpoint}"
        response = await self.client.get(url, params=params, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("API GET failed", url=url, status=response.status_code)
            return None
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """Make POST request to enterprise API"""
        url = f"{self.api_base_url}{endpoint}"
        response = await self.client.post(url, json=data, headers=self.headers)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            logger.error("API POST failed", url=url, status=response.status_code)
            return None
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """Make PUT request to enterprise API"""
        url = f"{self.api_base_url}{endpoint}"
        response = await self.client.put(url, json=data, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("API PUT failed", url=url, status=response.status_code)
            return None
    
    async def delete(self, endpoint: str) -> bool:
        """Make DELETE request to enterprise API"""
        url = f"{self.api_base_url}{endpoint}"
        response = await self.client.delete(url, headers=self.headers)
        
        if response.status_code in [200, 204]:
            return True
        else:
            logger.error("API DELETE failed", url=url, status=response.status_code)
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Utility functions for MCP integration
class MCPAgentMixin:
    """Mixin class to add MCP capabilities to A2A agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcp_clients: Dict[str, MCPClient] = {}
        self.api_wrappers: Dict[str, EnterpriseAPIWrapper] = {}
    
    def add_mcp_server(self, name: str, server_url: str, auth_token: Optional[str] = None):
        """Add an MCP server connection"""
        self.mcp_clients[name] = MCPClient(server_url, auth_token)
        logger.info("Added MCP server", name=name, url=server_url)
    
    def add_api_wrapper(self, name: str, api_base_url: str, auth_token: Optional[str] = None):
        """Add an enterprise API wrapper"""
        self.api_wrappers[name] = EnterpriseAPIWrapper(api_base_url, auth_token)
        logger.info("Added API wrapper", name=name, url=api_base_url)
    
    async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """Call a tool on an MCP server"""
        if server_name not in self.mcp_clients:
            raise ValueError(f"MCP server {server_name} not found")
        
        client = self.mcp_clients[server_name]
        result = await client.call_tool(tool_name, **kwargs)
        
        logger.info("Called MCP tool", server=server_name, tool=tool_name, success=result is not None)
        return result
    
    async def get_mcp_resource(self, server_name: str, uri: str) -> Any:
        """Get a resource from an MCP server"""
        if server_name not in self.mcp_clients:
            raise ValueError(f"MCP server {server_name} not found")
        
        client = self.mcp_clients[server_name]
        result = await client.get_resource(uri)
        
        logger.info("Got MCP resource", server=server_name, uri=uri, success=result is not None)
        return result
    
    async def call_enterprise_api(self, api_name: str, method: str, endpoint: str, **kwargs) -> Any:
        """Call an enterprise API through wrapper"""
        if api_name not in self.api_wrappers:
            raise ValueError(f"API wrapper {api_name} not found")
        
        wrapper = self.api_wrappers[api_name]
        
        if method.upper() == "GET":
            result = await wrapper.get(endpoint, kwargs.get("params"))
        elif method.upper() == "POST":
            result = await wrapper.post(endpoint, kwargs.get("data", {}))
        elif method.upper() == "PUT":
            result = await wrapper.put(endpoint, kwargs.get("data", {}))
        elif method.upper() == "DELETE":
            result = await wrapper.delete(endpoint)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        logger.info("Called enterprise API", api=api_name, method=method, endpoint=endpoint, success=result is not None)
        return result
    
    async def cleanup_mcp_connections(self):
        """Clean up MCP client connections"""
        for client in self.mcp_clients.values():
            await client.close()
        
        for wrapper in self.api_wrappers.values():
            await wrapper.close()
        
        logger.info("Cleaned up MCP connections") 