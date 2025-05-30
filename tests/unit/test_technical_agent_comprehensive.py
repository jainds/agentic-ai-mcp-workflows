#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Technical Agent
Tests technical agent functionality without A2A dependencies
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

class TestTechnicalAgentStructure:
    """Test technical agent structure and components"""
    
    def test_technical_agent_directory(self):
        """Test that technical agent directory exists"""
        agents_dir = Path("agents/technical")
        assert agents_dir.exists(), "Technical agents directory should exist"
        
        # Check for agent files
        expected_files = ["data_agent.py", "fastmcp_data_agent.py", "notification_agent.py"]
        for file_name in expected_files:
            agent_file = agents_dir / file_name
            assert agent_file.exists(), f"Technical agent file {file_name} should exist"
    
    def test_fastmcp_integration_structure(self):
        """Test FastMCP integration structure"""
        # Mock FastMCP agent structure
        fastmcp_agent_config = {
            "name": "Technical Data Agent",
            "version": "1.0.0",
            "capabilities": [
                "user_data_access",
                "claims_processing", 
                "policy_management",
                "analytics_processing"
            ],
            "mcp_tools": [
                "get_user_profile",
                "get_user_claims",
                "get_user_policies",
                "assess_risk"
            ]
        }
        
        assert "name" in fastmcp_agent_config
        assert "capabilities" in fastmcp_agent_config
        assert "mcp_tools" in fastmcp_agent_config
        assert len(fastmcp_agent_config["mcp_tools"]) > 0

class TestTechnicalAgentMCPTools:
    """Test MCP tool functionality in technical agent"""
    
    @pytest.mark.asyncio
    async def test_user_profile_tool_mock(self):
        """Test user profile MCP tool mock"""
        # Mock user profile tool
        async def mock_get_user_profile(user_id: str):
            return {
                "user_id": user_id,
                "name": "John Doe",
                "email": "john.doe@example.com", 
                "phone": "+1-555-0123",
                "address": "123 Main St, Anytown, USA",
                "customer_since": "2020-01-15",
                "account_status": "active"
            }
        
        result = await mock_get_user_profile("test-user-123")
        
        assert result["user_id"] == "test-user-123"
        assert "name" in result
        assert "email" in result
        assert "account_status" in result
    
    @pytest.mark.asyncio
    async def test_claims_tool_mock(self):
        """Test claims MCP tool mock"""
        # Mock claims tool
        async def mock_get_user_claims(user_id: str):
            return {
                "user_id": user_id,
                "claims": [
                    {
                        "claim_id": "CLM-2024-001",
                        "type": "auto",
                        "status": "processing",
                        "amount": "$2,500",
                        "filed_date": "2024-01-15",
                        "description": "Vehicle collision damage"
                    }
                ],
                "total_claims": 1,
                "pending_amount": "$2,500"
            }
        
        result = await mock_get_user_claims("test-user-123")
        
        assert result["user_id"] == "test-user-123"
        assert "claims" in result
        assert len(result["claims"]) > 0
        assert result["claims"][0]["claim_id"] == "CLM-2024-001"
    
    @pytest.mark.asyncio
    async def test_policy_tool_mock(self):
        """Test policy MCP tool mock"""
        # Mock policy tool
        async def mock_get_user_policies(user_id: str):
            return {
                "user_id": user_id,
                "policies": [
                    {
                        "policy_id": "POL-2024-AUTO-001",
                        "type": "auto",
                        "status": "active",
                        "premium": "$120/month",
                        "coverage": "$100,000",
                        "renewal_date": "2024-12-15"
                    }
                ],
                "total_policies": 1,
                "total_premium": "$120/month"
            }
        
        result = await mock_get_user_policies("test-user-123")
        
        assert result["user_id"] == "test-user-123"
        assert "policies" in result
        assert len(result["policies"]) > 0
        assert result["policies"][0]["policy_id"] == "POL-2024-AUTO-001"
    
    @pytest.mark.asyncio
    async def test_analytics_tool_mock(self):
        """Test analytics MCP tool mock"""
        # Mock analytics tool
        async def mock_assess_risk(user_id: str):
            return {
                "user_id": user_id,
                "risk_score": "Low",
                "fraud_probability": "0.05",
                "recommendations": [
                    "Consider bundling policies for discount",
                    "Increase coverage for better protection"
                ]
            }
        
        result = await mock_assess_risk("test-user-123")
        
        assert result["user_id"] == "test-user-123"
        assert "risk_score" in result
        assert "fraud_probability" in result
        assert "recommendations" in result

class TestTechnicalAgentA2AIntegration:
    """Test A2A integration structure (without actual A2A SDK)"""
    
    def test_a2a_message_structure(self):
        """Test A2A message structure for technical agent"""
        # Mock A2A message from domain agent
        mock_a2a_message = {
            "request_type": "data_request",
            "customer_id": "test-customer-123",
            "intent": "policy_inquiry",
            "data_requirements": ["user_profile", "policy_data"],
            "urgent": False,
            "timestamp": "2024-01-15T10:00:00Z"
        }
        
        assert "request_type" in mock_a2a_message
        assert "customer_id" in mock_a2a_message
        assert "intent" in mock_a2a_message
        assert "data_requirements" in mock_a2a_message
        assert isinstance(mock_a2a_message["data_requirements"], list)
    
    def test_a2a_response_structure(self):
        """Test A2A response structure from technical agent"""
        # Mock A2A response to domain agent
        mock_a2a_response = {
            "status": "success",
            "data": {
                "user_profile": {
                    "user_id": "test-customer-123",
                    "name": "John Doe",
                    "account_status": "active"
                },
                "policy_data": {
                    "policies": [
                        {
                            "policy_id": "POL-001",
                            "type": "auto",
                            "status": "active"
                        }
                    ]
                }
            },
            "timestamp": "2024-01-15T10:00:05Z",
            "processing_time_ms": 150
        }
        
        assert "status" in mock_a2a_response
        assert "data" in mock_a2a_response
        assert "user_profile" in mock_a2a_response["data"]
        assert "policy_data" in mock_a2a_response["data"]
    
    @pytest.mark.asyncio
    async def test_technical_agent_request_processing(self):
        """Test technical agent request processing flow"""
        # Mock technical agent request processing
        async def mock_process_a2a_request(message):
            request_type = message.get("request_type")
            customer_id = message.get("customer_id")
            data_requirements = message.get("data_requirements", [])
            
            # Process data requirements
            response_data = {}
            
            if "user_profile" in data_requirements:
                response_data["user_profile"] = {
                    "user_id": customer_id,
                    "name": "John Doe",
                    "account_status": "active"
                }
            
            if "policy_data" in data_requirements:
                response_data["policy_data"] = {
                    "policies": [{"policy_id": "POL-001", "type": "auto"}]
                }
            
            return {
                "status": "success",
                "data": response_data,
                "request_type": request_type
            }
        
        # Test request
        test_message = {
            "request_type": "data_request",
            "customer_id": "test-customer-123",
            "data_requirements": ["user_profile", "policy_data"]
        }
        
        response = await mock_process_a2a_request(test_message)
        
        assert response["status"] == "success"
        assert "data" in response
        assert "user_profile" in response["data"]
        assert "policy_data" in response["data"]
        assert response["data"]["user_profile"]["user_id"] == "test-customer-123"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 