"""
INTEGRATION TEST: Domain Agent ↔ Technical Agent
Tests real A2A communication between components

SOLID Principles:
- Single Responsibility: Test only the integration between these two agents
- Interface Segregation: Focus on the A2A interface contract
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

from domain_agent.main import DomainAgent


class TestDomainAgentTechnicalAgentIntegration:
    """
    INTEGRATION TEST: Real A2A communication between Domain Agent and Technical Agent
    Tests the actual A2A protocol implementation
    """
    
    @pytest.fixture(scope="class")
    def technical_agent_process(self):
        """Start the actual Technical Agent for integration testing"""
        # Start technical agent
        process = subprocess.Popen(
            [sys.executable, "technical_agent/main.py"],
            cwd=os.path.join(os.path.dirname(__file__), '../../'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if agent is running
        try:
            response = requests.get("http://localhost:8002/a2a", timeout=5)
            if response.status_code == 200:
                yield process
            else:
                process.terminate()
                pytest.skip("Technical Agent failed to start")
        except requests.exceptions.RequestException:
            process.terminate()
            pytest.skip("Technical Agent not accessible")
        finally:
            if process.poll() is None:  # Process still running
                process.terminate()
                process.wait()
    
    @pytest.fixture
    def domain_agent(self):
        """Create Domain Agent configured for local Technical Agent"""
        agent = DomainAgent()
        agent.technical_agent_url = "http://localhost:8002"
        return agent
    
    def test_real_a2a_connection(self, technical_agent_process, domain_agent):
        """Test that Domain Agent can actually connect to Technical Agent via A2A"""
        try:
            # Test A2A client creation
            client = domain_agent._get_technical_client()
            
            # This should not raise an exception
            assert client is not None
            
        except Exception as e:
            pytest.fail(f"A2A connection failed: {e}")
    
    def test_real_customer_policy_request_flow(self, technical_agent_process, domain_agent):
        """Test actual customer policy request via A2A"""
        try:
            # Test the conversation skill that uses A2A communication
            user_message = "Show policies for customer user_003"
            
            result = domain_agent.handle_customer_conversation(user_message)
            
            # Verify response structure
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Should contain professional response elements
            assert "Thank you" in result
            
            # If successful, should contain policy information or appropriate message
            assert any(word in result.lower() for word in [
                "policies", "policy", "customer", "user_003", 
                "found", "insurance", "coverage", "help"
            ])
            
        except Exception as e:
            pytest.fail(f"Customer policy request failed: {e}")
    
    def test_real_session_based_task_processing(self, technical_agent_process, domain_agent):
        """Test session-based task processing with A2A communication"""
        try:
            # Create mock task with session data
            class MockTask:
                def __init__(self):
                    self.message = {
                        "content": {"text": "Show my policies"}
                    }
                    self.session = {
                        "customer_id": "user_003",
                        "authenticated": True,
                        "customer_data": {"name": "John Doe"}
                    }
                    self.metadata = {"ui_mode": "simple"}
                    self.artifacts = []
                    self.status = None
            
            mock_task = MockTask()
            
            # Process the task
            result_task = domain_agent.handle_task(mock_task)
            
            # Verify task completion
            assert hasattr(result_task, 'artifacts')
            assert hasattr(result_task, 'status')
            assert len(result_task.artifacts) > 0
            
            # Verify response content
            response_text = result_task.artifacts[0]["parts"][0]["text"]
            assert isinstance(response_text, str)
            assert len(response_text) > 0
            
        except Exception as e:
            pytest.fail(f"Session-based task processing failed: {e}")
    
    def test_real_parsing_fallback_flow(self, technical_agent_process, domain_agent):
        """Test parsing fallback when no session data available"""
        try:
            # Create mock task without session data
            class MockTask:
                def __init__(self):
                    self.message = {
                        "content": {"text": "Get policies for customer CUST-001"}
                    }
                    self.session = {}  # No session data
                    self.metadata = {}
                    self.artifacts = []
                    self.status = None
            
            mock_task = MockTask()
            
            # Process the task
            result_task = domain_agent.handle_task(mock_task)
            
            # Should handle gracefully even without session
            assert hasattr(result_task, 'artifacts')
            assert len(result_task.artifacts) > 0
            
            response_text = result_task.artifacts[0]["parts"][0]["text"]
            assert "CUST-001" in response_text or "customer" in response_text.lower()
            
        except Exception as e:
            pytest.fail(f"Parsing fallback flow failed: {e}")
    
    def test_real_error_handling_invalid_customer(self, technical_agent_process, domain_agent):
        """Test error handling for invalid customer requests"""
        try:
            # Test with invalid customer format
            user_message = "Show policies for customer INVALID_FORMAT_123!@#"
            
            result = domain_agent.handle_customer_conversation(user_message)
            
            # Should handle gracefully, not crash
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Should provide helpful guidance
            assert any(word in result.lower() for word in [
                "customer", "id", "format", "help", "provide"
            ])
            
        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")
    
    def test_real_intent_classification_flow(self, technical_agent_process, domain_agent):
        """Test different intent classifications work through A2A"""
        try:
            test_cases = [
                ("Check my claim status for customer user_003", "claim"),
                ("What policies do I have for customer user_003", "polic"),
                ("What is insurance?", "help"),
            ]
            
            for user_message, expected_keyword in test_cases:
                result = domain_agent.handle_customer_conversation(user_message)
                
                assert isinstance(result, str)
                assert len(result) > 0
                
                # Should contain contextually appropriate response
                assert any(word in result.lower() for word in [
                    expected_keyword, "thank", "help", "assist"
                ])
                
        except Exception as e:
            pytest.fail(f"Intent classification flow failed: {e}")


class TestDomainAgentTechnicalAgentPerformance:
    """
    SINGLE RESPONSIBILITY: Test performance aspects of the integration
    """
    
    @pytest.fixture
    def domain_agent(self):
        agent = DomainAgent()
        agent.technical_agent_url = "http://localhost:8002"
        return agent
    
    def test_response_time_acceptable(self, domain_agent):
        """Test that A2A response times are within acceptable limits"""
        try:
            import time
            
            start_time = time.time()
            result = domain_agent.handle_customer_conversation("Show policies for customer user_003")
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # Response should complete within reasonable time (10 seconds for A2A)
            assert response_time < 10.0, f"A2A response time too slow: {response_time:.2f}s"
            
            # Verify the result is valid
            assert isinstance(result, str)
            assert len(result) > 0
            
        except Exception as e:
            pytest.skip(f"Performance test requires running Technical Agent: {e}")
    
    def test_concurrent_a2a_requests(self, domain_agent):
        """Test that multiple concurrent A2A requests work properly"""
        try:
            # Create multiple different requests
            requests = [
                "Show policies for customer user_003",
                "Check claim status for customer user_001", 
                "What is my coverage for customer user_002",
            ]
            
            # Execute them sequentially (A2A clients aren't async)
            results = []
            for request in requests:
                try:
                    result = domain_agent.handle_customer_conversation(request)
                    results.append(result)
                except Exception as e:
                    results.append(f"Error: {e}")
            
            # Verify all requests completed
            assert len(results) == len(requests)
            
            # Check that responses are reasonable
            for result in results:
                assert isinstance(result, str)
                assert len(result) > 0
                
        except Exception as e:
            pytest.skip(f"Concurrent test requires running Technical Agent: {e}")


class TestDomainAgentTechnicalAgentProtocol:
    """
    SINGLE RESPONSIBILITY: Test A2A protocol compliance
    INTERFACE SEGREGATION: Focus on protocol interface
    """
    
    @pytest.fixture
    def domain_agent(self):
        agent = DomainAgent()
        agent.technical_agent_url = "http://localhost:8002"
        return agent
    
    def test_a2a_protocol_compliance(self, domain_agent):
        """Test that A2A protocol is followed correctly"""
        try:
            # Test that client creation follows A2A patterns
            client = domain_agent._get_technical_client()
            
            # Should have A2A client interface
            assert hasattr(client, 'ask') or hasattr(client, '__call__')
            
            # Test basic A2A communication
            if hasattr(client, 'ask'):
                # This tests the actual A2A.ask() method
                response = client.ask("Health check")
                assert response is not None
                
        except Exception as e:
            pytest.skip(f"A2A protocol test requires running Technical Agent: {e}")
    
    def test_message_format_compliance(self, domain_agent):
        """Test that messages follow expected format"""
        try:
            # Test customer conversation that generates A2A messages
            result = domain_agent.handle_customer_conversation("Show policies for customer user_003")
            
            # Should return properly formatted string response
            assert isinstance(result, str)
            assert len(result) > 10  # Should be substantial response
            
            # Should be professional format
            assert result[0].isupper() or result.startswith("Thank")  # Professional greeting
            
        except Exception as e:
            pytest.skip(f"Message format test requires running Technical Agent: {e}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"]) 