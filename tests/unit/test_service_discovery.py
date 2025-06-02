#!/usr/bin/env python3
"""
Unit tests for Service Discovery functionality
Tests the dynamic discovery of MCP services and tool registry management
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass
from typing import Dict, Any, List

import sys
import os

# Add technical_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'technical_agent'))

from service_discovery import (
    ServiceDiscovery, ServiceEndpoint, DiscoveredTool, 
    DiscoveredResource, DiscoveredPrompt, ServiceCapabilities
)

class TestServiceEndpoint:
    """Test ServiceEndpoint dataclass"""
    
    def test_service_endpoint_creation(self):
        """Test basic ServiceEndpoint creation"""
        endpoint = ServiceEndpoint(
            name="test_service",
            url="http://localhost:8001/mcp",
            description="Test service",
            enabled=True
        )
        
        assert endpoint.name == "test_service"
        assert endpoint.url == "http://localhost:8001/mcp"
        assert endpoint.description == "Test service"
        assert endpoint.enabled is True
        assert endpoint.timeout == 10  # default
        assert endpoint.retry_attempts == 3  # default

    def test_service_endpoint_defaults(self):
        """Test ServiceEndpoint with minimal parameters"""
        endpoint = ServiceEndpoint(name="minimal", url="http://test.com")
        
        assert endpoint.description == ""
        assert endpoint.enabled is True
        assert endpoint.timeout == 10
        assert endpoint.retry_attempts == 3

class TestDiscoveredTool:
    """Test DiscoveredTool dataclass"""
    
    def test_discovered_tool_creation(self):
        """Test DiscoveredTool creation with parameters"""
        tool = DiscoveredTool(
            name="get_policies",
            description="Get customer policies",
            service="policy_service",
            parameters={
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"]
            }
        )
        
        assert tool.name == "get_policies"
        assert tool.description == "Get customer policies"
        assert tool.service == "policy_service"
        assert "customer_id" in tool.parameters["properties"]
        assert "customer_id" in tool.parameters["required"]

class TestServiceCapabilities:
    """Test ServiceCapabilities dataclass"""
    
    def test_service_capabilities_creation(self):
        """Test ServiceCapabilities with tools and resources"""
        tool = DiscoveredTool("test_tool", "Test tool", "test_service")
        resource = DiscoveredResource("test_resource", "Test resource", "test_service", "http://test.com")
        
        capabilities = ServiceCapabilities(
            service_name="test_service",
            tools=[tool],
            resources=[resource],
            metadata={"version": "1.0"}
        )
        
        assert capabilities.service_name == "test_service"
        assert len(capabilities.tools) == 1
        assert len(capabilities.resources) == 1
        assert capabilities.metadata["version"] == "1.0"

class TestServiceDiscovery:
    """Test ServiceDiscovery class functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_services = [
            ServiceEndpoint(
                name="policy_service",
                url="http://localhost:8001/mcp",
                description="Policy service",
                enabled=True
            ),
            ServiceEndpoint(
                name="claims_service",
                url="http://localhost:8002/mcp", 
                description="Claims service",
                enabled=False
            )
        ]
        
        self.discovery = ServiceDiscovery(self.test_services)

    def test_initialization(self):
        """Test ServiceDiscovery initialization"""
        assert len(self.discovery.services_config) == 2
        assert self.discovery.services_config[0].name == "policy_service"
        assert self.discovery.services_config[1].enabled is False
        
        # Test with default services
        default_discovery = ServiceDiscovery()
        assert len(default_discovery.services_config) >= 1

    def test_get_default_services(self):
        """Test default services configuration"""
        discovery = ServiceDiscovery()
        default_services = discovery._get_default_services()
        
        assert len(default_services) >= 1
        assert any(s.name == "policy_service" for s in default_services)

    @pytest.mark.asyncio
    async def test_discover_service_mock(self):
        """Test service discovery with mocked FastMCP client"""
        
        # Mock tool objects
        mock_tool = Mock()
        mock_tool.name = "get_policies"
        mock_tool.description = "Get customer policies"
        mock_tool.inputSchema = {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"]
        }
        
        # Mock resource objects
        mock_resource = Mock()
        mock_resource.name = "customer_data"
        mock_resource.description = "Customer data resource"
        mock_resource.uri = "customer://data"
        mock_resource.mimeType = "application/json"
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.list_tools = AsyncMock(return_value=[mock_tool])
        mock_client.list_resources = AsyncMock(return_value=[mock_resource])
        mock_client.list_resource_templates = AsyncMock(return_value=[])
        mock_client.list_prompts = AsyncMock(return_value=[])
        
        with patch('service_discovery.Client', return_value=mock_client):
            service_config = self.test_services[0]  # policy_service
            capabilities = await self.discovery._discover_service(service_config)
            
            assert capabilities.service_name == "policy_service"
            assert len(capabilities.tools) == 1
            assert len(capabilities.resources) == 1
            assert capabilities.tools[0].name == "get_policies"
            assert capabilities.resources[0].name == "customer_data"

    def test_register_service_capabilities(self):
        """Test registering service capabilities in registries"""
        tool = DiscoveredTool("test_tool", "Test tool", "test_service")
        resource = DiscoveredResource("test_resource", "Test resource", "test_service", "http://test.com")
        
        capabilities = ServiceCapabilities(
            service_name="test_service",
            tools=[tool],
            resources=[resource]
        )
        
        self.discovery._register_service_capabilities(capabilities)
        
        # Check tool registry
        assert "test_tool" in self.discovery.tool_registry
        assert "test_service.test_tool" in self.discovery.tool_registry
        assert self.discovery.tool_registry["test_tool"] == tool
        
        # Check resource registry
        assert "test_resource" in self.discovery.resource_registry
        assert "test_service.test_resource" in self.discovery.resource_registry

    def test_get_available_tools(self):
        """Test getting available tools dictionary"""
        tool1 = DiscoveredTool("tool1", "First tool", "service1")
        tool2 = DiscoveredTool("tool2", "Second tool", "service2")
        
        # Register tools manually
        self.discovery.tool_registry["tool1"] = tool1
        self.discovery.tool_registry["tool2"] = tool2
        self.discovery.tool_registry["service1.tool1"] = tool1  # namespaced
        
        available_tools = self.discovery.get_available_tools()
        
        assert "tool1" in available_tools
        assert "tool2" in available_tools
        assert "service1.tool1" not in available_tools  # excludes namespaced
        assert available_tools["tool1"] == "First tool"

    def test_get_tool_by_name(self):
        """Test retrieving tool by name"""
        tool = DiscoveredTool("test_tool", "Test tool", "test_service")
        self.discovery.tool_registry["test_tool"] = tool
        
        retrieved_tool = self.discovery.get_tool_by_name("test_tool")
        assert retrieved_tool == tool
        
        # Test non-existent tool
        assert self.discovery.get_tool_by_name("nonexistent") is None

    def test_build_tools_description(self):
        """Test building formatted tools description"""
        tool1 = DiscoveredTool(
            "get_policies", 
            "Get customer policies", 
            "policy_service",
            parameters={
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"]
            }
        )
        
        capabilities = ServiceCapabilities(
            service_name="policy_service",
            tools=[tool1]
        )
        
        self.discovery.discovered_services["policy_service"] = capabilities
        
        description = self.discovery.build_tools_description()
        
        assert "Policy_Service Service Tools:" in description
        assert "get_policies: Get customer policies" in description
        assert "requires customer_id" in description

    def test_get_service_summary(self):
        """Test getting service summary"""
        tool = DiscoveredTool("test_tool", "Test tool", "test_service")
        capabilities = ServiceCapabilities(
            service_name="test_service",
            tools=[tool],
            metadata={"url": "http://test.com", "version": "1.0"}
        )
        
        self.discovery.discovered_services["test_service"] = capabilities
        self.discovery.tool_registry["test_tool"] = tool
        
        summary = self.discovery.get_service_summary()
        
        assert summary["total_services"] == 1
        assert summary["total_tools"] == 1
        assert "test_service" in summary["services"]
        assert summary["services"]["test_service"]["tools"] == 1

    def test_unregister_service_capabilities(self):
        """Test unregistering service capabilities"""
        tool = DiscoveredTool("test_tool", "Test tool", "test_service")
        capabilities = ServiceCapabilities(
            service_name="test_service",
            tools=[tool]
        )
        
        # Register first
        self.discovery._register_service_capabilities(capabilities)
        assert "test_tool" in self.discovery.tool_registry
        
        # Unregister
        self.discovery._unregister_service_capabilities(capabilities)
        assert "test_tool" not in self.discovery.tool_registry
        assert "test_service.test_tool" not in self.discovery.tool_registry

    @pytest.mark.asyncio
    async def test_refresh_service_mock(self):
        """Test refreshing a specific service"""
        # Setup initial state
        tool1 = DiscoveredTool("old_tool", "Old tool", "policy_service")
        old_capabilities = ServiceCapabilities(
            service_name="policy_service",
            tools=[tool1]
        )
        self.discovery.discovered_services["policy_service"] = old_capabilities
        self.discovery._register_service_capabilities(old_capabilities)
        
        # Mock new discovery result
        tool2 = DiscoveredTool("new_tool", "New tool", "policy_service")
        new_capabilities = ServiceCapabilities(
            service_name="policy_service", 
            tools=[tool2]
        )
        
        with patch.object(self.discovery, '_discover_service', return_value=new_capabilities):
            result = await self.discovery.refresh_service("policy_service")
            
            assert result is True
            assert "new_tool" in self.discovery.tool_registry
            assert "old_tool" not in self.discovery.tool_registry

    @pytest.mark.asyncio
    async def test_refresh_nonexistent_service(self):
        """Test refreshing a service that doesn't exist in config"""
        result = await self.discovery.refresh_service("nonexistent_service")
        assert result is False

    @pytest.mark.asyncio
    async def test_discover_all_services_mixed_results(self):
        """Test discovering multiple services with mixed success/failure"""
        
        # Mock one successful and one failed discovery
        success_tool = DiscoveredTool("success_tool", "Success tool", "policy_service")
        success_capabilities = ServiceCapabilities(
            service_name="policy_service",
            tools=[success_tool]
        )
        
        async def mock_discover_service(config):
            if config.name == "policy_service":
                return success_capabilities
            else:
                raise ConnectionError("Service unavailable")
        
        # Enable both services for this test
        self.discovery.services_config[1].enabled = True
        
        with patch.object(self.discovery, '_discover_service', side_effect=mock_discover_service):
            discovered = await self.discovery.discover_all_services()
            
            # Should have one successful discovery
            assert len(discovered) == 1
            assert "policy_service" in discovered
            assert len(discovered["policy_service"].tools) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 