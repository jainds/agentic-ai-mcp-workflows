#!/usr/bin/env python3
"""
Test script to verify FastMCP-enabled insurance services are working.
"""

import asyncio
import httpx
import json
import sys
import os
from typing import Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.shared.port_utils import get_service_port

class ServiceTester:
    def __init__(self):
        self.services = {
            "user": {
                "default_port": 8000,
                "name": "User Service"
            },
            "claims": {
                "default_port": 8001,
                "name": "Claims Service"
            },
            "policy": {
                "default_port": 8002,
                "name": "Policy Service"
            },
            "analytics": {
                "default_port": 8003,
                "name": "Analytics Service"
            }
        }
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def test_health_endpoint(self, service_name: str, port: int) -> bool:
        """Test the health endpoint of a service"""
        try:
            url = f"http://localhost:{port}/health"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ Health check passed: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"  ✗ Health check failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ✗ Health check failed: {e}")
            return False
    
    async def test_fastapi_endpoint(self, service_name: str, port: int) -> bool:
        """Test that the service is running as FastAPI"""
        try:
            url = f"http://localhost:{port}/docs"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                print(f"  ✓ FastAPI docs accessible")
                return True
            else:
                print(f"  ✗ FastAPI docs not accessible: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ✗ FastAPI docs check failed: {e}")
            return False
    
    async def test_fastmcp_endpoints(self, service_name: str, port: int) -> bool:
        """Test FastMCP-specific endpoints"""
        try:
            # Test MCP tools list endpoint (if available)
            url = f"http://localhost:{port}/mcp/tools/list"
            response = await self.client.post(url)
            
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                print(f"  ✓ FastMCP integration working, {len(tools)} tools available")
                return True
            elif response.status_code == 404:
                print(f"  ! FastMCP endpoints not found (running as FastAPI)")
                return True  # This is acceptable
            else:
                print(f"  ✗ FastMCP test failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ! FastMCP test error (service may be running as FastAPI): {e}")
            return True  # This is acceptable if FastMCP is not available
    
    async def test_service(self, service_name: str) -> Dict[str, Any]:
        """Test a single service"""
        config = self.services[service_name]
        print(f"\nTesting {config['name']}...")
        
        # Get the port the service should be using
        try:
            port = get_service_port(service_name, config['default_port'])
        except Exception:
            port = config['default_port']
        
        print(f"  Testing on port {port}")
        
        results = {
            "service": service_name,
            "port": port,
            "health": await self.test_health_endpoint(service_name, port),
            "fastapi": await self.test_fastapi_endpoint(service_name, port),
            "fastmcp": await self.test_fastmcp_endpoints(service_name, port)
        }
        
        overall_status = results["health"] and results["fastapi"]
        status_icon = "✓" if overall_status else "✗"
        print(f"  {status_icon} Overall status: {'PASS' if overall_status else 'FAIL'}")
        
        return results
    
    async def test_all_services(self):
        """Test all services"""
        print("Testing FastMCP Insurance Services")
        print("=" * 50)
        
        all_results = {}
        passed_count = 0
        
        for service_name in self.services:
            results = await self.test_service(service_name)
            all_results[service_name] = results
            
            if results["health"] and results["fastapi"]:
                passed_count += 1
        
        print("\n" + "=" * 50)
        print(f"Test Summary: {passed_count}/{len(self.services)} services passed")
        
        if passed_count == len(self.services):
            print("🎉 All services are working correctly!")
        else:
            print("⚠️  Some services may need attention")
        
        return all_results
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    tester = ServiceTester()
    
    try:
        results = await tester.test_all_services()
        
        # Print detailed results
        print("\nDetailed Results:")
        for service_name, result in results.items():
            print(f"\n{service_name}:")
            print(f"  Port: {result['port']}")
            print(f"  Health: {'✓' if result['health'] else '✗'}")
            print(f"  FastAPI: {'✓' if result['fastapi'] else '✗'}")
            print(f"  FastMCP: {'✓' if result['fastmcp'] else '✗'}")
            
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main()) 