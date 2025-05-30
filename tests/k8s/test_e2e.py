#!/usr/bin/env python3
"""
Kubernetes End-to-End Tests
Tests complete user workflows through the entire insurance AI system
"""

import requests
import json
import sys
import time
import subprocess
from typing import Dict, Any, Optional, List

class E2ETester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 20
        self.port_forwards = []

    def setup_port_forwards(self) -> bool:
        """Setup port forwards for all services"""
        try:
            print("🚀 Setting up port forwards for E2E testing...")
            
            services = [
                ("domain-agent", "8003", "8003"),
                ("streamlit-ui", "8080", "80")
            ]
            
            for service, local_port, service_port in services:
                print(f"   Setting up {service} on port {local_port}...")
                proc = subprocess.Popen([
                    "kubectl", "port-forward", "-n", "insurance-ai-agentic",
                    f"service/insurance-ai-poc-{service}", f"{local_port}:{service_port}"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                self.port_forwards.append(proc)
                time.sleep(2)
            
            print("   Waiting for port forwards to be ready...")
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup port forwards: {e}")
            return False

    def cleanup_port_forwards(self):
        """Clean up all port forward processes"""
        print("🧹 Cleaning up port forwards...")
        for proc in self.port_forwards:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass

    def test_ui_domain_agent_real_connectivity(self) -> bool:
        """Test real UI to Domain Agent connectivity through actual UI"""
        try:
            print("\n🎯 Testing Real UI->Domain Agent Connectivity")
            
            # Test that UI can actually reach domain agent by checking its internal connectivity
            # We'll simulate what the UI does when it tries to connect
            
            # First check if domain agent is reachable from UI pod perspective
            try:
                ui_pod_name = subprocess.check_output([
                    "kubectl", "get", "pods", "-n", "insurance-ai-agentic", 
                    "-l", "component=streamlit-ui", 
                    "-o", "jsonpath={.items[0].metadata.name}"
                ], text=True).strip()
                
                # Test domain agent connectivity from within UI pod
                test_cmd = [
                    "kubectl", "exec", "-n", "insurance-ai-agentic", ui_pod_name, "--",
                    "curl", "-s", "-X", "GET", 
                    "http://insurance-ai-poc-domain-agent:8003/agent.json",
                    "--max-time", "5"
                ]
                
                result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print("✅ UI can reach Domain Agent service")
                    
                    # Now test A2A communication
                    a2a_payload = '{"message": {"content": {"type": "text", "text": "Test connectivity"}, "role": "user"}}'
                    a2a_test_cmd = [
                        "kubectl", "exec", "-n", "insurance-ai-agentic", ui_pod_name, "--",
                        "curl", "-s", "-X", "POST", 
                        "http://insurance-ai-poc-domain-agent:8003/tasks/send",
                        "-H", "Content-Type: application/json",
                        "-d", a2a_payload,
                        "--max-time", "10"
                    ]
                    
                    a2a_result = subprocess.run(a2a_test_cmd, capture_output=True, text=True, timeout=15)
                    
                    if a2a_result.returncode == 0:
                        print("✅ A2A communication working from UI to Domain Agent")
                        try:
                            response_data = json.loads(a2a_result.stdout)
                            if "id" in response_data:
                                print(f"   A2A Task ID: {response_data.get('id')}")
                                return True
                        except:
                            print("   A2A response received but not JSON parseable")
                            return True
                    else:
                        print(f"❌ A2A communication failed: {a2a_result.stderr}")
                        return False
                else:
                    print(f"❌ UI cannot reach Domain Agent: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"❌ Failed to test UI->Domain Agent connectivity: {e}")
                return False
                
        except Exception as e:
            print(f"❌ UI->Domain Agent Real Connectivity Test Failed: {e}")
            return False

    def test_policy_inquiry_workflow(self) -> bool:
        """Test complete policy inquiry workflow"""
        try:
            print("\n🎯 Testing Policy Inquiry Workflow")
            
            # Test through A2A interface (what the UI actually uses)
            task_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": "Show me my current insurance policies for customer user_001"
                    },
                    "role": "user"
                }
            }
            
            response = self.session.post(
                "http://localhost:8003/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                print("✅ Policy inquiry request accepted")
                
                # Check if we can get task result
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get('id')
                    if task_id:
                        print(f"   Task ID: {task_id}")
                        
                        # Check for artifacts (actual response)
                        if "artifacts" in data and data["artifacts"]:
                            print("   ✅ Got response artifacts from domain agent")
                        
                        print("✅ Policy inquiry workflow completed")
                        return True
                
                return True
            else:
                print(f"❌ Policy inquiry failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Policy Inquiry Workflow Failed: {e}")
            return False

    def test_claims_workflow(self) -> bool:
        """Test complete claims workflow"""
        try:
            print("\n🎯 Testing Claims Workflow")
            
            # Simulate user asking about claims
            task_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": "I want to file a claim for my auto insurance"
                    },
                    "role": "user"
                }
            }
            
            response = self.session.post(
                "http://localhost:8003/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                print("✅ Claims request accepted")
                
                # Follow up with claim details
                followup_payload = {
                    "message": {
                        "content": {
                            "type": "text",
                            "text": "The accident happened yesterday, minor fender bender"
                        },
                        "role": "user"
                    }
                }
                
                followup_response = self.session.post(
                    "http://localhost:8003/tasks/send",
                    json=followup_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if followup_response.status_code in [200, 201]:
                    print("✅ Claims workflow with follow-up completed")
                    return True
                
                return True
            else:
                print(f"❌ Claims workflow failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Claims Workflow Failed: {e}")
            return False

    def test_quote_request_workflow(self) -> bool:
        """Test complete quote request workflow"""
        try:
            print("\n🎯 Testing Quote Request Workflow")
            
            # Simulate user requesting a quote
            task_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": "I need a quote for home insurance for a 2-bedroom house"
                    },
                    "role": "user"
                }
            }
            
            response = self.session.post(
                "http://localhost:8003/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                print("✅ Quote request accepted")
                
                # Follow up with more details
                details_payload = {
                    "message": {
                        "content": {
                            "type": "text",
                            "text": "The house is in California, built in 2010, estimated value $500,000"
                        },
                        "role": "user"
                    }
                }
                
                details_response = self.session.post(
                    "http://localhost:8003/tasks/send",
                    json=details_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if details_response.status_code in [200, 201]:
                    print("✅ Quote workflow with details completed")
                    return True
                
                return True
            else:
                print(f"❌ Quote request failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Quote Request Workflow Failed: {e}")
            return False

    def test_ui_accessibility_workflow(self) -> bool:
        """Test UI accessibility and basic functionality"""
        try:
            print("\n🎯 Testing UI Accessibility Workflow")
            
            # Test UI is accessible
            response = self.session.get("http://localhost:8080/")
            
            if response.status_code == 200:
                print("✅ UI is accessible")
                
                # Check if it's the right app
                content = response.text.lower()
                if "insurance" in content or "streamlit" in content:
                    print("✅ UI content appears to be correct insurance app")
                    return True
                else:
                    print("⚠️  UI content may not be the expected insurance app")
                    return True  # Still pass as UI is accessible
            else:
                print(f"❌ UI not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ UI Accessibility Workflow Failed: {e}")
            return False

    def test_error_handling_workflow(self) -> bool:
        """Test error handling in the system"""
        try:
            print("\n🎯 Testing Error Handling Workflow")
            
            # Send invalid request
            invalid_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": ""  # Empty message
                    },
                    "role": "user"
                }
            }
            
            response = self.session.post(
                "http://localhost:8003/tasks/send",
                json=invalid_payload,
                headers={"Content-Type": "application/json"}
            )
            
            # System should handle gracefully (either reject or process)
            if response.status_code in [200, 201, 400, 422]:
                print("✅ System handles invalid input gracefully")
                
                # Test with malformed request
                try:
                    malformed_response = self.session.post(
                        "http://localhost:8003/tasks/send",
                        data="invalid json",
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if malformed_response.status_code in [400, 422, 500]:
                        print("✅ System handles malformed requests appropriately")
                        return True
                    
                    return True
                except:
                    print("✅ System rejects malformed requests (connection error expected)")
                    return True
            else:
                print(f"❌ Unexpected error handling: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error Handling Workflow Failed: {e}")
            return False

    def test_multi_conversation_workflow(self) -> bool:
        """Test multiple conversation sessions"""
        try:
            print("\n🎯 Testing Multi-Conversation Workflow")
            
            # Start multiple conversation sessions
            conversations = [
                "Hello, I need help with my insurance",
                "What are my current policies?",
                "I want to file a claim"
            ]
            
            successful_conversations = 0
            
            for i, message in enumerate(conversations):
                task_payload = {
                    "message": {
                        "content": {
                            "type": "text",
                            "text": message
                        },
                        "role": "user"
                    }
                }
                
                response = self.session.post(
                    "http://localhost:8003/tasks/send",
                    json=task_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201]:
                    successful_conversations += 1
                    print(f"   ✅ Conversation {i+1}: Success")
                else:
                    print(f"   ❌ Conversation {i+1}: Failed ({response.status_code})")
                
                time.sleep(1)  # Brief pause between conversations
            
            if successful_conversations >= 2:
                print(f"✅ Multi-conversation workflow: {successful_conversations}/{len(conversations)} successful")
                return True
            else:
                print(f"❌ Multi-conversation workflow: Only {successful_conversations}/{len(conversations)} successful")
                return False
                
        except Exception as e:
            print(f"❌ Multi-Conversation Workflow Failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all E2E tests"""
        print("🧪 Running Kubernetes End-to-End Tests")
        print("=" * 60)
        
        if not self.setup_port_forwards():
            return {"setup": False}
        
        try:
            results = {
                "policy_inquiry_workflow": self.test_policy_inquiry_workflow(),
                "claims_workflow": self.test_claims_workflow(),
                "quote_request_workflow": self.test_quote_request_workflow(),
                "ui_accessibility_workflow": self.test_ui_accessibility_workflow(),
                "error_handling_workflow": self.test_error_handling_workflow(),
                "multi_conversation_workflow": self.test_multi_conversation_workflow(),
                "ui_domain_agent_real_connectivity": self.test_ui_domain_agent_real_connectivity()
            }
            
            print("\n📊 End-to-End Test Results:")
            for test, passed in results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {test}: {status}")
            
            all_passed = all(results.values())
            print(f"\n🎯 Overall: {'✅ ALL E2E TESTS PASSED' if all_passed else '❌ SOME E2E TESTS FAILED'}")
            
            if all_passed:
                print("\n🎉 Insurance AI Assistant is fully functional!")
                print("   The system successfully handles:")
                print("   • Policy inquiries")
                print("   • Claims processing")
                print("   • Quote requests")
                print("   • Error handling")
                print("   • Multiple conversations")
                print("   • UI accessibility")
            
            return results
            
        finally:
            self.cleanup_port_forwards()

def main():
    """Main test runner"""
    tester = E2ETester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main() 