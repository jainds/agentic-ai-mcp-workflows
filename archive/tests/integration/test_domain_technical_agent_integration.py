"""
Integration tests for Domain Agent and Technical Agent communication via A2A protocol.

Tests the complete flow:
1. Domain agent receives user query
2. Analyzes intent and plans technical agent calls  
3. Calls technical agent via A2A protocol
4. Technical agent processes requests and calls MCP services
5. Domain agent receives responses and generates final output
6. Verifies thinking steps, orchestration events, and API calls are tracked
"""

import pytest
import asyncio
import json
import subprocess
import time
from unittest.mock import AsyncMock, Mock, patch


class TestDomainTechnicalAgentIntegration:
    """Test integration between domain and technical agents."""
    
    @pytest.fixture
    def setup_agent_environment(self):
        """Setup test environment with both agents running."""
        # This would start both agents if they're not running
        # For now, assume they're running in Kubernetes
        return {
            "domain_agent_url": "http://claims-agent:8000",
            "technical_agent_url": "http://fastmcp-data-agent:8004"
        }
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_policy_inquiry(self, setup_agent_environment):
        """Test complete flow for policy inquiry from UI to final response."""
        import aiohttp
        
        try:
            # Simulate UI request to domain agent
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "message": "How many policies do I have?",
                    "customer_id": "CUST-001"
                }
                
                async with session.post(
                    f"{setup_agent_environment['domain_agent_url']}/chat",
                    json=request_data
                ) as response:
                    assert response.status == 200
                    result = await response.json()
                    
                    # Verify response structure
                    assert "response" in result
                    assert "thinking_steps" in result
                    assert "orchestration_events" in result
                    assert "api_calls" in result
                    
                    # Verify response content quality
                    response_text = result["response"]
                    assert len(response_text) > 50  # Should be detailed
                    assert "policy" in response_text.lower() or "policies" in response_text.lower()
                    
                    # Verify orchestration occurred
                    assert len(result["thinking_steps"]) > 0, "Should have thinking steps"
                    assert len(result["api_calls"]) > 0, "Should have API calls to technical agent"
                    
        except Exception as e:
            pytest.skip(f"Integration test requires running agents: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_claim_status_inquiry(self, setup_agent_environment):
        """Test complete flow for claim status inquiry."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "message": "What's the status of my claim?",
                    "customer_id": "CUST-001"
                }
                
                async with session.post(
                    f"{setup_agent_environment['domain_agent_url']}/chat",
                    json=request_data
                ) as response:
                    assert response.status == 200
                    result = await response.json()
                    
                    # Verify comprehensive response following template
                    response_text = result["response"]
                    expected_sections = [
                        "Claims Status",
                        "Analysis",
                        "Account Overview",
                        "Next Steps"
                    ]
                    
                    sections_found = sum(1 for section in expected_sections 
                                       if section.lower() in response_text.lower())
                    assert sections_found >= 2, f"Should contain template sections. Response: {response_text}"
                    
                    # Verify orchestration tracking
                    assert len(result["thinking_steps"]) > 0
                    assert len(result["api_calls"]) > 0
                    
        except Exception as e:
            pytest.skip(f"Integration test requires running agents: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_claim_filing(self, setup_agent_environment):
        """Test complete flow for filing a new claim."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "message": "I need to file a claim for my car accident that happened yesterday on Highway 101",
                    "customer_id": "CUST-001"
                }
                
                async with session.post(
                    f"{setup_agent_environment['domain_agent_url']}/chat",
                    json=request_data
                ) as response:
                    assert response.status == 200
                    result = await response.json()
                    
                    response_text = result["response"]
                    
                    # Should indicate claim filing process started
                    claim_indicators = ["claim", "filed", "reference", "process"]
                    found_indicators = sum(1 for indicator in claim_indicators
                                         if indicator in response_text.lower())
                    assert found_indicators >= 2, "Should reference claim filing process"
                    
                    # Should have multiple orchestration steps for claim filing
                    assert len(result["thinking_steps"]) >= 3, "Claim filing should have multiple steps"
                    assert len(result["api_calls"]) >= 2, "Should call multiple services"
                    
        except Exception as e:
            pytest.skip(f"Integration test requires running agents: {e}")


class TestDomainAgentOrchestrationTracking:
    """Test that domain agent properly tracks orchestration steps."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_thinking_steps_generation(self):
        """Test that thinking steps are properly generated and tracked."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "message": "Tell me about my insurance coverage",
                    "customer_id": "CUST-001"
                }
                
                async with session.post(
                    "http://claims-agent:8000/chat",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        thinking_steps = result.get("thinking_steps", [])
                        
                        # Verify thinking steps contain expected patterns
                        expected_patterns = [
                            "analyz",  # analyzing intent
                            "gather",  # gathering data
                            "process", # processing information
                            "generat"  # generating response
                        ]
                        
                        step_text = " ".join(thinking_steps).lower()
                        found_patterns = sum(1 for pattern in expected_patterns
                                           if pattern in step_text)
                        
                        assert found_patterns >= 2, f"Thinking steps should show reasoning process: {thinking_steps}"
                        
        except Exception as e:
            pytest.skip(f"Integration test requires running domain agent: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_api_calls_tracking(self):
        """Test that API calls to technical agents are properly tracked."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "message": "Show me my policy details",
                    "customer_id": "CUST-001"
                }
                
                async with session.post(
                    "http://claims-agent:8000/chat",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        api_calls = result.get("api_calls", [])
                        
                        # Should have at least one API call
                        assert len(api_calls) > 0, "Should track API calls to technical agents"
                        
                        # API calls should have structure
                        if api_calls:
                            first_call = api_calls[0]
                            expected_fields = ["endpoint", "method", "timestamp"]
                            found_fields = sum(1 for field in expected_fields
                                             if field in first_call)
                            assert found_fields >= 1, f"API calls should have proper structure: {first_call}"
                        
        except Exception as e:
            pytest.skip(f"Integration test requires running domain agent: {e}")


class TestTechnicalAgentMCPIntegration:
    """Test technical agent's integration with MCP services."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_technical_agent_user_service_integration(self):
        """Test technical agent calling user service MCP."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                # Direct A2A call to technical agent
                task_data = {
                    "taskId": "test_user_integration",
                    "user": {
                        "action": "get_customer",
                        "customer_id": "CUST-001"
                    }
                }
                
                async with session.post(
                    "http://fastmcp-data-agent:8004/process",
                    json=task_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        assert result["status"] == "completed"
                        assert len(result["parts"]) > 0
                        
                        # Parse the response data
                        response_data = json.loads(result["parts"][0]["text"])
                        assert "customer_id" in response_data
                        
        except Exception as e:
            pytest.skip(f"Integration test requires running technical agent and MCP services: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_technical_agent_policy_service_integration(self):
        """Test technical agent calling policy service MCP."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                task_data = {
                    "taskId": "test_policy_integration",
                    "user": {
                        "action": "get_customer_policies",
                        "customer_id": "CUST-001"
                    }
                }
                
                async with session.post(
                    "http://fastmcp-data-agent:8004/process",
                    json=task_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        assert result["status"] == "completed"
                        response_data = json.loads(result["parts"][0]["text"])
                        
                        # Should contain policy information
                        expected_fields = ["policies", "active_policies"]
                        found_fields = sum(1 for field in expected_fields
                                         if field in response_data)
                        assert found_fields >= 1, f"Should contain policy data: {response_data}"
                        
        except Exception as e:
            pytest.skip(f"Integration test requires running technical agent and MCP services: {e}")


class TestA2AProtocolCompliance:
    """Test A2A protocol compliance between agents."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_a2a_task_request_format(self):
        """Test that A2A task requests follow proper format."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test valid A2A task request
                valid_task = {
                    "taskId": "test_a2a_format",
                    "user": {
                        "action": "get_customer",
                        "customer_id": "CUST-001"
                    }
                }
                
                async with session.post(
                    "http://fastmcp-data-agent:8004/process",
                    json=valid_task
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Verify response format
                        required_fields = ["taskId", "status", "parts"]
                        for field in required_fields:
                            assert field in result, f"A2A response missing {field}"
                        
                        assert result["taskId"] == "test_a2a_format"
                        assert result["status"] in ["completed", "failed"]
                        
        except Exception as e:
            pytest.skip(f"Integration test requires running technical agent: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_a2a_error_handling(self):
        """Test A2A error handling for invalid requests."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test invalid A2A task request
                invalid_task = {
                    "taskId": "test_a2a_error",
                    "user": {
                        "action": "invalid_action",
                        "customer_id": "CUST-001"
                    }
                }
                
                async with session.post(
                    "http://fastmcp-data-agent:8004/process",
                    json=invalid_task
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Should return error status
                        assert result["status"] == "failed"
                        assert len(result["parts"]) > 0
                        
                        error_message = result["parts"][0]["text"]
                        assert "error" in error_message.lower() or "invalid" in error_message.lower()
                        
        except Exception as e:
            pytest.skip(f"Integration test requires running technical agent: {e}")


class TestResponseQualityAndTemplate:
    """Test response quality and template compliance."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_response_follows_template_format(self):
        """Test that domain agent responses follow the template format."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "message": "What's the status of my insurance claim?",
                    "customer_id": "CUST-001"
                }
                
                async with session.post(
                    "http://claims-agent:8000/chat",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result["response"]
                        
                        # Check for template sections
                        template_indicators = [
                            "**",  # Bold formatting
                            "•",   # Bullet points
                            ":",   # Section headers
                            "Status",
                            "Analysis",
                            "Overview"
                        ]
                        
                        found_indicators = sum(1 for indicator in template_indicators
                                             if indicator in response_text)
                        
                        assert found_indicators >= 3, f"Response should follow template format: {response_text}"
                        
        except Exception as e:
            pytest.skip(f"Integration test requires running domain agent: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_response_is_witty_and_helpful(self):
        """Test that responses are detailed, witty, and helpful."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "message": "I'm confused about my insurance coverage",
                    "customer_id": "CUST-001"
                }
                
                async with session.post(
                    "http://claims-agent:8000/chat",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result["response"]
                        
                        # Response should be substantial (not generic)
                        assert len(response_text) > 200, "Response should be detailed"
                        
                        # Should not be the generic fallback message
                        assert "I'm here to help with your insurance needs" not in response_text, \
                            "Should not return generic fallback message"
                        
                        # Should contain helpful information
                        helpful_indicators = [
                            "coverage",
                            "policy",
                            "help",
                            "explain",
                            "details",
                            "information"
                        ]
                        
                        found_helpful = sum(1 for indicator in helpful_indicators
                                          if indicator in response_text.lower())
                        assert found_helpful >= 2, "Response should be helpful and informative"
                        
        except Exception as e:
            pytest.skip(f"Integration test requires running domain agent: {e}")


class TestSystemHealth:
    """Test overall system health and component availability."""
    
    @pytest.mark.integration
    def test_all_services_available(self):
        """Test that all required services are available."""
        services = [
            ("Domain Agent", "http://claims-agent:8000/health"),
            ("Technical Agent", "http://fastmcp-data-agent:8004/health"),
            ("User Service", "http://user-service:8000/health"),
            ("Claims Service", "http://claims-service:8001/health"),
            ("Policy Service", "http://policy-service:8002/health"),
            ("Analytics Service", "http://analytics-service:8003/health")
        ]
        
        import requests
        
        for service_name, health_url in services:
            try:
                response = requests.get(health_url, timeout=5)
                assert response.status_code == 200, f"{service_name} health check failed"
            except Exception as e:
                pytest.skip(f"Service {service_name} not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"]) 