# LLM Integration Testing Guide

This guide explains how to test the LLM integration functionality in the agentic AI system, including API key validation and agent LLM interactions.

## Overview

The testing suite includes:
- **Unit Tests**: Mock-based tests that don't require real API keys
- **Integration Tests**: Real API tests that require valid API keys
- **Agent Tests**: Tests for agent LLM integration functionality
- **End-to-End Tests**: Complete workflow tests

## Quick Start

### 1. Setup Environment

First, create your environment configuration:

```bash
# Create a sample .env file
python scripts/test_llm_integration.py setup

# Edit .env.example with your actual API keys and copy to .env
cp .env.example .env
# Edit .env with your actual API keys
```

### 2. Run Tests

```bash
# Run all unit tests (no API key required)
python scripts/test_llm_integration.py unit

# Run integration tests (requires valid API key)
python scripts/test_llm_integration.py integration

# Run all tests
python scripts/test_llm_integration.py all

# Quick smoke test
python scripts/test_llm_integration.py smoke
```

## Environment Variables

### Required for Integration Tests

- `OPENROUTER_API_KEY`: Your OpenRouter API key (starts with `sk-or-v1-`)
- Alternative: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

### Optional Configuration

- `PRIMARY_MODEL`: Primary model to use (default: `openai/gpt-4o-mini`)
- `FALLBACK_MODEL`: Fallback model (default: `anthropic/claude-3-haiku`)
- `EMBEDDING_MODEL`: Embedding model (default: `openai/text-embedding-ada-002`)
- `OPENROUTER_BASE_URL`: API base URL (default: `https://openrouter.ai/api/v1`)

## Test Categories

### 1. API Key Validation Tests

Tests that verify API key loading and validation:

```bash
# Test API key functionality
python scripts/test_llm_integration.py api-key
```

**What it tests:**
- Loading API key from environment variables
- Explicit API key override
- Missing API key error handling
- Invalid API key detection

### 2. LLM Client Tests

Tests for the core LLM client functionality:

```bash
# Run LLM client tests
python -m pytest tests/unit/test_llm_client.py -v
```

**What it tests:**
- Chat completion functionality
- Embedding generation
- Model fallback mechanisms
- Error handling (timeouts, rate limits, etc.)
- Response parsing and validation

### 3. Agent LLM Integration Tests

Tests for agent-specific LLM functionality:

```bash
# Test agent LLM integration
python scripts/test_llm_integration.py agents
```

**What it tests:**
- Support agent intent extraction
- Claims agent claim detail extraction
- Response generation with context
- Error handling in agent workflows
- Concurrent LLM requests

### 4. Integration Tests

End-to-end tests with real API calls:

```bash
# Run integration tests (requires API key)
python scripts/test_llm_integration.py integration
```

**What it tests:**
- Real API connectivity
- Different model providers (OpenAI, Anthropic)
- Fallback mechanisms with real models
- Rate limiting and error handling
- Complete agent workflows

## Test Structure

```
tests/
├── conftest.py                           # Pytest configuration and fixtures
├── unit/
│   ├── test_llm_client.py               # LLM client unit tests
│   └── test_agent_llm_integration.py    # Agent LLM integration tests
└── integration/
    └── test_llm_api_integration.py      # Real API integration tests
```

## Running Specific Tests

### Unit Tests Only (No API Key Required)

```bash
# All unit tests
python -m pytest tests/unit/ -v -m "not integration"

# Specific test class
python -m pytest tests/unit/test_llm_client.py::TestOpenRouterClient -v

# Specific test method
python -m pytest tests/unit/test_llm_client.py::TestOpenRouterClient::test_chat_completion_success -v
```

### Integration Tests (Requires API Key)

```bash
# All integration tests
python -m pytest tests/ -v -m integration

# Specific integration test
python -m pytest tests/integration/test_llm_api_integration.py::TestRealLLMAPIIntegration::test_basic_chat_completion -v
```

### Agent-Specific Tests

```bash
# Support agent tests
python -m pytest tests/unit/test_agent_llm_integration.py::TestSupportAgentLLMIntegration -v

# Claims agent tests
python -m pytest tests/unit/test_agent_llm_integration.py::TestClaimsAgentLLMIntegration -v

# Error handling tests
python -m pytest tests/unit/test_agent_llm_integration.py::TestAgentLLMErrorHandling -v
```

## Test Scenarios

### 1. API Key Validation

```python
# Test environment key loading
def test_env_key_loading():
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
        client = OpenRouterClient()
        assert client.api_key == "test-key"

# Test missing key error
def test_missing_key_error():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OpenRouter API key is required"):
            OpenRouterClient()
```

### 2. Agent LLM Integration

```python
# Test support agent intent extraction
async def test_extract_intent_functionality():
    user_message = "I want to check my policy status"
    result = await support_agent.extract_intent(user_message)
    assert result["intent"] == "policy_inquiry"
    assert result["confidence"] > 0.5

# Test response generation with context
async def test_generate_response_with_context():
    response = await support_agent.generate_response(
        "What's my policy status?",
        context="Policy inquiry for customer John Doe",
        information={"customer_id": 12345}
    )
    assert isinstance(response, str)
    assert len(response) > 0
```

### 3. Real API Integration

```python
# Test real chat completion
async def test_real_chat_completion():
    messages = [{"role": "user", "content": "Say 'Hello World'"}]
    response = await real_client.chat_completion(messages)
    assert isinstance(response, LLMResponse)
    assert len(response.content) > 0
    assert response.provider == "openai"
```

## Error Handling Tests

The test suite includes comprehensive error handling scenarios:

### Network Errors
- Connection timeouts
- Network unavailability
- DNS resolution failures

### API Errors
- Invalid API keys
- Rate limiting
- Model unavailability
- Malformed requests

### Agent Errors
- LLM service failures
- Invalid JSON responses
- Timeout handling
- Graceful degradation

## Performance Tests

### Concurrent Requests
```python
async def test_concurrent_llm_requests():
    tasks = [agent.generate_response(msg) for msg in messages]
    responses = await asyncio.gather(*tasks)
    assert len(responses) == len(messages)
```

### Token Usage Tracking
```python
async def test_llm_token_usage_tracking():
    response = await client.chat_completion(messages)
    assert "usage" in response.usage
    assert response.usage["total_tokens"] > 0
```

## Debugging Tests

### Verbose Output
```bash
# Run with verbose output
python -m pytest tests/ -v -s

# Show local variables on failure
python -m pytest tests/ -v -l

# Stop on first failure
python -m pytest tests/ -x
```

### Test Specific Scenarios
```bash
# Test only API key validation
python -m pytest tests/ -k "api_key" -v

# Test only error handling
python -m pytest tests/ -k "error" -v

# Test only real API calls
python -m pytest tests/ -k "real_" -v
```

## Continuous Integration

For CI/CD pipelines, use environment-specific test commands:

```bash
# CI environment (no real API keys)
python scripts/test_llm_integration.py unit

# Staging environment (with API keys)
python scripts/test_llm_integration.py all

# Production validation (smoke test only)
python scripts/test_llm_integration.py smoke
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   ❌ No OPENROUTER_API_KEY found in environment
   ```
   Solution: Set the `OPENROUTER_API_KEY` environment variable

2. **Invalid API Key**
   ```
   HTTPStatusError: 401 Unauthorized
   ```
   Solution: Verify your API key is correct and has sufficient credits

3. **Rate Limiting**
   ```
   HTTPStatusError: 429 Too Many Requests
   ```
   Solution: Implement backoff or reduce request frequency

4. **Model Unavailable**
   ```
   Model 'some/model' not available
   ```
   Solution: Check model availability or use fallback models

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Use Mock Tests for Development**: Unit tests with mocks are faster and don't consume API credits
2. **Real API Tests for Validation**: Use integration tests to validate actual API functionality
3. **Environment Separation**: Use different API keys for testing vs production
4. **Rate Limit Awareness**: Be mindful of API rate limits in tests
5. **Error Handling**: Always test error scenarios and edge cases
6. **Cleanup**: Ensure proper cleanup of resources (close HTTP clients)

## Example Test Run

```bash
$ python scripts/test_llm_integration.py all

🚀 LLM Integration Test Runner
📁 Working directory: /path/to/project

🧪 Running unit tests (mocked LLM calls)...
Running: python -m pytest tests/unit/test_llm_client.py tests/unit/test_agent_llm_integration.py -v -m not integration --tb=short
========================= test session starts =========================
tests/unit/test_llm_client.py::TestOpenRouterClient::test_client_initialization_with_env_key PASSED
tests/unit/test_llm_client.py::TestOpenRouterClient::test_chat_completion_success PASSED
tests/unit/test_agent_llm_integration.py::TestSupportAgentLLMIntegration::test_extract_intent_functionality PASSED
========================= 15 passed in 2.34s =========================

✅ Valid API key found

🌐 Running integration tests (real API calls)...
Running: python -m pytest tests/integration/test_llm_api_integration.py -v -m integration --tb=short
========================= test session starts =========================
tests/integration/test_llm_api_integration.py::TestRealLLMAPIIntegration::test_basic_chat_completion PASSED
tests/integration/test_llm_api_integration.py::TestAgentLLMWorkflows::test_support_agent_intent_extraction PASSED
========================= 8 passed in 12.45s =========================

✅ All tests passed!

✅ all tests completed successfully!
```

This comprehensive testing setup ensures that your LLM integration is robust, reliable, and properly handles both success and error scenarios. 