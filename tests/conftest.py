import pytest
import os
import asyncio
from typing import Generator


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require real API keys)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (use mocks)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_vars():
    """Fixture providing mock environment variables for testing"""
    return {
        "OPENROUTER_API_KEY": "sk-or-v1-test-key-12345",
        "PRIMARY_MODEL": "openai/gpt-4o-mini",
        "FALLBACK_MODEL": "anthropic/claude-3-haiku",
        "EMBEDDING_MODEL": "openai/text-embedding-ada-002",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
        "CUSTOMER_AGENT_URL": "http://localhost:8010",
        "POLICY_AGENT_URL": "http://localhost:8011",
        "CLAIMS_DATA_AGENT_URL": "http://localhost:8012"
    }


@pytest.fixture
def real_api_key():
    """Fixture that provides real API key or skips test if not available"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key.startswith("sk-or-v1-test"):
        pytest.skip("Real API key not available for integration testing")
    return api_key


@pytest.fixture
def sample_messages():
    """Fixture providing sample messages for testing"""
    return [
        {"role": "user", "content": "Hello, I need help with my insurance policy"},
        {"role": "assistant", "content": "I'd be happy to help you with your policy. What specific information do you need?"},
        {"role": "user", "content": "I want to check my policy status"}
    ]


@pytest.fixture
def sample_customer_data():
    """Fixture providing sample customer data for testing"""
    return {
        "customer_id": 12345,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "policies": [
            {
                "policy_id": 1001,
                "type": "auto",
                "status": "active",
                "premium": 1200,
                "next_payment": "2024-02-15"
            },
            {
                "policy_id": 1002,
                "type": "home",
                "status": "active",
                "premium": 800,
                "next_payment": "2024-02-20"
            }
        ]
    }


@pytest.fixture
def sample_claim_data():
    """Fixture providing sample claim data for testing"""
    return {
        "claim_id": 5001,
        "customer_id": 12345,
        "policy_id": 1001,
        "incident_type": "auto_accident",
        "status": "in_progress",
        "date_filed": "2024-01-15",
        "description": "Rear-end collision at intersection",
        "estimated_damage": 3500
    }


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and content"""
    for item in items:
        # Mark integration tests
        if "integration" in str(item.fspath) or "real_" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Mark unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "concurrent" in item.name or "rate_limit" in item.name:
            item.add_marker(pytest.mark.slow) 