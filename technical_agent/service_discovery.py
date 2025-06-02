#!/usr/bin/env python3
"""
Service Discovery for Technical Agent
Dynamically discovers tools, resources, and capabilities from MCP services
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from fastmcp import Client
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class ServiceEndpoint:
    """Configuration for an MCP service endpoint"""
    name: str
    url: str
    description: str = ""
    enabled: bool = True
    timeout: int = 10
    retry_attempts: int = 3

@dataclass 
class DiscoveredTool:
    """Represents a discovered tool from an MCP service"""
    name: str
    description: str
    service: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    result_schema: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)

@dataclass
class DiscoveredResource:
    """Represents a discovered resource from an MCP service"""
    name: str
    description: str
    service: str
    uri: str
    mime_type: str = ""

@dataclass
class DiscoveredPrompt:
    """Represents a discovered prompt template from an MCP service"""
    name: str
    description: str
    service: str
    template: str
    arguments: List[str] = field(default_factory=list)

@dataclass
class ServiceCapabilities:
    """Complete capabilities of a discovered service"""
    service_name: str
    tools: List[DiscoveredTool] = field(default_factory=list)
    resources: List[DiscoveredResource] = field(default_factory=list)
    prompts: List[DiscoveredPrompt] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ServiceDiscovery:
    """
    Dynamic service discovery for MCP services
    Connects to multiple services and builds a comprehensive tool registry
    """
    
    def __init__(self, services_config: List[ServiceEndpoint] = None):
        """
        Initialize service discovery with service endpoints
        
        Args:
            services_config: List of service endpoints to discover
        """
        self.services_config = services_config or self._get_default_services()
        self.discovered_services: Dict[str, ServiceCapabilities] = {}
        self.tool_registry: Dict[str, DiscoveredTool] = {}
        self.resource_registry: Dict[str, DiscoveredResource] = {}
        self.prompt_registry: Dict[str, DiscoveredPrompt] = {}
        
        logger.info(f"ServiceDiscovery initialized with {len(self.services_config)} services")
    
    def _get_default_services(self) -> List[ServiceEndpoint]:
        """Default service configuration"""
        return [
            ServiceEndpoint(
                name="policy_service",
                url="http://localhost:8001/mcp",
                description="Insurance policy management service",
                enabled=True
            ),
            ServiceEndpoint(
                name="claims_service", 
                url="http://localhost:8002/mcp",
                description="Insurance claims processing service",
                enabled=False  # Not implemented yet
            )
        ]
    
    async def discover_all_services(self) -> Dict[str, ServiceCapabilities]:
        """
        Discover capabilities from all configured services
        
        Returns:
            Dictionary mapping service names to their capabilities
        """
        logger.info("Starting service discovery process")
        
        discovery_tasks = []
        for service_config in self.services_config:
            if service_config.enabled:
                task = self._discover_service(service_config)
                discovery_tasks.append(task)
        
        # Execute discovery in parallel
        results = await asyncio.gather(*discovery_tasks, return_exceptions=True)
        
        # Process results
        successful_discoveries = 0
        for i, result in enumerate(results):
            service_config = [s for s in self.services_config if s.enabled][i]
            
            if isinstance(result, Exception):
                logger.error(f"Failed to discover service {service_config.name}: {result}")
            else:
                self.discovered_services[service_config.name] = result
                self._register_service_capabilities(result)
                successful_discoveries += 1
                logger.info(f"Successfully discovered service: {service_config.name}")
        
        logger.info(f"Service discovery completed: {successful_discoveries}/{len([s for s in self.services_config if s.enabled])} services discovered")
        
        return self.discovered_services
    
    async def _discover_service(self, service_config: ServiceEndpoint) -> ServiceCapabilities:
        """
        Discover capabilities of a single MCP service using FastMCP Client
        
        Args:
            service_config: Configuration for the service to discover
            
        Returns:
            ServiceCapabilities object with discovered tools, resources, prompts
        """
        logger.info(f"Discovering service: {service_config.name} at {service_config.url}")
        
        capabilities = ServiceCapabilities(service_name=service_config.name)
        
        try:
            # Use FastMCP Client for proper transport handling
            client = Client(service_config.url)
            
            async with client:
                # Discover tools
                try:
                    tools = await client.list_tools()
                    for tool in tools:
                        # Extract input schema for parameters
                        input_schema = getattr(tool, 'inputSchema', {})
                        
                        discovered_tool = DiscoveredTool(
                            name=tool.name,
                            description=tool.description or "",
                            service=service_config.name,
                            parameters=input_schema
                        )
                        capabilities.tools.append(discovered_tool)
                        logger.debug(f"Discovered tool: {tool.name}")
                        
                    logger.info(f"Discovered {len(capabilities.tools)} tools from {service_config.name}")
                except Exception as e:
                    logger.warning(f"Failed to discover tools from {service_config.name}: {e}")
                
                # Discover resources
                try:
                    resources = await client.list_resources()
                    for resource in resources:
                        discovered_resource = DiscoveredResource(
                            name=resource.name,
                            description=resource.description or "",
                            service=service_config.name,
                            uri=resource.uri,
                            mime_type=getattr(resource, 'mimeType', '')
                        )
                        capabilities.resources.append(discovered_resource)
                        logger.debug(f"Discovered resource: {resource.name}")
                        
                    logger.info(f"Discovered {len(capabilities.resources)} resources from {service_config.name}")
                except Exception as e:
                    logger.warning(f"Failed to discover resources from {service_config.name}: {e}")
                
                # Discover resource templates
                try:
                    templates = await client.list_resource_templates()
                    for template in templates:
                        discovered_resource = DiscoveredResource(
                            name=template.name,
                            description=template.description or "",
                            service=service_config.name,
                            uri=template.uriTemplate,
                            mime_type=getattr(template, 'mimeType', '')
                        )
                        capabilities.resources.append(discovered_resource)
                        logger.debug(f"Discovered resource template: {template.name}")
                        
                    logger.info(f"Discovered {len(templates)} resource templates from {service_config.name}")
                except Exception as e:
                    logger.warning(f"Failed to discover resource templates from {service_config.name}: {e}")
                
                # Discover prompts
                try:
                    prompts = await client.list_prompts()
                    for prompt in prompts:
                        discovered_prompt = DiscoveredPrompt(
                            name=prompt.name,
                            description=prompt.description or "",
                            service=service_config.name,
                            template="",  # Would need to fetch template content
                            arguments=getattr(prompt, 'arguments', [])
                        )
                        capabilities.prompts.append(discovered_prompt)
                        logger.debug(f"Discovered prompt: {prompt.name}")
                        
                    logger.info(f"Discovered {len(capabilities.prompts)} prompts from {service_config.name}")
                except Exception as e:
                    logger.warning(f"Failed to discover prompts from {service_config.name}: {e}")
                
                # Get service metadata
                capabilities.metadata = {
                    "url": service_config.url,
                    "description": service_config.description,
                    "tool_count": len(capabilities.tools),
                    "resource_count": len(capabilities.resources),
                    "prompt_count": len(capabilities.prompts),
                    "transport": "streamable-http"  # We're using the high-level client
                }
        
        except Exception as e:
            logger.error(f"Failed to connect to service {service_config.name}: {e}")
            raise
        
        logger.info(f"Service {service_config.name} discovery complete: {len(capabilities.tools)} tools, {len(capabilities.resources)} resources, {len(capabilities.prompts)} prompts")
        
        return capabilities
    
    def _register_service_capabilities(self, capabilities: ServiceCapabilities):
        """Register discovered capabilities in global registries"""
        
        # Register tools
        for tool in capabilities.tools:
            tool_key = f"{capabilities.service_name}.{tool.name}"
            self.tool_registry[tool_key] = tool
            # Also register with just the tool name for convenience
            if tool.name not in self.tool_registry:
                self.tool_registry[tool.name] = tool
        
        # Register resources
        for resource in capabilities.resources:
            resource_key = f"{capabilities.service_name}.{resource.name}"
            self.resource_registry[resource_key] = resource
            if resource.name not in self.resource_registry:
                self.resource_registry[resource.name] = resource
        
        # Register prompts
        for prompt in capabilities.prompts:
            prompt_key = f"{capabilities.service_name}.{prompt.name}"
            self.prompt_registry[prompt_key] = prompt
            if prompt.name not in self.prompt_registry:
                self.prompt_registry[prompt.name] = prompt
    
    def get_available_tools(self) -> Dict[str, str]:
        """
        Get all available tools in format expected by LLM planning
        
        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {
            name: tool.description 
            for name, tool in self.tool_registry.items()
            if not '.' in name  # Only include non-namespaced names
        }
    
    def get_tool_by_name(self, tool_name: str) -> Optional[DiscoveredTool]:
        """Get tool details by name"""
        return self.tool_registry.get(tool_name)
    
    def get_tools_by_service(self, service_name: str) -> List[DiscoveredTool]:
        """Get all tools from a specific service"""
        if service_name in self.discovered_services:
            return self.discovered_services[service_name].tools
        return []
    
    def build_tools_description(self) -> str:
        """
        Build formatted tools description for LLM prompts
        
        Returns:
            Formatted string describing all available tools
        """
        tools_desc = []
        
        for service_name, capabilities in self.discovered_services.items():
            if capabilities.tools:
                tools_desc.append(f"\n# {service_name.title()} Service Tools:")
                for tool in capabilities.tools:
                    # Extract parameter requirements
                    params = []
                    if tool.parameters and 'properties' in tool.parameters:
                        required = tool.parameters.get('required', [])
                        for param_name in required:
                            params.append(f"requires {param_name}")
                    
                    param_text = f" ({', '.join(params)})" if params else ""
                    tools_desc.append(f"- {tool.name}: {tool.description}{param_text}")
        
        return "\n".join(tools_desc)
    
    def get_service_summary(self) -> Dict[str, Any]:
        """Get summary of all discovered services"""
        summary = {
            "total_services": len(self.discovered_services),
            "total_tools": len([k for k in self.tool_registry.keys() if '.' not in k]),
            "total_resources": len([k for k in self.resource_registry.keys() if '.' not in k]),
            "total_prompts": len([k for k in self.prompt_registry.keys() if '.' not in k]),
            "services": {}
        }
        
        for service_name, capabilities in self.discovered_services.items():
            summary["services"][service_name] = {
                "tools": len(capabilities.tools),
                "resources": len(capabilities.resources), 
                "prompts": len(capabilities.prompts),
                "metadata": capabilities.metadata
            }
        
        return summary
    
    async def refresh_service(self, service_name: str) -> bool:
        """
        Refresh capabilities for a specific service
        
        Args:
            service_name: Name of service to refresh
            
        Returns:
            True if refresh successful, False otherwise
        """
        service_config = next((s for s in self.services_config if s.name == service_name), None)
        if not service_config:
            logger.error(f"Service {service_name} not found in configuration")
            return False
        
        try:
            capabilities = await self._discover_service(service_config)
            
            # Remove old registrations
            old_capabilities = self.discovered_services.get(service_name)
            if old_capabilities:
                self._unregister_service_capabilities(old_capabilities)
            
            # Add new registrations
            self.discovered_services[service_name] = capabilities
            self._register_service_capabilities(capabilities)
            
            logger.info(f"Successfully refreshed service: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh service {service_name}: {e}")
            return False
    
    def _unregister_service_capabilities(self, capabilities: ServiceCapabilities):
        """Remove service capabilities from registries"""
        for tool in capabilities.tools:
            tool_key = f"{capabilities.service_name}.{tool.name}"
            self.tool_registry.pop(tool_key, None)
            # Only remove simple name if it points to this service
            if self.tool_registry.get(tool.name) == tool:
                self.tool_registry.pop(tool.name, None)
        
        for resource in capabilities.resources:
            resource_key = f"{capabilities.service_name}.{resource.name}"
            self.resource_registry.pop(resource_key, None)
            if self.resource_registry.get(resource.name) == resource:
                self.resource_registry.pop(resource.name, None)
        
        for prompt in capabilities.prompts:
            prompt_key = f"{capabilities.service_name}.{prompt.name}"
            self.prompt_registry.pop(prompt_key, None)
            if self.prompt_registry.get(prompt.name) == prompt:
                self.prompt_registry.pop(prompt.name, None) 