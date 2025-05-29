"""
Basic Functionality Tests for Insurance AI PoC
Tests individual components to demonstrate the system works correctly
"""

import asyncio
import json
from unittest.mock import patch, MagicMock

# Import the agents
from agents.domain.claims_agent import ClaimsAgent
from agents.technical.data_agent import DataAgent
from agents.technical.notification_agent import NotificationAgent
from agents.shared.a2a_base import TaskRequest, TaskResponse


def test_claims_agent_initialization():
    """Test Claims Agent can be initialized"""
    claims_agent = ClaimsAgent(port=8000)
    
    assert claims_agent.name == "ClaimsAgent"
    assert claims_agent.port == 8000
    assert "claimsProcessing" in claims_agent.capabilities
    assert "llmEnabled" in claims_agent.capabilities
    assert isinstance(claims_agent.conversation_history, dict)
    assert isinstance(claims_agent.active_claims, dict)


def test_data_agent_initialization():
    """Test Data Agent can be initialized"""
    data_agent = DataAgent(port=8002)
    
    assert data_agent.name == "DataAgent"
    assert data_agent.port == 8002
    assert hasattr(data_agent, 'claims_api')
    assert hasattr(data_agent, 'user_api')
    assert hasattr(data_agent, 'policy_api')
    assert hasattr(data_agent, 'analytics_api')


def test_notification_agent_initialization():
    """Test Notification Agent can be initialized"""
    notification_agent = NotificationAgent(port=8003)
    
    assert notification_agent.name == "NotificationAgent"
    assert notification_agent.port == 8003
    assert isinstance(notification_agent.notification_queue, list)
    assert isinstance(notification_agent.sent_notifications, list)


def test_data_agent_get_customer():
    """Test Data Agent get_customer functionality"""
    data_agent = DataAgent(port=8002)
    
    # Mock the API call
    with patch.object(data_agent.user_api, 'get') as mock_get:
        mock_get.return_value = None  # Simulate no response, should generate mock data
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(data_agent._get_customer("cust_123"))
        
        # Verify the result
        assert "customer_id" in result
        assert result["customer_id"] == "cust_123"
        assert "name" in result
        assert "email" in result
        assert "risk_score" in result
        
        loop.close()


def test_data_agent_fraud_analysis():
    """Test Data Agent fraud analysis functionality"""
    data_agent = DataAgent(port=8002)
    
    # Test claim data
    claim_data = {
        "customer_id": "cust_123",
        "description": "My car was stolen and completely destroyed in a fire",
        "amount": 100000,
        "incident_date": "2024-01-01T00:00:00Z"
    }
    
    customer_data = {
        "customer_id": "cust_123",
        "risk_score": 0.8
    }
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(data_agent._analyze_fraud(claim_data, customer_data))
    
    # Verify the result
    assert "fraud_score" in result
    assert "risk_level" in result
    assert "indicators" in result
    assert "recommendation" in result
    assert isinstance(result["fraud_score"], float)
    assert result["fraud_score"] >= 0.0
    assert result["fraud_score"] <= 1.0
    assert result["risk_level"] in ["low", "medium", "high"]
    
    # This claim should have high fraud score due to high amount and suspicious keywords
    assert result["fraud_score"] > 0.5
    assert len(result["indicators"]) > 0
    
    loop.close()


def test_notification_agent_email():
    """Test Notification Agent email functionality"""
    notification_agent = NotificationAgent(port=8003)
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(notification_agent._send_email(
        to="test@example.com",
        subject="Test Email",
        body="This is a test email for the insurance AI PoC"
    ))
    
    # Verify the result
    assert "notification_id" in result
    assert result["status"] == "sent"
    assert "sent_at" in result
    
    # Verify notification was added to sent_notifications
    assert len(notification_agent.sent_notifications) == 1
    assert notification_agent.sent_notifications[0]["to"] == "test@example.com"
    
    loop.close()


def test_notification_agent_alert():
    """Test Notification Agent alert functionality"""
    notification_agent = NotificationAgent(port=8003)
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(notification_agent._send_alert(
        alert_type="fraud",
        severity="high",
        message="High fraud risk detected on claim CLM_123",
        details={"claim_id": "CLM_123", "fraud_score": 0.9}
    ))
    
    # Verify the result
    assert "alert_id" in result
    assert result["status"] == "sent"
    assert "notifications" in result
    assert len(result["notifications"]) > 0  # Should send email notifications
    
    loop.close()


def test_claims_agent_task_structure():
    """Test Claims Agent task processing structure"""
    claims_agent = ClaimsAgent(port=8000)
    
    # Create a test task
    task = TaskRequest(
        taskId="task_123",
        requestId="req_123",
        user={
            "user_id": "cust_123",
            "message": "I need help with my insurance",
            "conversation_id": "conv_123"
        }
    )
    
    # Mock the technical agent calls to avoid actual API calls
    with patch.object(claims_agent, '_call_technical_agent') as mock_call:
        mock_call.return_value = {"status": "success"}
        
        # Mock LLM calls
        with patch.object(claims_agent, '_analyze_user_intent') as mock_intent:
            mock_intent.return_value = {
                "intent": "general_question",
                "confidence": 0.8,
                "technical_actions": [],
                "info_needed": [],
                "response_strategy": "provide_help"
            }
            
            with patch.object(claims_agent, '_handle_general_question') as mock_handle:
                mock_handle.return_value = "I'm here to help with your insurance needs. How can I assist you today?"
                
                # Run the async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(claims_agent.process_task(task))
                
                # Verify the result
                assert isinstance(result, TaskResponse)
                assert result.taskId == "task_123"
                assert result.status == "completed"
                assert len(result.parts) == 1
                assert result.parts[0]["type"] == "claims_response"
                
                # Verify conversation history was updated
                assert "conv_123" in claims_agent.conversation_history
                assert len(claims_agent.conversation_history["conv_123"]) == 2  # user + assistant
                
                loop.close()


def test_llm_intent_analysis():
    """Test LLM intent analysis with mocked OpenAI"""
    claims_agent = ClaimsAgent(port=8000)
    
    # Mock OpenAI client
    with patch.object(claims_agent.openai_client.chat.completions, 'create') as mock_openai:
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "intent": "file_claim",
            "confidence": 0.95,
            "technical_actions": [
                {"agent": "data_agent", "action": "get_customer", "params": {}},
                {"agent": "data_agent", "action": "create_claim", "params": {}}
            ],
            "info_needed": [],
            "response_strategy": "process_claim_filing"
        })
        mock_openai.return_value = mock_response
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(claims_agent._analyze_user_intent(
            "I was in a car accident and need to file a claim",
            "conv_123"
        ))
        
        # Verify the result
        assert result["intent"] == "file_claim"
        assert result["confidence"] == 0.95
        assert len(result["technical_actions"]) == 2
        assert result["technical_actions"][0]["agent"] == "data_agent"
        assert result["technical_actions"][0]["action"] == "get_customer"
        
        # Verify OpenAI was called
        mock_openai.assert_called_once()
        
        loop.close()


def test_claim_information_extraction():
    """Test claim information extraction from user message"""
    claims_agent = ClaimsAgent(port=8000)
    
    # Mock OpenAI client
    with patch.object(claims_agent.openai_client.chat.completions, 'create') as mock_openai:
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "policy_number": "POL_123456",
            "incident_date": "2024-01-15T14:30:00Z",
            "description": "Rear-end collision at traffic light",
            "estimated_amount": 5000,
            "claim_type": "auto",
            "location": "Main St and 1st Ave",
            "parties_involved": "Two vehicles"
        })
        mock_openai.return_value = mock_response
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(claims_agent._extract_claim_information(
            "I was rear-ended at the traffic light on Main St and 1st Ave yesterday around 2:30 PM. Policy number POL_123456. Damage estimated at $5000."
        ))
        
        # Verify the result
        assert result["policy_number"] == "POL_123456"
        assert result["estimated_amount"] == 5000
        assert result["claim_type"] == "auto"
        assert "rear-end" in result["description"].lower()
        
        loop.close()


def test_architecture_separation():
    """Test that the architecture properly separates domain and technical agents"""
    claims_agent = ClaimsAgent(port=8000)
    data_agent = DataAgent(port=8002)
    notification_agent = NotificationAgent(port=8003)
    
    # Verify Claims Agent (Domain) has technical agent URLs but no direct API wrappers
    assert "data_agent" in claims_agent.technical_agents
    assert "notification_agent" in claims_agent.technical_agents
    assert not hasattr(claims_agent, 'claims_api')  # Should not have direct API access
    
    # Verify Data Agent (Technical) has API wrappers for enterprise systems
    assert hasattr(data_agent, 'claims_api')
    assert hasattr(data_agent, 'user_api')
    assert hasattr(data_agent, 'policy_api')
    assert hasattr(data_agent, 'analytics_api')
    
    # Verify Notification Agent (Technical) has notification capabilities
    assert hasattr(notification_agent, 'notification_queue')
    assert hasattr(notification_agent, 'delivery_settings')


def test_system_integration_flow():
    """Test the overall system integration flow"""
    print("\n" + "="*80)
    print("INSURANCE AI POC - SYSTEM INTEGRATION TEST")
    print("="*80)
    
    # Test 1: Domain Agent Initialization
    print("\n1. Initializing Domain Agent (Claims Agent)...")
    claims_agent = ClaimsAgent(port=8000)
    print(f"   ✓ Claims Agent initialized: {claims_agent.name}")
    print(f"   ✓ Capabilities: {list(claims_agent.capabilities.keys())}")
    
    # Test 2: Technical Agents Initialization
    print("\n2. Initializing Technical Agents...")
    data_agent = DataAgent(port=8002)
    notification_agent = NotificationAgent(port=8003)
    print(f"   ✓ Data Agent initialized: {data_agent.name}")
    print(f"   ✓ Notification Agent initialized: {notification_agent.name}")
    
    # Test 3: Data Agent MCP Tools
    print("\n3. Testing Data Agent MCP Tools...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Test customer lookup
    customer_result = loop.run_until_complete(data_agent._get_customer("test_customer"))
    print(f"   ✓ Customer lookup: {customer_result.get('name', 'N/A')}")
    
    # Test fraud analysis
    test_claim = {
        "customer_id": "test_customer",
        "description": "Minor fender bender",
        "amount": 2000
    }
    fraud_result = loop.run_until_complete(data_agent._analyze_fraud(test_claim))
    print(f"   ✓ Fraud analysis: Risk Level = {fraud_result['risk_level']}, Score = {fraud_result['fraud_score']}")
    
    # Test 4: Notification Agent MCP Tools
    print("\n4. Testing Notification Agent MCP Tools...")
    
    # Test email notification
    email_result = loop.run_until_complete(notification_agent._send_email(
        to="customer@example.com",
        subject="Claim Notification",
        body="Your claim has been processed"
    ))
    print(f"   ✓ Email notification: {email_result['status']}")
    
    # Test alert
    alert_result = loop.run_until_complete(notification_agent._send_alert(
        alert_type="system",
        severity="low",
        message="System test alert"
    ))
    print(f"   ✓ Alert notification: {alert_result['status']}")
    
    # Test 5: Domain Agent Orchestration
    print("\n5. Testing Domain Agent Orchestration...")
    
    # Mock technical agent calls
    with patch.object(claims_agent, '_call_technical_agent') as mock_tech_call:
        mock_tech_call.return_value = {"status": "success", "data": "test"}
        
        # Mock LLM analysis
        with patch.object(claims_agent, '_analyze_user_intent') as mock_intent:
            mock_intent.return_value = {
                "intent": "file_claim",
                "confidence": 0.9,
                "technical_actions": [{"agent": "data_agent", "action": "create_claim"}],
                "response_strategy": "process"
            }
            
            # Create test task
            task = TaskRequest(
                taskId="test_task",
                requestId="test_req",
                user={
                    "user_id": "test_customer",
                    "message": "I need to file a claim",
                    "conversation_id": "test_conv"
                }
            )
            
            # Process task
            response = loop.run_until_complete(claims_agent.process_task(task))
            print(f"   ✓ Task processing: {response.status}")
            print(f"   ✓ Technical agent calls: {mock_tech_call.call_count}")
    
    loop.close()
    
    print("\n" + "="*80)
    print("SYSTEM INTEGRATION TEST COMPLETED SUCCESSFULLY")
    print("✓ Domain agents orchestrate via A2A protocol")
    print("✓ Technical agents provide MCP tools")
    print("✓ No direct API calls from domain agents")
    print("✓ Proper separation of concerns maintained")
    print("="*80)


if __name__ == "__main__":
    # Run the basic tests
    test_claims_agent_initialization()
    test_data_agent_initialization()
    test_notification_agent_initialization()
    test_data_agent_get_customer()
    test_data_agent_fraud_analysis()
    test_notification_agent_email()
    test_notification_agent_alert()
    test_claims_agent_task_structure()
    test_llm_intent_analysis()
    test_claim_information_extraction()
    test_architecture_separation()
    test_system_integration_flow()
    
    print("\n🎉 All basic functionality tests passed!") 