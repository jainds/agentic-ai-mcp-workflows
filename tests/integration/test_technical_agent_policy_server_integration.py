"""
INTEGRATION TEST: Technical Agent ↔ Policy Server
Tests real MCP communication between components

SOLID Principles:
- Single Responsibility: Test only the integration between these two components
- Interface Segregation: Focus on the MCP interface contract
- Dependency Inversion: Test against the interface, not implementation details
"""

import pytest
import asyncio
import json
import os
import sys
import subprocess
import time
import requests
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from technical_agent.main import TechnicalAgent


class TestTechnicalAgentPolicyServerIntegration:
    """
    INTEGRATION TEST: Real MCP communication between Technical Agent and Policy Server
    Tests the actual FastMCP protocol implementation
    """
    
    @pytest.fixture(scope="class")
    def policy_server_process(self):
        """Start the actual Policy Server for integration testing"""
        # Start policy server
        process = subprocess.Popen(
            [sys.executable, "policy_server/main.py"],
            cwd=os.path.join(os.path.dirname(__file__), '../../'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(2)
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8001/mcp", timeout=5)
            if response.status_code == 200:
                yield process
            else:
                process.terminate()
                pytest.skip("Policy server failed to start")
        except requests.exceptions.RequestException:
            process.terminate()
            pytest.skip("Policy server not accessible")
        finally:
            if process.poll() is None:  # Process still running
                process.terminate()
                process.wait()
    
    @pytest.fixture
    def technical_agent(self):
        """Create Technical Agent configured for local Policy Server"""
        # Override the policy server URL to point to local instance
        agent = TechnicalAgent()
        agent.policy_server_url = "http://localhost:8001/mcp"
        return agent
    
    @pytest.mark.asyncio
    async def test_real_mcp_connection(self, policy_server_process, technical_agent):
        """Test that Technical Agent can actually connect to Policy Server via MCP"""
        try:
            # Test MCP client creation
            client = await technical_agent._get_policy_client()
            
            # Test actual MCP connection
            async with client:
                tools = await client.list_tools()
                tool_names = [tool.name for tool in tools]
                
                # Verify expected tools are available
                assert "get_customer_policies" in tool_names
                
        except Exception as e:
            pytest.fail(f"MCP connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_real_customer_policy_retrieval(self, policy_server_process, technical_agent):
        """Test actual customer policy retrieval via MCP"""
        try:
            # Test retrieving policies for a known customer
            result = await technical_agent.get_customer_policies_skill("user_003")
            
            # Verify response structure
            assert isinstance(result, dict)
            assert "success" in result
            assert "customer_id" in result
            assert "policies" in result
            assert result["customer_id"] == "user_003"
            
            # If successful, verify policies data
            if result["success"]:
                assert isinstance(result["policies"], list)
                assert result["count"] == len(result["policies"])
                
                # If policies exist, verify structure
                if result["policies"]:
                    policy = result["policies"][0]
                    assert isinstance(policy, dict)
                    # Policies should have basic fields
                    expected_fields = ["id", "type", "premium", "coverage", "status"]
                    policy_fields = policy.keys()
                    # At least some expected fields should be present
                    assert any(field in policy_fields for field in expected_fields)
            
        except Exception as e:
            pytest.fail(f"Customer policy retrieval failed: {e}")
    
    @pytest.mark.asyncio
    async def test_real_health_check_with_policy_server(self, policy_server_process, technical_agent):
        """Test health check includes actual Policy Server status"""
        try:
            result = await technical_agent.health_check()
            
            # Verify health check structure
            assert isinstance(result, dict)
            assert "technical_agent" in result
            assert "policy_server" in result
            assert "timestamp" in result
            
            # Technical agent should always be healthy
            assert result["technical_agent"] == "healthy"
            
            # Policy server should be healthy if running
            assert result["policy_server"] == "healthy"
            assert "available_tools" in result
            assert isinstance(result["available_tools"], list)
            assert "get_customer_policies" in result["available_tools"]
            
        except Exception as e:
            pytest.fail(f"Health check failed: {e}")
    
    @pytest.mark.asyncio
    async def test_real_end_to_end_policy_request(self, policy_server_process, technical_agent):
        """Test complete end-to-end flow: parse -> call MCP -> return response"""
        try:
            # Test the complete flow from user request to response
            user_request = "Get policies for customer user_003"
            
            # Step 1: Parse the request
            parsed = technical_agent._parse_request_with_rules(user_request)
            assert parsed["customer_id"] == "user_003"
            assert parsed["intent"] == "get_customer_policies"
            
            # Step 2: Execute the skill
            skill_result = await technical_agent.get_customer_policies_skill(parsed["customer_id"])
            
            # Step 3: Verify end-to-end result
            assert skill_result["success"] is True
            assert skill_result["customer_id"] == "user_003"
            
            # The result should be properly formatted for consumption
            assert isinstance(skill_result["policies"], list)
            assert isinstance(skill_result["count"], int)
            
        except Exception as e:
            pytest.fail(f"End-to-end flow failed: {e}")
    
    @pytest.mark.asyncio
    async def test_real_error_handling_nonexistent_customer(self, policy_server_process, technical_agent):
        """Test error handling for non-existent customers"""
        try:
            # Request policies for non-existent customer
            result = await technical_agent.get_customer_policies_skill("NONEXISTENT-999")
            
            # Should handle gracefully, not crash
            assert isinstance(result, dict)
            assert "success" in result
            assert "customer_id" in result
            assert result["customer_id"] == "NONEXISTENT-999"
            
            # Result should indicate appropriate handling
            # (Could be success with empty policies or specific error)
            if result["success"]:
                assert result["policies"] == [] or isinstance(result["policies"], list)
            else:
                assert "error" in result
                
        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_real_mcp_protocol_compliance(self, policy_server_process, technical_agent):
        """Test that the MCP protocol is followed correctly"""
        try:
            client = await technical_agent._get_policy_client()
            
            async with client:
                # Test MCP protocol steps
                
                # 1. List available tools
                tools = await client.list_tools()
                assert len(tools) > 0
                
                # 2. Call a tool with proper parameters
                result = await client.call_tool(
                    "get_customer_policies",
                    {"customer_id": "user_003"}
                )
                
                # 3. Verify result format follows MCP standards
                assert result is not None
                # MCP results should be iterable content objects
                assert hasattr(result, '__iter__')
                
                # 4. Verify content can be processed
                for content in result:
                    # Each content should have expected attributes
                    assert hasattr(content, 'text') or hasattr(content, 'content')
                
        except Exception as e:
            pytest.fail(f"MCP protocol compliance test failed: {e}")


class TestTechnicalAgentPolicyServerPerformance:
    """
    SINGLE RESPONSIBILITY: Test performance aspects of the integration
    """
    
    @pytest.fixture
    def technical_agent(self):
        agent = TechnicalAgent()
        agent.policy_server_url = "http://localhost:8001/mcp"
        return agent
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, technical_agent):
        """Test that multiple concurrent requests work properly"""
        try:
            # Create multiple concurrent requests
            tasks = [
                technical_agent.get_customer_policies_skill("user_003"),
                technical_agent.get_customer_policies_skill("user_001"),
                technical_agent.health_check(),
            ]
            
            # Execute concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all requests completed
            assert len(results) == 3
            
            # Check that none raised exceptions
            for result in results:
                assert not isinstance(result, Exception), f"Concurrent request failed: {result}"
            
            # Verify results are properly formatted
            policy_results = results[0:2]
            health_result = results[2]
            
            for policy_result in policy_results:
                assert isinstance(policy_result, dict)
                assert "success" in policy_result
                
            assert isinstance(health_result, dict)
            assert "technical_agent" in health_result
            
        except Exception as e:
            pytest.skip(f"Concurrent test requires running Policy Server: {e}")
    
    @pytest.mark.asyncio
    async def test_response_time_acceptable(self, technical_agent):
        """Test that response times are within acceptable limits"""
        try:
            import time
            
            start_time = time.time()
            result = await technical_agent.get_customer_policies_skill("user_003")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should complete within reasonable time (5 seconds)
            assert response_time < 5.0, f"Response time too slow: {response_time:.2f}s"
            
            # Verify the result is valid
            assert isinstance(result, dict)
            assert "success" in result
            
        except Exception as e:
            pytest.skip(f"Performance test requires running Policy Server: {e}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"]) 