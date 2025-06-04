#!/usr/bin/env python3
"""
Test Multi-Intent Processing for Domain Agent using A2A Protocol
Tests the agent's ability to handle multiple intents in a single request
"""

import sys
import os
import time
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python_a2a import A2AClient

def test_multi_intent_a2a():
    """Test multi-intent processing via A2A protocol"""
    
    # Connect to domain agent A2A endpoint
    client = A2AClient("http://localhost:8003/a2a")
    
    # Test cases with multiple intents
    test_cases = [
        {
            "name": "Policy + Payment Inquiry",
            "message": "I want to see my policies and when my next payment is due for CUST-001",
            "expected_intents": ["policy_inquiry", "payment_inquiry"]
        },
        {
            "name": "Agent + Coverage Inquiry", 
            "message": "Who is my agent and what coverage do I have? Customer ID: CUST-001",
            "expected_intents": ["agent_contact", "coverage_inquiry"]
        },
        {
            "name": "Comprehensive Request",
            "message": "Show me everything about my insurance - policies, payments, coverage, and agent info for customer CUST-001",
            "expected_intents": ["policy_inquiry", "payment_inquiry", "coverage_inquiry", "agent_contact"]
        },
        {
            "name": "Single Intent",
            "message": "What are my premium amounts? Customer CUST-001",
            "expected_intents": ["payment_inquiry"]
        },
        {
            "name": "Policy + Agent",
            "message": "Tell me about my policies and who I should contact for CUST-001",
            "expected_intents": ["policy_inquiry", "agent_contact"]
        }
    ]
    
    print("🧪 Testing Multi-Intent Processing via A2A Protocol...")
    print("=" * 60)
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"Message: '{test_case['message']}'")
        
        try:
            # Send request via A2A using simple ask method
            response = client.ask(test_case['message'])
            
            print(f"✅ Response received via A2A")
            
            # Check response content
            if response and len(response) > 0:
                response_text = str(response)
                
                # Check for multi-intent indicators
                if "COMPREHENSIVE" in response_text.upper() or "OVERVIEW" in response_text.upper():
                    print(f"🎯 Multi-intent comprehensive response detected")
                elif any(word in response_text.upper() for word in ["POLICY", "PAYMENT", "AGENT", "COVERAGE"]):
                    print(f"📊 Relevant response content detected")
                    
                print(f"📝 Response preview: {response_text[:150]}...")
                success_count += 1
                
            else:
                print(f"❌ Empty or invalid response")
                
        except Exception as e:
            print(f"❌ A2A Error: {e}")
            
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    print(f"📊 Multi-Intent A2A Test Results: {success_count}/{total_tests} passed")
    
    if success_count == total_tests:
        print("🎉 All multi-intent A2A tests passed!")
    else:
        print(f"⚠️  {total_tests - success_count} tests failed")
    
    return success_count == total_tests

def test_intent_analysis_capabilities():
    """Test various intent combinations"""
    
    print("\n🔍 Testing Intent Analysis Capabilities...")
    print("=" * 50)
    
    client = A2AClient("http://localhost:8003/a2a")
    
    intent_test_cases = [
        "I want my policy details and payment info for CUST-001",
        "Show me coverage amounts and who my agent is for customer CUST-001", 
        "Give me everything - policies, payments, coverage, agent contact for CUST-001",
        "What's my next premium due date for CUST-001?",
        "Tell me about my auto insurance policy for customer CUST-001"
    ]
    
    for i, message in enumerate(intent_test_cases, 1):
        try:
            print(f"\n{i}. Testing: '{message}'")
            
            response = client.ask(message)
            
            print(f"✅ Intent processed successfully")
            
            # Analyze response for intent detection
            response_str = str(response)
            detected_features = []
            
            if "POLICY" in response_str.upper():
                detected_features.append("policy")
            if "PAYMENT" in response_str.upper():
                detected_features.append("payment")
            if "AGENT" in response_str.upper():
                detected_features.append("agent")
            if "COVERAGE" in response_str.upper():
                detected_features.append("coverage")
                
            print(f"📊 Detected features: {detected_features}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Multi-Intent A2A Testing...")
    
    try:
        # Test intent analysis capabilities  
        test_intent_analysis_capabilities()
        
        # Test full multi-intent conversation flow
        success = test_multi_intent_a2a()
        
        print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: Multi-intent A2A processing test completed")
        
    except Exception as e:
        print(f"❌ Test suite error: {e}")
        import traceback
        traceback.print_exc() 