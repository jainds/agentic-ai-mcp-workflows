#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Insurance AI POC test suite
Provides common test utilities, markers, and fixtures
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock
from typing import Generator, Any

# Add source directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'policy_server'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'technical_agent'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'domain_agent'))

def pytest_configure(config):
    """Configure pytest markers and options"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing without API calls"""
    mock_client = Mock()
    
    # Mock completion response
    mock_completion = Mock()
    mock_completion.choices = [Mock()]
    mock_completion.choices[0].message.content = '''
    {
        "plan_type": "single_tool",
        "reasoning": "User wants basic information",
        "tool_name": "get_policies",
        "parameters": {"customer_id": "CUST-001"}
    }
    '''
    
    mock_client.chat.completions.create.return_value = mock_completion
    return mock_client

@pytest.fixture
def mock_fastmcp_client():
    """Mock FastMCP client for testing service discovery"""
    mock_client = AsyncMock()
    
    # Mock tool
    mock_tool = Mock()
    mock_tool.name = "get_policies"
    mock_tool.description = "Get customer policies"
    mock_tool.inputSchema = {
        "type": "object",
        "properties": {"customer_id": {"type": "string"}},
        "required": ["customer_id"]
    }
    
    # Mock resource
    mock_resource = Mock()
    mock_resource.name = "customer_data"
    mock_resource.description = "Customer data resource"
    mock_resource.uri = "customer://data"
    mock_resource.mimeType = "application/json"
    
    # Setup client methods
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.list_tools = AsyncMock(return_value=[mock_tool])
    mock_client.list_resources = AsyncMock(return_value=[mock_resource])
    mock_client.list_resource_templates = AsyncMock(return_value=[])
    mock_client.list_prompts = AsyncMock(return_value=[])
    
    return mock_client

@pytest.fixture
def sample_customer_data():
    """Sample customer data for testing"""
    return {
        "customer_id": "CUST-001",
        "name": "John Doe",
        "email": "john.doe@email.com",
        "phone": "555-0123",
        "policies": [
            {
                "policy_id": "P001",
                "type": "Auto",
                "status": "Active",
                "premium": "150.00",
                "next_payment_date": "2024-02-15"
            },
            {
                "policy_id": "P002", 
                "type": "Home",
                "status": "Active",
                "premium": "200.00",
                "next_payment_date": "2024-02-15"
            }
        ]
    }

@pytest.fixture
def sample_tool_call_result():
    """Sample MCP tool call result for testing"""
    mock_result = [Mock()]
    mock_result[0].text = '''
    [
        {
            "policy_id": "P001",
            "type": "Auto", 
            "status": "Active",
            "premium": "150.00"
        }
    ]
    '''
    return mock_result

@pytest.fixture
def policy_server():
    """Policy server instance for testing"""
    try:
        from main import PolicyServer
        return PolicyServer()
    except ImportError:
        pytest.skip("PolicyServer not available for testing")

@pytest.fixture
def service_discovery_config():
    """Service discovery configuration for testing"""
    from service_discovery import ServiceEndpoint
    
    return [
        ServiceEndpoint(
            name="policy_service",
            url="http://localhost:8001/mcp",
            description="Policy management service",
            enabled=True
        ),
        ServiceEndpoint(
            name="claims_service",
            url="http://localhost:8002/mcp",
            description="Claims processing service", 
            enabled=False  # Disabled for testing
        )
    ]

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location"""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)

@pytest.fixture
def temp_test_data_dir(tmp_path):
    """Create temporary directory with test data files"""
    test_data = tmp_path / "test_data"
    test_data.mkdir()
    
    # Create sample JSON files
    customers_file = test_data / "customers.json"
    customers_file.write_text('''
    {
        "CUST-001": {
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "555-0123"
        }
    }
    ''')
    
    policies_file = test_data / "policies.json"
    policies_file.write_text('''
    {
        "CUST-001": [
            {
                "policy_id": "P001",
                "type": "Auto",
                "status": "Active"
            }
        ]
    }
    ''')
    
    return test_data

class TestHelpers:
    """Helper utilities for tests"""
    
    @staticmethod
    def assert_api_response_structure(response, required_fields):
        """Assert that API response has required structure"""
        assert isinstance(response, (dict, list))
        
        if isinstance(response, dict):
            for field in required_fields:
                assert field in response, f"Missing required field: {field}"
        elif isinstance(response, list) and response:
            # Check first item structure
            for field in required_fields:
                assert field in response[0], f"Missing required field: {field}"
    
    @staticmethod
    def assert_tool_call_format(tool_call_result):
        """Assert that tool call result has proper format"""
        assert hasattr(tool_call_result[0], 'text')
        # Should be valid JSON
        import json
        json.loads(tool_call_result[0].text)
    
    @staticmethod
    def create_mock_execution_plan(plan_type="single_tool", tool_name="get_policies"):
        """Create mock execution plan for testing"""
        if plan_type == "single_tool":
            return {
                "plan_type": "single_tool",
                "reasoning": "Test plan",
                "tool_name": tool_name,
                "parameters": {"customer_id": "CUST-001"}
            }
        elif plan_type == "multi_tool":
            return {
                "plan_type": "multi_tool",
                "reasoning": "Multi-tool test plan",
                "execution_order": "parallel",
                "tool_calls": [
                    {
                        "tool_name": "get_policies",
                        "parameters": {"customer_id": "CUST-001"},
                        "result_key": "policies",
                        "reasoning": "Get policies"
                    },
                    {
                        "tool_name": "get_agent",
                        "parameters": {"customer_id": "CUST-001"}, 
                        "result_key": "agent",
                        "reasoning": "Get agent info"
                    }
                ]
            }

# Global test helper instance
test_helpers = TestHelpers() 