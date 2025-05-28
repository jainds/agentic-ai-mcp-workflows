import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
from datetime import datetime, date


class MCPToolType(str, Enum):
    FUNCTION = "function"
    RESOURCE = "resource"


@dataclass
class MCPParameter:
    name: str
    type: str
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


@dataclass
class MCPTool:
    name: str
    description: str
    parameters: List[MCPParameter]
    tool_type: MCPToolType = MCPToolType.FUNCTION
    handler: Optional[Callable] = None


@dataclass
class MCPToolResult:
    success: bool
    content: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPToolRegistry:
    """Registry for MCP tools that can be called by LLM agents"""
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.logger = logging.getLogger(__name__)
        self.http_client = None
        
        # Service URLs
        self.service_urls = {
            "customer": "http://customer-service:8000",
            "policy": "http://policy-service:8001", 
            "claims": "http://claims-service:8002"
        }
        
        # Register all tools
        self._register_customer_tools()
        self._register_policy_tools()
        self._register_claims_tools()
    
    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client
    
    def register_tool(self, tool: MCPTool):
        """Register a new MCP tool"""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered MCP tool: {tool.name}")
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get MCP tool definitions for LLM consumption"""
        definitions = []
        
        for tool in self.tools.values():
            definition = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            for param in tool.parameters:
                prop = {
                    "type": param.type,
                    "description": param.description
                }
                
                if param.enum:
                    prop["enum"] = param.enum
                if param.default is not None:
                    prop["default"] = param.default
                
                definition["function"]["parameters"]["properties"][param.name] = prop
                
                if param.required:
                    definition["function"]["parameters"]["required"].append(param.name)
            
            definitions.append(definition)
        
        return definitions
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Call an MCP tool with given parameters"""
        if tool_name not in self.tools:
            return MCPToolResult(
                success=False,
                content=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        tool = self.tools[tool_name]
        
        try:
            if tool.handler:
                result = await tool.handler(**parameters)
                return MCPToolResult(success=True, content=result)
            else:
                return MCPToolResult(
                    success=False,
                    content=None,
                    error=f"No handler defined for tool '{tool_name}'"
                )
        except Exception as e:
            self.logger.error(f"Error calling tool {tool_name}: {str(e)}")
            return MCPToolResult(
                success=False,
                content=None,
                error=str(e)
            )
    
    def _register_customer_tools(self):
        """Register customer service tools"""
        
        # Get Customer Info
        async def get_customer_info(customer_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['customer']}/customer/{customer_id}")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_customer_info",
            description="Retrieve detailed customer information by customer ID",
            parameters=[
                MCPParameter("customer_id", "integer", "The customer ID to lookup", required=True)
            ],
            handler=get_customer_info
        ))
        
        # Get Customer Summary
        async def get_customer_summary(customer_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['customer']}/customer/{customer_id}/summary")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_customer_summary", 
            description="Get customer summary information including policy count",
            parameters=[
                MCPParameter("customer_id", "integer", "The customer ID to lookup", required=True)
            ],
            handler=get_customer_summary
        ))
        
        # Search Customers
        async def search_customers(query: str, limit: int = 10) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(
                f"{self.service_urls['customer']}/search/customers",
                params={"q": query, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="search_customers",
            description="Search customers by name or email address",
            parameters=[
                MCPParameter("query", "string", "Search query (name or email)", required=True),
                MCPParameter("limit", "integer", "Maximum number of results", required=False, default=10)
            ],
            handler=search_customers
        ))
    
    def _register_policy_tools(self):
        """Register policy service tools"""
        
        # Get Policy Info
        async def get_policy_info(policy_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['policy']}/policy/{policy_id}")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_policy_info",
            description="Retrieve detailed policy information by policy ID",
            parameters=[
                MCPParameter("policy_id", "integer", "The policy ID to lookup", required=True)
            ],
            handler=get_policy_info
        ))
        
        # Get Policy Status
        async def get_policy_status(policy_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['policy']}/policy/{policy_id}/status")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_policy_status",
            description="Get policy status including active status and expiration information",
            parameters=[
                MCPParameter("policy_id", "integer", "The policy ID to check", required=True)
            ],
            handler=get_policy_status
        ))
        
        # Get Customer Policies
        async def get_customer_policies(customer_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['policy']}/customer/{customer_id}/policies")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_customer_policies",
            description="Get all policies for a specific customer",
            parameters=[
                MCPParameter("customer_id", "integer", "The customer ID to lookup policies for", required=True)
            ],
            handler=get_customer_policies
        ))
        
        # Get Policy Coverages
        async def get_policy_coverages(policy_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['policy']}/policy/{policy_id}/coverages")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_policy_coverages",
            description="Get coverage details and limits for a policy",
            parameters=[
                MCPParameter("policy_id", "integer", "The policy ID to get coverages for", required=True)
            ],
            handler=get_policy_coverages
        ))
        
        # Search Policies
        async def search_policies(query: str, limit: int = 10) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(
                f"{self.service_urls['policy']}/search/policies",
                params={"q": query, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="search_policies",
            description="Search policies by policy number or customer ID",
            parameters=[
                MCPParameter("query", "string", "Search query (policy number or customer ID)", required=True),
                MCPParameter("limit", "integer", "Maximum number of results", required=False, default=10)
            ],
            handler=search_policies
        ))
    
    def _register_claims_tools(self):
        """Register claims service tools"""
        
        # Get Claim Info
        async def get_claim_info(claim_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['claims']}/claim/{claim_id}")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_claim_info",
            description="Retrieve detailed claim information by claim ID",
            parameters=[
                MCPParameter("claim_id", "integer", "The claim ID to lookup", required=True)
            ],
            handler=get_claim_info
        ))
        
        # Get Claim Status
        async def get_claim_status(claim_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['claims']}/claim/{claim_id}/status")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_claim_status",
            description="Get claim status and timeline information",
            parameters=[
                MCPParameter("claim_id", "integer", "The claim ID to check status for", required=True)
            ],
            handler=get_claim_status
        ))
        
        # Create Claim
        async def create_claim(customer_id: int, policy_id: int, claim_type: str, incident_date: str, 
                             location: str, description: str, claimed_amount: float = 0.0) -> Dict[str, Any]:
            client = await self.get_http_client()
            
            claim_data = {
                "customer_id": customer_id,
                "policy_id": policy_id,
                "claim_type": claim_type,
                "incident_details": {
                    "incident_date": incident_date,
                    "location": location,
                    "description": description
                },
                "claimed_amount": claimed_amount,
                "priority": "medium"
            }
            
            response = await client.post(f"{self.service_urls['claims']}/claim", json=claim_data)
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="create_claim",
            description="Create a new insurance claim",
            parameters=[
                MCPParameter("customer_id", "integer", "Customer ID filing the claim", required=True),
                MCPParameter("policy_id", "integer", "Policy ID for the claim", required=True),
                MCPParameter("claim_type", "string", "Type of claim", required=True, 
                           enum=["auto_accident", "auto_theft", "home_fire", "home_theft", "home_water_damage", "other"]),
                MCPParameter("incident_date", "string", "Date of incident (YYYY-MM-DD)", required=True),
                MCPParameter("location", "string", "Location where incident occurred", required=True),
                MCPParameter("description", "string", "Description of what happened", required=True),
                MCPParameter("claimed_amount", "number", "Estimated damage amount", required=False, default=0.0)
            ],
            handler=create_claim
        ))
        
        # Get Customer Claims
        async def get_customer_claims(customer_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['claims']}/customer/{customer_id}/claims")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_customer_claims",
            description="Get all claims for a specific customer",
            parameters=[
                MCPParameter("customer_id", "integer", "The customer ID to lookup claims for", required=True)
            ],
            handler=get_customer_claims
        ))
        
        # Get Policy Claims
        async def get_policy_claims(policy_id: int) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(f"{self.service_urls['claims']}/policy/{policy_id}/claims")
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="get_policy_claims",
            description="Get all claims for a specific policy",
            parameters=[
                MCPParameter("policy_id", "integer", "The policy ID to lookup claims for", required=True)
            ],
            handler=get_policy_claims
        ))
        
        # Add Claim Note
        async def add_claim_note(claim_id: int, content: str, author: str, is_internal: bool = False) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.post(
                f"{self.service_urls['claims']}/claim/{claim_id}/notes",
                params={"content": content, "author": author, "is_internal": is_internal}
            )
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="add_claim_note",
            description="Add a note to a claim",
            parameters=[
                MCPParameter("claim_id", "integer", "The claim ID to add note to", required=True),
                MCPParameter("content", "string", "Content of the note", required=True),
                MCPParameter("author", "string", "Name of note author", required=True),
                MCPParameter("is_internal", "boolean", "Whether note is internal only", required=False, default=False)
            ],
            handler=add_claim_note
        ))
        
        # Search Claims
        async def search_claims(query: str, limit: int = 10) -> Dict[str, Any]:
            client = await self.get_http_client()
            response = await client.get(
                f"{self.service_urls['claims']}/search/claims",
                params={"q": query, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        
        self.register_tool(MCPTool(
            name="search_claims",
            description="Search claims by claim number, customer ID, or policy ID",
            parameters=[
                MCPParameter("query", "string", "Search query", required=True),
                MCPParameter("limit", "integer", "Maximum number of results", required=False, default=10)
            ],
            handler=search_claims
        ))
    
    async def close(self):
        """Close HTTP client"""
        if self.http_client:
            await self.http_client.aclose()


class MCPToolMixin:
    """Mixin to add MCP tool capabilities to agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcp_registry = MCPToolRegistry()
    
    async def call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Call an MCP tool"""
        return await self.mcp_registry.call_tool(tool_name, parameters)
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools for LLM"""
        return self.mcp_registry.get_tool_definitions()
    
    async def process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple tool calls from LLM"""
        results = []
        
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            tool_name = function.get("name")
            parameters = function.get("arguments", {})
            
            if isinstance(parameters, str):
                try:
                    parameters = json.loads(parameters)
                except json.JSONDecodeError:
                    parameters = {}
            
            result = await self.call_mcp_tool(tool_name, parameters)
            
            results.append({
                "tool_call_id": tool_call.get("id", "unknown"),
                "function_name": tool_name,
                "result": result.content if result.success else {"error": result.error}
            })
        
        return results
    
    async def close_mcp_tools(self):
        """Close MCP tool connections"""
        if hasattr(self, 'mcp_registry'):
            await self.mcp_registry.close()


# Global registry instance
_global_registry = None

def get_mcp_registry() -> MCPToolRegistry:
    """Get global MCP tool registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = MCPToolRegistry()
    return _global_registry

async def initialize_mcp_tools(service_urls: Optional[Dict[str, str]] = None):
    """Initialize MCP tools with custom service URLs"""
    registry = get_mcp_registry()
    
    if service_urls:
        registry.service_urls.update(service_urls)
    
    return registry