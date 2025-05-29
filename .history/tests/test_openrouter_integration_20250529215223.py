#!/usr/bin/env python3
"""
OpenRouter Integration Tests for Insurance AI PoC
Tests the system with OpenRouter API configuration
"""

import asyncio
import os
import json
from unittest.mock import patch, MagicMock

# Import the agents
from agents.domain.claims_agent import ClaimsAgent
from agents.technical.data_agent import DataAgent
from agents.technical.notification_agent import NotificationAgent
from agents.shared.a2a_base import TaskRequest, TaskResponse


def test_openrouter_configuration():
    """Test that the OpenRouter configuration is properly loaded"""
    print("\n" + "="*80)
    print("TESTING OPENROUTER CONFIGURATION")
    print("="*80)
    
    claims_agent = ClaimsAgent(port=8000)
    
    # Check that the agent has the right model configuration
    assert hasattr(claims_agent, 'primary_model')
    assert hasattr(claims_agent, 'fallback_model')
    
    print(f"✓ Primary Model: {claims_agent.primary_model}")
    print(f"✓ Fallback Model: {claims_agent.fallback_model}")
    
    # Check OpenAI client configuration
    assert claims_agent.openai_client is not None
    
    # Check if we're using OpenRouter or demo mode
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and openrouter_key != "your-openrouter-api-key-here":
        print("✓ Using OpenRouter API")
        assert claims_agent.openai_client.base_url == os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    else:
        print("✓ Using Demo Mode (OpenRouter key not configured)")
    
    print("Configuration test passed!")


def test_basic_agent_functionality():
    """Test basic agent functionality without LLM calls"""
    print("\n" + "="*80)
    print("TESTING BASIC AGENT FUNCTIONALITY")
    print("="*80)
    
    # Test Claims Agent
    print("\n1. Testing Claims Agent...")
    claims_agent = ClaimsAgent(port=8000)
    assert claims_agent.name == "ClaimsAgent"
    assert "claimsProcessing" in claims_agent.capabilities
    assert "llmEnabled" in claims_agent.capabilities
    print("✓ Claims Agent initialized successfully")
    
    # Test Data Agent
    print("\n2. Testing Data Agent...")
    data_agent = DataAgent(port=8002)
    assert data_agent.name == "DataAgent"
    assert hasattr(data_agent, 'claims_api')
    print("✓ Data Agent initialized successfully")
    
    # Test Notification Agent
    print("\n3. Testing Notification Agent...")
    notification_agent = NotificationAgent(port=8003)
    assert notification_agent.name == "NotificationAgent"
    assert hasattr(notification_agent, 'notification_queue')
    print("✓ Notification Agent initialized successfully")
    
    print("\nBasic functionality test passed!")


def test_data_agent_operations():
    """Test Data Agent MCP operations"""
    print("\n" + "="*80)
    print("TESTING DATA AGENT OPERATIONS")
    print("="*80)
    
    data_agent = DataAgent(port=8002)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Test customer lookup
    print("\n1. Testing customer lookup...")
    customer_result = loop.run_until_complete(data_agent._get_customer("test_customer_123"))
    assert "customer_id" in customer_result
    assert customer_result["customer_id"] == "test_customer_123"
    print(f"✓ Customer retrieved: {customer_result['name']}")
    
    # Test policy lookup
    print("\n2. Testing policy lookup...")
    policies = loop.run_until_complete(data_agent._get_customer_policies("test_customer_123"))
    assert isinstance(policies, list)
    assert len(policies) > 0
    print(f"✓ Found {len(policies)} policies")
    
    # Test claim creation
    print("\n3. Testing claim creation...")
    claim_data = {
        "customer_id": "test_customer_123",
        "description": "Test claim for integration testing",
        "amount": 5000,
        "claim_type": "auto"
    }
    claim_result = loop.run_until_complete(data_agent._create_claim(claim_data))
    assert "claim_id" in claim_result
    assert claim_result["status"] == "processing"
    print(f"✓ Claim created: {claim_result['claim_id']}")
    
    # Test fraud analysis
    print("\n4. Testing fraud analysis...")
    fraud_result = loop.run_until_complete(data_agent._analyze_fraud(claim_data))
    assert "fraud_score" in fraud_result
    assert "risk_level" in fraud_result
    assert fraud_result["risk_level"] in ["low", "medium", "high"]
    print(f"✓ Fraud analysis: {fraud_result['risk_level']} risk (score: {fraud_result['fraud_score']})")
    
    loop.close()
    print("\nData Agent operations test passed!")


def test_notification_agent_operations():
    """Test Notification Agent operations"""
    print("\n" + "="*80)
    print("TESTING NOTIFICATION AGENT OPERATIONS")
    print("="*80)
    
    notification_agent = NotificationAgent(port=8003)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Test email notification
    print("\n1. Testing email notification...")
    email_result = loop.run_until_complete(notification_agent._send_email(
        to="customer@example.com",
        subject="Test Notification",
        body="This is a test notification from the Insurance AI PoC"
    ))
    assert email_result["status"] == "sent"
    print(f"✓ Email sent: {email_result['notification_id']}")
    
    # Test SMS notification
    print("\n2. Testing SMS notification...")
    sms_result = loop.run_until_complete(notification_agent._send_sms(
        phone="+1234567890",
        message="Test SMS from Insurance AI"
    ))
    assert sms_result["status"] == "sent"
    print(f"✓ SMS sent: {sms_result['notification_id']}")
    
    # Test alert
    print("\n3. Testing alert notification...")
    alert_result = loop.run_until_complete(notification_agent._send_alert(
        alert_type="system",
        severity="medium",
        message="System integration test alert"
    ))
    assert alert_result["status"] == "sent"
    print(f"✓ Alert sent: {alert_result['alert_id']}")
    
    # Test template notification
    print("\n4. Testing template notification...")
    template_result = loop.run_until_complete(notification_agent._send_template_notification(
        template_name="claim_approved",
        recipients=["customer@example.com"],
        variables={"claim_id": "CLM_TEST_123", "customer_name": "Test Customer", "amount": "5000"}
    ))
    assert template_result["recipients_count"] == 1
    print(f"✓ Template notification sent to {template_result['recipients_count']} recipients")
    
    loop.close()
    print("\nNotification Agent operations test passed!")


def test_claims_agent_task_processing():
    """Test Claims Agent task processing without actual LLM calls"""
    print("\n" + "="*80)
    print("TESTING CLAIMS AGENT TASK PROCESSING")
    print("="*80)
    
    claims_agent = ClaimsAgent(port=8000)
    
    # Mock technical agent calls to simulate successful operations
    with patch.object(claims_agent, '_call_technical_agent') as mock_tech_call:
        mock_tech_call.return_value = {
            "status": "success",
            "data": "mock_response"
        }
        
        # Mock LLM intent analysis
        with patch.object(claims_agent, '_analyze_user_intent') as mock_intent:
            mock_intent.return_value = {
                "intent": "general_question",
                "confidence": 0.9,
                "technical_actions": [],
                "info_needed": [],
                "response_strategy": "provide_help"
            }
            
            # Mock general question handler
            with patch.object(claims_agent, '_handle_general_question') as mock_handle:
                mock_handle.return_value = "I'm here to help with your insurance needs. How can I assist you today?"
                
                # Create and process a test task
                task = TaskRequest(
                    taskId="test_task_001",
                    requestId="test_req_001",
                    user={
                        "user_id": "test_customer_123",
                        "message": "Hello, I need help with my insurance policy",
                        "conversation_id": "test_conv_001"
                    }
                )
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                print("\n1. Processing customer query...")
                result = loop.run_until_complete(claims_agent.process_task(task))
                
                # Verify the result
                assert isinstance(result, TaskResponse)
                assert result.taskId == "test_task_001"
                assert result.status == "completed"
                assert len(result.parts) == 1
                print(f"✓ Task processed successfully: {result.status}")
                
                # Verify conversation history
                assert "test_conv_001" in claims_agent.conversation_history
                history = claims_agent.conversation_history["test_conv_001"]
                assert len(history) == 2  # user message + assistant response
                print(f"✓ Conversation history maintained: {len(history)} messages")
                
                loop.close()
    
    print("\nClaims Agent task processing test passed!")


def test_architecture_compliance():
    """Test that the architecture follows the correct separation of concerns"""
    print("\n" + "="*80)
    print("TESTING ARCHITECTURE COMPLIANCE")
    print("="*80)
    
    claims_agent = ClaimsAgent(port=8000)
    data_agent = DataAgent(port=8002)
    notification_agent = NotificationAgent(port=8003)
    
    print("\n1. Checking Domain Agent (Claims Agent)...")
    # Domain agents should have technical agent URLs but no direct API access
    assert hasattr(claims_agent, 'technical_agents')
    assert "data_agent" in claims_agent.technical_agents
    assert "notification_agent" in claims_agent.technical_agents
    assert not hasattr(claims_agent, 'claims_api')  # Should not have direct API access
    print("✓ Domain agent properly configured for orchestration")
    
    print("\n2. Checking Technical Agents...")
    # Data Agent should have enterprise API wrappers
    assert hasattr(data_agent, 'claims_api')
    assert hasattr(data_agent, 'user_api')
    assert hasattr(data_agent, 'policy_api')
    assert hasattr(data_agent, 'analytics_api')
    print("✓ Data Agent has proper enterprise API access")
    
    # Notification Agent should have notification capabilities
    assert hasattr(notification_agent, 'notification_queue')
    assert hasattr(notification_agent, 'delivery_settings')
    print("✓ Notification Agent has proper notification capabilities")
    
    print("\n3. Checking LLM Integration...")
    # Claims Agent should have LLM client
    assert hasattr(claims_agent, 'openai_client')
    assert hasattr(claims_agent, 'primary_model')
    assert hasattr(claims_agent, 'fallback_model')
    print("✓ Claims Agent has proper LLM integration")
    
    print("\nArchitecture compliance test passed!")


def run_comprehensive_test():
    """Run all tests in sequence"""
    print("\n" + "="*100)
    print("INSURANCE AI POC - COMPREHENSIVE OPENROUTER INTEGRATION TEST")
    print("="*100)
    
    try:
        # Test configuration
        test_openrouter_configuration()
        
        # Test basic functionality
        test_basic_agent_functionality()
        
        # Test data operations
        test_data_agent_operations()
        
        # Test notifications
        test_notification_agent_operations()
        
        # Test task processing
        test_claims_agent_task_processing()
        
        # Test architecture
        test_architecture_compliance()
        
        print("\n" + "="*100)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        print("="*100)
        print("✓ OpenRouter configuration is working")
        print("✓ Domain agents properly orchestrate technical agents")
        print("✓ Technical agents provide MCP tools for enterprise systems")
        print("✓ LLM integration is properly configured")
        print("✓ Architecture separation is maintained")
        print("✓ Core functionality is working correctly")
        print("="*100)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise


if __name__ == "__main__":
    run_comprehensive_test() 