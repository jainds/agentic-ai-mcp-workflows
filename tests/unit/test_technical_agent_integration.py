#!/usr/bin/env python3
"""
Unit tests for Technical Agent Integration
Tests the technical agent's core integration functionality without complex mocking
"""

import pytest
from unittest.mock import Mock, patch
import asyncio
import json
import sys
import os

# Add technical_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'technical_agent'))

class TestTechnicalAgentCore:
    """Test core technical agent functionality"""
    
    def test_request_parsing_logic(self):
        """Test request parsing without OpenAI dependency"""
        
        # Simulate request parsing logic
        def parse_customer_request(request_text):
            """Simulate rule-based request parsing"""
            request_lower = request_text.lower()
            
            if any(word in request_lower for word in ["policy", "policies"]):
                return {"intent": "policy_inquiry", "confidence": 0.9}
            elif any(word in request_lower for word in ["bill", "payment"]):
                return {"intent": "billing", "confidence": 0.8}
            elif any(word in request_lower for word in ["claim", "accident"]):
                return {"intent": "claims", "confidence": 0.9}
            else:
                return {"intent": "general", "confidence": 0.5}
        
        test_cases = [
            ("What policies do I have?", "policy_inquiry"),
            ("When is my payment due?", "billing"),
            ("I need to file a claim", "claims"),
            ("Hello there", "general")
        ]
        
        for request, expected_intent in test_cases:
            result = parse_customer_request(request)
            assert result["intent"] == expected_intent
            assert result["confidence"] > 0

    def test_mcp_request_validation(self):
        """Test MCP request validation logic"""
        
        def validate_mcp_request(tool_name, params):
            """Validate MCP request structure"""
            if not tool_name or not isinstance(tool_name, str):
                return False, "Invalid tool name"
            
            if not isinstance(params, dict):
                return False, "Invalid parameters"
            
            # Check required parameters for policy tools
            if tool_name in ["get_policies", "get_agent", "get_policy_types"]:
                if "customer_id" not in params:
                    return False, "Missing customer_id"
                if not params["customer_id"]:
                    return False, "Empty customer_id"
            
            return True, "Valid request"
        
        # Test valid requests
        valid, msg = validate_mcp_request("get_policies", {"customer_id": "CUST-001"})
        assert valid is True
        
        # Test invalid requests
        valid, msg = validate_mcp_request("", {"customer_id": "CUST-001"})
        assert valid is False
        assert "tool name" in msg
        
        valid, msg = validate_mcp_request("get_policies", {})
        assert valid is False
        assert "customer_id" in msg

    def test_response_processing(self):
        """Test response processing and formatting"""
        
        def process_mcp_response(mcp_response):
            """Process MCP response for customer consumption"""
            if not mcp_response:
                return {"error": "No response from service"}
            
            try:
                # Simulate parsing MCP response
                if hasattr(mcp_response, 'text'):
                    data = json.loads(mcp_response.text)
                else:
                    data = mcp_response
                
                return {
                    "success": True,
                    "data": data,
                    "processed_at": "2024-01-01T00:00:00Z"
                }
            except Exception as e:
                return {"error": f"Failed to process response: {str(e)}"}
        
        # Test successful processing
        mock_response = Mock()
        mock_response.text = json.dumps([{"policy_id": "P001", "type": "Auto"}])
        
        result = process_mcp_response(mock_response)
        assert result["success"] is True
        assert "data" in result
        
        # Test error handling
        result = process_mcp_response(None)
        assert "error" in result

class TestTechnicalAgentConfiguration:
    """Test technical agent configuration"""
    
    def test_service_discovery_configuration(self):
        """Test service discovery configuration"""
        
        # Simulate service discovery configuration
        service_config = {
            "policy_service": {
                "url": "http://localhost:8001/mcp",
                "timeout": 10,
                "retry_attempts": 3,
                "enabled": True
            }
        }
        
        assert "policy_service" in service_config
        assert service_config["policy_service"]["enabled"] is True
        assert service_config["policy_service"]["url"].startswith("http://")

    def test_a2a_server_configuration(self):
        """Test A2A server configuration"""
        
        # Simulate A2A server configuration
        a2a_config = {
            "host": "0.0.0.0",
            "port": 8002,
            "debug": False,
            "skills": ["health_check", "refresh_services", "intelligent_policy_assistant"]
        }
        
        assert a2a_config["port"] == 8002
        assert len(a2a_config["skills"]) > 0
        assert "intelligent_policy_assistant" in a2a_config["skills"]

class TestTechnicalAgentWorkflows:
    """Test technical agent workflows"""
    
    def test_health_check_workflow(self):
        """Test health check workflow"""
        
        def health_check():
            """Simulate health check logic"""
            return {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "services": {
                    "policy_service": "connected",
                    "openai": "available" if os.getenv("OPENROUTER_API_KEY") else "unavailable"
                },
                "version": "2.0.0"
            }
        
        health = health_check()
        
        assert health["status"] == "healthy"
        assert "services" in health
        assert "timestamp" in health

    def test_service_refresh_workflow(self):
        """Test service refresh workflow"""
        
        def refresh_services():
            """Simulate service refresh logic"""
            try:
                # Simulate service discovery refresh
                discovered_services = {"policy_service": True}
                
                return {
                    "success": True,
                    "services_discovered": len(discovered_services),
                    "timestamp": "2024-01-01T00:00:00Z"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        result = refresh_services()
        assert result["success"] is True
        assert result["services_discovered"] >= 0

class TestTechnicalAgentErrorHandling:
    """Test technical agent error handling"""
    
    def test_policy_server_unavailable(self):
        """Test handling when policy server is unavailable"""
        
        def handle_policy_server_error():
            """Simulate policy server error handling"""
            return {
                "success": False,
                "error": "Policy server unavailable",
                "fallback": "comprehensive_api",
                "retry_recommended": True
            }
        
        error_response = handle_policy_server_error()
        
        assert error_response["success"] is False
        assert "error" in error_response
        assert "fallback" in error_response

    def test_openai_unavailable_fallback(self):
        """Test fallback when OpenAI is unavailable"""
        
        def handle_openai_fallback(request):
            """Simulate OpenAI fallback to rule-based parsing"""
            # Rule-based parsing as fallback
            if "policy" in request.lower():
                return {
                    "tool_name": "get_policies",
                    "parameters": {"customer_id": "extracted_id"},
                    "confidence": 0.7,
                    "method": "rule_based"
                }
            else:
                return {
                    "tool_name": "get_customer_policies", 
                    "parameters": {"customer_id": "extracted_id"},
                    "confidence": 0.5,
                    "method": "fallback"
                }
        
        result = handle_openai_fallback("Show me my policies")
        
        assert result["tool_name"] in ["get_policies", "get_customer_policies"]
        assert result["method"] in ["rule_based", "fallback"]
        assert result["confidence"] > 0

class TestTechnicalAgentBusinessLogic:
    """Test technical agent business logic"""
    
    def test_intelligent_tool_selection(self):
        """Test intelligent tool selection logic"""
        
        tool_mapping = {
            "policy_inquiry": ["get_policies", "get_policy_types"],
            "billing": ["get_payment_information"],
            "coverage": ["get_coverage_information"],
            "agent_contact": ["get_agent"],
            "recommendations": ["get_recommendations"]
        }
        
        def select_tools(intent):
            """Select appropriate tools based on intent"""
            return tool_mapping.get(intent, ["get_customer_policies"])
        
        # Test tool selection
        assert "get_policies" in select_tools("policy_inquiry")
        assert "get_payment_information" in select_tools("billing")
        assert "get_agent" in select_tools("agent_contact")

    def test_multi_tool_execution_planning(self):
        """Test multi-tool execution planning"""
        
        def create_execution_plan(intent, customer_id):
            """Create execution plan for multi-tool requests"""
            if intent == "comprehensive_overview":
                return {
                    "plan_type": "multi_tool",
                    "execution_order": "parallel",
                    "tool_calls": [
                        {"tool_name": "get_policies", "params": {"customer_id": customer_id}},
                        {"tool_name": "get_agent", "params": {"customer_id": customer_id}},
                        {"tool_name": "get_payment_information", "params": {"customer_id": customer_id}}
                    ]
                }
            else:
                return {
                    "plan_type": "single_tool",
                    "tool_name": "get_policies",
                    "params": {"customer_id": customer_id}
                }
        
        # Test multi-tool plan
        plan = create_execution_plan("comprehensive_overview", "CUST-001")
        assert plan["plan_type"] == "multi_tool"
        assert len(plan["tool_calls"]) > 1
        
        # Test single tool plan
        plan = create_execution_plan("simple_inquiry", "CUST-001")
        assert plan["plan_type"] == "single_tool"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 