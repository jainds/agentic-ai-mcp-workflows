import pytest
import os
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from agents.llm_client import OpenRouterClient, LLMMessage, LLMResponse, LLMSkillMixin
import httpx


class TestOpenRouterClient:
    """Test suite for OpenRouter LLM client"""

    @pytest.fixture
    def mock_api_key(self):
        """Fixture providing a mock API key"""
        return "sk-or-v1-test-key-12345"

    @pytest.fixture
    def client(self, mock_api_key):
        """Fixture providing an OpenRouter client with mock API key"""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": mock_api_key}):
            return OpenRouterClient()

    @pytest.fixture
    def mock_response_data(self):
        """Fixture providing mock API response data"""
        return {
            "choices": [{
                "message": {
                    "content": "This is a test response from the AI model."
                },
                "finish_reason": "stop"
            }],
            "model": "openai/gpt-4o-mini",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25
            }
        }

    def test_client_initialization_with_env_key(self, mock_api_key):
        """Test that client initializes correctly with API key from environment"""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": mock_api_key}):
            client = OpenRouterClient()
            assert client.api_key == mock_api_key
            assert client.base_url == "https://openrouter.ai/api/v1"

    def test_client_initialization_with_explicit_key(self):
        """Test that client initializes correctly with explicitly provided API key"""
        test_key = "sk-or-v1-explicit-key-67890"
        client = OpenRouterClient(api_key=test_key)
        assert client.api_key == test_key

    def test_client_initialization_without_key_raises_error(self):
        """Test that client raises error when no API key is provided"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenRouter API key is required"):
                OpenRouterClient()

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, client, mock_response_data):
        """Test successful chat completion"""
        messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            response = await client.chat_completion(messages)
            
            assert isinstance(response, LLMResponse)
            assert response.content == "This is a test response from the AI model."
            assert response.model == "openai/gpt-4o-mini"
            assert response.provider == "openai"
            assert response.finish_reason == "stop"
            
            # Verify the request was made correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "/chat/completions"
            payload = call_args[0][1]
            assert payload["messages"] == messages
            assert "model" in payload

    @pytest.mark.asyncio
    async def test_chat_completion_with_llm_message_objects(self, client, mock_response_data):
        """Test chat completion with LLMMessage objects"""
        messages = [
            LLMMessage(role="user", content="Hello, how are you?")
        ]

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            response = await client.chat_completion(messages)
            
            assert isinstance(response, LLMResponse)
            assert response.content == "This is a test response from the AI model."
            
            # Verify messages were converted correctly
            call_args = mock_request.call_args
            payload = call_args[0][1]
            assert payload["messages"][0]["role"] == "user"
            assert payload["messages"][0]["content"] == "Hello, how are you?"

    @pytest.mark.asyncio
    async def test_chat_completion_with_fallback(self, client):
        """Test chat completion with fallback model when primary fails"""
        messages = [{"role": "user", "content": "Test message"}]
        
        # Mock primary model failure and fallback success
        fallback_response = {
            "choices": [{"message": {"content": "Fallback response"}, "finish_reason": "stop"}],
            "model": "anthropic/claude-3-haiku",
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        }

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            # First call fails, second succeeds
            mock_request.side_effect = [
                httpx.HTTPStatusError("Model unavailable", request=Mock(), response=Mock()),
                fallback_response
            ]
            
            response = await client.chat_completion(messages, use_fallback=True)
            
            assert response.content == "Fallback response"
            assert response.model == "anthropic/claude-3-haiku"
            assert response.provider == "anthropic"
            
            # Verify both calls were made
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_chat_completion_failure_without_fallback(self, client):
        """Test chat completion failure when fallback is disabled"""
        messages = [{"role": "user", "content": "Test message"}]

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.HTTPStatusError(
                "API Error", request=Mock(), response=Mock()
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.chat_completion(messages, use_fallback=False)

    @pytest.mark.asyncio
    async def test_embedding_success(self, client):
        """Test successful embedding generation"""
        embedding_response = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "openai/text-embedding-ada-002",
            "usage": {"prompt_tokens": 5, "total_tokens": 5}
        }

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = embedding_response
            
            response = await client.embedding("Test text")
            
            assert response == embedding_response
            
            # Verify the request
            call_args = mock_request.call_args
            assert call_args[0][0] == "/embeddings"
            payload = call_args[0][1]
            assert payload["input"] == "Test text"
            assert "model" in payload

    @pytest.mark.asyncio
    async def test_make_request_http_error(self, client):
        """Test HTTP error handling in _make_request"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch.object(client.http_client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=Mock(), response=mock_response
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await client._make_request("/test", {})

    @pytest.mark.asyncio
    async def test_make_request_network_error(self, client):
        """Test network error handling in _make_request"""
        with patch.object(client.http_client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.RequestError("Network error")
            
            with pytest.raises(httpx.RequestError):
                await client._make_request("/test", {})

    def test_get_provider_from_model(self, client):
        """Test provider extraction from model names"""
        assert client._get_provider_from_model("openai/gpt-4") == "openai"
        assert client._get_provider_from_model("anthropic/claude-3") == "anthropic"
        assert client._get_provider_from_model("google/gemini-pro") == "google"
        assert client._get_provider_from_model("unknown-model") == "unknown"

    @pytest.mark.asyncio
    async def test_client_close(self, client):
        """Test client cleanup"""
        with patch.object(client.http_client, 'aclose', new_callable=AsyncMock) as mock_close:
            await client.close()
            mock_close.assert_called_once()


class TestLLMSkillMixin:
    """Test suite for LLM skill mixin functionality"""

    class MockAgent(LLMSkillMixin):
        """Mock agent class for testing LLM skills"""
        def __init__(self):
            # Mock the LLM client initialization to avoid requiring API key
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test-key"}):
                super().__init__()
            self.logger = Mock()

    @pytest.fixture
    def agent(self):
        """Fixture providing a mock agent with LLM skills"""
        return self.MockAgent()

    @pytest.fixture
    def mock_llm_response(self):
        """Fixture providing a mock LLM response"""
        return LLMResponse(
            content="Test response",
            model="openai/gpt-4o-mini",
            usage={"total_tokens": 25},
            finish_reason="stop",
            provider="openai"
        )

    @pytest.mark.asyncio
    async def test_llm_chat_success(self, agent, mock_llm_response):
        """Test successful LLM chat interaction"""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_llm_response
            
            response = await agent.llm_chat(messages)
            
            assert response == "Test response"
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_chat_with_system_prompt(self, agent, mock_llm_response):
        """Test LLM chat with system prompt"""
        messages = [{"role": "user", "content": "Hello"}]
        system_prompt = "You are a helpful assistant"
        
        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_llm_response
            
            response = await agent.llm_chat(messages, system_prompt=system_prompt)
            
            assert response == "Test response"
            
            # Verify system prompt was added
            call_args = mock_chat.call_args[0][0]
            assert call_args[0]["role"] == "system"
            assert call_args[0]["content"] == system_prompt

    @pytest.mark.asyncio
    async def test_extract_intent_success(self, agent):
        """Test intent extraction functionality"""
        user_message = "I want to check my policy status"
        
        mock_response = LLMResponse(
            content='{"intent": "policy_inquiry", "confidence": 0.95, "entities": {"policy_type": "auto"}}',
            model="openai/gpt-4o-mini",
            usage={"total_tokens": 30},
            finish_reason="stop",
            provider="openai"
        )
        
        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            result = await agent.extract_intent(user_message)
            
            assert result["intent"] == "policy_inquiry"
            assert result["confidence"] == 0.8  # Default confidence from implementation
            assert "explanation" in result

    @pytest.mark.asyncio
    async def test_extract_intent_invalid_json(self, agent):
        """Test intent extraction with invalid JSON response"""
        user_message = "I want to check my policy status"
        
        mock_response = LLMResponse(
            content="Invalid JSON response",
            model="openai/gpt-4o-mini",
            usage={"total_tokens": 20},
            finish_reason="stop",
            provider="openai"
        )
        
        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            result = await agent.extract_intent(user_message)
            
            # Should return default intent when JSON parsing fails
            assert result["intent"] == "general_support"
            assert result["confidence"] == 0.8  # Default confidence for successful response

    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, agent, mock_llm_response):
        """Test response generation with context and information"""
        user_message = "What's my policy status?"
        context = "Policy inquiry"
        information = {"customer_id": 123, "policy_count": 2}
        
        with patch.object(agent.llm_client, 'chat_completion', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_llm_response
            
            response = await agent.generate_response(user_message, context, information)
            
            assert response == "Test response"
            
            # Verify context and information were included in the prompt
            call_args = mock_chat.call_args[0][0]
            user_prompt = call_args[-1]["content"]
            assert "Policy inquiry" in user_prompt
            assert "customer_id" in user_prompt

    @pytest.mark.asyncio
    async def test_close_llm_client(self, agent):
        """Test LLM client cleanup"""
        with patch.object(agent.llm_client, 'close', new_callable=AsyncMock) as mock_close:
            await agent.close_llm_client()
            mock_close.assert_called_once()


class TestRealAPIIntegration:
    """Integration tests with real API (requires valid API key)"""

    @pytest.fixture
    def real_client(self):
        """Fixture for real API client (skipped if no API key)"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-test"):
            pytest.skip("Real API key not available for integration testing")
        return OpenRouterClient(api_key=api_key)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_chat_completion(self, real_client):
        """Test actual API call (requires real API key)"""
        messages = [
            {"role": "user", "content": "Say 'Hello, this is a test!' and nothing else."}
        ]
        
        try:
            response = await real_client.chat_completion(
                messages, 
                model="openai/gpt-4o-mini",
                max_tokens=50
            )
            
            assert isinstance(response, LLMResponse)
            assert len(response.content) > 0
            assert response.model.startswith("openai/")
            assert response.provider == "openai"
            assert "total_tokens" in response.usage
            
        finally:
            await real_client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_embedding(self, real_client):
        """Test actual embedding API call (requires real API key)"""
        pytest.skip("OpenRouter doesn't support embeddings endpoint")
        
        try:
            response = await real_client.embedding(
                "This is a test sentence for embedding.",
                model="openai/text-embedding-ada-002"
            )
            
            assert "data" in response
            assert len(response["data"]) > 0
            assert "embedding" in response["data"][0]
            assert len(response["data"][0]["embedding"]) > 0
            
        finally:
            await real_client.close()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_key_validation(self):
        """Test API key validation with invalid key"""
        invalid_client = OpenRouterClient(api_key="sk-invalid-key")
        
        messages = [{"role": "user", "content": "Test"}]
        
        try:
            with pytest.raises(httpx.HTTPStatusError):
                await invalid_client.chat_completion(messages)
        finally:
            await invalid_client.close()


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/unit/test_llm_client.py -v
    # Run integration tests with: python -m pytest tests/unit/test_llm_client.py -v -m integration
    pass 