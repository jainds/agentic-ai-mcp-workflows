#!/usr/bin/env python3
"""
Test Script for Focused Policy Server APIs
Demonstrates the new modular API design vs legacy comprehensive API
"""

import asyncio
import json
import sys
import time
from fastmcp import Client

async def test_focused_apis():
    """Test the new focused policy server APIs"""
    
    # Policy server URL
    policy_server_url = "http://localhost:8001"
    
    # Test customer ID
    test_customer_id = "CUST-001"
    
    print("🧪 Testing New Focused Policy Server APIs")
    print("=" * 60)
    
    try:
        async with Client(policy_server_url) as client:
            
            # Test 1: Policy Summary (Overview)
            print("\n📋 Test 1: Policy Summary")
            print("-" * 30)
            start_time = time.time()
            summary_result = await client.call_tool("get_policy_summary", {"customer_id": test_customer_id})
            summary_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {summary_duration:.3f}s")
            for content in summary_result:
                if hasattr(content, 'text'):
                    summary_data = json.loads(content.text)
                    print(f"📊 Summary: {summary_data['total_policies']} policies, ${summary_data['total_coverage']:,.2f} coverage")
                    print(f"   Policy Types: {', '.join(summary_data['policy_types'])}")
                    print(f"   Active Policies: {summary_data['active_policies']}")
                    break
            
            # Test 2: Policy List (Basic Info)
            print("\n📋 Test 2: Policy List")
            print("-" * 30)
            start_time = time.time()
            list_result = await client.call_tool("get_policy_list", {"customer_id": test_customer_id})
            list_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {list_duration:.3f}s")
            for content in list_result:
                if hasattr(content, 'text'):
                    policies = json.loads(content.text)
                    print(f"📝 Found {len(policies)} policies:")
                    for policy in policies:
                        print(f"   - {policy['id']}: {policy['type']} (${policy['premium']}/month)")
                    break
            
            # Test 3: Payment Information
            print("\n💰 Test 3: Payment Information")
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
                        print(f"   - {payment['policy_id']}: ${payment['premium']} ({payment['billing_cycle']})")
                        print(f"     Next Due: {payment['next_payment_due']}")
                    break
            
            # Test 4: Coverage Information
            print("\n🛡️  Test 4: Coverage Information")
            print("-" * 30)
            start_time = time.time()
            coverage_result = await client.call_tool("get_policy_coverage", {"customer_id": test_customer_id})
            coverage_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {coverage_duration:.3f}s")
            for content in coverage_result:
                if hasattr(content, 'text'):
                    coverage = json.loads(content.text)
                    print(f"🛡️  Coverage Details:")
                    for cov in coverage:
                        print(f"   - {cov['policy_id']}: ${cov['coverage_amount']:,.2f} coverage")
                        print(f"     Deductible: ${cov['deductible']}")
                    break
            
            # Test 5: Assigned Agents
            print("\n👥 Test 5: Assigned Agents")
            print("-" * 30)
            start_time = time.time()
            agents_result = await client.call_tool("get_assigned_agents", {"customer_id": test_customer_id})
            agents_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {agents_duration:.3f}s")
            for content in agents_result:
                if hasattr(content, 'text'):
                    agents = json.loads(content.text)
                    print(f"👤 Assigned Agents:")
                    for agent in agents:
                        print(f"   - {agent['name']} ({agent['email']})")
                        print(f"     Phone: {agent['phone']}")
                        print(f"     Handles: {', '.join(agent['handles_policy_types'])}")
                    break
            
            # Test 6: Specific Policy Details
            print("\n🔍 Test 6: Specific Policy Details")
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
                    print(f"   Type: {details['type']}")
                    print(f"   Premium: ${details['premium']}")
                    print(f"   Coverage: ${details['coverage_amount']:,.2f}")
                    if 'vehicle' in details.get('details', {}):
                        vehicle = details['details']['vehicle']
                        print(f"   Vehicle: {vehicle['year']} {vehicle['make']} {vehicle['model']}")
                    break
            
            # Test 7: Filtered Payment Information (Auto only)
            print("\n💰 Test 7: Auto Policy Payment Information")
            print("-" * 30)
            start_time = time.time()
            auto_payment_result = await client.call_tool("get_payment_information", 
                                                        {"customer_id": test_customer_id, "policy_type": "auto"})
            auto_payment_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {auto_payment_duration:.3f}s")
            for content in auto_payment_result:
                if hasattr(content, 'text'):
                    auto_payments = json.loads(content.text)
                    print(f"🚗 Auto Policy Payments:")
                    for payment in auto_payments:
                        print(f"   - {payment['policy_id']}: ${payment['premium']} ({payment['billing_cycle']})")
                    break
            
            # Test 8: Compare with Legacy Comprehensive API
            print("\n🔄 Test 8: Legacy Comprehensive API (for comparison)")
            print("-" * 30)
            start_time = time.time()
            legacy_result = await client.call_tool("get_customer_policies", {"customer_id": test_customer_id})
            legacy_duration = time.time() - start_time
            
            print(f"⏱️  Duration: {legacy_duration:.3f}s")
            for content in legacy_result:
                if hasattr(content, 'text'):
                    legacy_data = json.loads(content.text)
                    print(f"📦 Legacy API returned {len(legacy_data)} items")
                    print(f"   (1 summary + {len(legacy_data)-1} detailed policies)")
                    
                    # Calculate data size
                    legacy_size = len(json.dumps(legacy_data))
                    print(f"   Data size: {legacy_size:,} bytes")
                    break
            
            # Performance Summary
            print("\n📊 Performance Summary")
            print("=" * 60)
            focused_total = (summary_duration + list_duration + payment_duration + 
                           coverage_duration + agents_duration + details_duration + auto_payment_duration)
            
            print(f"🎯 Focused APIs Total:      {focused_total:.3f}s (7 calls)")
            print(f"🔄 Legacy Comprehensive:    {legacy_duration:.3f}s (1 call)")
            print(f"⚡ Average per focused API: {focused_total/7:.3f}s")
            
            if focused_total < legacy_duration:
                savings = ((legacy_duration - focused_total) / legacy_duration) * 100
                print(f"✅ Focused APIs are {savings:.1f}% faster overall")
            else:
                overhead = ((focused_total - legacy_duration) / legacy_duration) * 100
                print(f"⚠️  Multiple focused calls have {overhead:.1f}% overhead")
            
            print("\n🎯 Benefits of Focused APIs:")
            print("   • Reduced data transfer for specific queries")
            print("   • Better caching opportunities")
            print("   • More granular error handling")
            print("   • Easier to optimize individual endpoints")
            print("   • Cleaner client code for specific use cases")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

async def test_performance_comparison():
    """Compare performance between focused and comprehensive APIs"""
    
    policy_server_url = "http://localhost:8001"
    test_customer_id = "CUST-001"
    
    print("\n🏃 Performance Comparison Test")
    print("=" * 60)
    
    try:
        async with Client(policy_server_url) as client:
            
            # Test scenario: Customer wants only payment information
            print("\n💰 Scenario: Customer wants only payment information")
            print("-" * 50)
            
            # Focused API approach
            print("🎯 Using Focused Payment API:")
            start_time = time.time()
            payment_result = await client.call_tool("get_payment_information", {"customer_id": test_customer_id})
            focused_duration = time.time() - start_time
            
            focused_data_size = 0
            for content in payment_result:
                if hasattr(content, 'text'):
                    focused_data_size = len(content.text)
                    break
            
            print(f"   ⏱️  Time: {focused_duration:.3f}s")
            print(f"   📦 Data: {focused_data_size:,} bytes")
            
            # Legacy comprehensive API approach
            print("\n🔄 Using Legacy Comprehensive API:")
            start_time = time.time()
            legacy_result = await client.call_tool("get_customer_policies", {"customer_id": test_customer_id})
            legacy_duration = time.time() - start_time
            
            legacy_data_size = 0
            for content in legacy_result:
                if hasattr(content, 'text'):
                    legacy_data_size = len(content.text)
                    break
            
            print(f"   ⏱️  Time: {legacy_duration:.3f}s")
            print(f"   📦 Data: {legacy_data_size:,} bytes")
            
            # Analysis
            print("\n📊 Analysis:")
            time_savings = ((legacy_duration - focused_duration) / legacy_duration) * 100 if legacy_duration > 0 else 0
            data_savings = ((legacy_data_size - focused_data_size) / legacy_data_size) * 100 if legacy_data_size > 0 else 0
            
            print(f"   ⚡ Time savings: {time_savings:.1f}%")
            print(f"   💾 Data savings: {data_savings:.1f}%")
            print(f"   🎯 Efficiency gain: {(time_savings + data_savings) / 2:.1f}%")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

if __name__ == "__main__":
    print("🧪 Policy Server Focused APIs Test Suite")
    print("=" * 60)
    print("Testing new modular API design against legacy comprehensive API")
    print()
    
    # Check if policy server is running
    try:
        import requests
        response = requests.get("http://localhost:8001/agent.json", timeout=5)
        if response.status_code != 200:
            print("❌ Policy server is not running on localhost:8001")
            print("   Please start it with: python policy_server/main.py")
            sys.exit(1)
    except Exception:
        print("❌ Cannot connect to policy server on localhost:8001")
        print("   Please start it with: python policy_server/main.py")
        sys.exit(1)
    
    # Run tests
    async def run_all_tests():
        success = await test_focused_apis()
        if success:
            await test_performance_comparison()
            
            print("\n✅ All tests completed successfully!")
            print("\n🎯 Recommendation:")
            print("   Use focused APIs for specific data needs")
            print("   Use legacy comprehensive API only when you need all data")
        else:
            print("\n❌ Tests failed")
            sys.exit(1)
    
    asyncio.run(run_all_tests()) 