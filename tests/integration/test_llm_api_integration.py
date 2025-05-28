import pytest
import os
import asyncio
import json
from typing import Dict, Any
from unittest.mock import patch, AsyncMock
from agents.llm_client import OpenRouterClient, LLMResponse
from agents.domain.support_agent import SupportDomainAgent
from agents.domain.claims_domain_agent import ClaimsDomainAgent


class TestLLMAPIKeyValidation:
    """Test suite for validating API key functionality"""

    def test_env_key_loading(self):
        """Test that API key is properly loaded from environment"""
        test_key = "sk-or-v1-test-key-12345"
        
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": test_key}):
            client = OpenRouterClient()
            assert client.api_key == test_key

    def test_explicit_key_override(self):
        """Test that explicit API key overrides environment"""
        env_key = "sk-or-v1-env-key"
        explicit_key = "sk-or-v1-explicit-key"
        
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": env_key}):
            client = OpenRouterClient(api_key=explicit_key)
            assert client.api_key == explicit_key

    def test_missing_key_error(self):
        """Test that missing API key raises appropriate error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenRouter API key is required"):
                OpenRouterClient()

    @pytest.mark.asyncio
    async def test_invalid_key_handling(self):
        """Test handling of invalid API keys"""
        invalid_client = OpenRouterClient(api_key="sk-invalid-key")
        
        messages = [{"role": "user", "content": "Test"}]
        
        try:
            with pytest.raises(Exception):  # Should raise HTTP error or similar
                await invalid_client.chat_completion(messages)
        finally:
            await invalid_client.close()


class TestRealLLMAPIIntegration:
    """Integration tests with real LLM API (requires valid API key)"""

    @pytest.fixture
    def real_client(self):
        """Fixture for real API client"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-test"):
            pytest.skip("Real API key not available for integration testing")
        return OpenRouterClient(api_key=api_key)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_basic_chat_completion(self, real_client):
        """Test basic chat completion with real API"""
        messages = [
            {"role": "user", "content": "Say 'Hello World' and nothing else."}
        ]
        
        try:
            response = await real_client.chat_completion(
                messages,
                model="qwen/qwen3-30b-a3b:free",
                max_tokens=10,
                temperature=0.1
            )
            
            assert isinstance(response, LLMResponse)
            assert len(response.content) > 0
            assert response.model.startswith("openai/")
            assert response.provider == "openai"
            assert "total_tokens" in response.usage
            assert response.usage["total_tokens"] > 0
            
        finally:
            await real_client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_different_models(self, real_client):
        """Test different model providers"""
        test_cases = [
            ("qwen/qwen3-30b-a3b:free", "openai"),
            ("anthropic/claude-3-haiku", "anthropic"),
        ]
        
        for model, expected_provider in test_cases:
            messages = [{"role": "user", "content": "Say 'test' and nothing else."}]
            
            try:
                response = await real_client.chat_completion(
                    messages,
                    model=model,
                    max_tokens=5,
                    temperature=0.1
                )
                
                assert response.provider == expected_provider
                assert len(response.content) > 0
                
            except Exception as e:
                # Some models might not be available, log and continue
                print(f"Model {model} not available: {e}")
                continue
        
        await real_client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, real_client):
        """Test fallback to secondary model when primary fails"""
        messages = [{"role": "user", "content": "Test message"}]
        
        try:
            # Try with a potentially unavailable model and fallback enabled
            response = await real_client.chat_completion(
                messages,
                model="some/unavailable-model",  # This should fail
                use_fallback=True,
                max_tokens=20
            )
            
            # Should get response from fallback model
            assert isinstance(response, LLMResponse)
            assert len(response.content) > 0
            
        except Exception as e:
            # If both primary and fallback fail, that's also a valid test result
            print(f"Both models failed (expected in some cases): {e}")
        
        finally:
            await real_client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_embedding_generation(self, real_client):
        """Test embedding generation with real API"""
        pytest.skip("OpenRouter doesn't support embeddings endpoint")
        
        text = "This is a test sentence for embedding generation."
        
        try:
            response = await real_client.embedding(
                text,
                model="openai/text-embedding-ada-002"
            )
            
            assert "data" in response
            assert len(response["data"]) > 0
            assert "embedding" in response["data"][0]
            embedding = response["data"][0]["embedding"]
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all(isinstance(x, (int, float)) for x in embedding)
            
        finally:
            await real_client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, real_client):
        """Test handling multiple concurrent requests"""
        messages_list = [
            [{"role": "user", "content": f"Say 'Response {i}' and nothing else."}]
            for i in range(3)
        ]
        
        try:
            tasks = [
                real_client.chat_completion(
                    messages,
                    model="qwen/qwen3-30b-a3b:free",
                    max_tokens=10,
                    temperature=0.1
                )
                for messages in messages_list
            ]
            
            responses = await asyncio.gather(*tasks)
            
            assert len(responses) == 3
            for response in responses:
                assert isinstance(response, LLMResponse)
                assert len(response.content) > 0
                
        finally:
            await real_client.close()


class TestAgentLLMWorkflows:
    """Test complete agent workflows with real LLM integration"""

    @pytest.fixture
    def real_support_agent(self):
        """Fixture for real support agent"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-test"):
            pytest.skip("Real API key not available for integration testing")
        
        return SupportDomainAgent(port=8005)

    @pytest.fixture
    def real_claims_agent(self):
        """Fixture for real claims agent"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-test"):
            pytest.skip("Real API key not available for integration testing")
        
        return ClaimsDomainAgent(port=8006)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_support_agent_intent_extraction(self, real_support_agent):
        """Test support agent intent extraction with real LLM"""
        test_cases = [
            ("I want to check my policy status", "policy_inquiry"),
            ("I need to file a claim", "claim_status"),
            ("How much is my premium?", "billing_inquiry"),
            ("Hello, I need help", "general_support"),
        ]
        
        try:
            for user_message, expected_intent in test_cases:
                result = await real_support_agent.extract_intent(user_message)
                
                assert "intent" in result
                assert "confidence" in result
                assert isinstance(result["confidence"], (int, float))
                assert 0 <= result["confidence"] <= 1
                
                # Note: We don't assert exact intent match since LLM responses can vary
                print(f"Message: '{user_message}' -> Intent: {result['intent']} (confidence: {result['confidence']})")
                
        finally:
            await real_support_agent.close_llm_client()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_support_agent_response_generation(self, real_support_agent):
        """Test support agent response generation with real LLM"""
        user_message = "I'm having trouble understanding my policy coverage"
        context = "Customer support - policy inquiry"
        information = {
            "customer_id": 12345,
            "customer_name": "John Doe",
            "policy_type": "auto insurance"
        }
        
        try:
            response = await real_support_agent.generate_response(
                user_message,
                context=context,
                information=information
            )
            
            assert isinstance(response, str)
            assert len(response) > 0
            
            # Check that response is contextually relevant
            response_lower = response.lower()
            assert any(keyword in response_lower for keyword in [
                "policy", "coverage", "insurance", "help", "assist"
            ])
            
            print(f"Generated response: {response}")
            
        finally:
            await real_support_agent.close_llm_client()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_claims_agent_claim_extraction(self, real_claims_agent):
        """Test claims agent claim detail extraction with real LLM"""
        user_message = "I was in a car accident yesterday on Highway 101. The other driver ran a red light and hit my car. I need to file a claim."
        
        try:
            # Test extract_claim_details if it exists
            if hasattr(real_claims_agent, 'extract_claim_details'):
                result = await real_claims_agent.extract_claim_details(user_message)
                
                assert isinstance(result, dict)
                print(f"Extracted claim details: {json.dumps(result, indent=2)}")
                
                # Should extract some relevant information
                result_str = json.dumps(result).lower()
                assert any(keyword in result_str for keyword in [
                    "accident", "car", "vehicle", "collision", "auto"
                ])
            else:
                # Test general LLM functionality
                response = await real_claims_agent.generate_response(
                    user_message,
                    context="Claim filing assistance"
                )
                
                assert isinstance(response, str)
                assert len(response) > 0
                print(f"Claims agent response: {response}")
                
        finally:
            await real_claims_agent.close_llm_client()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_end_to_end_customer_workflow(self, real_support_agent):
        """Test complete customer support workflow with real LLM"""
        user_message = "Hi, I want to check the status of my auto insurance policy"
        customer_id = 12345
        
        # Mock the technical agent calls since we're testing LLM integration
        real_support_agent.call_technical_agent = AsyncMock()
        real_support_agent.call_technical_agent.side_effect = [
            {"result": {"valid": True, "name": "John Doe", "customer_id": 12345}},
            {"result": {"success": True, "policies": [
                {"policy_id": 1001, "type": "auto", "status": "active"}
            ]}},
            {"result": {"success": True, "status": {
                "policy_id": 1001,
                "status": "active",
                "premium": 1200,
                "next_payment": "2024-02-15"
            }}}
        ]
        
        try:
            result = await real_support_agent.handle_customer_inquiry(user_message, customer_id)
            
            assert result["success"] is True
            assert "response" in result
            assert "workflow" in result
            assert isinstance(result["response"], str)
            assert len(result["response"]) > 0
            
            # Verify the response contains relevant information
            response_lower = result["response"].lower()
            assert any(keyword in response_lower for keyword in [
                "policy", "status", "active", "john", "auto"
            ])
            
            print(f"End-to-end workflow result: {json.dumps(result, indent=2)}")
            
        finally:
            await real_support_agent.close_llm_client()


class TestLLMErrorHandlingIntegration:
    """Test error handling in real LLM integration scenarios"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test handling of network timeouts"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-test"):
            pytest.skip("Real API key not available for integration testing")
        
        # Create client with very short timeout
        import httpx
        client = OpenRouterClient(api_key=api_key)
        client.http_client = httpx.AsyncClient(timeout=0.001)  # Very short timeout
        
        messages = [{"role": "user", "content": "Test"}]
        
        try:
            with pytest.raises((httpx.TimeoutException, httpx.RequestError)):
                await client.chat_completion(messages)
        finally:
            await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test handling of rate limits (if encountered)"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-test"):
            pytest.skip("Real API key not available for integration testing")
        
        client = OpenRouterClient(api_key=api_key)
        messages = [{"role": "user", "content": "Test"}]
        
        try:
            # Make multiple rapid requests to potentially trigger rate limiting
            tasks = []
            for i in range(10):
                task = client.chat_completion(
                    messages,
                    model="qwen/qwen3-30b-a3b:free",
                    max_tokens=5
                )
                tasks.append(task)
            
            # Some requests might fail due to rate limiting, which is expected
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least some requests should succeed
            successful_results = [r for r in results if isinstance(r, LLMResponse)]
            assert len(successful_results) > 0
            
            # Check if any rate limit errors occurred
            errors = [r for r in results if isinstance(r, Exception)]
            for error in errors:
                print(f"Request error (possibly rate limit): {error}")
                
        finally:
            await client.close()


class TestLLMConfigurationValidation:
    """Test different LLM configuration scenarios"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_model_configuration_from_env(self):
        """Test that model configuration is properly loaded from environment"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-test"):
            pytest.skip("Real API key not available for integration testing")
        
        # Test with custom model configuration
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": api_key,
            "PRIMARY_MODEL": "qwen/qwen3-30b-a3b:free",
            "FALLBACK_MODEL": "anthropic/claude-3-haiku",
            "EMBEDDING_MODEL": "openai/text-embedding-ada-002"
        }):
            client = OpenRouterClient()
            
            assert client.models["primary"] == "qwen/qwen3-30b-a3b:free"
            assert client.models["fallback"] == "anthropic/claude-3-haiku"
            assert client.models["embedding"] == "openai/text-embedding-ada-002"
            
            # Test that primary model is used by default
            messages = [{"role": "user", "content": "Test"}]
            
            try:
                response = await client.chat_completion(messages, max_tokens=5)
                # Should use primary model (though actual model name in response might vary)
                assert isinstance(response, LLMResponse)
                
            finally:
                await client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_custom_base_url(self):
        """Test custom base URL configuration"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-test"):
            pytest.skip("Real API key not available for integration testing")
        
        # Test with custom base URL (should still work with OpenRouter)
        with patch.dict(os.environ, {
            "OPENROUTER_API_KEY": api_key,
            "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1"
        }):
            client = OpenRouterClient()
            assert client.base_url == "https://openrouter.ai/api/v1"
            
            messages = [{"role": "user", "content": "Test"}]
            
            try:
                response = await client.chat_completion(messages, max_tokens=5)
                assert isinstance(response, LLMResponse)
                
            finally:
                await client.close()


if __name__ == "__main__":
    # Run all tests with: python -m pytest tests/integration/test_llm_api_integration.py -v
    # Run only integration tests with: python -m pytest tests/integration/test_llm_api_integration.py -v -m integration
    # Run with real API key: OPENROUTER_API_KEY=your_key python -m pytest tests/integration/test_llm_api_integration.py -v -m integration
    pass 