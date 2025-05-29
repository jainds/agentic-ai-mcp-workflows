"""
System Integration Tests for Insurance AI PoC
Tests the complete flow from customer queries to technical agent execution
"""

import pytest
import asyncio
import json
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Import the agents
from agents.domain.claims_agent import ClaimsAgent
from agents.technical.data_agent import DataAgent
from agents.technical.notification_agent import NotificationAgent
from agents.shared.a2a_base import TaskRequest, TaskResponse


class TestSystemIntegration:
    """Test the complete system integration"""

    @pytest.fixture
    async def claims_agent(self):
        """Create a Claims Agent for testing"""
        agent = ClaimsAgent(port=8000)
        yield agent

    @pytest.fixture
    async def data_agent(self):
        """Create a Data Agent for testing"""
        agent = DataAgent(port=8002)
        yield agent

    @pytest.fixture
    async def notification_agent(self):
        """Create a Notification Agent for testing"""
        agent = NotificationAgent(port=8003)
        yield agent

    @pytest.mark.asyncio
    async def test_claim_filing_flow(self, claims_agent):
        """Test the complete claim filing flow"""
        
        # Mock the technical agent calls
        with patch.object(claims_agent, '_call_technical_agent') as mock_tech_call:
            
            # Set up mock responses from technical agents
            def mock_technical_agent_response(agent_name: str, task_data: Dict[str, Any]):
                action = task_data.get("action")
                
                if agent_name == "data_agent":
                    if action == "get_customer":
                        return {
                            "customer_id": "cust_123",
                            "name": "John Doe",
                            "email": "john.doe@email.com",
                            "risk_score": 0.3
                        }
                    elif action == "get_customer_policies":
                        return [{
                            "policy_number": "POL_123",
                            "policy_type": "auto",
                            "coverage_limit": 50000,
                            "status": "active"
                        }]
                    elif action == "create_claim":
                        return {
                            "claim_id": "CLM_123",
                            "status": "processing",
                            "created_at": "2024-01-01T00:00:00Z"
                        }
                    elif action == "analyze_fraud":
                        return {
                            "fraud_score": 0.2,
                            "risk_level": "low",
                            "indicators": [],
                            "recommendation": "Standard processing"
                        }
                
                elif agent_name == "notification_agent":
                    if action == "send_template_notification":
                        return {
                            "notification_id": "NOTIF_123",
                            "status": "sent"
                        }
                
                return {"status": "success"}
            
            mock_tech_call.side_effect = mock_technical_agent_response
            
            # Create a claim filing task
            task = TaskRequest(
                taskId="task_123",
                requestId="req_123",
                user={
                    "user_id": "cust_123",
                    "message": "I need to file a claim for my car accident yesterday. My policy number is POL_123. The damage is estimated at $5000.",
                    "conversation_id": "conv_123"
                }
            )
            
            # Process the task
            response = await claims_agent.process_task(task)
            
            # Verify the response
            assert response.status == "completed"
            assert response.taskId == "task_123"
            assert len(response.parts) == 1
            assert "claim" in response.parts[0]["text"].lower()
            
            # Verify technical agent calls were made
            assert mock_tech_call.call_count >= 4  # get_customer, get_policies, create_claim, analyze_fraud
            
            # Verify specific calls
            call_args = [call.args for call in mock_tech_call.call_args_list]
            agent_calls = [args[0] for args in call_args]
            
            assert "data_agent" in agent_calls
            assert "notification_agent" in agent_calls

    @pytest.mark.asyncio
    async def test_status_check_flow(self, claims_agent):
        """Test the claim status check flow"""
        
        with patch.object(claims_agent, '_call_technical_agent') as mock_tech_call:
            
            # Mock response from data agent
            mock_tech_call.return_value = [
                {
                    "claim_id": "CLM_123",
                    "status": "processing",
                    "created_at": "2024-01-01T00:00:00Z",
                    "amount": 5000
                }
            ]
            
            # Create a status check task
            task = TaskRequest(
                taskId="task_status",
                requestId="req_status",
                user={
                    "user_id": "cust_123",
                    "message": "What's the status of my claims?",
                    "conversation_id": "conv_status"
                }
            )
            
            # Process the task
            response = await claims_agent.process_task(task)
            
            # Verify the response
            assert response.status == "completed"
            assert "claim" in response.parts[0]["text"].lower()
            
            # Verify data agent was called
            mock_tech_call.assert_called()
            args = mock_tech_call.call_args.args
            assert args[0] == "data_agent"
            assert args[1]["action"] == "get_customer_claims"

    @pytest.mark.asyncio
    async def test_fraud_inquiry_flow(self, claims_agent):
        """Test the fraud inquiry flow"""
        
        with patch.object(claims_agent, '_call_technical_agent') as mock_tech_call:
            
            # Mock response from notification agent
            mock_tech_call.return_value = {
                "alert_id": "ALERT_123",
                "status": "sent"
            }
            
            # Create a fraud inquiry task
            task = TaskRequest(
                taskId="task_fraud",
                requestId="req_fraud",
                user={
                    "user_id": "cust_123",
                    "message": "I think there's fraudulent activity on my account",
                    "conversation_id": "conv_fraud"
                }
            )
            
            # Process the task
            response = await claims_agent.process_task(task)
            
            # Verify the response
            assert response.status == "completed"
            assert "fraud" in response.parts[0]["text"].lower()
            
            # Verify notification agent was called
            mock_tech_call.assert_called()
            args = mock_tech_call.call_args.args
            assert args[0] == "notification_agent"
            assert args[1]["action"] == "send_alert"

    @pytest.mark.asyncio
    async def test_data_agent_tools(self, data_agent):
        """Test Data Agent MCP tools"""
        
        # Test get_customer tool
        customer_result = await data_agent._get_customer("cust_123")
        assert "customer_id" in customer_result
        assert customer_result["customer_id"] == "cust_123"
        
        # Test get_customer_policies tool
        policies_result = await data_agent._get_customer_policies("cust_123")
        assert isinstance(policies_result, list)
        assert len(policies_result) > 0
        assert "policy_number" in policies_result[0]
        
        # Test create_claim tool
        claim_data = {
            "customer_id": "cust_123",
            "description": "Test claim",
            "amount": 1000,
            "claim_type": "auto"
        }
        claim_result = await data_agent._create_claim(claim_data)
        assert "claim_id" in claim_result
        assert claim_result["status"] == "processing"
        
        # Test fraud analysis tool
        fraud_result = await data_agent._analyze_fraud(claim_data)
        assert "fraud_score" in fraud_result
        assert "risk_level" in fraud_result
        assert isinstance(fraud_result["fraud_score"], float)
        assert fraud_result["fraud_score"] >= 0.0
        assert fraud_result["fraud_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_notification_agent_tools(self, notification_agent):
        """Test Notification Agent MCP tools"""
        
        # Test email notification
        email_result = await notification_agent._send_email(
            to="test@example.com",
            subject="Test Email",
            body="This is a test email"
        )
        assert email_result["status"] == "sent"
        assert "notification_id" in email_result
        
        # Test SMS notification
        sms_result = await notification_agent._send_sms(
            phone="+1234567890",
            message="Test SMS"
        )
        assert sms_result["status"] == "sent"
        assert "notification_id" in sms_result
        
        # Test alert sending
        alert_result = await notification_agent._send_alert(
            alert_type="fraud",
            severity="high",
            message="Test fraud alert"
        )
        assert alert_result["status"] == "sent"
        assert "alert_id" in alert_result
        
        # Test template notification
        template_result = await notification_agent._send_template_notification(
            template_name="claim_approved",
            recipients=["customer@example.com"],
            variables={"claim_id": "CLM_123", "customer_name": "John Doe", "amount": "5000"}
        )
        assert template_result["recipients_count"] == 1

    @pytest.mark.asyncio
    async def test_llm_intent_analysis(self, claims_agent):
        """Test LLM intent analysis functionality"""
        
        # Mock OpenAI client
        with patch.object(claims_agent.openai_client.chat.completions, 'create') as mock_openai:
            
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps({
                "intent": "file_claim",
                "confidence": 0.9,
                "technical_actions": [
                    {"agent": "data_agent", "action": "get_customer", "params": {}},
                    {"agent": "data_agent", "action": "create_claim", "params": {}}
                ],
                "info_needed": [],
                "response_strategy": "process_claim"
            })
            mock_openai.return_value = mock_response
            
            # Test intent analysis
            result = await claims_agent._analyze_user_intent(
                "I need to file a claim for my car accident",
                "conv_123"
            )
            
            # Verify the result
            assert result["intent"] == "file_claim"
            assert result["confidence"] == 0.9
            assert len(result["technical_actions"]) == 2
            assert result["technical_actions"][0]["agent"] == "data_agent"
            
            # Verify OpenAI was called
            mock_openai.assert_called_once()

    @pytest.mark.asyncio
    async def test_conversation_history(self, claims_agent):
        """Test conversation history management"""
        
        conversation_id = "conv_history_test"
        
        # Mock technical agent calls
        with patch.object(claims_agent, '_call_technical_agent'):
            
            # Send first message
            task1 = TaskRequest(
                taskId="task_1",
                requestId="req_1",
                user={
                    "user_id": "cust_123",
                    "message": "Hello, I need help with insurance",
                    "conversation_id": conversation_id
                }
            )
            
            await claims_agent.process_task(task1)
            
            # Send second message
            task2 = TaskRequest(
                taskId="task_2",
                requestId="req_2",
                user={
                    "user_id": "cust_123",
                    "message": "I want to file a claim",
                    "conversation_id": conversation_id
                }
            )
            
            await claims_agent.process_task(task2)
            
            # Verify conversation history
            assert conversation_id in claims_agent.conversation_history
            history = claims_agent.conversation_history[conversation_id]
            
            # Should have 4 entries: user message 1, assistant response 1, user message 2, assistant response 2
            assert len(history) == 4
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"
            assert history[2]["role"] == "user"
            assert history[3]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_error_handling(self, claims_agent):
        """Test error handling in the system"""
        
        # Mock technical agent to raise an exception
        with patch.object(claims_agent, '_call_technical_agent') as mock_tech_call:
            mock_tech_call.side_effect = Exception("Technical agent error")
            
            # Create a task
            task = TaskRequest(
                taskId="task_error",
                requestId="req_error", 
                user={
                    "user_id": "cust_123",
                    "message": "File a claim",
                    "conversation_id": "conv_error"
                }
            )
            
            # Process the task
            response = await claims_agent.process_task(task)
            
            # Verify error is handled gracefully
            assert response.status == "failed"
            assert "error" in response.parts[0]["text"].lower()
            assert "error" in response.metadata

    @pytest.mark.asyncio
    async def test_end_to_end_claim_processing(self, claims_agent):
        """Test complete end-to-end claim processing"""
        
        with patch.object(claims_agent, '_call_technical_agent') as mock_tech_call:
            
            # Set up comprehensive mock responses
            responses = {
                ("data_agent", "get_customer"): {
                    "customer_id": "cust_123",
                    "name": "John Doe",
                    "email": "john.doe@email.com",
                    "risk_score": 0.3
                },
                ("data_agent", "get_customer_policies"): [{
                    "policy_number": "POL_123",
                    "policy_type": "auto",
                    "coverage_limit": 50000,
                    "status": "active"
                }],
                ("data_agent", "create_claim"): {
                    "claim_id": "CLM_123",
                    "status": "processing",
                    "created_at": "2024-01-01T00:00:00Z"
                },
                ("data_agent", "analyze_fraud"): {
                    "fraud_score": 0.2,
                    "risk_level": "low",
                    "indicators": [],
                    "recommendation": "Standard processing"
                },
                ("notification_agent", "send_template_notification"): {
                    "notification_id": "NOTIF_123",
                    "status": "sent"
                }
            }
            
            def side_effect(agent_name, task_data):
                action = task_data.get("action")
                return responses.get((agent_name, action), {"status": "success"})
            
            mock_tech_call.side_effect = side_effect
            
            # Create realistic claim filing message
            task = TaskRequest(
                taskId="task_e2e",
                requestId="req_e2e",
                user={
                    "user_id": "cust_123",
                    "message": "I was in a car accident yesterday on Highway 101. Another driver rear-ended me at a red light. My car has significant damage to the rear bumper and trunk. The police report number is PR-2024-001. I estimate the damage at around $8,000. My policy number is POL_123.",
                    "conversation_id": "conv_e2e"
                }
            )
            
            # Process the task
            response = await claims_agent.process_task(task)
            
            # Comprehensive verification
            assert response.status == "completed"
            assert response.taskId == "task_e2e"
            
            # Verify response content
            response_text = response.parts[0]["text"].lower()
            assert "claim" in response_text
            assert any(keyword in response_text for keyword in ["filed", "created", "processed"])
            
            # Verify all required technical agent calls were made
            call_count_by_agent = {}
            for call in mock_tech_call.call_args_list:
                agent_name = call.args[0]
                call_count_by_agent[agent_name] = call_count_by_agent.get(agent_name, 0) + 1
            
            assert call_count_by_agent.get("data_agent", 0) >= 3  # get_customer, policies, create_claim, analyze_fraud
            assert call_count_by_agent.get("notification_agent", 0) >= 1  # send confirmation
            
            # Verify conversation history was updated
            assert "conv_e2e" in claims_agent.conversation_history
            history = claims_agent.conversation_history["conv_e2e"]
            assert len(history) == 2  # user message + assistant response
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 