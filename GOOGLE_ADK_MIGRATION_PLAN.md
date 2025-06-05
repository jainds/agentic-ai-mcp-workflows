# Google ADK Migration Plan: Insurance AI Agents

## Executive Summary

This document outlines the comprehensive migration strategy for converting our current insurance AI agent system to Google's Agent Development Kit (ADK). The migration will transform our FastAPI/Flask-based agents into a production-ready, multi-agent system optimized for Google Cloud deployment.

## Current System Analysis

### Existing Architecture
- **Domain Agent** (Port 8003): Customer conversation handler with LLM-based intent analysis
- **Technical Agent** (Port 8002): A2A protocol bridge to Policy FastMCP server
- **Policy Server** (Port 8001): FastMCP server providing insurance data access
- **Technologies**: FastAPI, Flask, OpenAI/OpenRouter, Python A2A, MCP protocol

### Current Strengths
✅ **Modular Architecture**: Clear separation between domain and technical agents  
✅ **LLM Integration**: Advanced intent analysis and response formatting  
✅ **Monitoring**: Comprehensive Langfuse and Prometheus integration  
✅ **Session Management**: Customer authentication and context handling  
✅ **Production Ready**: Kubernetes deployment with health checks  

### Migration Drivers
🎯 **Enhanced Multi-Agent Coordination**: ADK's native agent orchestration  
🎯 **Google Cloud Integration**: Optimized for Vertex AI and Google services  
🎯 **Standardized Agent Protocol**: Industry-standard agent communication  
🎯 **Built-in Evaluation**: Systematic agent performance testing  
🎯 **Enterprise Security**: Native authentication and authorization  

## Migration Strategy Overview

### Phase 1: Foundation Setup (Week 1-2)
- ADK environment setup and tooling
- Core agent framework implementation
- Basic agent-to-agent communication

### Phase 2: Agent Conversion (Week 3-5)
- Domain Agent → ADK LlmAgent conversion
- Technical Agent → ADK specialized agent
- Policy Server → ADK tool integration

### Phase 3: Advanced Features (Week 6-7)
- Multi-agent orchestration
- Session management integration
- Monitoring system adaptation

### Phase 4: Testing & Deployment (Week 8-9)
- Comprehensive testing with ADK evaluation framework
- Performance optimization
- Production deployment to Vertex AI Agent Engine

## Detailed Migration Plan

## Phase 1: Foundation Setup

### 1.1 ADK Environment Setup

```bash
# Install ADK and dependencies
pip install google-adk
pip install google-cloud-storage
pip install google-cloud-vertex-ai

# Create project structure
insurance-adk/
├── agents/
│   ├── domain_agent.py
│   ├── technical_agent.py
│   └── policy_agent.py
├── tools/
│   ├── policy_tools.py
│   ├── customer_tools.py
│   └── session_tools.py
├── config/
│   ├── agent_config.py
│   └── model_config.py
├── tests/
│   ├── agent_tests.py
│   └── evaluation/
├── requirements.txt
└── .env
```

### 1.2 Core Configuration

```python
# config/model_config.py
from google.adk.models import VertexAI, LiteLLM

def get_model_config():
    return {
        "primary_model": VertexAI(model="gemini-2.0-flash-exp"),
        "fallback_model": LiteLLM(model="openai/gpt-4o-mini"),
        "evaluation_model": VertexAI(model="gemini-2.5-pro")
    }
```

### 1.3 Authentication & Security Setup

```python
# config/auth_config.py
from google.adk.auth import AuthConfig

auth_config = AuthConfig(
    service_account_path="path/to/service-account.json",
    vertex_ai_project="insurance-ai-poc",
    vertex_ai_location="us-central1"
)
```

## Phase 2: Agent Conversion

### 2.1 Domain Agent Conversion

**Current Implementation → ADK Migration**

```python
# agents/domain_agent.py - NEW ADK Implementation
from google.adk.agents import LlmAgent
from google.adk.tools import Tool
from tools.session_tools import SessionManager
from tools.policy_tools import PolicyQueryTool

class InsuranceDomainAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="insurance_domain_agent",
            model="gemini-2.0-flash-exp",
            description="Conversational insurance agent handling customer inquiries",
            instruction="""You are an expert insurance domain agent. 
            Analyze customer intents and coordinate with technical agents to provide 
            comprehensive insurance information including policies, coverage, payments, and claims.""",
            tools=[
                SessionManager(),
                PolicyQueryTool(),
                # More tools...
            ],
            sub_agents=[
                "technical_agent",
                "claims_agent"  # Future expansion
            ]
        )
    
    def process_customer_inquiry(self, message: str, session_data: dict):
        """Enhanced customer inquiry processing with ADK context"""
        # ADK automatically handles tool selection and agent delegation
        return self.run(
            input=message,
            context={
                "session": session_data,
                "customer_authenticated": session_data.get("authenticated", False)
            }
        )
```

### 2.2 Technical Agent Conversion

```python
# agents/technical_agent.py - NEW ADK Implementation
from google.adk.agents import LlmAgent
from google.adk.tools import Tool
from tools.policy_tools import MCPPolicyTool

class InsuranceTechnicalAgent(LlmAgent):
    def __init__(self):
        super().__init__(
            name="insurance_technical_agent",
            model="gemini-2.0-flash-exp",
            description="Technical agent for policy data retrieval and processing",
            instruction="""You are a technical insurance agent specializing in 
            policy data retrieval, customer information lookup, and system integration.
            Use MCP tools to access policy servers and format responses appropriately.""",
            tools=[
                MCPPolicyTool(server_url="http://localhost:8001/mcp"),
                # Customer lookup tools
                # Payment processing tools
            ]
        )
    
    async def handle_policy_request(self, customer_id: str, request_type: str):
        """Handle policy requests with ADK tool orchestration"""
        return await self.run_async(
            input=f"Get {request_type} for customer {customer_id}",
            context={"customer_id": customer_id, "request_type": request_type}
        )
```

### 2.3 Tool Integration Strategy

**MCP Server Integration as ADK Tools**

```python
# tools/policy_tools.py
from google.adk.tools import Tool
import httpx
import json

class MCPPolicyTool(Tool):
    """ADK Tool wrapper for MCP Policy Server"""
    
    def __init__(self, server_url: str):
        super().__init__(
            name="policy_lookup",
            description="Retrieve policy information for customers using MCP protocol"
        )
        self.server_url = server_url
    
    async def execute(self, customer_id: str, query_type: str = "policies") -> dict:
        """Execute MCP call and return structured results"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.server_url}/tools/call",
                json={
                    "name": "get_customer_policies",
                    "arguments": {"customer_id": customer_id}
                }
            )
            return response.json()

class SessionManager(Tool):
    """Session management tool for customer authentication"""
    
    def __init__(self):
        super().__init__(
            name="session_manager",
            description="Manage customer sessions and authentication state"
        )
    
    def get_session_data(self, session_id: str) -> dict:
        """Retrieve session data for authenticated customers"""
        # Implementation for session retrieval
        pass
    
    def validate_customer(self, customer_id: str) -> bool:
        """Validate customer authentication"""
        # Implementation for customer validation
        pass
```

## Phase 3: Advanced Features

### 3.1 Multi-Agent Orchestration

```python
# agents/orchestrator.py
from google.adk.agents import LlmAgent, Sequential, Parallel
from agents.domain_agent import InsuranceDomainAgent
from agents.technical_agent import InsuranceTechnicalAgent

class InsuranceOrchestrator(LlmAgent):
    def __init__(self):
        super().__init__(
            name="insurance_orchestrator",
            model="gemini-2.5-pro",
            description="Main orchestrator for insurance agent system",
            instruction="""You coordinate multiple insurance agents to provide 
            comprehensive customer service. Route requests appropriately and 
            synthesize responses from multiple agents.""",
            sub_agents=[
                InsuranceDomainAgent(),
                InsuranceTechnicalAgent()
            ]
        )
    
    def handle_complex_inquiry(self, customer_message: str, session_data: dict):
        """Handle complex inquiries requiring multiple agent coordination"""
        
        # ADK automatically handles agent selection and coordination
        workflow = Sequential([
            ("intent_analysis", "domain_agent"),
            ("data_retrieval", "technical_agent"),
            ("response_synthesis", "domain_agent")
        ])
        
        return workflow.run(
            input=customer_message,
            context={"session": session_data}
        )
```

### 3.2 Session Management Integration

```python
# tools/session_tools.py
from google.adk.tools import Tool
from google.adk.state import State

class ADKSessionManager(Tool):
    """ADK-native session management"""
    
    def __init__(self):
        super().__init__(
            name="session_manager",
            description="Advanced session management with ADK state"
        )
    
    def get_or_create_session(self, user_id: str, state: State) -> dict:
        """Get or create session with ADK state management"""
        session_key = f"session_{user_id}"
        
        if session_key in state:
            return state.get(session_key)
        
        # Create new session
        session_data = {
            "user_id": user_id,
            "authenticated": False,
            "conversation_history": [],
            "created_at": datetime.now().isoformat()
        }
        
        state.set(session_key, session_data)
        return session_data
    
    def update_session(self, user_id: str, updates: dict, state: State):
        """Update session with new information"""
        session_key = f"session_{user_id}"
        session_data = state.get(session_key, {})
        session_data.update(updates)
        state.set(session_key, session_data)
```

### 3.3 Monitoring Integration

```python
# monitoring/adk_monitoring.py
from google.adk.callbacks import Callback
from monitoring.providers.langfuse_provider import LangfuseProvider

class ADKLangfuseCallback(Callback):
    """Integration between ADK and existing Langfuse monitoring"""
    
    def __init__(self):
        self.langfuse = LangfuseProvider()
    
    def on_agent_start(self, agent_name: str, input_data: dict):
        """Track agent execution start"""
        if self.langfuse.is_enabled():
            self.trace_id = self.langfuse.start_trace(
                name=f"adk_agent_{agent_name}",
                input=input_data
            )
    
    def on_agent_end(self, agent_name: str, output_data: dict, success: bool):
        """Track agent execution completion"""
        if self.langfuse.is_enabled():
            self.langfuse.end_trace(
                trace_id=self.trace_id,
                output=output_data,
                success=success
            )
    
    def on_tool_call(self, tool_name: str, inputs: dict, outputs: dict):
        """Track tool calls within agents"""
        if self.langfuse.is_enabled():
            self.langfuse.log_tool_call(
                tool_name=tool_name,
                inputs=inputs,
                outputs=outputs
            )
```

## Phase 4: Testing & Deployment

### 4.1 ADK Evaluation Framework

```python
# tests/evaluation/agent_evaluation.py
from google.adk.evaluation import AgentEvaluator, TestCase

def create_insurance_test_cases():
    """Create comprehensive test cases for insurance agents"""
    return [
        TestCase(
            name="policy_inquiry_authenticated",
            input="What are my policy details?",
            context={"session": {"customer_id": "CUST-001", "authenticated": True}},
            expected_output_contains=["policy", "coverage", "premium"],
            evaluation_criteria=["accuracy", "completeness", "response_time"]
        ),
        TestCase(
            name="claims_inquiry_unauthenticated",
            input="I need to file a claim",
            context={"session": {"authenticated": False}},
            expected_output_contains=["login", "authentication"],
            evaluation_criteria=["security", "user_guidance"]
        ),
        # More test cases...
    ]

def run_agent_evaluation():
    """Run comprehensive agent evaluation"""
    evaluator = AgentEvaluator(
        agent=InsuranceOrchestrator(),
        test_cases=create_insurance_test_cases(),
        evaluation_model="gemini-2.5-pro"
    )
    
    results = evaluator.evaluate()
    return results
```

### 4.2 Deployment Configuration

```python
# deployment/vertex_ai_config.py
from google.adk.deploy import VertexAIConfig

def create_deployment_config():
    """Create Vertex AI Agent Engine deployment configuration"""
    return VertexAIConfig(
        project_id="insurance-ai-poc",
        region="us-central1",
        agent_name="insurance-adk-system",
        runtime_config={
            "machine_type": "n1-standard-4",
            "max_replicas": 10,
            "min_replicas": 2
        },
        environment_variables={
            "LANGFUSE_SECRET_KEY": "from_secret_manager",
            "POLICY_SERVER_URL": "internal_service_url"
        }
    )
```

### 4.3 Migration Testing Strategy

```bash
# Test execution pipeline
#!/bin/bash

# Phase 1: Unit Tests
echo "Running ADK unit tests..."
python -m pytest tests/unit/ -v

# Phase 2: Integration Tests
echo "Running ADK integration tests..."
python -m pytest tests/integration/ -v

# Phase 3: Agent Evaluation
echo "Running ADK agent evaluation..."
python tests/evaluation/agent_evaluation.py

# Phase 4: Performance Tests
echo "Running performance comparison..."
python tests/performance/adk_vs_current.py

# Phase 5: End-to-End Tests
echo "Running E2E tests..."
adk eval tests/evaluation/e2e_test_cases.json
```

## Risk Assessment & Mitigation

### High-Risk Areas
❌ **Session Management Complexity**: Current thread-local session handling  
🛠️ **Mitigation**: Implement ADK State management with comprehensive testing

❌ **MCP Protocol Integration**: Complex tool calling patterns  
🛠️ **Mitigation**: Create robust ADK tool wrappers with fallback mechanisms

❌ **Monitoring System Migration**: Extensive Langfuse integration  
🛠️ **Mitigation**: Phased migration with parallel monitoring systems

### Medium-Risk Areas
⚠️ **Performance Changes**: Different execution patterns  
🛠️ **Mitigation**: Comprehensive performance testing and optimization

⚠️ **Deployment Complexity**: New Vertex AI Agent Engine deployment  
🛠️ **Mitigation**: Gradual rollout with canary deployments

## Migration Timeline

| Phase | Duration | Key Deliverables | Success Criteria |
|-------|----------|------------------|------------------|
| **Phase 1** | 2 weeks | ADK setup, basic agents | Agents respond to simple queries |
| **Phase 2** | 3 weeks | Converted agents, tool integration | Feature parity with current system |
| **Phase 3** | 2 weeks | Multi-agent orchestration | Complex workflows functioning |
| **Phase 4** | 2 weeks | Testing, deployment | Production-ready ADK system |

## Success Metrics

### Functional Metrics
- ✅ **Feature Parity**: 100% of current functionality migrated
- ✅ **Response Accuracy**: ≥95% correct responses in evaluation
- ✅ **Agent Coordination**: Multi-agent workflows functioning smoothly

### Performance Metrics
- 🚀 **Response Time**: ≤2s for simple queries, ≤5s for complex
- 🚀 **Throughput**: Handle current load with 20% headroom
- 🚀 **Availability**: 99.9% uptime SLA

### Quality Metrics
- 📊 **Code Coverage**: ≥90% test coverage for all agents
- 📊 **Evaluation Score**: ≥85% on ADK evaluation framework
- 📊 **Monitoring**: Full observability maintained

## Benefits Realization

### Immediate Benefits (Post-Migration)
- 🎯 **Standardized Framework**: Industry-standard agent development
- 🎯 **Enhanced Coordination**: Native multi-agent orchestration
- 🎯 **Google Cloud Integration**: Optimized for Vertex AI ecosystem

### Long-term Benefits (3-6 months)
- 🚀 **Scalability**: Vertex AI Agent Engine auto-scaling
- 🚀 **Extensibility**: Easy addition of new specialized agents
- 🚀 **Maintenance**: Reduced operational overhead with managed services

## Conclusion

The migration to Google ADK represents a strategic evolution of our insurance AI system. By leveraging ADK's native multi-agent capabilities, Google Cloud integration, and enterprise-grade features, we'll create a more robust, scalable, and maintainable agent system.

The phased approach ensures minimal disruption while systematically upgrading our architecture to meet future requirements for AI agent deployment at scale.

## Next Steps

1. **Week 1**: Get stakeholder approval and setup ADK development environment
2. **Week 2**: Begin Phase 1 implementation with core team
3. **Week 3**: Start agent conversion with continuous testing
4. **Week 4**: Implement monitoring integration and evaluation framework
5. **Week 8**: Production deployment preparation and rollout planning

---

*This migration plan is designed to be executed iteratively with continuous validation at each phase. Regular checkpoints should be established to ensure alignment with business objectives and technical requirements.* 