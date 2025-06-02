#!/usr/bin/env python3
"""
Test Script for Simple Business-Focused Policy APIs
Demonstrates the new simplified API design
"""

import asyncio
import json
import sys
import time
from fastmcp import Client

async def test_simple_business_apis():
    """Test the new simple business-focused policy server APIs"""
    
    # Policy server URL  
    policy_server_url = "http://localhost:8001"
    
    # Test customer ID
    test_customer_id = "CUST-001"
    
    print("🏢 Testing Simple Business-Focused Policy APIs")
    print("=" * 60)
    
    try:
        async with Client(policy_server_url) as client:
            
            # Test 1: Get Policies (Basic List)
            print("\n📋 Test 1: Get Policies (Basic)")
            print("-" * 30)
            start_time = time.time()
            policies_result = await client.call_tool("get_policies", {"customer_id": test_customer_id})
            policies_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {policies_duration:.3f}s")
            for content in policies_result:
                if hasattr(content, 'text'):
                    policies = json.loads(content.text)
                    print(f"📝 Found {len(policies)} policies:")
                    for policy in policies:
                        print(f"   - {policy['id']}: {policy['type']} (${policy['premium']}/month, ${policy['coverage_amount']:,.0f} coverage)")
                    break
            
            # Test 2: Get Agent
            print("\n👤 Test 2: Get Agent")
            print("-" * 30)
            start_time = time.time()
            agent_result = await client.call_tool("get_agent", {"customer_id": test_customer_id})
            agent_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {agent_duration:.3f}s")
            for content in agent_result:
                if hasattr(content, 'text'):
                    agent = json.loads(content.text)
                    print(f"👨‍💼 Agent: {agent['name']}")
                    print(f"   📧 Email: {agent['email']}")
                    print(f"   📞 Phone: {agent['phone']}")
                    print(f"   🏷️  Handles: {', '.join(agent['handles_policy_types'])}")
                    break
            
            # Test 3: Get Policy Types
            print("\n🏷️  Test 3: Get Policy Types")
            print("-" * 30)
            start_time = time.time()
            types_result = await client.call_tool("get_policy_types", {"customer_id": test_customer_id})
            types_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {types_duration:.3f}s")
            for content in types_result:
                if hasattr(content, 'text'):
                    types = json.loads(content.text)
                    print(f"📋 Policy Types: {', '.join(types)}")
                    break
            
            # Test 4: Get Payment Information
            print("\n💰 Test 4: Get Payment Information")
            print("-" * 30)
            start_time = time.time()
            payment_result = await client.call_tool("get_payment_information", {"customer_id": test_customer_id})
            payment_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {payment_duration:.3f}s")
            for content in payment_result:
                if hasattr(content, 'text'):
                    payments = json.loads(content.text)
                    print(f"💳 Payment Information:")
                    for payment in payments:
                        print(f"   - {payment['policy_type']}: ${payment['premium']} ({payment['billing_cycle']})")
                        print(f"     Due: {payment['next_payment_due']}, Method: {payment['payment_method']}")
                    break
            
            # Test 5: Get Coverage Information
            print("\n🛡️  Test 5: Get Coverage Information")
            print("-" * 30)
            start_time = time.time()
            coverage_result = await client.call_tool("get_coverage_information", {"customer_id": test_customer_id})
            coverage_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {coverage_duration:.3f}s")
            for content in coverage_result:
                if hasattr(content, 'text'):
                    coverage = json.loads(content.text)
                    print(f"🛡️  Coverage Details:")
                    for cov in coverage:
                        print(f"   - {cov['policy_type']}: ${cov['coverage_amount']:,.0f} coverage, ${cov['deductible']} deductible")
                        print(f"     Types: {', '.join(cov['coverage_types'])}")
                    break
            
            # Test 6: Get Deductibles
            print("\n💸 Test 6: Get Deductibles")
            print("-" * 30)
            start_time = time.time()
            deductibles_result = await client.call_tool("get_deductibles", {"customer_id": test_customer_id})
            deductibles_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {deductibles_duration:.3f}s")
            for content in deductibles_result:
                if hasattr(content, 'text'):
                    deductibles = json.loads(content.text)
                    print(f"💸 Deductibles:")
                    for ded in deductibles:
                        print(f"   - {ded['policy_type']}: ${ded['deductible']} (on ${ded['coverage_amount']:,.0f} coverage)")
                    break
            
            # Test 7: Get Policy Details (Specific Policy)
            print("\n🔍 Test 7: Get Policy Details")
            print("-" * 30)
            test_policy_id = "POL-2024-AUTO-002"
            start_time = time.time()
            details_result = await client.call_tool("get_policy_details", {"policy_id": test_policy_id})
            details_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {details_duration:.3f}s")
            for content in details_result:
                if hasattr(content, 'text'):
                    details = json.loads(content.text)
                    print(f"📄 Policy Details for {test_policy_id}:")
                    print(f"   Type: {details['type']}, Status: {details['status']}")
                    print(f"   Premium: ${details['premium']}, Coverage: ${details['coverage_amount']:,.0f}")
                    if 'vehicle' in details.get('details', {}):
                        vehicle = details['details']['vehicle']
                        print(f"   Vehicle: {vehicle['year']} {vehicle['make']} {vehicle['model']}")
                    print(f"   Agent: {details['assigned_agent']['name']} ({details['assigned_agent']['email']})")
                    break
            
            # Test 8: Get Recommendations
            print("\n🎯 Test 8: Get Recommendations")
            print("-" * 30)
            start_time = time.time()
            recommendations_result = await client.call_tool("get_recommendations", {"customer_id": test_customer_id})
            recommendations_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {recommendations_duration:.3f}s")
            for content in recommendations_result:
                if hasattr(content, 'text'):
                    recommendations = json.loads(content.text)
                    print(f"🎯 Product Recommendations:")
                    for rec in recommendations:
                        print(f"   - {rec['product_type'].upper()} ({rec['priority']} priority)")
                        print(f"     Reason: {rec['reason']}")
                        print(f"     Savings: {rec['potential_savings']}")
                    break
            
            # Test 9: Get Policy List (Detailed)
            print("\n📝 Test 9: Get Policy List (Detailed)")
            print("-" * 30)
            start_time = time.time()
            list_result = await client.call_tool("get_policy_list", {"customer_id": test_customer_id})
            list_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {list_duration:.3f}s")
            for content in list_result:
                if hasattr(content, 'text'):
                    policy_list = json.loads(content.text)
                    print(f"📋 Detailed Policy List:")
                    for policy in policy_list:
                        print(f"   - {policy['id']}: {policy['type']} ({policy['status']})")
                        print(f"     ${policy['premium']}/month, {policy['billing_cycle']}, ${policy['deductible']} deductible")
                        print(f"     Period: {policy['start_date'][:10]} to {policy['end_date'][:10]}")
                    break
            
            # Performance Summary
            print("\n📊 Performance Summary")
            print("=" * 60)
            total_time = (policies_duration + agent_duration + types_duration + payment_duration + 
                         coverage_duration + deductibles_duration + details_duration + 
                         recommendations_duration + list_duration)
            
            print(f"🏢 Simple Business APIs Total: {total_time:.3f}s (9 calls)")
            print(f"⚡ Average per API:             {total_time/9:.3f}s")
            
            print("\n✨ Benefits of Simple Business APIs:")
            print("   • Intuitive business-focused names")
            print("   • Single responsibility per API")
            print("   • Easy to understand and use")
            print("   • Perfect for specific business questions")
            print("   • Excellent for building focused UIs")
            print("   • Built-in product recommendations")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

async def test_real_world_scenarios():
    """Test real-world business scenarios using the simple APIs"""
    
    policy_server_url = "http://localhost:8001"
    test_customer_id = "CUST-001"
    
    print("\n🌍 Real-World Business Scenarios")
    print("=" * 60)
    
    try:
        async with Client(policy_server_url) as client:
            
            # Scenario 1: Customer calls asking "What policies do I have?"
            print("\n📞 Scenario 1: 'What policies do I have?'")
            print("-" * 40)
            policies_result = await client.call_tool("get_policies", {"customer_id": test_customer_id})
            for content in policies_result:
                if hasattr(content, 'text'):
                    policies = json.loads(content.text)
                    print("✅ Answer: You have the following policies:")
                    for policy in policies:
                        print(f"   • {policy['type'].title()} Insurance (${policy['premium']}/month)")
                    break
            
            # Scenario 2: Customer asks "When is my next payment due?"
            print("\n📞 Scenario 2: 'When is my next payment due?'")
            print("-" * 40)
            payment_result = await client.call_tool("get_payment_information", {"customer_id": test_customer_id})
            for content in payment_result:
                if hasattr(content, 'text'):
                    payments = json.loads(content.text)
                    print("✅ Answer: Your upcoming payments:")
                    for payment in sorted(payments, key=lambda x: x['next_payment_due']):
                        print(f"   • {payment['policy_type'].title()}: ${payment['premium']} due {payment['next_payment_due'][:10]}")
                    break
            
            # Scenario 3: Customer asks "Who is my agent?"
            print("\n📞 Scenario 3: 'Who is my agent?'")
            print("-" * 40)
            agent_result = await client.call_tool("get_agent", {"customer_id": test_customer_id})
            for content in agent_result:
                if hasattr(content, 'text'):
                    agent = json.loads(content.text)
                    print(f"✅ Answer: Your agent is {agent['name']}")
                    print(f"   📧 Email: {agent['email']}")
                    print(f"   📞 Phone: {agent['phone']}")
                    break
            
            # Scenario 4: Customer asks "What's my deductible?"
            print("\n📞 Scenario 4: 'What are my deductibles?'")
            print("-" * 40)
            deductibles_result = await client.call_tool("get_deductibles", {"customer_id": test_customer_id})
            for content in deductibles_result:
                if hasattr(content, 'text'):
                    deductibles = json.loads(content.text)
                    print("✅ Answer: Your deductibles are:")
                    for ded in deductibles:
                        print(f"   • {ded['policy_type'].title()}: ${ded['deductible']}")
                    break
            
            # Scenario 5: Sales opportunity - "What other products might interest me?"
            print("\n📞 Scenario 5: 'What other products might interest me?'")
            print("-" * 40)
            recommendations_result = await client.call_tool("get_recommendations", {"customer_id": test_customer_id})
            for content in recommendations_result:
                if hasattr(content, 'text'):
                    recommendations = json.loads(content.text)
                    print("✅ Answer: Based on your current policies, we recommend:")
                    for rec in recommendations:
                        print(f"   • {rec['product_type'].title()} Insurance ({rec['priority']} priority)")
                        print(f"     💡 {rec['reason']}")
                        print(f"     💰 {rec['potential_savings']}")
                    break
            
    except Exception as e:
        print(f"❌ Scenario test failed: {e}")

if __name__ == "__main__":
    print("🏢 Simple Business-Focused APIs Test Suite")
    print("=" * 60)
    print("Testing new simplified business API design")
    print()
    
    # Check if policy server is running
    try:
        import requests
        response = requests.get("http://localhost:8001/", timeout=5)
        # FastMCP servers may not have a root endpoint, so just check connection
        print("✅ Policy server connection successful")
    except Exception:
        print("❌ Cannot connect to policy server on localhost:8001")
        print("   Please start it with: python policy_server/main.py")
        sys.exit(1)
    
    # Run tests
    async def run_all_tests():
        success = await test_simple_business_apis()
        if success:
            await test_real_world_scenarios()
            
            print("\n🎉 All tests completed successfully!")
            print("\n💼 Business Benefits:")
            print("   ✅ APIs match business language")
            print("   ✅ Easy for developers to understand")
            print("   ✅ Perfect for customer service scenarios")
            print("   ✅ Built-in sales opportunities (recommendations)")
            print("   ✅ Single-purpose, focused responses")
        else:
            print("\n❌ Tests failed")
            sys.exit(1)
    
    asyncio.run(run_all_tests()) 