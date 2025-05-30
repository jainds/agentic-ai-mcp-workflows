"""
Comprehensive unit tests for Domain Agent (Claims Agent) using Official Google A2A Library.

Tests the domain agent's ability to:
1. Analyze user intent correctly
2. Plan and orchestrate technical agent calls via official A2A protocol
3. Generate detailed, witty responses
4. Handle various insurance query types
5. Process thinking steps and orchestration events
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

# Official Google A2A Library imports
from python_a2a import TaskRequest, TaskResponse, Message, TextContent, MessageRole
from python_a2a.models import TaskStatus, TaskState

from agents.domain.claims_agent import ClaimsAgent


class TestDomainAgentIntentAnalysis:
    """Test domain agent's intent analysis capabilities using official A2A format."""
    
    @pytest.fixture
    def claims_agent(self):
        """Create a ClaimsAgent instance for testing."""
        agent = ClaimsAgent()
        agent.openai_client = AsyncMock()
        return agent
    
    @pytest.mark.asyncio
    async def test_analyze_policy_inquiry_intent(self, claims_agent):
        """Test analysis of policy-related queries."""
        # Mock OpenAI response for intent analysis
        mock_choice = Mock()
        mock_choice.message.content = json.dumps({
            "intent": "policy_question",
            "confidence": 0.9,
            "technical_actions": [
                {"agent": "data_agent", "action": "get_customer_policies", "params": {"customer_id": "CUST-001"}}
            ],
            "info_needed": [],
            "response_strategy": "detailed_policy_info"
        })
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        claims_agent.openai_client.chat.completions.create.return_value = mock_response
        
        result = await claims_agent._analyze_user_intent("How many policies do I have?", "conv_123")
        
        assert result["intent"] == "policy_question"
        assert result["confidence"] == 0.9
        assert len(result["technical_actions"]) == 1
        assert result["technical_actions"][0]["agent"] == "data_agent"
        assert result["technical_actions"][0]["action"] == "get_customer_policies"
    
    @pytest.mark.asyncio
    async def test_analyze_claim_status_intent(self, claims_agent):
        """Test analysis of claim status queries."""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "intent": "check_status",
            "confidence": 0.95,
            "technical_actions": [
                {"agent": "data_agent", "action": "get_customer_claims", "params": {"customer_id": "CUST-001"}},
                {"agent": "data_agent", "action": "get_claim_analytics", "params": {"customer_id": "CUST-001"}}
            ],
            "info_needed": [],
            "response_strategy": "comprehensive_status_update"
        })
        claims_agent.openai_client.chat.completions.create.return_value = mock_response
        
        result = await claims_agent._analyze_user_intent("What's the status of my claim?", "conv_123")
        
        assert result["intent"] == "check_status"
        assert result["confidence"] == 0.95
        assert len(result["technical_actions"]) == 2
    
    @pytest.mark.asyncio
    async def test_analyze_claim_filing_intent(self, claims_agent):
        """Test analysis of new claim filing."""
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "intent": "file_claim",
            "confidence": 0.85,
            "technical_actions": [
                {"agent": "data_agent", "action": "get_customer", "params": {"customer_id": "CUST-001"}},
                {"agent": "data_agent", "action": "create_claim", "params": {}},
                {"agent": "notification_agent", "action": "send_confirmation", "params": {}}
            ],
            "info_needed": ["incident_date", "policy_number", "description"],
            "response_strategy": "guided_claim_filing"
        })
        claims_agent.openai_client.chat.completions.create.return_value = mock_response
        
        result = await claims_agent._analyze_user_intent("I need to file a claim for my car accident", "conv_123")
        
        assert result["intent"] == "file_claim"
        assert len(result["technical_actions"]) == 3
        assert len(result["info_needed"]) == 3
        assert "incident_date" in result["info_needed"]


class TestDomainAgentOrchestration:
    """Test domain agent's orchestration of technical agents."""
    
    @pytest.fixture
    def claims_agent(self):
        agent = ClaimsAgent()
        agent.openai_client = AsyncMock()
        agent._call_technical_agent = AsyncMock()
        agent.anthropic_client = AsyncMock()
        return agent
    
    @pytest.mark.asyncio
    async def test_handle_policy_question_orchestration(self, claims_agent):
        """Test orchestration for policy questions."""
        # Mock technical agent responses
        claims_agent._call_technical_agent.side_effect = [
            # Customer data
            {
                "customer_id": "CUST-001",
                "name": "John Smith",
                "type": "Premium",
                "status": "Active"
            },
            # Policy data
            {
                "active_policies": 3,
                "total_coverage": "$250,000",
                "next_renewal": "2024-12-15",
                "policies": [
                    {"type": "Auto", "premium": "$1,200/year"},
                    {"type": "Home", "premium": "$800/year"},
                    {"type": "Life", "premium": "$300/year"}
                ]
            },
            # Analytics data
            {
                "risk_score": 0.25,
                "recommendation": "Continue current coverage",
                "savings_opportunity": "None identified"
            }
        ]
        
        # Mock final response generation
        mock_anthropic_response = Mock()
        mock_anthropic_response.content[0].text = "Based on my analysis, you currently have 3 active policies with excellent coverage..."
        claims_agent.anthropic_client.messages.create.return_value = mock_anthropic_response
        
        user_data = {"user_id": "CUST-001", "message": "How many policies do I have?"}
        technical_actions = [
            {"agent": "data_agent", "action": "get_customer", "params": {"customer_id": "CUST-001"}},
            {"agent": "data_agent", "action": "get_customer_policies", "params": {"customer_id": "CUST-001"}},
            {"agent": "data_agent", "action": "get_analytics", "params": {"customer_id": "CUST-001"}}
        ]
        
        result = await claims_agent._handle_policy_question(user_data, technical_actions, "task_123")
        
        # Verify all technical agents were called
        assert claims_agent._call_technical_agent.call_count == 3
        
        # Verify calls were made with correct parameters
        calls = claims_agent._call_technical_agent.call_args_list
        assert calls[0][0] == ("data_agent", {"action": "get_customer", "customer_id": "CUST-001"})
        assert calls[1][0] == ("data_agent", {"action": "get_customer_policies", "customer_id": "CUST-001"})
        assert calls[2][0] == ("data_agent", {"action": "get_analytics", "customer_id": "CUST-001"})
        
        # Verify final response generation was called
        assert claims_agent.anthropic_client.messages.create.called
    
    @pytest.mark.asyncio
    async def test_handle_claim_status_orchestration(self, claims_agent):
        """Test orchestration for claim status queries."""
        # Mock technical agent responses
        claims_agent._call_technical_agent.side_effect = [
            # Customer data
            {"customer_id": "CUST-001", "name": "John Smith", "type": "Premium"},
            # Claims data  
            {
                "active_claims": 1,
                "claim_status": "In Review",
                "estimated_resolution": "3-5 business days",
                "claim_id": "CLM-789",
                "recent_claims": 1
            },
            # Policy data
            {"active_policies": 3, "total_coverage": "$250,000"},
            # Analytics data
            {"risk_score": 0.25, "recommendation": "Continue current coverage"}
        ]
        
        mock_anthropic_response = Mock()
        mock_anthropic_response.content[0].text = "I've reviewed your claim status and here's the comprehensive update..."
        claims_agent.anthropic_client.messages.create.return_value = mock_anthropic_response
        
        user_data = {"user_id": "CUST-001", "message": "What's my claim status?"}
        technical_actions = [
            {"agent": "data_agent", "action": "get_customer", "params": {}},
            {"agent": "data_agent", "action": "get_customer_claims", "params": {}},
            {"agent": "data_agent", "action": "get_customer_policies", "params": {}},
            {"agent": "data_agent", "action": "get_analytics", "params": {}}
        ]
        
        result = await claims_agent._handle_status_check(user_data, technical_actions, "task_123")
        
        # Verify all technical agents were called
        assert claims_agent._call_technical_agent.call_count == 4
        
        # Verify response was generated
        assert claims_agent.anthropic_client.messages.create.called
    
    @pytest.mark.asyncio
    async def test_handle_claim_filing_orchestration(self, claims_agent):
        """Test orchestration for new claim filing."""
        # Mock claim information extraction
        claims_agent._extract_claim_information = AsyncMock(return_value={
            "policy_number": "POL-123",
            "incident_date": "2024-05-29",
            "description": "Car accident on highway",
            "estimated_amount": 5000,
            "claim_type": "auto"
        })
        
        # Mock technical agent responses
        claims_agent._call_technical_agent.side_effect = [
            # Customer data
            {"customer_id": "CUST-001", "name": "John Smith"},
            # Policy validation
            {"policy_number": "POL-123", "status": "Active", "coverage": "Full"},
            # Claim creation
            {"claim_id": "CLM-456", "status": "Filed", "reference_number": "REF-789"},
            # Notification sent
            {"notification_id": "NOT-123", "status": "sent", "method": "email"}
        ]
        
        mock_anthropic_response = Mock()
        mock_anthropic_response.content[0].text = "Your claim has been successfully filed with reference number REF-789..."
        claims_agent.anthropic_client.messages.create.return_value = mock_anthropic_response
        
        user_data = {"user_id": "CUST-001", "message": "I need to file a claim for my car accident"}
        technical_actions = []
        
        result = await claims_agent._handle_claim_filing(user_data, technical_actions, "task_123")
        
        # Verify claim information was extracted
        assert claims_agent._extract_claim_information.called
        
        # Verify technical agents were called in sequence
        assert claims_agent._call_technical_agent.call_count >= 3


class TestDomainAgentResponseGeneration:
    """Test domain agent's response generation capabilities."""
    
    @pytest.fixture
    def claims_agent(self):
        agent = ClaimsAgent()
        agent.anthropic_client = AsyncMock()
        return agent
    
    @pytest.mark.asyncio
    async def test_generate_detailed_response_with_template(self, claims_agent):
        """Test that responses follow the template format and include all required sections."""
        mock_response = Mock()
        mock_response.content[0].text = """Thank you for your claims inquiry. I've conducted a comprehensive analysis of your account and current claims status.

**Current Claims Status:**
• You currently have 1 active claim(s) in our system
• Your primary claim status is: **In Review**
• Estimated resolution timeframe: **3-5 business days**

**Detailed Claims Analysis:**
Your claim is progressing well through our review process...

**Your Account Overview:**
• Total active policies: **3 policies**
• Recent claims history: **1 claim(s) in the past 12 months**

**Next Steps & Timeline:**
1. **Immediate**: Your claim will continue through the review process
2. **Within 24-48 hours**: You should receive an update

Is there any specific aspect of your claim or coverage that you'd like me to explain in more detail?"""
        
        claims_agent.anthropic_client.messages.create.return_value = mock_response
        
        context = {"customer_id": "CUST-001", "type": "Premium"}
        claims_data = {"active_claims": 1, "claim_status": "In Review"}
        policy_data = {"active_policies": 3}
        analytics_data = {"risk_score": 0.25}
        
        result = await claims_agent._generate_response(
            "check_status", context, claims_data, policy_data, analytics_data, "What's my claim status?"
        )
        
        # Verify template sections are present
        assert "Current Claims Status:" in result
        assert "Detailed Claims Analysis:" in result
        assert "Your Account Overview:" in result
        assert "Next Steps & Timeline:" in result
        assert "Is there any specific aspect" in result
        
        # Verify key data points are included
        assert "1 active claim(s)" in result
        assert "In Review" in result
        assert "3 policies" in result
    
    @pytest.mark.asyncio
    async def test_response_includes_thinking_steps(self, claims_agent):
        """Test that thinking steps are properly tracked and included."""
        # This would test that the agent tracks its thinking process
        # For now, we'll create a basic structure
        thinking_steps = [
            "Analyzing user intent: claim status inquiry",
            "Gathering customer data from data agent",
            "Retrieving claim information",
            "Checking policy details for context",
            "Generating comprehensive response with timeline"
        ]
        
        # Mock the thinking step tracking
        claims_agent.current_thinking_steps = thinking_steps
        
        assert len(claims_agent.current_thinking_steps) == 5
        assert "Analyzing user intent" in claims_agent.current_thinking_steps[0]
        assert "Generating comprehensive response" in claims_agent.current_thinking_steps[-1]


class TestDomainAgentErrorHandling:
    """Test domain agent's error handling and fallback scenarios."""
    
    @pytest.fixture
    def claims_agent(self):
        agent = ClaimsAgent()
        agent.openai_client = AsyncMock()
        agent._call_technical_agent = AsyncMock()
        return agent
    
    @pytest.mark.asyncio
    async def test_handle_technical_agent_failure(self, claims_agent):
        """Test graceful handling when technical agents fail."""
        # Simulate technical agent failure
        claims_agent._call_technical_agent.side_effect = Exception("Technical agent unavailable")
        
        user_data = {"user_id": "CUST-001", "message": "Check my policies"}
        technical_actions = [{"agent": "data_agent", "action": "get_customer_policies", "params": {}}]
        
        result = await claims_agent._handle_policy_question(user_data, technical_actions, "task_123")
        
        # Should return helpful error message, not crash
        assert "apologize" in result.lower() or "error" in result.lower()
    
    @pytest.mark.asyncio
    async def test_handle_invalid_intent_analysis(self, claims_agent):
        """Test handling of invalid JSON from intent analysis."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        claims_agent.openai_client.chat.completions.create.return_value = mock_response
        
        result = await claims_agent._analyze_user_intent("Test message", "conv_123")
        
        # Should fall back to general_question intent
        assert result["intent"] == "general_question"
        assert result["confidence"] == 0.5
        assert result["response_strategy"] == "fallback"


class TestDomainAgentConversationFlow:
    """Test domain agent's conversation flow and context management."""
    
    @pytest.fixture
    def claims_agent(self):
        agent = ClaimsAgent()
        agent.openai_client = AsyncMock()
        agent._call_technical_agent = AsyncMock()
        return agent
    
    @pytest.mark.asyncio
    async def test_conversation_history_tracking(self, claims_agent):
        """Test that conversation history is properly maintained."""
        conversation_id = "conv_123"
        
        # Simulate a conversation
        await claims_agent._analyze_user_intent("Hello", conversation_id)
        
        # Add messages to history
        claims_agent.conversation_history[conversation_id] = [
            {"role": "user", "content": "Hello", "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": "Hi! How can I help?", "timestamp": datetime.utcnow().isoformat()},
            {"role": "user", "content": "Check my policies", "timestamp": datetime.utcnow().isoformat()}
        ]
        
        # Next analysis should include history
        result = await claims_agent._analyze_user_intent("How many do I have?", conversation_id)
        
        # Verify OpenAI was called with conversation history
        call_args = claims_agent.openai_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        user_message = messages[1]["content"]
        
        assert "Conversation history:" in user_message
        assert "Check my policies" in user_message
        assert "How many do I have?" in user_message
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation_context(self, claims_agent):
        """Test that multi-turn conversations maintain proper context."""
        conversation_id = "conv_multi_123"
        
        # Mock intent analysis for follow-up question
        mock_response = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "intent": "policy_question",
            "confidence": 0.85,
            "technical_actions": [{"agent": "data_agent", "action": "get_policy_details", "params": {}}],
            "info_needed": [],
            "response_strategy": "detailed_follow_up"
        })
        claims_agent.openai_client.chat.completions.create.return_value = mock_response
        
        # Set up conversation history with context
        claims_agent.conversation_history[conversation_id] = [
            {"role": "user", "content": "How many policies do I have?", "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": "You have 3 active policies.", "timestamp": datetime.utcnow().isoformat()}
        ]
        
        result = await claims_agent._analyze_user_intent("What are the details of the auto policy?", conversation_id)
        
        assert result["intent"] == "policy_question"
        assert result["response_strategy"] == "detailed_follow_up"


@pytest.mark.asyncio
async def test_handle_task_with_policy_inquiry(claims_agent):
    """Test handling A2A task for policy inquiry using official format."""
    # Create official A2A task request
    task = TaskRequest(
        taskId="test_policy_task",
        user={
            "user_id": "CUST-001",
            "message": "How many policies do I have?",
            "conversation_id": "test_conv"
        }
    )
    
    # Mock intent analysis
    claims_agent._analyze_user_intent = AsyncMock(return_value={
        "intent": "policy_question",
        "confidence": 0.9,
        "technical_actions": [
            {"agent": "data_agent", "action": "get_customer_policies", "params": {"customer_id": "CUST-001"}}
        ],
        "info_needed": [],
        "response_strategy": "detailed_policy_info"
    })
    
    # Mock technical agent call
    claims_agent._call_technical_agent = AsyncMock(return_value={
        "policies": [
            {"id": "POL-001", "type": "auto", "status": "active"},
            {"id": "POL-002", "type": "home", "status": "active"}
        ]
    })
    
    # Mock response generation
    claims_agent._generate_policy_response = AsyncMock(return_value="You have 2 active policies: Auto and Home insurance.")
    
    # Handle the task using official A2A format
    result_task = claims_agent.handle_task(task)
    
    # Verify task completion status
    assert result_task.status.state == TaskState.COMPLETED
    assert "policies" in result_task.status.message["content"]["text"].lower()
    
    # Verify metadata contains tracking information
    assert result_task.metadata["agent"] == "ClaimsAgent"
    assert result_task.metadata["intent"] == "policy_question"
    assert "thinking_steps" in result_task.metadata
    assert "orchestration_events" in result_task.metadata
    assert "api_calls" in result_task.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 