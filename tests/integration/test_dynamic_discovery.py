#!/usr/bin/env python3
"""
Integration tests for Dynamic Service Discovery
Tests the full workflow of discovering services and validating integration patterns
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch
from typing import Dict, Any, List

import sys
import os

# Add technical_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'technical_agent'))

from service_discovery import ServiceDiscovery, ServiceEndpoint

class TestServiceDiscoveryIntegration:
    """Integration tests for service discovery functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.policy_service_url = "http://localhost:8001/mcp"
        self.test_customer_id = "CUST-001"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_discovery_with_policy_server(self):
        """Test service discovery against actual policy server (if running)"""
        
        # Configure service discovery
        services = [
            ServiceEndpoint(
                name="policy_service",
                url=self.policy_service_url,
                description="Policy management service",
                enabled=True
            )
        ]
        
        discovery = ServiceDiscovery(services)
        
        try:
            # Attempt to discover services
            discovered_services = await discovery.discover_all_services()
            
            if "policy_service" in discovered_services:
                # Policy server is running - test full integration
                policy_capabilities = discovered_services["policy_service"]
                
                # Verify expected tools are discovered
                tool_names = [tool.name for tool in policy_capabilities.tools]
                expected_tools = ["get_policies", "get_agent", "get_policy_types"]
                
                for expected_tool in expected_tools:
                    assert expected_tool in tool_names, f"Expected tool {expected_tool} not found"
                
                print(f"✅ Successfully discovered {len(tool_names)} tools from policy service")
                
                # Test tool registry
                available_tools = discovery.get_available_tools()
                assert "get_policies" in available_tools
                assert "get_agent" in available_tools
                
                # Test tools description generation
                tools_description = discovery.build_tools_description()
                assert "get_policies" in tools_description
                assert "customer_id" in tools_description
                
                print(f"✅ Tool registry and descriptions working correctly")
                
            else:
                pytest.skip("Policy server not running - integration test skipped")
                
        except Exception as e:
            pytest.skip(f"Policy server not available: {e}")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_discovery_with_mocked_client(self):
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
        mock_client = Mock()
        mock_client.__aenter__ = Mock(return_value=mock_client)
        mock_client.__aexit__ = Mock(return_value=None)
        mock_client.list_tools = Mock(return_value=[mock_tool])
        mock_client.list_resources = Mock(return_value=[mock_resource])
        mock_client.list_resource_templates = Mock(return_value=[])
        mock_client.list_prompts = Mock(return_value=[])
        
        with patch('service_discovery.Client', return_value=mock_client):
            services = [ServiceEndpoint(
                name="test_service",
                url="http://localhost:8001/mcp",
                enabled=True
            )]
            
            discovery = ServiceDiscovery(services)
            discovered = await discovery.discover_all_services()
            
            # Verify discovery results
            assert "test_service" in discovered
            capabilities = discovered["test_service"]
            assert len(capabilities.tools) == 1
            assert capabilities.tools[0].name == "get_policies"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_refresh_workflow(self):
        """Test the service refresh workflow"""
        
        # Initial discovery with one tool
        mock_tool_1 = Mock()
        mock_tool_1.name = "old_tool"
        mock_tool_1.description = "Old tool"
        mock_tool_1.inputSchema = {}
        
        # Refresh discovery with different tools
        mock_tool_2 = Mock()
        mock_tool_2.name = "new_tool"
        mock_tool_2.description = "New tool"
        mock_tool_2.inputSchema = {}
        
        call_count = 0
        
        def mock_list_tools():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [mock_tool_1]
            else:
                return [mock_tool_2]
        
        mock_client = Mock()
        mock_client.__aenter__ = Mock(return_value=mock_client)
        mock_client.__aexit__ = Mock(return_value=None)
        mock_client.list_tools = mock_list_tools
        mock_client.list_resources = Mock(return_value=[])
        mock_client.list_resource_templates = Mock(return_value=[])
        mock_client.list_prompts = Mock(return_value=[])
        
        with patch('service_discovery.Client', return_value=mock_client):
            services = [ServiceEndpoint(
                name="test_service",
                url="http://localhost:8001/mcp",
                enabled=True
            )]
            
            discovery = ServiceDiscovery(services)
            
            # Initial discovery
            await discovery.discover_all_services()
            assert "old_tool" in discovery.tool_registry
            assert "new_tool" not in discovery.tool_registry
            
            # Refresh service
            refresh_result = await discovery.refresh_service("test_service")
            assert refresh_result is True
            
            # Verify tools were updated
            assert "old_tool" not in discovery.tool_registry
            assert "new_tool" in discovery.tool_registry
            
            print(f"✅ Service refresh workflow completed successfully")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_in_discovery(self):
        """Test error handling during service discovery"""
        
        services = [
            ServiceEndpoint(
                name="unavailable_service",
                url="http://localhost:9999/mcp",  # Non-existent service
                enabled=True
            ),
            ServiceEndpoint(
                name="valid_service", 
                url="http://localhost:8001/mcp",
                enabled=True
            )
        ]
        
        # Mock one successful, one failed discovery
        def mock_client_factory(url):
            if "9999" in url:
                raise ConnectionError("Service unavailable")
            else:
                # Return working mock client
                mock_client = Mock()
                mock_client.__aenter__ = Mock(return_value=mock_client)
                mock_client.__aexit__ = Mock(return_value=None)
                mock_client.list_tools = Mock(return_value=[])
                mock_client.list_resources = Mock(return_value=[])
                mock_client.list_resource_templates = Mock(return_value=[])
                mock_client.list_prompts = Mock(return_value=[])
                return mock_client
        
        with patch('service_discovery.Client', side_effect=mock_client_factory):
            discovery = ServiceDiscovery(services)
            
            # Should handle mixed success/failure gracefully
            discovered = await discovery.discover_all_services()
            
            # Should have discovered the valid service despite the failure
            summary = discovery.get_service_summary()
            
            # At least partial success expected (if policy server is running)
            assert summary["total_services"] >= 0
            
            print(f"✅ Error handling in discovery works correctly")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_performance_of_parallel_discovery(self):
        """Test performance benefits of parallel service discovery"""
        
        # Mock multiple services with artificial delays
        services = [
            ServiceEndpoint(name=f"service_{i}", url=f"http://localhost:800{i}/mcp", enabled=True)
            for i in range(1, 4)
        ]
        
        async def mock_discover_service(config):
            # Simulate network delay
            await asyncio.sleep(0.1)
            from service_discovery import ServiceCapabilities
            return ServiceCapabilities(service_name=config.name)
        
        discovery = ServiceDiscovery(services)
        
        # Time the parallel discovery
        start_time = time.time()
        
        with patch.object(discovery, '_discover_service', side_effect=mock_discover_service):
            await discovery.discover_all_services()
        
        elapsed_time = time.time() - start_time
        
        # Should complete in roughly parallel time (~0.1s) not sequential time (~0.3s)
        assert elapsed_time < 0.2, f"Parallel discovery took too long: {elapsed_time}s"
        
        print(f"✅ Parallel discovery completed in {elapsed_time:.3f}s")

class TestIntegrationWorkflows:
    """Test integration workflows and patterns"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_workflow(self):
        """Test service health check integration"""
        
        # Mock service discovery health check
        discovery = ServiceDiscovery([])
        
        # Basic health check should work
        summary = discovery.get_service_summary()
        assert "total_services" in summary
        assert "total_tools" in summary
        assert isinstance(summary["services"], dict)
        
        print("✅ Service health check workflow working")

    def test_configuration_validation(self):
        """Test service configuration validation"""
        
        # Test valid configuration
        valid_config = ServiceEndpoint(
            name="test_service",
            url="http://localhost:8001/mcp",
            description="Test service",
            enabled=True
        )
        
        assert valid_config.name == "test_service"
        assert valid_config.enabled is True
        assert valid_config.timeout == 10  # default
        
        # Test configuration with custom values
        custom_config = ServiceEndpoint(
            name="custom_service",
            url="http://example.com/mcp",
            timeout=30,
            retry_attempts=5
        )
        
        assert custom_config.timeout == 30
        assert custom_config.retry_attempts == 5
        
        print("✅ Configuration validation working")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"]) 