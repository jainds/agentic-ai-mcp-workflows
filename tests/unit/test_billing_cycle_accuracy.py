#!/usr/bin/env python3
"""
Test billing cycle accuracy in insurance AI responses
Ensures that premium billing frequencies are displayed correctly
"""

import asyncio
import json
import requests
import time

def test_billing_cycle_accuracy():
    """Test that billing cycles are displayed accurately"""
    
    # Test data expectations based on mock_data.json
    expected_data = {
        "CUST-001": {
            "auto_policy": {
                "premium": 95.00,
                "billing_cycle": "quarterly"
            },
            "life_policy": {
                "premium": 45.00,
                "billing_cycle": "monthly"
            }
        }
    }
    
    print("🧪 Testing Billing Cycle Accuracy")
    print("=" * 50)
    
    # Test 1: Basic policy inquiry (should not assume /month)
    print("\n1️⃣ Testing basic policy inquiry...")
    response = requests.post(
        "http://localhost:8003/tasks/send",
        headers={"Content-Type": "application/json"},
        json={
            "message": {"content": {"text": "What insurance policies do I have? (session_customer_id: CUST-001)"}},
            "session": {"customer_id": "CUST-001", "authenticated": True}
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        text = result["artifacts"][0]["parts"][0]["text"]
        print(f"Response: {text}")
        
        # Should NOT contain incorrect "/month" assumptions
        if "$95/month" in text:
            print("❌ FAIL: Incorrectly shows auto premium as monthly")
            return False
        elif "$95 (quarterly)" in text or "$45 (monthly)" in text:
            print("✅ PASS: Shows accurate billing cycles")
        elif "$95" in text and "$45" in text and "/month" not in text:
            print("✅ PASS: Shows premiums without incorrect frequency assumptions")
        else:
            print("⚠️  UNKNOWN: Response format not recognized")
    
    # Test 2: Detailed policy inquiry (should include billing cycles)
    print("\n2️⃣ Testing detailed policy inquiry...")
    response = requests.post(
        "http://localhost:8003/tasks/send",
        headers={"Content-Type": "application/json"},
        json={
            "message": {"content": {"text": "Show me detailed policy information with billing cycles (session_customer_id: CUST-001)"}},
            "session": {"customer_id": "CUST-001", "authenticated": True}
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        text = result["artifacts"][0]["parts"][0]["text"]
        print(f"Response: {text}")
        
        # Should contain accurate billing cycles
        if "$95 (quarterly)" in text and "$45 (monthly)" in text:
            print("✅ PASS: Shows accurate billing cycles in detailed view")
            return True
        else:
            print("❌ FAIL: Missing or incorrect billing cycle information")
            return False
    
    return False

def test_payment_inquiry_accuracy():
    """Test that payment inquiries include billing cycle context"""
    
    print("\n3️⃣ Testing payment inquiry...")
    response = requests.post(
        "http://localhost:8003/tasks/send",
        headers={"Content-Type": "application/json"},
        json={
            "message": {"content": {"text": "When is my next payment due? (session_customer_id: CUST-001)"}},
            "session": {"customer_id": "CUST-001", "authenticated": True}
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        text = result["artifacts"][0]["parts"][0]["text"]
        print(f"Response: {text}")
        
        # Should show payment amounts and dates
        if "$45.00" in text and "$95.00" in text:
            print("✅ PASS: Shows accurate payment amounts")
            return True
        else:
            print("❌ FAIL: Missing payment information")
            return False
    
    return False

if __name__ == "__main__":
    print("🚀 Starting Billing Cycle Accuracy Tests")
    print("Testing against live system at localhost:8003")
    
    try:
        # Test basic accuracy
        basic_test = test_billing_cycle_accuracy()
        
        # Test payment accuracy  
        payment_test = test_payment_inquiry_accuracy()
        
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS:")
        print(f"✅ Billing Cycle Accuracy: {'PASS' if basic_test else 'FAIL'}")
        print(f"✅ Payment Inquiry Accuracy: {'PASS' if payment_test else 'FAIL'}")
        
        if basic_test and payment_test:
            print("\n🎉 ALL TESTS PASSED! Billing cycle accuracy is working correctly.")
        else:
            print("\n❌ SOME TESTS FAILED. Check the responses above.")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 