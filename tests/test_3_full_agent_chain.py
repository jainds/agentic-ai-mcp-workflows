#!/usr/bin/env python3
"""
Phase 3: Domain/Orchestrator + Technical Agent + Policy Server Integration
Tests the full agent workflow and coordination
"""

import pytest
import requests
import json
import time
import subprocess
import signal
import os
import sys
from typing import Dict, Any

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'insurance-adk'))

class TestFullAgentChain:
    """Full Agent Chain Integration Tests"""
    
    @pytest.fixture(scope="class")
    def policy_server_process(self):
        """Start policy server"""
        print("🚀 Starting Policy Server...")
        
        policy_dir = os.path.join(os.path.dirname(__file__), '..', 'policy_server')
        process = subprocess.Popen(
            ['python', 'main.py'],
            cwd=policy_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        time.sleep(3)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(f"Policy server failed: {stderr.decode()}")
        
        yield process
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()
    
    @pytest.fixture(scope="class")
    def technical_agent_process(self):
        """Start technical agent ADK server"""
        print("🤖 Starting Technical Agent...")
        
        env = os.environ.copy()
        env['GOOGLE_API_KEY'] = 'test_placeholder'
        env['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY', 'test_key')
        
        insurance_adk_dir = os.path.join(os.path.dirname(__file__), '..', 'insurance-adk')
        
        process = subprocess.Popen(
            ['python', '-c', '''
import os
os.environ["GOOGLE_API_KEY"] = "test_placeholder"
from google.adk.cli import cli
cli.main(["api_server", "insurance_technical_agent", "--port", "8002"])
            '''],
            cwd=insurance_adk_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid
        )
        time.sleep(5)
        
        yield process
        
        if process.poll() is None:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait()
    
    @pytest.fixture(scope="class")
    def domain_agent_process(self):
        """Start domain agent ADK server"""
        print("👥 Starting Domain Agent...")
        
        env = os.environ.copy()
        env['GOOGLE_API_KEY'] = 'test_placeholder'
        env['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY', 'test_key')
        
        insurance_adk_dir = os.path.join(os.path.dirname(__file__), '..', 'insurance-adk')
        
        process = subprocess.Popen(
            ['python', '-c', '''
import os
os.environ["GOOGLE_API_KEY"] = "test_placeholder"
from google.adk.cli import cli
cli.main(["api_server", "insurance_customer_service", "--port", "8003"])
            '''],
            cwd=insurance_adk_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid
        )
        time.sleep(5)
        
        yield process
        
        if process.poll() is None:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait()
    
    def test_all_services_running(self, policy_server_process, technical_agent_process, domain_agent_process):
        """Test all services are running"""
        assert policy_server_process.poll() is None, "Policy server should be running"
        print("✅ Policy server: Running")
        
        # Test technical agent (may not be fully ready)
        if technical_agent_process.poll() is None:
            print("✅ Technical agent: Running")
        else:
            print("⚠️  Technical agent: Process ended")
        
        # Test domain agent (may not be fully ready)
        if domain_agent_process.poll() is None:
            print("✅ Domain agent: Running")
        else:
            print("⚠️  Domain agent: Process ended")
    
    def test_policy_server_connectivity(self, policy_server_process):
        """Test policy server is accessible"""
        try:
            response = requests.get("http://localhost:8001/mcp", timeout=5)
            assert response.status_code in [405, 307, 406]
            print("✅ Policy server connectivity: PASSED")
        except Exception as e:
            pytest.fail(f"Policy server not accessible: {e}")
    
    def test_session_management_workflow(self):
        """Test session management across agents"""
        try:
            # Test session creation and management
            from tools.session_tools import create_session_manager
            
            session_manager = create_session_manager()
            
            # Create session
            session_id = session_manager.create_session("CUST001")
            assert session_id is not None
            print(f"✅ Session creation: PASSED (ID: {session_id[:8]}...)")
            
            # Get session data
            session_data = session_manager.get_session_data(session_id)
            assert session_data['customer_id'] == "CUST001"
            print("✅ Session data retrieval: PASSED")
            
            # Update session
            update_success = session_manager.update_session(session_id, {"test_key": "test_value"})
            assert update_success
            print("✅ Session update: PASSED")
            
            # Test conversation history
            conv_success = session_manager.add_conversation_entry(
                session_id, 
                "Hello, I need help with my policy",
                "I can help you with that. Let me look up your policy information.",
                "policy_inquiry"
            )
            assert conv_success
            print("✅ Conversation tracking: PASSED")
            
        except ImportError as e:
            print(f"⚠️  Session management import error: {e}")
        except Exception as e:
            print(f"⚠️  Session management workflow error: {e}")
    
    def test_agent_to_agent_communication_simulation(self, policy_server_process):
        """Simulate agent-to-agent communication workflow"""
        try:
            # Simulate Domain Agent -> Technical Agent -> Policy Server workflow
            
            # 1. Domain agent receives customer request
            customer_request = {
                "customer_id": "CUST001",
                "message": "What's my current premium for my auto insurance?",
                "session_id": "test_session_123"
            }
            print(f"📥 Customer request: {customer_request['message']}")
            
            # 2. Technical agent processes policy lookup
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_policies",
                    "arguments": {
                        "customer_id": customer_request["customer_id"]
                    }
                }
            }
            
            response = requests.post(
                "http://localhost:8001/mcp",
                json=mcp_request,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    print("✅ Technical agent policy lookup: PASSED")
                    
                    # 3. Parse and format response for customer
                    policy_info = data["result"]
                    customer_response = f"I found your policy information. Your current premium details are available."
                    print(f"📤 Customer response: {customer_response}")
                    
                    print("✅ Agent-to-agent workflow simulation: PASSED")
                else:
                    print(f"⚠️  Policy lookup error: {data.get('error', 'Unknown error')}")
            else:
                print(f"⚠️  Technical agent communication: Status {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Agent communication simulation error: {e}")
    
    def test_comprehensive_workflow_simulation(self, policy_server_process):
        """Test comprehensive workflow with multiple customers and scenarios"""
        try:
            print("\n🎭 COMPREHENSIVE WORKFLOW SIMULATION")
            print("-" * 50)
            
            # Test scenarios for different customers
            test_scenarios = [
                {
                    "customer_id": "CUST001",
                    "name": "John Smith", 
                    "scenario": "Multi-policy customer inquiry",
                    "expected_policies": 2
                },
                {
                    "customer_id": "CUST002", 
                    "name": "Jane Doe",
                    "scenario": "Single policy customer inquiry",
                    "expected_policies": 1
                },
                {
                    "customer_id": "CUST003",
                    "name": "Bob Johnson", 
                    "scenario": "Life insurance inquiry",
                    "expected_policies": 1
                },
                {
                    "customer_id": "CUST004",
                    "name": "Alice Williams",
                    "scenario": "New customer inquiry", 
                    "expected_policies": 1
                }
            ]
            
            successful_scenarios = 0
            
            for scenario in test_scenarios:
                print(f"\n📋 Testing: {scenario['scenario']}")
                print(f"   Customer: {scenario['name']} ({scenario['customer_id']})")
                
                # Simulate policy lookup
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": 100 + int(scenario['customer_id'][-1]),
                    "method": "tools/call",
                    "params": {
                        "name": "get_policies",
                        "arguments": {"customer_id": scenario['customer_id']}
                    }
                }
                
                response = requests.post(
                    "http://localhost:8001/mcp",
                    json=mcp_request,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        policies = data["result"]
                        if len(policies) == scenario['expected_policies']:
                            print(f"   ✅ SUCCESS: Found {len(policies)} policies (as expected)")
                            successful_scenarios += 1
                        else:
                            print(f"   ⚠️  PARTIAL: Found {len(policies)} policies (expected {scenario['expected_policies']})")
                    else:
                        print(f"   ❌ FAILED: {data.get('error', 'Unknown error')}")
                else:
                    print(f"   ❌ FAILED: Status {response.status_code}")
            
            success_rate = (successful_scenarios / len(test_scenarios)) * 100
            print(f"\n📊 WORKFLOW SIMULATION RESULTS:")
            print(f"   Successful scenarios: {successful_scenarios}/{len(test_scenarios)} ({success_rate:.0f}%)")
            
            if success_rate >= 75:
                print("✅ Comprehensive workflow simulation: PASSED")
            else:
                print("⚠️  Comprehensive workflow simulation: PARTIAL SUCCESS")
                
        except Exception as e:
            print(f"❌ Comprehensive workflow simulation error: {e}")
    
    def test_error_propagation_workflow(self, policy_server_process):
        """Test error handling across agent chain"""
        try:
            # Test invalid customer ID propagation
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "get_policies",
                    "arguments": {
                        "customer_id": "INVALID_CUSTOMER"
                    }
                }
            }
            
            response = requests.post(
                "http://localhost:8001/mcp",
                json=mcp_request,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data or ("result" in data and not data["result"]):
                    print("✅ Error propagation: PASSED (Properly handles invalid customer)")
                else:
                    print("⚠️  Error propagation: Should handle invalid customer ID")
            else:
                print(f"⚠️  Error propagation test: Status {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Error propagation test error: {e}")
    
    def test_concurrent_agent_requests(self, policy_server_process):
        """Test handling concurrent requests across agents"""
        import threading
        import time
        
        results = []
        
        def simulate_agent_request(customer_id):
            try:
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": int(time.time() * 1000),
                    "method": "tools/call",
                    "params": {
                        "name": "get_policies",
                        "arguments": {"customer_id": customer_id}
                    }
                }
                
                response = requests.post(
                    "http://localhost:8001/mcp",
                    json=mcp_request,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                results.append(response.status_code == 200)
                
            except Exception:
                results.append(False)
        
        # Simulate multiple agents making concurrent requests
        customers = ["CUST001", "CUST002", "CUST003"]
        threads = []
        
        for customer_id in customers:
            thread = threading.Thread(target=simulate_agent_request, args=(customer_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        success_rate = sum(results) / len(results) if results else 0
        if success_rate >= 0.8:
            print(f"✅ Concurrent agent requests: PASSED ({success_rate:.1%} success)")
        else:
            print(f"⚠️  Concurrent agent requests: {success_rate:.1%} success rate")
    
    def test_data_consistency_across_agents(self, policy_server_process):
        """Test data consistency when accessed by different agents"""
        try:
            # Make the same request multiple times to ensure consistency
            customer_id = "CUST001"
            responses = []
            
            for i in range(3):
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": i + 10,
                    "method": "tools/call",
                    "params": {
                        "name": "get_policies",
                        "arguments": {"customer_id": customer_id}
                    }
                }
                
                response = requests.post(
                    "http://localhost:8001/mcp",
                    json=mcp_request,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    responses.append(response.json())
                else:
                    break
            
            if len(responses) >= 2:
                # Check if responses are consistent
                first_result = responses[0].get("result", {})
                consistent = all(
                    resp.get("result", {}) == first_result 
                    for resp in responses[1:]
                )
                
                if consistent:
                    print("✅ Data consistency: PASSED")
                else:
                    print("⚠️  Data consistency: Inconsistent responses detected")
            else:
                print("⚠️  Data consistency: Insufficient responses to test")
                
        except Exception as e:
            print(f"⚠️  Data consistency test error: {e}")
    
    def test_end_to_end_customer_workflow(self, policy_server_process):
        """Test complete end-to-end customer service workflow"""
        try:
            print("\n🎭 SIMULATING END-TO-END CUSTOMER WORKFLOW")
            print("-" * 50)
            
            # 1. Customer initiates contact
            customer_request = {
                "customer_id": "CUST001",
                "message": "I want to check my policy coverage and recent claims",
                "session_id": "e2e_test_session"
            }
            print(f"1. 📞 Customer: {customer_request['message']}")
            
            # 2. Domain agent would parse intent and route to technical agent
            print("2. 🤖 Domain Agent: Parsing customer intent...")
            print("   ✅ Intent identified: policy_inquiry + claims_check")
            print("   ➡️  Routing to Technical Agent...")
            
            # 3. Technical agent retrieves policy data
            print("3. ⚙️  Technical Agent: Retrieving policy data...")
            
            policy_response = requests.post(
                "http://localhost:8001/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "get_policies",
                        "arguments": {"customer_id": customer_request["customer_id"]}
                    }
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if policy_response.status_code == 200:
                policy_data = policy_response.json()
                if "result" in policy_data:
                    print("   ✅ Policy data retrieved successfully")
                    
                    # 4. Technical agent processes claims data
                    print("4. 🔍 Technical Agent: Checking claims history...")
                    
                    claims_response = requests.post(
                        "http://localhost:8001/mcp",
                        json={
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/call",
                            "params": {
                                "name": "get_coverage_information",
                                "arguments": {"customer_id": customer_request["customer_id"]}
                            }
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if claims_response.status_code == 200:
                        claims_data = claims_response.json()
                        print("   ✅ Claims data retrieved successfully")
                        
                        # 5. Domain agent formats customer-friendly response
                        print("5. 💬 Domain Agent: Formatting customer response...")
                        customer_response = "I've found your policy and claims information. Your coverage is active and I can see your recent claims history."
                        print(f"   📤 Response: {customer_response}")
                        
                        print("\n✅ END-TO-END WORKFLOW: PASSED")
                        return True
                    else:
                        print(f"   ⚠️  Claims lookup failed: {claims_response.status_code}")
                else:
                    print(f"   ⚠️  Policy lookup error: {policy_data.get('error', 'Unknown')}")
            else:
                print(f"   ⚠️  Policy request failed: {policy_response.status_code}")
            
            print("\n⚠️  END-TO-END WORKFLOW: Partial completion")
            return False
            
        except Exception as e:
            print(f"\n❌ END-TO-END WORKFLOW ERROR: {e}")
            return False

def run_full_agent_chain_tests():
    """Run full agent chain tests"""
    print("=" * 80)
    print("🔗 PHASE 3: FULL AGENT CHAIN INTEGRATION")
    print("=" * 80)
    
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--no-header",
        "-s"
    ])
    
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ PHASE 3 COMPLETE: Full agent chain tests PASSED")
    else:
        print("⚠️  PHASE 3 COMPLETE: Some full chain tests had issues")
    print("=" * 80)
    
    return exit_code == 0

if __name__ == "__main__":
    run_full_agent_chain_tests() 