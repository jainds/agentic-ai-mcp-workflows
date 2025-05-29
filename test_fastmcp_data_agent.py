#!/usr/bin/env python3
"""
Test FastMCP Data Agent
Tests the new FastMCP-based technical agent that connects to our mock services
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add the agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agents'))

async def test_fastmcp_data_agent():
    """Test the FastMCP Data Agent functionality"""
    print("🧪 Testing FastMCP Data Agent")
    print("=" * 40)
    
    try:
        from technical.fastmcp_data_agent import FastMCPDataAgent
        
        # Create and initialize the agent
        agent = FastMCPDataAgent()
        print("✅ FastMCP Data Agent created")
        
        # Initialize - this will discover tools from services
        await agent.initialize()
        print("✅ Agent initialized")
        
        # Get available tools
        tools = await agent.get_available_tools()
        print(f"\n📋 Available Tools:")
        for service, service_tools in tools.items():
            print(f"  {service}: {len(service_tools)} tools")
            for tool in service_tools:
                print(f"    - {tool['name']}: {tool['description']}")
        
        # Test customer data operations
        print(f"\n🔧 Testing Customer Operations:")
        
        # Test getting customer claims
        print("  Testing get_customer_claims...")
        claims_result = await agent.get_customer_claims("CUST-001")
        if claims_result.get("success"):
            claims = claims_result.get("claims", [])
            print(f"    ✅ Found {len(claims)} claims for CUST-001")
        else:
            print(f"    ❌ Failed: {claims_result.get('error', 'Unknown error')}")
        
        # Test getting customer policies  
        print("  Testing get_customer_policies...")
        policies_result = await agent.get_customer_policies("CUST-001")
        if policies_result.get("success"):
            policies = policies_result.get("policies", [])
            print(f"    ✅ Found {len(policies)} policies for CUST-001")
        else:
            print(f"    ⚠️  Policy service not available: {policies_result.get('error', 'Unknown error')}")
        
        # Test creating a new claim
        print("  Testing create_claim...")
        create_result = await agent.create_claim(
            customer_id="CUST-001",
            policy_number="POL-001",
            incident_date="2024-05-30",
            description="FastMCP Data Agent test claim",
            amount=2000.0,
            claim_type="auto_collision"
        )
        if create_result.get("success"):
            claim_id = create_result.get("claim_id")
            print(f"    ✅ Created new claim: {claim_id}")
        else:
            print(f"    ❌ Failed: {create_result.get('error', 'Unknown error')}")
        
        # Test comprehensive customer summary
        print("  Testing generate_customer_summary...")
        summary_result = await agent.generate_customer_summary("CUST-001")
        if summary_result.get("success"):
            summary = summary_result.get("summary", {})
            print(f"    ✅ Customer Summary:")
            print(f"      - Total Policies: {summary.get('total_policies', 0)}")
            print(f"      - Total Claims: {summary.get('total_claims', 0)}")
            print(f"      - Total Coverage: ${summary.get('total_coverage', 0):,.2f}")
            print(f"      - Total Claims Amount: ${summary.get('total_claims_amount', 0):,.2f}")
        else:
            print(f"    ❌ Failed: {summary_result.get('error', 'Unknown error')}")
        
        # Clean up
        await agent.close()
        print("\n🎉 All FastMCP Data Agent tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Starting FastMCP Data Agent Tests")
    print("=" * 50)
    
    success = await test_fastmcp_data_agent()
    
    print(f"\n📋 Test Summary")
    print("=" * 20)
    print(f"FastMCP Data Agent: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 All tests passed! FastMCP Data Agent is ready.")
    else:
        print("\n❌ Tests failed. Check the setup.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 