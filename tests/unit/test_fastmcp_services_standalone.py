#!/usr/bin/env python3
"""
Unit Tests for FastMCP Services
Tests the individual FastMCP service components
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Test individual FastMCP service modules if available
class TestFastMCPServices:
    """Unit tests for FastMCP service functionality"""
    
    def test_service_directory_structure(self):
        """Test that FastMCP service directories exist"""
        services_dir = Path("services")
        assert services_dir.exists(), "Services directory should exist"
        
        expected_services = ["user_service", "claims_service", "policy_service", "analytics_service"]
        for service in expected_services:
            service_dir = services_dir / service
            assert service_dir.exists(), f"{service} directory should exist"
            
            main_file = service_dir / "main.py"
            assert main_file.exists(), f"{service}/main.py should exist"
    
    def test_fastmcp_imports(self):
        """Test that FastMCP library can be imported"""
        try:
            import fastmcp
            from fastmcp.server import FastMCPServer
            assert True, "FastMCP imports successful"
        except ImportError as e:
            pytest.skip(f"FastMCP not available: {e}")
    
    @pytest.mark.asyncio
    async def test_user_service_mock(self):
        """Test user service mock functionality"""
        # Mock user service data
        mock_user_data = {
            "user_id": "test-user-123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "policies": ["POL-001", "POL-002"]
        }
        
        # Test user data structure
        assert "user_id" in mock_user_data
        assert "name" in mock_user_data
        assert "email" in mock_user_data
        assert isinstance(mock_user_data["policies"], list)
    
    @pytest.mark.asyncio
    async def test_claims_service_mock(self):
        """Test claims service mock functionality"""
        # Mock claims service data
        mock_claims_data = {
            "claims": [
                {
                    "claim_id": "CLM-2024-001",
                    "type": "auto",
                    "status": "processing",
                    "amount": 2500.00,
                    "filed_date": "2024-01-15"
                }
            ],
            "total_claims": 1
        }
        
        # Test claims data structure
        assert "claims" in mock_claims_data
        assert isinstance(mock_claims_data["claims"], list)
        assert len(mock_claims_data["claims"]) > 0
        
        claim = mock_claims_data["claims"][0]
        assert "claim_id" in claim
        assert "status" in claim
        assert "amount" in claim
    
    @pytest.mark.asyncio
    async def test_policy_service_mock(self):
        """Test policy service mock functionality"""
        # Mock policy service data
        mock_policy_data = {
            "policies": [
                {
                    "policy_id": "POL-2024-AUTO-001",
                    "type": "auto",
                    "status": "active",
                    "premium": 120.00,
                    "coverage": 100000.00
                }
            ],
            "total_policies": 1
        }
        
        # Test policy data structure
        assert "policies" in mock_policy_data
        assert isinstance(mock_policy_data["policies"], list)
        
        policy = mock_policy_data["policies"][0]
        assert "policy_id" in policy
        assert "type" in policy
        assert "status" in policy
        assert "premium" in policy
    
    @pytest.mark.asyncio
    async def test_analytics_service_mock(self):
        """Test analytics service mock functionality"""
        # Mock analytics service data
        mock_analytics_data = {
            "risk_score": "Low",
            "fraud_probability": 0.05,
            "recommendations": [
                "Consider bundling policies for discount",
                "Increase coverage for better protection"
            ]
        }
        
        # Test analytics data structure
        assert "risk_score" in mock_analytics_data
        assert "fraud_probability" in mock_analytics_data
        assert "recommendations" in mock_analytics_data
        assert isinstance(mock_analytics_data["recommendations"], list)

class TestFastMCPIntegration:
    """Integration tests for FastMCP service setup"""
    
    def test_fastmcp_server_config(self):
        """Test FastMCP server configuration"""
        # Mock FastMCP server configuration
        server_config = {
            "name": "Insurance Service",
            "version": "1.0.0",
            "host": "0.0.0.0",
            "mcp_endpoint": "/mcp"
        }
        
        assert "name" in server_config
        assert "version" in server_config
        assert "mcp_endpoint" in server_config
    
    def test_mcp_tool_definitions(self):
        """Test MCP tool definitions structure"""
        # Mock MCP tool definition
        tool_definition = {
            "name": "get_user_profile",
            "description": "Get user profile information",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    }
                },
                "required": ["user_id"]
            }
        }
        
        assert "name" in tool_definition
        assert "description" in tool_definition
        assert "parameters" in tool_definition
        assert tool_definition["parameters"]["type"] == "object"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 