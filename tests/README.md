# Insurance AI POC Test Suite

This directory contains comprehensive tests for the Insurance AI POC system, organized by test type and functionality.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_service_discovery.py    # Service discovery functionality
│   ├── test_api_structure.py        # Policy server API structure
│   └── test_intelligent_agent.py    # LLM-powered agent functionality
├── integration/             # Integration tests between components
│   └── test_dynamic_discovery.py    # Service discovery integration
├── e2e/                    # End-to-end business scenario tests
│   └── test_focused_apis.py         # Customer service scenarios
├── conftest.py             # Pytest configuration and fixtures
└── README.md               # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Service Discovery**: Tests dynamic MCP service discovery, tool registry management, and service configuration
- **API Structure**: Tests individual policy server APIs, data structures, and business logic validation
- **Intelligent Agent**: Tests LLM-powered tool selection, execution planning, and error handling

### Integration Tests (`tests/integration/`)
- **Dynamic Discovery**: Tests full workflow of service discovery with technical agent integration
- **Multi-service Orchestration**: Tests interaction between multiple MCP services
- **Service Refresh**: Tests dynamic service updates and tool registry refresh

### End-to-End Tests (`tests/e2e/`)
- **Focused APIs**: Real customer service scenarios demonstrating business value
- **Performance Comparison**: Data transfer efficiency and response time comparisons
- **Business Workflows**: Complete customer service workflows using focused APIs

## Running Tests

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Run All Tests
```bash
# From project root
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v -m integration

# End-to-end tests only
python -m pytest tests/e2e/ -v -m e2e

# Exclude integration tests (for faster development)
python -m pytest tests/ -v -m "not integration"
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=policy_server --cov=technical_agent --cov-report=html
```

### Run Specific Test Files
```bash
# Test service discovery
python -m pytest tests/unit/test_service_discovery.py -v

# Test focused APIs with business scenarios
python -m pytest tests/e2e/test_focused_apis.py -v

# Test intelligent agent functionality
python -m pytest tests/unit/test_intelligent_agent.py -v
```

## Test Markers

Tests are marked with the following markers for selective execution:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests requiring external services
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.asyncio` - Async tests

### Running Tests by Marker
```bash
# Run only unit tests
python -m pytest -m unit

# Run everything except slow tests
python -m pytest -m "not slow"

# Run integration tests only
python -m pytest -m integration
```

## Test Fixtures and Utilities

### Available Fixtures
- `mock_openai_client` - Mock OpenAI client for testing without API calls
- `mock_fastmcp_client` - Mock FastMCP client for service discovery testing
- `sample_customer_data` - Sample customer data for consistent testing
- `policy_server` - Policy server instance for testing
- `service_discovery_config` - Service discovery configuration

### Test Helpers
The `TestHelpers` class provides utilities for:
- API response structure validation
- Tool call format validation
- Mock execution plan creation

## Integration Test Requirements

Integration tests require running services:

### Policy Server
```bash
# Terminal 1: Start policy server
python policy_server/main.py
```

### Technical Agent (Optional for full integration)
```bash
# Terminal 2: Start technical agent
python technical_agent/main.py
```

### Running Integration Tests with Services
```bash
# With services running
python -m pytest tests/integration/ -v

# Skip integration tests if services not available
python -m pytest tests/ -v -m "not integration"
```

## Test Data and Scenarios

### Customer Service Scenarios Tested
1. **Quick Policy Lookup**: "What policies do I have?"
2. **Billing Inquiry**: "When is my next payment due?"
3. **Agent Contact**: "Who is my insurance agent?"
4. **Coverage Verification**: "What am I covered for?"
5. **Recommendations**: "What other insurance should I consider?"
6. **Claims Preparation**: "What are my deductibles?"

### Performance Metrics Validated
- **Data Transfer Efficiency**: 70-80% reduction vs comprehensive API
- **Response Time**: Focused APIs faster than comprehensive
- **Multi-API Efficiency**: Multiple focused calls competitive with single comprehensive call

## Business Value Demonstration

The test suite demonstrates:

1. **Developer Productivity**: Clear API contracts and focused functionality
2. **Data Efficiency**: Significant reduction in data transfer for specific use cases
3. **Customer Service Speed**: Fast responses for common customer inquiries
4. **System Extensibility**: Dynamic service discovery supports new microservices
5. **Intelligent Orchestration**: LLM-powered tool selection optimizes multi-tool scenarios

## Continuous Integration

For CI/CD pipelines:

```bash
# Fast test suite (unit tests only)
python -m pytest tests/unit/ --cov=policy_server --cov=technical_agent

# Full test suite with services
docker-compose up -d  # Start services
python -m pytest tests/ --cov=policy_server --cov=technical_agent
docker-compose down   # Stop services
```

## Adding New Tests

### For New APIs
1. Add unit tests in `tests/unit/test_api_structure.py`
2. Add business scenario tests in `tests/e2e/test_focused_apis.py`
3. Update service discovery tests if new tools added

### For New Services
1. Add service discovery tests in `tests/unit/test_service_discovery.py`
2. Add integration tests in `tests/integration/test_dynamic_discovery.py`
3. Update configuration in `conftest.py`

### Test Naming Convention
- Unit tests: `test_<functionality>_<scenario>`
- Integration tests: `test_<component>_with_<component>`
- E2E tests: `test_<business_scenario>`

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `PYTHONPATH` includes source directories
2. **Service Connection**: Check if required services are running for integration tests
3. **Async Test Issues**: Ensure `pytest-asyncio` is installed

### Debug Mode
```bash
# Run with verbose output and no capture
python -m pytest tests/ -v -s

# Run specific test with debugging
python -m pytest tests/unit/test_service_discovery.py::TestServiceDiscovery::test_initialization -v -s
``` 