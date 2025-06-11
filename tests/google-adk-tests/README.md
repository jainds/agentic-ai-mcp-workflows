# Google ADK Tests

This directory contains test files for the official Google ADK v1.2.1 implementation.

## Test Files

- **`test_google_adk_agents.py`** - Basic agent creation and validation tests
- **`demo_google_adk.py`** - Comprehensive demo showcasing Google ADK features  
- **`test_a2a_communication.py`** - A2A communication protocol tests

## Running Tests

From the main project directory:

```bash
# Basic agent tests
python tests/google-adk-tests/test_google_adk_agents.py

# Full demo
python tests/google-adk-tests/demo_google_adk.py

# A2A communication tests
python tests/google-adk-tests/test_a2a_communication.py
```

## Test Results

✅ **Google ADK Implementation**: All agents using official `google.adk.agents` classes  
✅ **Framework**: Google ADK v1.2.1 confirmed  
✅ **A2A Protocol**: python-a2a v0.5.6 working  
✅ **Agent Types**: BaseAgent and LlmAgent properly implemented  
✅ **Multi-Agent**: Sub-agent hierarchies working correctly  

## Architecture

The tests validate our implementation follows patterns from [google/adk-samples](https://github.com/google/adk-samples/tree/main/python/agents/customer-service). 