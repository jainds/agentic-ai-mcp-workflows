#!/usr/bin/env python3
"""
Test FastMCP Integration with Insurance Services
Tests the FastMCP implementation in claims and policy services
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class MCPTester:
    """Test client for FastMCP services"""
    
    def __init__(self):
        self.base_urls = {
            "user": "http://localhost:8000",
            "claims": "http://localhost:8001",
            "policy": "http://localhost:8002",
            "analytics": "http://localhost:8003"
        }
        self.auth_token = "test-token-12345"  # Mock token for testing
        
    async def test_service_health(self, service: str) -> bool:
        """Test if service is healthy"""
        try:
            base_url = self.base_urls.get(service)
            if not base_url:
                print(f"❌ Unknown service: {service}")
                return False
                
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/health")
                if response.status_code == 200:
                    print(f"✅ {service.title()} Service: Healthy")
                    return True
                else:
                    print(f"❌ {service.title()} Service: Not healthy (status: {response.status_code})")
                    return False
        except Exception as e:
            print(f"❌ {service.title()} Service: Connection failed - {str(e)}")
            return False
    
    async def test_mcp_tools_list(self, service: str) -> bool:
        """Test MCP tools listing endpoint"""
        try:
            base_url = self.base_urls.get(service)
            if not base_url:
                return False
                
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{base_url}/mcp/tools/list")
                if response.status_code == 200:
                    tools_data = response.json()
                    tools = tools_data.get("tools", [])
                    print(f"✅ {service.title()} MCP Tools: {len(tools)} tools available")
                    for tool in tools:
                        print(f"   - {tool['name']}: {tool['description']}")
                    return True
                else:
                    print(f"❌ {service.title()} MCP Tools: Failed (status: {response.status_code})")
                    return False
        except Exception as e:
            print(f"❌ {service.title()} MCP Tools: Error - {str(e)}")
            return False
    
    async def test_mcp_tool_call(self, service: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Test calling a specific MCP tool"""
        try:
            base_url = self.base_urls.get(service)
            if not base_url:
                return False
                
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{base_url}/mcp/call", json=payload)
                if response.status_code == 200:
                    result_data = response.json()
                    result = result_data.get("result", {})
                    content = result.get("content", [])
                    
                    if content and len(content) > 0:
                        tool_result = json.loads(content[0].get("text", "{}"))
                        print(f"✅ {service.title()} Tool '{tool_name}': Success")
                        if tool_result.get("success"):
                            print(f"   Result: {json.dumps(tool_result, indent=2)}")
                        else:
                            print(f"   Error: {tool_result.get('error', 'Unknown error')}")
                        return True
                    else:
                        print(f"❌ {service.title()} Tool '{tool_name}': Empty result")
                        return False
                else:
                    print(f"❌ {service.title()} Tool '{tool_name}': Failed (status: {response.status_code})")
                    return False
        except Exception as e:
            print(f"❌ {service.title()} Tool '{tool_name}': Error - {str(e)}")
            return False
    
    async def test_claims_service(self):
        """Test Claims Service MCP integration"""
        print("\n🧪 Testing Claims Service MCP Integration")
        print("=" * 50)
        
        # Health check
        healthy = await self.test_service_health("claims")
        if not healthy:
            return False
        
        # List MCP tools
        tools_available = await self.test_mcp_tools_list("claims")
        if not tools_available:
            return False
        
        # Test list_claims tool
        await self.test_mcp_tool_call("claims", "list_claims", {
            "customer_id": "CUST-001"
        })
        
        # Test get_claim_details tool
        await self.test_mcp_tool_call("claims", "get_claim_details", {
            "claim_id": "CLM-001",
            "customer_id": "CUST-001"
        })
        
        # Test create_claim tool
        await self.test_mcp_tool_call("claims", "create_claim", {
            "customer_id": "CUST-001",
            "policy_number": "POL-001",
            "incident_date": "2024-05-30",
            "description": "FastMCP test claim",
            "amount": 1000.0,
            "claim_type": "auto_collision"
        })
        
        return True
    
    async def test_policy_service(self):
        """Test Policy Service MCP integration"""
        print("\n🧪 Testing Policy Service MCP Integration")
        print("=" * 50)
        
        # Health check
        healthy = await self.test_service_health("policy")
        if not healthy:
            print("⚠️  Policy service not available, skipping MCP tests")
            return False
        
        # List MCP tools
        tools_available = await self.test_mcp_tools_list("policy")
        if not tools_available:
            return False
        
        # Test list_policies tool
        await self.test_mcp_tool_call("policy", "list_policies", {
            "customer_id": "CUST-001"
        })
        
        # Test get_coverage_summary tool
        await self.test_mcp_tool_call("policy", "get_coverage_summary", {
            "customer_id": "CUST-001"
        })
        
        # Test calculate_quote tool
        await self.test_mcp_tool_call("policy", "calculate_quote", {
            "customer_id": "CUST-001",
            "policy_type": "auto",
            "coverage_amount": 50000.0,
            "risk_factors": {
                "age": 35,
                "location": "low_risk",
                "claims_history": 0
            }
        })
        
        return True
    
    async def run_all_tests(self):
        """Run all MCP integration tests"""
        print("🚀 Starting FastMCP Integration Tests")
        print("=" * 60)
        
        claims_success = await self.test_claims_service()
        policy_success = await self.test_policy_service()
        
        print("\n📊 Test Summary")
        print("=" * 30)
        print(f"Claims Service MCP: {'✅ PASS' if claims_success else '❌ FAIL'}")
        print(f"Policy Service MCP: {'✅ PASS' if policy_success else '❌ FAIL'}")
        
        overall_success = claims_success and policy_success
        print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '⚠️  SOME TESTS FAILED'}")
        
        return overall_success

async def main():
    """Main test function"""
    tester = MCPTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 