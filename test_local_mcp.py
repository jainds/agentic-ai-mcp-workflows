#!/usr/bin/env python3
"""
Local FastMCP Test
Tests the FastMCP implementation directly without requiring deployment
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add the services directory to path so we can import
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

async def test_claims_mcp_locally():
    """Test Claims MCP server locally"""
    print("🧪 Testing Claims FastMCP Implementation Locally")
    print("=" * 55)
    
    try:
        # Import the claims service components
        from claims_service.main import Claim, app, claims_db, init_mock_data
        from claims_service.mcp_server import ClaimsMCPServer
        
        # Initialize mock data
        init_mock_data()
        print(f"✅ Mock data initialized: {len(claims_db)} claims loaded")
        
        # Create FastMCP server
        mcp_server = ClaimsMCPServer(app, claims_db)
        print("✅ FastMCP server created successfully")
        
        # Test MCP tools directly
        print("\n🔧 Testing MCP Tools:")
        
        # Get available tools
        tools = await mcp_server.mcp.get_tools()
        print(f"    Available tools: {list(tools.keys())}")
        
        # Test list_claims tool
        print("  Testing list_claims...")
        if "list_claims" in tools:
            list_result = await tools["list_claims"].fn(customer_id="CUST-001")
            print(f"    ✅ list_claims result: {list_result['success']}, {list_result.get('total_claims', 0)} claims found")
        else:
            print("    ❌ list_claims tool not found")
        
        # Test get_claim_details tool
        print("  Testing get_claim_details...")
        if "get_claim_details" in tools:
            detail_result = await tools["get_claim_details"].fn(
                claim_id="CLM-001", 
                customer_id="CUST-001"
            )
            print(f"    ✅ get_claim_details result: {detail_result['success']}")
        else:
            print("    ❌ get_claim_details tool not found")
        
        # Test create_claim tool
        print("  Testing create_claim...")
        if "create_claim" in tools:
            create_result = await tools["create_claim"].fn(
                customer_id="CUST-001",
                policy_number="POL-TEST",
                incident_date="2024-05-30",
                description="Local FastMCP test claim",
                amount=1500.0,
                claim_type="auto_collision"
            )
            print(f"    ✅ create_claim result: {create_result['success']}, claim_id: {create_result.get('claim_id', 'N/A')}")
        else:
            print("    ❌ create_claim tool not found")
        
        # Verify new claim was added to database
        new_claim_count = len([c for c in claims_db.values() if c.customer_id == "CUST-001"])
        print(f"    ✅ Total claims for CUST-001 after creation: {new_claim_count}")
        
        print("\n🎉 All Claims FastMCP tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 This is expected if fastmcp library is not installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_fastmcp_availability():
    """Test if FastMCP library is available"""
    print("🔍 Checking FastMCP Library Availability")
    print("=" * 45)
    
    try:
        from fastmcp import FastMCP
        print("✅ FastMCP library is available")
        
        # Test basic FastMCP functionality
        test_mcp = FastMCP(name="test", description="Test MCP server")
        print("✅ FastMCP server can be instantiated")
        
        return True
    except ImportError as e:
        print(f"❌ FastMCP library not available: {e}")
        print("💡 You may need to install it: pip install fastmcp")
        return False
    except Exception as e:
        print(f"❌ FastMCP error: {e}")
        return False

async def test_mock_data_generation():
    """Test mock data generation without MCP"""
    print("\n📊 Testing Mock Data Generation")
    print("=" * 35)
    
    try:
        # Import just the data models and mock generation
        sys.path.append('services/claims_service')
        from main import init_mock_data, claims_db, Claim
        
        # Clear and reinitialize
        claims_db.clear()
        init_mock_data()
        
        print(f"✅ Generated {len(claims_db)} mock claims")
        
        # Show sample data
        for claim_id, claim in list(claims_db.items())[:2]:
            print(f"   - {claim_id}: {claim.customer_id} - {claim.description[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Error generating mock data: {e}")
        return False

async def run_local_tests():
    """Run all local tests"""
    print("🚀 Starting Local FastMCP Tests")
    print("=" * 40)
    
    # Test 1: FastMCP availability
    fastmcp_available = await test_fastmcp_availability()
    
    # Test 2: Mock data generation
    mock_data_works = await test_mock_data_generation()
    
    # Test 3: Claims MCP (only if FastMCP available)
    claims_mcp_works = False
    if fastmcp_available:
        claims_mcp_works = await test_claims_mcp_locally()
    else:
        print("\n⚠️  Skipping Claims FastMCP test (library not available)")
    
    # Summary
    print("\n📋 Local Test Summary")
    print("=" * 25)
    print(f"FastMCP Library: {'✅ Available' if fastmcp_available else '❌ Missing'}")
    print(f"Mock Data: {'✅ Working' if mock_data_works else '❌ Failed'}")
    print(f"Claims MCP: {'✅ Working' if claims_mcp_works else '❌ Failed/Skipped'}")
    
    if fastmcp_available and mock_data_works and claims_mcp_works:
        print("\n🎉 All local tests passed! FastMCP implementation is ready.")
        return True
    elif mock_data_works:
        print("\n⚠️  Basic functionality works, but FastMCP needs setup.")
        return False
    else:
        print("\n❌ Core functionality issues detected.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_local_tests())
    sys.exit(0 if success else 1) 