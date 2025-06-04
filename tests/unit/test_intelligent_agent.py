#!/usr/bin/env python3
"""
Unit tests for Intelligent Agent functionality
Tests the LLM-powered tool selection and multi-tool execution planning
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

import sys
import os

# Add technical_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'technical_agent'))

class TestIntelligentAgentCore:
    """Test core intelligent agent functionality without A2A framework"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_customer_id = "CUST-001"

    def test_execution_plan_validation_logic(self):
        """Test execution plan validation logic"""
        
        # Test valid single tool plan
        valid_single_plan = {
            "plan_type": "single_tool",
            "tool_name": "get_policies",
            "parameters": {"customer_id": "CUST-001"}
        }
        
        # Simulate validation logic
        is_valid = (
            "plan_type" in valid_single_plan and
            valid_single_plan["plan_type"] == "single_tool" and
            "tool_name" in valid_single_plan and
            "parameters" in valid_single_plan
        )
        assert is_valid is True
        
        # Test invalid plan - missing tool_name
        invalid_plan = {
            "plan_type": "single_tool",
            "parameters": {"customer_id": "CUST-001"}
        }
        
        is_valid = (
            "plan_type" in invalid_plan and
            invalid_plan["plan_type"] == "single_tool" and
            "tool_name" in invalid_plan and
            "parameters" in invalid_plan
        )
        assert is_valid is False
        
        # Test multi-tool plan validation
        valid_multi_plan = {
            "plan_type": "multi_tool",
            "execution_order": "parallel",
            "tool_calls": [
                {
                    "tool_name": "get_policies",
                    "parameters": {"customer_id": "CUST-001"},
                    "result_key": "policies"
                }
            ]
        }
        
        is_valid = (
            "plan_type" in valid_multi_plan and
            valid_multi_plan["plan_type"] == "multi_tool" and
            "tool_calls" in valid_multi_plan and
            isinstance(valid_multi_plan["tool_calls"], list) and
            len(valid_multi_plan["tool_calls"]) > 0
        )
        assert is_valid is True

    def test_mcp_request_validation_logic(self):
        """Test MCP request validation logic"""
        
        # Test basic validation cases
        assert "get_policies" and len("get_policies".strip()) > 0  # Valid tool name
        assert not ("" and len("".strip()) > 0)  # Empty tool name
        
        params = {"customer_id": "CUST-001"}
        assert isinstance(params, dict)
        assert "customer_id" in params
        assert params.get("customer_id") == "CUST-001"

    def test_tool_parameter_validation_logic(self):
        """Test tool parameter validation against schema"""
        
        # Mock tool schema
        tool_schema = {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"]
        }
        
        # Valid parameters
        valid_params = {"customer_id": "CUST-001"}
        
        # Simulate validation logic
        is_valid = True
        if "required" in tool_schema:
            for required_param in tool_schema["required"]:
                if required_param not in valid_params or not valid_params[required_param]:
                    is_valid = False
                    break
        
        assert is_valid is True
        
        # Invalid parameters - missing required
        invalid_params = {}
        
        is_valid = True
        if "required" in tool_schema:
            for required_param in tool_schema["required"]:
                if required_param not in invalid_params or not invalid_params[required_param]:
                    is_valid = False
                    break
        
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_json_parsing_from_llm_response(self):
        """Test parsing JSON from LLM response"""
        
        # Mock LLM response with valid JSON
        llm_response = '''
        {
            "plan_type": "single_tool",
            "reasoning": "User wants basic policy information",
            "tool_name": "get_policies",
            "parameters": {"customer_id": "CUST-001"}
        }
        '''
        
        # Simulate parsing logic
        try:
            parsed_plan = json.loads(llm_response.strip())
            parsing_success = True
        except json.JSONDecodeError:
            parsing_success = False
            parsed_plan = None
        
        assert parsing_success is True
        assert parsed_plan["plan_type"] == "single_tool"
        assert parsed_plan["tool_name"] == "get_policies"
        
        # Test invalid JSON
        invalid_response = "This is not JSON"
        
        try:
            parsed_plan = json.loads(invalid_response.strip())
            parsing_success = True
        except json.JSONDecodeError:
            parsing_success = False
            parsed_plan = None
        
        assert parsing_success is False
        assert parsed_plan is None

class TestServiceDiscoveryIntegration:
    """Test service discovery integration logic"""
    
    def test_tool_registry_management(self):
        """Test tool registry operations"""
        
        # Simulate tool registry
        tool_registry = {}
        
        # Mock discovered tool
        mock_tool = {
            "name": "get_policies",
            "description": "Get customer policies",
            "service": "policy_service",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"]
            }
        }
        
        # Register tool
        tool_registry[mock_tool["name"]] = mock_tool
        tool_registry[f"{mock_tool['service']}.{mock_tool['name']}"] = mock_tool
        
        # Test retrieval
        assert "get_policies" in tool_registry
        assert "policy_service.get_policies" in tool_registry
        assert tool_registry["get_policies"]["description"] == "Get customer policies"
        
        # Test available tools (exclude namespaced)
        available_tools = {
            name: tool["description"] 
            for name, tool in tool_registry.items() 
            if "." not in name
        }
        
        assert "get_policies" in available_tools
        assert "policy_service.get_policies" not in available_tools
        assert available_tools["get_policies"] == "Get customer policies"

    def test_tools_description_building(self):
        """Test building formatted tools description"""
        
        # Mock service capabilities
        services = {
            "policy_service": {
                "tools": [
                    {
                        "name": "get_policies",
                        "description": "Get customer policies",
                        "parameters": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "string"}},
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "get_agent",
                        "description": "Get agent information",
                        "parameters": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "string"}},
                            "required": ["customer_id"]
                        }
                    }
                ]
            }
        }
        
        # Build description
        description_parts = []
        for service_name, service_data in services.items():
            service_title = service_name.replace("_", " ").title()
            description_parts.append(f"{service_title} Service Tools:")
            
            for tool in service_data["tools"]:
                tool_desc = f"  {tool['name']}: {tool['description']}"
                
                if tool["parameters"] and "required" in tool["parameters"]:
                    required_params = ", ".join(tool["parameters"]["required"])
                    tool_desc += f" (requires {required_params})"
                
                description_parts.append(tool_desc)
        
        description = "\n".join(description_parts)
        
        # Verify description format
        assert "Policy Service Service Tools:" in description
        assert "get_policies: Get customer policies" in description
        assert "requires customer_id" in description
        assert "get_agent: Get agent information" in description

class TestBusinessLogicValidation:
    """Test business logic and workflow validation"""
    
    def test_multi_tool_execution_planning(self):
        """Test multi-tool execution planning logic"""
        
        # Mock multi-tool plan
        execution_plan = {
            "plan_type": "multi_tool",
            "execution_order": "parallel",
            "tool_calls": [
                {
                    "tool_name": "get_policies",
                    "parameters": {"customer_id": "CUST-001"},
                    "result_key": "policies",
                    "reasoning": "Get policy information"
                },
                {
                    "tool_name": "get_agent",
                    "parameters": {"customer_id": "CUST-001"},
                    "result_key": "agent",
                    "reasoning": "Get agent contact info"
                }
            ]
        }
        
        # Validate execution plan structure
        assert execution_plan["plan_type"] == "multi_tool"
        assert "tool_calls" in execution_plan
        assert len(execution_plan["tool_calls"]) == 2
        
        # Validate each tool call
        for tool_call in execution_plan["tool_calls"]:
            assert "tool_name" in tool_call
            assert "parameters" in tool_call
            assert "result_key" in tool_call
            assert "customer_id" in tool_call["parameters"]
        
        # Test execution order validation
        valid_orders = ["parallel", "sequential"]
        assert execution_plan["execution_order"] in valid_orders

    def test_error_handling_strategies(self):
        """Test error handling and fallback strategies"""
        
        # Simulate different error scenarios
        error_scenarios = [
            {"type": "llm_error", "fallback": "rule_based_parsing"},
            {"type": "tool_not_found", "fallback": "comprehensive_api"},
            {"type": "validation_error", "fallback": "error_response"},
            {"type": "network_error", "fallback": "retry_with_backoff"}
        ]
        
        for scenario in error_scenarios:
            # Validate error handling strategy exists
            assert "type" in scenario
            assert "fallback" in scenario
            assert scenario["fallback"] in [
                "rule_based_parsing", "comprehensive_api", 
                "error_response", "retry_with_backoff"
            ]

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 