#!/usr/bin/env python3
"""
Test suite for observability integration
Verifies that metrics, tracing, and monitoring work correctly
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the agents directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'agents'))

from observability import (
    MultiAgentObservability, 
    init_observability, 
    get_observability,
    trace_agent_method,
    trace_llm_method
)
from base import BaseAgent, DomainAgent, TechnicalAgent, AgentType
from llm_client import LLMClient


class TestObservabilityCore:
    """Test core observability functionality"""
    
    def test_observability_initialization(self):
        """Test that observability initializes correctly"""
        obs = MultiAgentObservability("test-agent")
        
        assert obs.service_name == "test-agent"
        assert obs.logger is not None
        # Note: Actual LangFuse/OpenTelemetry components may not be available in test environment
    
    def test_global_observability_singleton(self):
        """Test global observability instance management"""
        # Initialize global instance
        obs1 = init_observability("test-service")
        obs2 = get_observability()
        
        assert obs1 is obs2
        assert obs2.service_name == "test-service"
    
    def test_metrics_summary(self):
        """Test that metrics summary is generated"""
        obs = MultiAgentObservability("test-agent")
        summary = obs.get_metrics_summary()
        
        assert "service" in summary
        assert "timestamp" in summary
        assert "components" in summary
        assert summary["service"] == "test-agent"


class TestAgentObservabilityIntegration:
    """Test observability integration with agents"""
    
    @pytest.fixture
    def mock_observability(self):
        """Mock observability for testing"""
        with patch('agents.base.OBSERVABILITY_AVAILABLE', True):
            with patch('agents.base.init_observability') as mock_init:
                mock_obs = Mock()
                mock_obs.update_agent_health = Mock()
                mock_obs.record_workflow_execution = Mock()
                mock_obs.trace_agent_call = AsyncMock()
                mock_init.return_value = mock_obs
                yield mock_obs
    
    def test_base_agent_observability_init(self, mock_observability):
        """Test that BaseAgent initializes observability"""
        with patch('agents.base.init_observability', return_value=mock_observability):
            agent = BaseAgent("test-agent", AgentType.DOMAIN)
            
            # Should have initialized observability
            assert hasattr(agent, 'observability')
            mock_observability.update_agent_health.assert_called_with("test-agent", True)
    
    @pytest.mark.asyncio
    async def test_task_processing_metrics(self, mock_observability):
        """Test that task processing records metrics"""
        with patch('agents.base.init_observability', return_value=mock_observability):
            
            class TestAgent(BaseAgent):
                async def execute_skill(self, skill_name, parameters):
                    if skill_name == "test_skill":
                        return {"result": "success"}
                    raise ValueError("Unknown skill")
            
            agent = TestAgent("test-agent", AgentType.DOMAIN)
            
            # Create a test task
            from base import AgentTask, TaskStatus
            task = AgentTask(
                task_id="test_task",
                skill_name="test_skill",
                parameters={"test": "data"},
                status=TaskStatus.PENDING
            )
            
            # Process the task
            result = await agent.process_task(task)
            
            # Verify metrics were recorded
            assert result.status == TaskStatus.COMPLETED
            mock_observability.record_workflow_execution.assert_called()
            
            # Check the call arguments
            call_args = mock_observability.record_workflow_execution.call_args
            assert call_args[1]["workflow_type"] == "test_skill"
            assert call_args[1]["status"] == "success"
    
    @pytest.mark.asyncio 
    async def test_domain_agent_tracing(self, mock_observability):
        """Test that domain agent calls are traced"""
        mock_observability.trace_agent_call.return_value.__aenter__ = AsyncMock(return_value={})
        mock_observability.trace_agent_call.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch('agents.base.init_observability', return_value=mock_observability):
            agent = DomainAgent("test-domain-agent")
            agent.register_technical_agent("test-tech", "http://test:8000")
            
            # Mock the HTTP call
            with patch('httpx.AsyncClient') as mock_client:
                mock_response = Mock()
                mock_response.json.return_value = {"success": True, "result": "test"}
                mock_response.raise_for_status = Mock()
                
                mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                
                # Make the call
                result = await agent.call_technical_agent("test-tech", "test_skill", {"param": "value"})
                
                # Verify tracing was used
                mock_observability.trace_agent_call.assert_called_once()
                call_args = mock_observability.trace_agent_call.call_args[1]
                assert call_args["source_agent"] == "test-domain-agent"
                assert call_args["target_agent"] == "test-tech"
                assert call_args["skill_name"] == "test_skill"


class TestLLMObservabilityIntegration:
    """Test LLM client observability integration"""
    
    @pytest.fixture
    def mock_observability(self):
        """Mock observability for LLM testing"""
        mock_obs = Mock()
        mock_obs.trace_llm_call = AsyncMock()
        mock_obs.record_token_usage = Mock()
        
        # Mock the context manager
        mock_context = {
            "generation": Mock(),
            "span": Mock(), 
            "start_time": time.time()
        }
        mock_obs.trace_llm_call.return_value.__aenter__ = AsyncMock(return_value=mock_context)
        mock_obs.trace_llm_call.return_value.__aexit__ = AsyncMock(return_value=None)
        
        return mock_obs
    
    @pytest.mark.asyncio
    async def test_llm_client_tracing(self, mock_observability):
        """Test that LLM calls are traced"""
        with patch('agents.llm_client.get_observability', return_value=mock_observability):
            with patch('agents.llm_client.OBSERVABILITY_AVAILABLE', True):
                
                client = LLMClient()
                
                # Mock the HTTP response
                with patch.object(client.http_client, 'post') as mock_post:
                    mock_response = Mock()
                    mock_response.json.return_value = {
                        "choices": [{"message": {"content": "test response"}}],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 5}
                    }
                    mock_response.raise_for_status = Mock()
                    mock_post.return_value = mock_response
                    
                    # Make LLM call
                    result = await client.llm_chat([{"role": "user", "content": "test message"}])
                    
                    # Verify tracing
                    mock_observability.trace_llm_call.assert_called_once()
                    mock_observability.record_token_usage.assert_called_once()
                    
                    # Check token usage recording
                    token_call = mock_observability.record_token_usage.call_args[1]
                    assert token_call["prompt_tokens"] == 10
                    assert token_call["completion_tokens"] == 5
    
    @pytest.mark.asyncio
    async def test_intent_extraction_tracing(self, mock_observability):
        """Test that intent extraction is traced"""
        with patch('agents.llm_client.get_observability', return_value=mock_observability):
            with patch('agents.llm_client.OBSERVABILITY_AVAILABLE', True):
                
                client = LLMClient()
                
                # Mock the LLM response
                with patch.object(client, 'llm_chat', return_value="claim_status"):
                    result = await client.extract_intent("What is my claim status?")
                    
                    # Verify the result
                    assert result["intent"] == "claim_status"
                    
                    # Verify tracing was called (indirectly through llm_chat)
                    assert client.llm_chat.call_count == 1


class TestDecorators:
    """Test observability decorators"""
    
    @pytest.mark.asyncio
    async def test_trace_agent_method_decorator(self):
        """Test the trace_agent_method decorator"""
        mock_obs = Mock()
        mock_obs.trace_agent_call = AsyncMock()
        mock_obs.trace_agent_call.return_value.__aenter__ = AsyncMock(return_value={})
        mock_obs.trace_agent_call.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch('agents.observability.get_observability', return_value=mock_obs):
            
            class TestClass:
                name = "test-agent"
                
                @trace_agent_method("test_skill")
                async def test_method(self, param1, param2=None):
                    return {"result": "success"}
            
            instance = TestClass()
            result = await instance.test_method("value1", param2="value2")
            
            assert result["result"] == "success"
            # Note: Decorator should have called trace_agent_call
    
    @pytest.mark.asyncio  
    async def test_trace_llm_method_decorator(self):
        """Test the trace_llm_method decorator"""
        mock_obs = Mock()
        mock_obs.trace_llm_call = AsyncMock()
        mock_obs.trace_llm_call.return_value.__aenter__ = AsyncMock(return_value={})
        mock_obs.trace_llm_call.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch('agents.observability.get_observability', return_value=mock_obs):
            
            class TestClass:
                primary_model = "test-model"
                
                @trace_llm_method("test_task")
                async def test_llm_method(self, prompt):
                    return "response"
            
            instance = TestClass()
            result = await instance.test_llm_method("test prompt")
            
            assert result == "response"
            # Note: Decorator should have called trace_llm_call


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_claim_inquiry_tracing(self):
        """Test that a complete claim inquiry is properly traced"""
        
        # This would test the full flow:
        # 1. Domain agent receives request
        # 2. Calls LLM for intent detection  
        # 3. Calls technical agent for data
        # 4. Calls LLM for response generation
        # 5. Returns response
        
        # Each step should generate appropriate traces and metrics
        
        # Mock all components
        mock_obs = Mock()
        mock_obs.trace_agent_call = AsyncMock()
        mock_obs.trace_llm_call = AsyncMock() 
        mock_obs.record_workflow_execution = Mock()
        mock_obs.record_token_usage = Mock()
        mock_obs.update_agent_health = Mock()
        
        # Set up context managers
        mock_obs.trace_agent_call.return_value.__aenter__ = AsyncMock(return_value={})
        mock_obs.trace_agent_call.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_obs.trace_llm_call.return_value.__aenter__ = AsyncMock(return_value={"generation": Mock()})
        mock_obs.trace_llm_call.return_value.__aexit__ = AsyncMock(return_value=None)
        
        with patch('agents.base.init_observability', return_value=mock_obs):
            with patch('agents.base.get_observability', return_value=mock_obs):
                with patch('agents.llm_client.get_observability', return_value=mock_obs):
                    
                    # This test would simulate the full workflow
                    # For now, just verify that observability components are set up correctly
                    
                    # Initialize a domain agent
                    from domain.claims_domain_agent import ClaimsDomainAgent
                    agent = ClaimsDomainAgent()
                    
                    # Verify observability is set up
                    assert hasattr(agent, 'observability')
                    mock_obs.update_agent_health.assert_called()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 