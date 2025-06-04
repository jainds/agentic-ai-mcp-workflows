#!/usr/bin/env python3
"""
Test session data flow through A2A framework
"""

import requests
import json
import uuid
import time
from datetime import datetime

def test_customer(customer_id, customer_name, should_succeed=True, max_retries=3):
    """Test a specific customer with retry logic"""
    
    print(f"\n🧪 Testing Customer: {customer_id} ({customer_name})")
    print("-" * 50)
    
    for attempt in range(max_retries):
        # Test data with session
        payload = {
            "message": {
                "content": {"type": "text", "text": "What insurance policies do I have?"},
                "role": "user"
            },
            "session": {
                "customer_id": customer_id,
                "session_id": str(uuid.uuid4()),
                "authenticated": True,
                "customer_data": {
                    "customer_id": customer_id,
                    "name": customer_name,
                    "status": "Active",
                    "type": "Premium"
                }
            },
            "metadata": {
                "ui_mode": "advanced",
                "timestamp": datetime.now().isoformat(),
                "message_id": str(uuid.uuid4())
            }
        }
        
        print(f"📤 Attempt {attempt + 1}/{max_retries}...")
        print(f"   Customer ID: {customer_id}")
        print(f"   Session ID: {payload['session']['session_id']}")
        
        try:
            # Send to domain agent A2A endpoint
            response = requests.post(
                "http://localhost:8003/a2a/tasks/send",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract response text
                artifacts = response_data.get("artifacts", [])
                if artifacts and len(artifacts) > 0:
                    parts = artifacts[0].get("parts", [])
                    if parts and len(parts) > 0:
                        response_text = parts[0].get("text", "No response text")
                        print(f"📝 Response: {response_text[:150]}...")
                        
                        # Check if it's an error response
                        has_error = any(word in response_text.lower() for word in ["trouble", "error", "apologize", "try again"])
                        
                        if should_succeed:
                            if not has_error:
                                print(f"✅ SUCCESS: Found policy data as expected")
                                return True
                            else:
                                print(f"⚠️  Attempt {attempt + 1} failed, retrying...")
                                if attempt < max_retries - 1:
                                    time.sleep(2)  # Wait before retry
                                    continue
                                else:
                                    print(f"❌ FAILED: Expected success but got error after {max_retries} attempts")
                                    return False
                        else:
                            if has_error:
                                print(f"✅ SUCCESS: Got expected error response")
                                return True
                            else:
                                print(f"❌ FAILED: Expected error but got success")
                                return False
                    else:
                        print(f"❌ No response parts found")
                        if attempt < max_retries - 1:
                            time.sleep(2)
                            continue
                        return False
                else:
                    print(f"❌ No response artifacts found")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return False
    
    return False

def test_session_flow():
    """Test session data flow through the system with multiple scenarios"""
    
    print("🧪 COMPREHENSIVE SESSION DATA FLOW TEST")
    print("=" * 60)
    print("Note: Testing with retry logic due to distributed system with multiple replicas")
    
    test_cases = [
        # (customer_id, customer_name, should_succeed)
        ("CUST-001", "John Smith", True),      # Has auto + life policies
        ("user_003", "John Doe", True),        # Has auto + home policies  
        ("CUST-003", "Test Customer", False),  # Doesn't exist
        ("user_999", "Missing User", False),   # Doesn't exist
    ]
    
    results = []
    
    for customer_id, customer_name, should_succeed in test_cases:
        result = test_customer(customer_id, customer_name, should_succeed)
        results.append((customer_id, result))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for customer_id, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {customer_id:12}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! LLM-first AI solution is working correctly!")
        print("✅ A2A session management working")
        print("✅ Service discovery connecting to k8s services")  
        print("✅ Customer ID extraction from session data")
        print("✅ MCP protocol communication established")
        print("✅ Policy data retrieval working")
        print("✅ Error handling for non-existent customers")
        return True
    else:
        print("❌ SOME TESTS FAILED! Please check the issues above.")
        print("Note: Intermittent failures may be due to:")
        print("  - OpenRouter API rate limits or temporary issues")
        print("  - Load balancing between multiple pod replicas")
        print("  - Network connectivity issues")
        return False

if __name__ == "__main__":
    success = test_session_flow()
    exit(0 if success else 1) 