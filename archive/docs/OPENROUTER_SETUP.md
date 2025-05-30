# OpenRouter Integration Setup

This document explains how to configure and use OpenRouter API with the Insurance AI PoC.

## Overview

The Insurance AI PoC supports multiple LLM providers:
- **OpenRouter** (recommended) - Access to multiple models through one API
- **OpenAI** - Direct OpenAI API access
- **Demo Mode** - For testing without API keys

## OpenRouter Configuration

### 1. Get an OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Create an account
3. Get your API key from the dashboard

### 2. Configure Environment Variables

Update your `.env` file with the following configuration:

```bash
# LLM API Configuration
OPENROUTER_API_KEY=your-actual-openrouter-api-key-here

# Model Configuration
PRIMARY_MODEL=qwen/qwen3-30b-a3b:free
FALLBACK_MODEL=microsoft/mai-ds-r1:free
EMBEDDING_MODEL=microsoft/mai-ds-r1:free

# OpenRouter Configuration
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### 3. Available Models

OpenRouter provides access to many models. Some free options include:

- `qwen/qwen3-30b-a3b:free` - Qwen 3 model (recommended for primary)
- `microsoft/mai-ds-r1:free` - Microsoft model
- `meta-llama/llama-3.2-1b-instruct:free` - Llama 3.2 model
- `mistralai/mistral-7b-instruct:free` - Mistral 7B model

For paid models, you can use:
- `openai/gpt-4o` - GPT-4 Optimized
- `openai/gpt-4o-mini` - GPT-4 Mini
- `anthropic/claude-3.5-sonnet` - Claude 3.5 Sonnet

## Testing the Configuration

### Run the OpenRouter Integration Test

```bash
source .venv/bin/activate
export PYTHONPATH=/path/to/insurance-ai-poc:$PYTHONPATH
python tests/test_openrouter_llm.py
```

This will test:
- ✅ Configuration loading
- ✅ Model selection
- ✅ LLM API calls (if API key is configured)
- ✅ Claim information extraction

### Run the Comprehensive Test Suite

```bash
source .venv/bin/activate
export PYTHONPATH=/path/to/insurance-ai-poc:$PYTHONPATH
python tests/test_openrouter_integration.py
```

This runs the full test suite including:
- Agent initialization
- Data operations
- Notification functionality
- Task processing
- Architecture compliance

## How It Works

### 1. Claims Agent LLM Integration

The Claims Agent uses LLM for:

```python
# Intent analysis
result = await claims_agent._analyze_user_intent(
    "I was in a car accident and need to file a claim",
    conversation_id
)

# Claim information extraction
claim_info = await claims_agent._extract_claim_information(
    "Policy POL-123, accident yesterday, $5000 damage"
)

# Response generation
response = await claims_agent._generate_claim_response(
    claim_result, fraud_analysis, policy_data
)
```

### 2. Model Fallback

The system automatically uses:
1. **Primary Model** (e.g., `qwen/qwen3-30b-a3b:free`) for main tasks
2. **Fallback Model** (e.g., `microsoft/mai-ds-r1:free`) if primary fails
3. **Demo Mode** if no API key is configured

### 3. Architecture Integration

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claims Agent  │    │   Data Agent    │    │Notification Agent│
│  (Domain + LLM) │◄──►│ (Technical+MCP) │    │ (Technical+MCP) │
│                 │    │                 │    │                 │
│ • Intent Analysis│    │ • Customer Data │    │ • Email/SMS     │
│ • Claim Extract │    │ • Fraud Analysis│    │ • Alerts        │
│ • Response Gen  │    │ • Policy Info   │    │ • Templates     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  OpenRouter API │
                    │                 │
                    │ • qwen/qwen3    │
                    │ • microsoft/mai │
                    │ • llama-3.2     │
                    │ • claude-3.5    │
                    └─────────────────┘
```

## Example Usage

### Filing a Claim

When a customer sends:
> "I was rear-ended yesterday at 5th and Main. Policy POL-AUTO-123. About $8000 damage."

The system:

1. **Claims Agent** uses LLM to analyze intent: `file_claim`
2. **Claims Agent** extracts claim info via LLM
3. **Claims Agent** orchestrates **Data Agent** via A2A protocol
4. **Data Agent** creates claim and analyzes fraud via MCP tools
5. **Claims Agent** orchestrates **Notification Agent**
6. **Notification Agent** sends confirmation email via MCP tools
7. **Claims Agent** generates response via LLM

### Sample LLM Prompt

```
You are an expert insurance claims agent AI. Analyze the user's message and determine:
1. Primary intent (file_claim, check_status, fraud_inquiry, general_question, etc.)
2. Required technical agent actions (data_agent, notification_agent, integration_agent)
3. Information needed from user
4. Response strategy

Available technical agents:
- data_agent: Access policy data, customer information, claims history, fraud analysis
- notification_agent: Send notifications, alerts, emails, SMS
- integration_agent: Interface with external systems, payment processing

Respond in JSON format with: {"intent": str, "confidence": float, "technical_actions": [{"agent": str, "action": str, "params": {}}], "info_needed": [str], "response_strategy": str}
```

## Performance Considerations

### Free Models
- **Pros**: No cost, good for development/testing
- **Cons**: Rate limits, potentially lower quality responses
- **Best for**: Development, testing, proof of concepts

### Paid Models
- **Pros**: Higher quality, better reasoning, fewer rate limits
- **Cons**: Usage costs
- **Best for**: Production deployments

### Caching
- The system caches customer/policy data to reduce API calls
- LLM responses are not cached (to ensure fresh analysis)
- Consider implementing response caching for production

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check your OpenRouter API key
   - Ensure the key is correctly set in `.env`

2. **Model Not Found**
   - Verify the model name is correct
   - Check OpenRouter documentation for available models

3. **Rate Limiting**
   - Switch to a paid model
   - Implement request queuing
   - Add retry logic with exponential backoff

4. **Import Errors**
   - Ensure virtual environment is activated
   - Set PYTHONPATH correctly
   - Install dependencies: `pip install -r requirements.txt`

### Debug Mode

Set environment variable for detailed logging:

```bash
export LOG_LEVEL=DEBUG
python tests/test_openrouter_llm.py
```

## Production Deployment

For production use:

1. **Use paid models** for better reliability
2. **Implement proper error handling** and retries
3. **Monitor API usage** and costs
4. **Set up proper logging** and alerting
5. **Consider model warm-up** for faster responses
6. **Implement rate limiting** to control costs

## Cost Management

- Monitor usage through OpenRouter dashboard
- Set up billing alerts
- Use free models for development
- Implement request caching where appropriate
- Consider model switching based on complexity 