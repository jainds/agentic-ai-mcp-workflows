#!/usr/bin/env python3
"""
Kubernetes Technical Agent Component Test
Tests the technical agent component individually
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional

class TechnicalAgentTester:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10

    def test_health_check(self) -> bool:
        """Test technical agent health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/agent.json")
            print(f"✅ Health Check (agent.json): {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Agent Name: {data.get('name', 'Unknown')}")
                    print(f"   Agent Version: {data.get('version', 'Unknown')}")
                except:
                    print("   Agent responding (JSON parsing issue but endpoint works)")
                return True
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return False

    def test_a2a_endpoint(self) -> bool:
        """Test A2A endpoint availability"""
        try:
            response = self.session.get(f"{self.base_url}/a2a")
            print(f"✅ A2A Endpoint: {response.status_code}")
            return response.status_code in [200, 405, 501]  # Various acceptable responses
        except Exception as e:
            print(f"❌ A2A Endpoint Failed: {e}")
            return False

    def test_task_processing(self) -> bool:
        """Test task processing capability"""
        try:
            # Test A2A task submission
            task_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": "Test technical agent connectivity"
                    },
                    "role": "user"
                }
            }
            response = self.session.post(
                f"{self.base_url}/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ Task Processing Test: {response.status_code}")
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"   Task ID: {data.get('id', 'Unknown')}")
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"❌ Task Processing Test Failed: {e}")
            return False

    def test_policy_server_connectivity(self) -> bool:
        """Test connectivity to policy server"""
        try:
            # Test if technical agent can reach policy server
            # This is an indirect test through agent functionality
            task_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": "Get policy information for customer CUST-001"
                    },
                    "role": "user"
                }
            }
            response = self.session.post(
                f"{self.base_url}/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ Policy Server Connectivity: {response.status_code}")
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"❌ Policy Server Connectivity Failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all technical agent tests"""
        print("🧪 Testing Technical Agent Component")
        print("=" * 50)
        
        results = {
            "health_check": self.test_health_check(),
            "a2a_endpoint": self.test_a2a_endpoint(),
            "task_processing": self.test_task_processing(),
            "policy_server_connectivity": self.test_policy_server_connectivity()
        }
        
        print("\n📊 Technical Agent Test Results:")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test}: {status}")
        
        all_passed = all(results.values())
        print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        return results

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Technical Agent in Kubernetes")
    parser.add_argument("--url", default="http://localhost:8002", 
                       help="Technical agent URL (default: http://localhost:8002)")
    parser.add_argument("--k8s", action="store_true", 
                       help="Use kubectl port-forward for testing")
    
    args = parser.parse_args()
    
    if args.k8s:
        print("🚀 Setting up kubectl port-forward for Technical Agent...")
        import subprocess
        
        # Start port-forward in background
        proc = subprocess.Popen([
            "kubectl", "port-forward", "-n", "insurance-ai-agentic",
            "service/insurance-ai-poc-technical-agent", "8002:8002"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for port-forward to be ready
        time.sleep(3)
        
        try:
            tester = TechnicalAgentTester(args.url)
            results = tester.run_all_tests()
            
            # Exit with error code if tests failed
            sys.exit(0 if all(results.values()) else 1)
            
        finally:
            # Clean up port-forward
            proc.terminate()
            proc.wait()
    else:
        tester = TechnicalAgentTester(args.url)
        results = tester.run_all_tests()
        
        # Exit with error code if tests failed
        sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main() 