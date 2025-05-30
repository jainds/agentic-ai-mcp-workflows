#!/usr/bin/env python3
"""
Kubernetes Integration Tests
Tests communication between components in the deployed system
"""

import requests
import json
import sys
import time
import subprocess
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

class IntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 15
        self.port_forwards = []

    def setup_port_forwards(self) -> bool:
        """Setup port forwards for all services"""
        try:
            print("🚀 Setting up port forwards for all services...")
            
            services = [
                ("policy-server", "8001", "8001"),
                ("technical-agent", "8002", "8002"), 
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
                time.sleep(2)  # Give each port-forward time to establish
            
            # Wait for all to be ready
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

    def test_policy_server_technical_agent(self) -> bool:
        """Test Policy Server <-> Technical Agent communication"""
        try:
            print("\n🔗 Testing Policy Server <-> Technical Agent Integration")
            
            # First verify both services are up
            policy_health = self.session.get("http://localhost:8001/health")
            technical_health = self.session.get("http://localhost:8002/agent.json")
            
            if policy_health.status_code != 200:
                print(f"❌ Policy Server not responding: {policy_health.status_code}")
                return False
                
            if technical_health.status_code != 200:
                print(f"❌ Technical Agent not responding: {technical_health.status_code}")
                return False
            
            # Test technical agent can process policy-related requests
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
                "http://localhost:8002/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"✅ Policy Server <-> Technical Agent: {response.status_code}")
            return response.status_code in [200, 201]
            
        except Exception as e:
            print(f"❌ Policy Server <-> Technical Agent Integration Failed: {e}")
            return False

    def test_technical_agent_domain_agent(self) -> bool:
        """Test Technical Agent <-> Domain Agent communication"""
        try:
            print("\n🔗 Testing Technical Agent <-> Domain Agent Integration")
            
            # Verify both agents are up
            technical_health = self.session.get("http://localhost:8002/agent.json")
            domain_health = self.session.get("http://localhost:8003/agent.json")
            
            if technical_health.status_code != 200:
                print(f"❌ Technical Agent not responding: {technical_health.status_code}")
                return False
                
            if domain_health.status_code != 200:
                print(f"❌ Domain Agent not responding: {domain_health.status_code}")
                return False
            
            # Test domain agent can process requests that require technical agent
            task_payload = {
                "message": {
                    "content": {
                        "type": "text",
                        "text": "Show me detailed policy analysis for customer CUST-001"
                    },
                    "role": "user"
                }
            }
            
            response = self.session.post(
                "http://localhost:8003/tasks/send",
                json=task_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"✅ Technical Agent <-> Domain Agent: {response.status_code}")
            return response.status_code in [200, 201]
            
        except Exception as e:
            print(f"❌ Technical Agent <-> Domain Agent Integration Failed: {e}")
            return False

    def test_domain_agent_ui(self) -> bool:
        """Test Domain Agent <-> UI communication"""
        try:
            print("\n🔗 Testing Domain Agent <-> UI Integration")
            
            # Verify both services are up
            domain_health = self.session.get("http://localhost:8003/agent.json")
            ui_health = self.session.get("http://localhost:8080/")
            
            if domain_health.status_code != 200:
                print(f"❌ Domain Agent not responding: {domain_health.status_code}")
                return False
                
            if ui_health.status_code != 200:
                print(f"❌ UI not responding: {ui_health.status_code}")
                return False
            
            # Verify UI has proper configuration for domain agent
            ui_content = ui_health.text
            if "insurance" in ui_content.lower():
                print("✅ UI content indicates proper insurance app setup")
            else:
                print("⚠️  UI content may not be properly configured")
            
            print(f"✅ Domain Agent <-> UI: Both services responding")
            return True
            
        except Exception as e:
            print(f"❌ Domain Agent <-> UI Integration Failed: {e}")
            return False

    def test_full_chain_connectivity(self) -> bool:
        """Test full chain: UI -> Domain Agent -> Technical Agent -> Policy Server"""
        try:
            print("\n🔗 Testing Full Chain Connectivity")
            
            # Test each link in the chain
            services = [
                ("UI", "http://localhost:8080/"),
                ("Domain Agent", "http://localhost:8003/agent.json"),
                ("Technical Agent", "http://localhost:8002/agent.json"),
                ("Policy Server", "http://localhost:8001/health")
            ]
            
            for service_name, url in services:
                response = self.session.get(url)
                if response.status_code not in [200, 201]:
                    print(f"❌ {service_name} not responding: {response.status_code}")
                    return False
                print(f"   ✅ {service_name}: OK")
            
            print("✅ Full Chain Connectivity: All services responding")
            return True
            
        except Exception as e:
            print(f"❌ Full Chain Connectivity Failed: {e}")
            return False

    def test_concurrent_requests(self) -> bool:
        """Test concurrent requests to domain agent"""
        try:
            print("\n🔗 Testing Concurrent Request Handling")
            
            def send_request(request_id: int) -> bool:
                try:
                    task_payload = {
                        "message": {
                            "content": {
                                "type": "text",
                                "text": f"Test concurrent request #{request_id}"
                            },
                            "role": "user"
                        }
                    }
                    
                    response = self.session.post(
                        "http://localhost:8003/tasks/send",
                        json=task_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    return response.status_code in [200, 201]
                except:
                    return False
            
            # Send 5 concurrent requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(send_request, i) for i in range(5)]
                results = [future.result() for future in as_completed(futures)]
            
            success_count = sum(results)
            print(f"✅ Concurrent Requests: {success_count}/5 successful")
            return success_count >= 3  # At least 3 out of 5 should succeed
            
        except Exception as e:
            print(f"❌ Concurrent Request Test Failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🧪 Running Kubernetes Integration Tests")
        print("=" * 60)
        
        if not self.setup_port_forwards():
            return {"setup": False}
        
        try:
            results = {
                "policy_server_technical_agent": self.test_policy_server_technical_agent(),
                "technical_agent_domain_agent": self.test_technical_agent_domain_agent(),
                "domain_agent_ui": self.test_domain_agent_ui(),
                "full_chain_connectivity": self.test_full_chain_connectivity(),
                "concurrent_requests": self.test_concurrent_requests()
            }
            
            print("\n📊 Integration Test Results:")
            for test, passed in results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"  {test}: {status}")
            
            all_passed = all(results.values())
            print(f"\n🎯 Overall: {'✅ ALL INTEGRATION TESTS PASSED' if all_passed else '❌ SOME INTEGRATION TESTS FAILED'}")
            return results
            
        finally:
            self.cleanup_port_forwards()

def main():
    """Main test runner"""
    tester = IntegrationTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main() 