#!/usr/bin/env python3
"""
Kubernetes Policy Server Component Test
Tests the policy server component individually
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional

class PolicyServerTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10

    def test_health_check(self) -> bool:
        """Test policy server health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            print(f"✅ Health Check: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return False

    def test_mcp_endpoint(self) -> bool:
        """Test MCP endpoint availability"""
        try:
            response = self.session.get(f"{self.base_url}/mcp")
            print(f"✅ MCP Endpoint: {response.status_code}")
            return response.status_code in [200, 405]  # 405 is OK for GET on POST endpoint
        except Exception as e:
            print(f"❌ MCP Endpoint Failed: {e}")
            return False

    def test_policy_data(self) -> bool:
        """Test policy data retrieval"""
        try:
            # Test MCP call for policies
            mcp_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            response = self.session.post(
                f"{self.base_url}/mcp", 
                json=mcp_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ Policy Data Test: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Policy Data Test Failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all policy server tests"""
        print("🧪 Testing Policy Server Component")
        print("=" * 50)
        
        results = {
            "health_check": self.test_health_check(),
            "mcp_endpoint": self.test_mcp_endpoint(),
            "policy_data": self.test_policy_data()
        }
        
        print("\n📊 Policy Server Test Results:")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test}: {status}")
        
        all_passed = all(results.values())
        print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        return results

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Policy Server in Kubernetes")
    parser.add_argument("--url", default="http://localhost:8001", 
                       help="Policy server URL (default: http://localhost:8001)")
    parser.add_argument("--k8s", action="store_true", 
                       help="Use kubectl port-forward for testing")
    
    args = parser.parse_args()
    
    if args.k8s:
        print("🚀 Setting up kubectl port-forward for Policy Server...")
        import subprocess
        import os
        
        # Start port-forward in background
        proc = subprocess.Popen([
            "kubectl", "port-forward", "-n", "insurance-ai-agentic",
            "service/insurance-ai-poc-policy-server", "8001:8001"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for port-forward to be ready
        time.sleep(3)
        
        try:
            tester = PolicyServerTester(args.url)
            results = tester.run_all_tests()
            
            # Exit with error code if tests failed
            sys.exit(0 if all(results.values()) else 1)
            
        finally:
            # Clean up port-forward
            proc.terminate()
            proc.wait()
    else:
        tester = PolicyServerTester(args.url)
        results = tester.run_all_tests()
        
        # Exit with error code if tests failed
        sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main() 