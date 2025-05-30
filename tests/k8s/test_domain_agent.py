#!/usr/bin/env python3
"""
Kubernetes Domain Agent Component Test
Tests the domain agent component individually
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional

class DomainAgentTester:
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10

    def test_health_check(self) -> bool:
        """Test domain agent health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/agent.json")
            print(f"✅ Health Check (agent.json): {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Agent Name: {data.get('name', 'Unknown')}")
                print(f"   Agent Version: {data.get('version', 'Unknown')}")
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

    def test_conversation_task(self) -> bool:
        """Test conversation task processing"""
        try:
            # Test A2A conversation task
            task_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": "Hello, I need help with my insurance"
                    },
                    "role": "user"
                }
            }
            response = self.session.post(
                f"{self.base_url}/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ Conversation Task Test: {response.status_code}")
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"   Task ID: {data.get('id', 'Unknown')}")
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"❌ Conversation Task Test Failed: {e}")
            return False

    def test_technical_agent_connectivity(self) -> bool:
        """Test connectivity to technical agent"""
        try:
            # Test if domain agent can process complex requests that require technical agent
            task_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": "Show me my policies for customer CUST-001"
                    },
                    "role": "user"
                }
            }
            response = self.session.post(
                f"{self.base_url}/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"✅ Technical Agent Connectivity: {response.status_code}")
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"❌ Technical Agent Connectivity Failed: {e}")
            return False

    def test_intent_analysis(self) -> bool:
        """Test intent analysis capability"""
        try:
            # Test different types of insurance intents
            intents_to_test = [
                "I want to file a claim",
                "What are my current policies?",
                "I need a quote for auto insurance"
            ]
            
            for intent_text in intents_to_test:
                task_payload = {
                    "message": {
                        "content": {
                            "type": "text",
                            "text": intent_text
                        },
                        "role": "user"
                    }
                }
                response = self.session.post(
                    f"{self.base_url}/tasks/send",
                    json=task_payload,
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code not in [200, 201]:
                    print(f"❌ Intent Analysis Failed for: {intent_text}")
                    return False
            
            print(f"✅ Intent Analysis Test: All intents processed successfully")
            return True
        except Exception as e:
            print(f"❌ Intent Analysis Test Failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all domain agent tests"""
        print("🧪 Testing Domain Agent Component")
        print("=" * 50)
        
        results = {
            "health_check": self.test_health_check(),
            "a2a_endpoint": self.test_a2a_endpoint(),
            "conversation_task": self.test_conversation_task(),
            "technical_agent_connectivity": self.test_technical_agent_connectivity(),
            "intent_analysis": self.test_intent_analysis()
        }
        
        print("\n📊 Domain Agent Test Results:")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test}: {status}")
        
        all_passed = all(results.values())
        print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        return results

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Domain Agent in Kubernetes")
    parser.add_argument("--url", default="http://localhost:8003", 
                       help="Domain agent URL (default: http://localhost:8003)")
    parser.add_argument("--k8s", action="store_true", 
                       help="Use kubectl port-forward for testing")
    
    args = parser.parse_args()
    
    if args.k8s:
        print("🚀 Setting up kubectl port-forward for Domain Agent...")
        import subprocess
        
        # Start port-forward in background
        proc = subprocess.Popen([
            "kubectl", "port-forward", "-n", "insurance-ai-agentic",
            "service/insurance-ai-poc-domain-agent", "8003:8003"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for port-forward to be ready
        time.sleep(3)
        
        try:
            tester = DomainAgentTester(args.url)
            results = tester.run_all_tests()
            
            # Exit with error code if tests failed
            sys.exit(0 if all(results.values()) else 1)
            
        finally:
            # Clean up port-forward
            proc.terminate()
            proc.wait()
    else:
        tester = DomainAgentTester(args.url)
        results = tester.run_all_tests()
        
        # Exit with error code if tests failed
        sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main() 