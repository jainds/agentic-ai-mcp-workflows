#!/usr/bin/env python3
"""
Comprehensive FastMCP Integration Tests
Tests all aspects of FastMCP functionality, MCP protocol compliance, and JSON data operations
"""

import pytest
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import httpx
from datetime import datetime
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastmcp import FastMCP
    from mcp import ClientSession, StdioServerParameters, stdio_client
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

from services.shared.fastmcp_data_service import FastMCPDataService, get_data_service


class TestFastMCPDataService:
    """Test the FastMCP data service functionality"""
    
    @pytest.fixture
    def data_service(self):
        """Create a data service instance for testing"""
        return FastMCPDataService()
    
    @pytest.fixture
    def sample_data_file(self, tmp_path):
        """Create a sample JSON data file for testing"""
        sample_data = {
            "users": [
                {
                    "id": "test_user_001",
                    "email": "test@example.com",
                    "name": "Test User",
                    "role": "customer",
                    "status": "active"
                },
                {
                    "id": "test_user_002", 
                    "email": "admin@example.com",
                    "name": "Admin User",
                    "role": "admin",
                    "status": "active"
                }
            ],
            "policies": [
                {
                    "id": "POL-TEST-001",
                    "customer_id": "test_user_001",
                    "type": "auto",
                    "status": "active",
                    "coverage_amount": 100000
                }
            ],
            "claims": [
                {
                    "id": "CLM-TEST-001",
                    "customer_id": "test_user_001",
                    "policy_id": "POL-TEST-001",
                    "status": "open",
                    "amount": 5000
                }
            ],
            "analytics": {
                "customer_risk_profiles": [
                    {
                        "customer_id": "test_user_001",
                        "risk_score": 2.5,
                        "risk_level": "low"
                    }
                ],
                "market_trends": {
                    "auto_insurance": {
                        "trend": "stable",
                        "growth_rate": 0.03
                    }
                },
                "fraud_indicators": []
            },
            "quotes": [
                {
                    "id": "QUO-TEST-001",
                    "customer_id": "test_user_001",
                    "type": "auto",
                    "premium": 1200,
                    "status": "pending"
                }
            ]
        }
        
        data_file = tmp_path / "test_data.json"
        with open(data_file, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        return str(data_file)
    
    def test_data_service_initialization(self, sample_data_file):
        """Test that data service initializes properly"""
        service = FastMCPDataService(data_file_path=sample_data_file)
        assert service is not None
        assert service.data is not None
        assert "users" in service.data
        assert len(service.data["users"]) == 2
    
    def test_json_data_loading(self, sample_data_file):
        """Test that JSON data loads correctly"""
        service = FastMCPDataService(data_file_path=sample_data_file)
        
        # Check that data was loaded
        assert service.data is not None
        assert isinstance(service.data, dict)
        
        # Check specific data structures
        assert "users" in service.data
        assert "policies" in service.data
        assert "claims" in service.data
        assert "analytics" in service.data
        assert "quotes" in service.data
        
        # Check data content
        assert len(service.data["users"]) == 2
        assert len(service.data["policies"]) == 1
        assert len(service.data["claims"]) == 1
        assert len(service.data["quotes"]) == 1
    
    def test_get_user_operations(self, data_service):
        """Test user retrieval operations"""
        # Test get user by ID (should work with real data)
        result = data_service.get_user(user_id="user_001")
        assert result["success"] is True
        assert "data" in result
        
        # Test get user by email
        result = data_service.get_user(email="john.doe@email.com")
        assert result["success"] is True
        assert "data" in result
        
        # Test invalid user ID
        result = data_service.get_user(user_id="invalid_user")
        assert result["success"] is False
        assert "error" in result
        
        # Test missing parameters
        result = data_service.get_user()
        assert result["success"] is False
        assert "error" in result
    
    def test_list_users_with_filtering(self, data_service):
        """Test user listing with filters"""
        # Test list all users
        result = data_service.list_users()
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"], list)
        assert result["count"] >= 0
        
        # Test filter by role
        result = data_service.list_users(role="customer")
        assert result["success"] is True
        assert isinstance(result["data"], list)
        
        # Test filter by status
        result = data_service.list_users(status="active")
        assert result["success"] is True
        assert isinstance(result["data"], list)
    
    def test_create_user_mock_operation(self, data_service):
        """Test user creation (mock operation)"""
        user_data = {
            "name": "Test User",
            "email": "testuser@example.com",
            "role": "customer",
            "status": "active"
        }
        
        result = data_service.create_user(user_data)
        assert result["success"] is True
        assert "data" in result
        assert "id" in result["data"]
        assert result["data"]["email"] == user_data["email"]
        assert "created_at" in result["data"]
    
    def test_policy_operations(self, data_service):
        """Test policy operations"""
        # Test get policy
        result = data_service.get_policy("POL-2024-001")
        assert result["success"] is True
        assert "data" in result
        
        # Test get customer policies
        result = data_service.get_customer_policies("user_003")
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"], list)
        assert "count" in result
        
        # Test create policy (mock)
        policy_data = {
            "customer_id": "user_001",
            "type": "auto",
            "coverage_amount": 100000,
            "premium": 1200
        }
        
        result = data_service.create_policy(policy_data)
        assert result["success"] is True
        assert "data" in result
        assert "id" in result["data"]
    
    def test_claims_operations(self, data_service):
        """Test claims operations"""
        # Test get claim
        result = data_service.get_claim("CLM-2024-001")
        assert result["success"] is True
        assert "data" in result
        
        # Test get customer claims
        result = data_service.get_customer_claims("user_003")
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"], list)
        
        # Test create claim (mock)
        claim_data = {
            "customer_id": "user_001",
            "policy_id": "POL-2024-001",
            "type": "collision",
            "amount": 5000,
            "description": "Fender bender"
        }
        
        result = data_service.create_claim(claim_data)
        assert result["success"] is True
        assert "data" in result
        assert "id" in result["data"]
        
        # Test update claim status (mock)
        result = data_service.update_claim_status("CLM-2024-001", "approved", "Claim approved for payment")
        assert result["success"] is True
    
    def test_analytics_operations(self, data_service):
        """Test analytics operations"""
        # Test get customer risk profile
        result = data_service.get_customer_risk_profile("user_003")
        assert result["success"] is True
        assert "data" in result
        
        # Test calculate fraud score
        claim_data = {
            "amount": 10000,
            "type": "theft",
            "location": "downtown",
            "time_of_day": "night"
        }
        
        result = data_service.calculate_fraud_score(claim_data)
        assert result["success"] is True
        assert "data" in result
        assert "fraud_score" in result["data"]
        assert 0 <= result["data"]["fraud_score"] <= 10
        
        # Test get market trends
        result = data_service.get_market_trends()
        assert result["success"] is True
        assert "data" in result
    
    def test_quote_operations(self, data_service):
        """Test quote operations"""
        # Test generate quote (mock)
        quote_data = {
            "customer_id": "user_001",
            "type": "auto",
            "coverage_amount": 100000,
            "vehicle_year": 2020,
            "vehicle_make": "Toyota"
        }
        
        result = data_service.generate_quote(quote_data)
        assert result["success"] is True
        assert "data" in result
        assert "premium" in result["data"]
        assert "id" in result["data"]
        
        # Test get quote
        quote_id = result["data"]["id"]
        result = data_service.get_quote(quote_id)
        # This will return false since it's a mock quote, but should not error
        assert "success" in result
    
    def test_available_tools_listing(self, data_service):
        """Test that all expected tools are available"""
        tools = data_service.get_available_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 15  # We expect at least 15 tools
        
        # Check for expected tool categories
        tool_names = [tool["name"] for tool in tools]
        
        # User tools
        assert "get_user" in tool_names
        assert "list_users" in tool_names
        assert "create_user" in tool_names
        
        # Policy tools
        assert "get_policy" in tool_names
        assert "get_customer_policies" in tool_names
        assert "create_policy" in tool_names
        
        # Claims tools
        assert "get_claim" in tool_names
        assert "get_customer_claims" in tool_names
        assert "create_claim" in tool_names
        assert "update_claim_status" in tool_names
        
        # Analytics tools
        assert "get_customer_risk_profile" in tool_names
        assert "calculate_fraud_score" in tool_names
        assert "get_market_trends" in tool_names
        
        # Quote tools
        assert "generate_quote" in tool_names
        assert "get_quote" in tool_names
        
        # Verify tool structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool


@pytest.mark.skipif(not FASTMCP_AVAILABLE, reason="FastMCP not available")
class TestFastMCPServer:
    """Test FastMCP server integration"""
    
    @pytest.fixture
    def mcp_server(self):
        """Get MCP server instance"""
        data_service = get_data_service()
        return data_service.get_server()
    
    def test_fastmcp_server_creation(self, mcp_server):
        """Test that FastMCP server is created properly"""
        assert mcp_server is not None
        assert hasattr(mcp_server, '_mcp_server')
    
    @pytest.mark.asyncio
    async def test_mcp_tool_listing(self, mcp_server):
        """Test MCP tool listing functionality"""
        # This tests the underlying FastMCP functionality
        tools = mcp_server._tool_registry
        assert len(tools) >= 15
        
        # Check that tools have proper structure
        for tool_name, tool_func in tools.items():
            assert callable(tool_func)
    
    @pytest.mark.asyncio
    async def test_mcp_tool_execution(self):
        """Test direct tool execution through data service"""
        data_service = get_data_service()
        
        # Test a simple tool execution
        result = data_service.get_user(user_id="user_001")
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result


class TestFastMCPErrorHandling:
    """Test error handling in FastMCP data service"""
    
    def test_invalid_json_file(self, tmp_path):
        """Test handling of invalid JSON file"""
        # Create invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json content {")
        
        # Should fall back to default data
        service = FastMCPDataService(data_file_path=str(invalid_file))
        assert service.data is not None
        assert isinstance(service.data, dict)
    
    def test_missing_json_file(self):
        """Test handling of missing JSON file"""
        # Should fall back to default data
        service = FastMCPDataService(data_file_path="/nonexistent/path/file.json")
        assert service.data is not None
        assert isinstance(service.data, dict)
    
    def test_invalid_tool_parameters(self, tmp_path):
        """Test tool behavior with invalid parameters"""
        service = FastMCPDataService()
        
        # Test tools with missing required parameters
        result = service.get_user()  # No user_id or email
        assert result["success"] is False
        
        # Test tools with invalid data types (this should be handled gracefully)
        result = service.get_policy(None)
        assert result["success"] is False
        
        # Test create operations with empty data
        result = service.create_user({})
        assert result["success"] is True  # Should still work with minimal data


class TestFastMCPPerformance:
    """Test performance characteristics of FastMCP service"""
    
    def test_data_loading_performance(self):
        """Test that data loading is reasonably fast"""
        start_time = time.time()
        service = FastMCPDataService()
        end_time = time.time()
        
        loading_time = end_time - start_time
        assert loading_time < 1.0  # Should load in under 1 second
    
    def test_tool_execution_performance(self):
        """Test that tool execution is reasonably fast"""
        service = FastMCPDataService()
        
        # Test multiple tool executions
        tools_to_test = [
            ("get_user", {"user_id": "user_001"}),
            ("list_users", {}),
            ("get_customer_policies", {"customer_id": "user_003"}),
            ("get_market_trends", {}),
        ]
        
        for tool_name, params in tools_to_test:
            start_time = time.time()
            result = None  # Initialize result
            if tool_name == "get_user":
                result = service.get_user(**params)
            elif tool_name == "list_users":
                result = service.list_users(**params)
            elif tool_name == "get_customer_policies":
                result = service.get_customer_policies(**params)
            elif tool_name == "get_market_trends":
                result = service.get_market_trends(**params)
            end_time = time.time()
            
            execution_time = end_time - start_time
            assert execution_time < 0.1  # Each tool should execute in under 100ms
            assert result is not None


def run_comprehensive_tests():
    """Run all tests as a comprehensive suite"""
    import subprocess
    import sys
    
    # Run pytest on this file
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short",
        "--durations=10"
    ], capture_output=True, text=True)
    
    print("FastMCP Comprehensive Test Results:")
    print("=" * 50)
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 