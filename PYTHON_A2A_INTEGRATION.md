# Python-A2A Integration for Insurance AI POC

This document describes the integration of `python-a2a` library for agent-to-agent communication in the Insurance AI POC project.

## Overview

The domain agent now plays two key roles using `python-a2a` for communication:

1. **Intent Understanding & Planning**: Parse user requests and create execution plans
2. **Task Routing & Coordination**: Route tasks to appropriate technical agents

Once tasks are complete, the domain agent prepares a response and sends it back to the user.

## Architecture

```
┌─────────────────┐    python-a2a     ┌─────────────────┐
│   Domain Agent  │◄──────────────────►│ Technical Agent │
│                 │                    │   (Data)        │
│  - Intent       │    python-a2a     ├─────────────────┤
│    Understanding│◄──────────────────►│ Technical Agent │
│  - Planning     │                    │ (Notification)  │
│  - Routing      │    python-a2a     ├─────────────────┤
│  - Response     │◄──────────────────►│ Technical Agent │
│    Preparation  │                    │   (FastMCP)     │
└─────────────────┘                    └─────────────────┘
```

## Key Components

### 1. Python A2A Base Classes

- **`agents/shared/python_a2a_base.py`**: Base classes for A2A agents using python-a2a
- **`PythonA2AAgent`**: Base agent class with communication capabilities
- **`PythonA2AClientWrapper`**: Client wrapper for easy agent communication

### 2. Domain Agent

- **`agents/domain/python_a2a_domain_agent.py`**: Domain agent implementation
- **Capabilities**:
  - Intent understanding using LLM
  - Execution plan creation
  - Task routing to technical agents
  - Response preparation and synthesis

### 3. Technical Agents

- **`agents/technical/python_a2a_technical_agent.py`**: Technical agent implementation
- **Types**:
  - `data`: Database operations and analytics
  - `notification`: Notification services
  - `fastmcp`: Tool-based operations

## Usage

### Environment Setup

1. Install dependencies:
```bash
source .venv/bin/activate
pip install python-a2a
```

2. Set environment variables:
```bash
export OPENROUTER_API_KEY="your_openrouter_key"  # or OPENAI_API_KEY
export LLM_MODEL="anthropic/claude-3.5-sonnet"   # or your preferred model
```

### Running Agents

#### Start Domain Agent
```bash
python -m agents.domain.python_a2a_domain_agent --port 8000
```

#### Start Technical Agents
```bash
# Data Agent
python -m agents.technical.python_a2a_technical_agent --port 8002 --type data

# Notification Agent  
python -m agents.technical.python_a2a_technical_agent --port 8003 --type notification

# FastMCP Agent
python -m agents.technical.python_a2a_technical_agent --port 8004 --type fastmcp
```

### Running the Demo

```bash
python examples/python_a2a_demo.py
```

This will:
1. Start all agents automatically
2. Test direct technical agent communication
3. Test full domain agent workflows
4. Demonstrate intent understanding and task routing

## Example Interactions

### 1. Claim Filing
```python
from python_a2a import A2AClient, Message, TextContent, MessageRole

client = A2AClient("http://localhost:8000")
message = Message(
    content=TextContent(text="I want to file a claim for my car accident. Policy POL123456."),
    role=MessageRole.USER
)
response = client.send_message(message)
```

**Flow**:
1. Domain agent understands intent: `claim_filing`
2. Creates execution plan with steps:
   - Validate policy (data agent)
   - Create claim record (data agent)
   - Fraud detection check (fastmcp agent)
   - Send confirmation (notification agent)
3. Routes tasks to technical agents
4. Aggregates results and prepares user-friendly response

### 2. Policy Inquiry
```python
message = Message(
    content=TextContent(text="Can you tell me about my policy details? Policy POL789012."),
    role=MessageRole.USER
)
response = client.send_message(message)
```

**Flow**:
1. Domain agent understands intent: `policy_inquiry`
2. Routes to data agent for policy details
3. Prepares comprehensive policy information response

## Agent Communication Protocol

### Message Format

All agents communicate using `python-a2a` standard message format:

```python
{
    "content": {
        "text": "message content or JSON task data",
        "type": "text"
    },
    "role": "user" | "agent",
    "message_id": "uuid",
    "conversation_id": "uuid"
}
```

### Task Data Format

Tasks sent between agents follow this structure:

```python
{
    "action": "action_name",
    "plan_context": {
        "intent": "primary_intent",
        "entities": {"key": "value"},
        "urgency": "low|medium|high"
    },
    "step_info": {
        "agent": "target_agent",
        "priority": 1
    },
    "previous_results": [...]
}
```

### Response Format

Technical agents respond with:

```python
{
    "task_id": "uuid",
    "action": "action_name", 
    "agent_type": "data|notification|fastmcp",
    "status": "completed|error",
    "timestamp": "ISO datetime",
    "data": {...}  # Result data
}
```

## Domain Agent Features

### Intent Understanding
- Uses LLM to analyze user requests
- Extracts entities, urgency, and complexity
- Maps to predefined intent categories

### Plan Creation
- Template-based planning for common intents
- Dynamic plan enhancement based on context
- Support for parallel and sequential execution

### Task Routing
- Intelligent routing using AI router (optional)
- Simple routing based on agent capabilities
- Error handling and fallback mechanisms

### Response Preparation
- LLM-powered response synthesis
- Context-aware response generation
- Error explanation and next steps

## Technical Agent Features

### Data Agent
- Policy validation and retrieval
- Claim record management
- Billing history and calculations
- General information lookup

### Notification Agent
- Multi-channel notifications (email, SMS, push)
- Template-based messaging
- Delivery tracking and status

### FastMCP Agent
- Tool execution and integration
- Fraud detection checks
- Risk assessment calculations
- External service integration

## Configuration

### Domain Agent Configuration
- `DATA_AGENT_URL`: Data agent endpoint (default: http://localhost:8002)
- `NOTIFICATION_AGENT_URL`: Notification agent endpoint (default: http://localhost:8003)
- `FASTMCP_AGENT_URL`: FastMCP agent endpoint (default: http://localhost:8004)

### LLM Configuration
- `OPENROUTER_API_KEY` or `OPENAI_API_KEY`: API key for LLM
- `LLM_MODEL`: Model name (default: anthropic/claude-3.5-sonnet)

## Benefits of Python-A2A Integration

1. **Standardized Communication**: All agents use the same A2A protocol
2. **Scalability**: Easy to add new agents and capabilities
3. **Interoperability**: Compatible with other A2A-compliant systems
4. **Modularity**: Clear separation between domain and technical concerns
5. **Flexibility**: Support for different execution patterns (sequential/parallel)
6. **Observability**: Built-in logging and tracing for debugging

## Future Enhancements

1. **Async Execution**: Implement true parallel task execution
2. **Streaming Responses**: Support for real-time response streaming
3. **Agent Discovery**: Dynamic agent discovery and registration
4. **Load Balancing**: Distribute tasks across multiple agent instances
5. **Caching**: Implement response caching for improved performance
6. **Monitoring**: Add metrics and health checks for all agents

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `python-a2a` is installed in the virtual environment
2. **Connection Refused**: Check if all agents are running on correct ports
3. **LLM Errors**: Verify API keys and model availability
4. **JSON Parsing**: Ensure task data is properly formatted

### Debug Mode

Enable debug logging:
```python
import structlog
structlog.configure(log_level="DEBUG")
```

### Health Checks

Test agent health:
```bash
curl http://localhost:8000/health  # Domain agent
curl http://localhost:8002/health  # Data agent
curl http://localhost:8003/health  # Notification agent
curl http://localhost:8004/health  # FastMCP agent
``` 