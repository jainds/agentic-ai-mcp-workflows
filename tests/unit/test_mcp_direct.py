#!/usr/bin/env python3
"""
Direct MCP Connection Test
Test the policy server MCP endpoint directly
"""

import json
import subprocess
import time
from mcp.client.streamable_http import StreamableHttpClient


async def test_mcp_direct():
    """Test MCP connection directly"""
    
    # Set up port forward for policy server
    print("🔌 Setting up port forward for policy server...")
    port_forward = subprocess.Popen([
        "kubectl", "port-forward", "-n", "insurance-ai-agentic",
        "service/insurance-ai-poc-policy-server", "8001:8001"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(3)  # Wait for port forward
    
    try:
        # Create MCP client
        print("🔍 Creating MCP client...")
        client = StreamableHttpClient("http://localhost:8001/mcp")
        
        # Initialize session
        print("🚀 Initializing MCP session...")
        await client.initialize()
        
        # List available tools
        print("📋 Listing available tools...")
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools.tools]}")
        
        # Test get_customer_policies
        print("🔍 Testing get_customer_policies for CUST-001...")
        result = await client.call_tool(
            "get_customer_policies",
            arguments={"customer_id": "CUST-001"}
        )
        
        print("✅ MCP call successful!")
        print(f"Result: {result}")
        
        # Close session
        await client.close()
        
    except Exception as e:
        print(f"❌ MCP test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up port forward
        print("🧹 Cleaning up port forward...")
        port_forward.terminate()
        port_forward.wait()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_mcp_direct()) 