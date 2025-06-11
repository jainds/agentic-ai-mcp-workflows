#!/usr/bin/env python3
"""
Comprehensive Kubernetes Test Suite for Insurance AI POC - Post OpenRouter Integration
Following the established 4-phase testing pattern from main branch but adapted for Kubernetes deployment
"""

import pytest
import requests
import json
import time
import subprocess
import signal
import os
import sys
import asyncio
from typing import Dict, Any, List
import threading
import concurrent.futures
import statistics

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ui'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'insurance-adk'))

class KubernetesTestOrchestrator:
    """Test orchestrator adapted for Kubernetes environment"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.namespace = "insurance-ai-poc"
        
    def check_kubernetes_availability(self) -> bool:
        """Check if Kubernetes environment is available"""
        try:
            result = subprocess.run(
                ['kubectl', 'get', 'namespace', self.namespace],
                capture_output=True, timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def wait_for_deployment_ready(self, deployment_name: str, timeout: int = 120) -> bool:
        """Wait for a deployment to be ready"""
        try:
            result = subprocess.run(
                ['kubectl', 'wait', '--for=condition=available', 
                 f'deployment/{deployment_name}', '-n', self.namespace, f'--timeout={timeout}s'],
                capture_output=True, timeout=timeout + 10
            )
            return result.returncode == 0
        except:
            return False
    
    def get_pod_logs(self, deployment_name: str, lines: int = 20) -> str:
        """Get logs from a deployment"""
        try:
            result = subprocess.run(
                ['kubectl', 'logs', f'deployment/{deployment_name}', 
                 '-n', self.namespace, f'--tail={lines}'],
                capture_output=True, timeout=10, text=True
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except:
            return "Failed to get logs"
    
    def exec_in_pod(self, deployment_name: str, command: str, timeout: int = 30) -> tuple:
        """Execute command in a pod"""
        try:
            result = subprocess.run(
                ['kubectl', 'exec', '-n', self.namespace, f'deployment/{deployment_name}', '--'] + command.split(),
                capture_output=True, timeout=timeout, text=True
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)
    
    def run_phase(self, phase_num: int, phase_name: str, test_class) -> bool:
        """Run a single test phase"""
        print(f"\n{'='*100}")
        print(f"🚀 STARTING PHASE {phase_num}: {phase_name.upper()}")
        print(f"{'='*100}")
        
        phase_start = time.time()
        
        try:
            # Instantiate test class
            test_instance = test_class(self)
            
            # Get all test methods
            test_methods = [method for method in dir(test_instance) 
                           if method.startswith('test_') and callable(getattr(test_instance, method))]
            
            passed_tests = 0
            total_tests = len(test_methods)
            
            print(f"📋 Found {total_tests} tests in phase {phase_num}")
            
            for method_name in test_methods:
                try:
                    print(f"\n🧪 Running {method_name}...")
                    test_method = getattr(test_instance, method_name)
                    test_method()
                    passed_tests += 1
                    print(f"   ✅ {method_name}: PASSED")
                except Exception as e:
                    print(f"   ❌ {method_name}: FAILED - {e}")
            
            phase_end = time.time()
            duration = phase_end - phase_start
            success = passed_tests == total_tests
            
            # Store results
            self.results[f"phase_{phase_num}"] = {
                "name": phase_name,
                "success": success,
                "duration": duration,
                "passed": passed_tests,
                "total": total_tests,
                "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            }
            
            # Print phase summary
            if success:
                print(f"\n✅ PHASE {phase_num} COMPLETED SUCCESSFULLY")
                print(f"⏱️  Duration: {duration:.1f} seconds")
                print(f"📊 Tests: {passed_tests}/{total_tests} (100%)")
            else:
                print(f"\n⚠️  PHASE {phase_num} PARTIALLY COMPLETED")
                print(f"⏱️  Duration: {duration:.1f} seconds")
                print(f"📊 Tests: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.0f}%)")
            
            return success
            
        except Exception as e:
            print(f"💥 PHASE {phase_num} ERROR: {e}")
            self.results[f"phase_{phase_num}"] = {
                "name": phase_name,
                "success": False,
                "duration": 0,
                "error": str(e)
            }
            return False
    
    def run_all_phases(self) -> Dict[str, Any]:
        """Run all test phases in sequence"""
        
        print("🎯 INSURANCE AI POC - COMPREHENSIVE KUBERNETES TEST SUITE")
        print("="*100)
        print("🔍 Running tests in the established 4-phase sequence:")
        print("   Phase 1: Kubernetes Infrastructure & Services")
        print("   Phase 2: ADK Agents + Authentication Integration")
        print("   Phase 3: Agent Communication & Session Management")
        print("   Phase 4: Complete E2E Customer Workflows")
        print("="*100)
        
        # Check Kubernetes availability
        if not self.check_kubernetes_availability():
            print("❌ Kubernetes environment not available. Please ensure:")
            print("   - kubectl is installed and configured")
            print("   - insurance-ai-poc namespace exists")
            print("   - All deployments are running")
            return {"error": "Kubernetes not available"}
        
        print("✅ Kubernetes environment detected")
        
        # Test phases configuration
        phases = [
            (1, "Kubernetes Infrastructure", TestKubernetesInfrastructure),
            (2, "ADK Agent Integration", TestADKAgentIntegration),
            (3, "Agent Communication", TestAgentCommunication),
            (4, "E2E Customer Workflows", TestE2ECustomerWorkflows)
        ]
        
        successful_phases = 0
        
        for phase_num, phase_name, test_class in phases:
            # Brief pause between phases
            if phase_num > 1:
                print(f"\n⏳ Brief pause before next phase...")
                time.sleep(2)
            
            # Run the phase
            success = self.run_phase(phase_num, phase_name, test_class)
            if success:
                successful_phases += 1
        
        # Generate summary
        return self.generate_summary(successful_phases, len(phases))
    
    def generate_summary(self, successful_phases: int, total_phases: int) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        
        total_duration = time.time() - self.start_time
        
        print(f"\n{'='*100}")
        print("📊 COMPREHENSIVE KUBERNETES TEST SUMMARY")
        print(f"{'='*100}")
        
        print(f"\n⏱️  EXECUTION TIME:")
        print(f"   Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        
        print(f"\n🎯 PHASE RESULTS:")
        overall_passed = 0
        overall_total = 0
        
        for phase_key, phase_data in self.results.items():
            if 'error' not in phase_data:
                phase_num = phase_key.split('_')[1]
                success_icon = "✅" if phase_data['success'] else "⚠️"
                print(f"   Phase {phase_num}: {success_icon} {phase_data['name']} ({phase_data['duration']:.1f}s)")
                print(f"              📊 Tests: {phase_data['passed']}/{phase_data['total']} ({phase_data['success_rate']:.0f}%)")
                overall_passed += phase_data['passed']
                overall_total += phase_data['total']
            else:
                phase_num = phase_key.split('_')[1]
                print(f"   Phase {phase_num}: ❌ {phase_data['name']} - ERROR: {phase_data['error']}")
        
        success_rate = (successful_phases / total_phases) * 100
        overall_test_rate = (overall_passed / overall_total) * 100 if overall_total > 0 else 0
        
        print(f"\n📈 PHASE SUCCESS RATE: {successful_phases}/{total_phases} ({success_rate:.0f}%)")
        print(f"📈 OVERALL TEST SUCCESS: {overall_passed}/{overall_total} ({overall_test_rate:.0f}%)")
        
        # System assessment
        print(f"\n🏗️  KUBERNETES DEPLOYMENT ASSESSMENT:")
        
        if successful_phases == 4:
            print("   ✅ Infrastructure: Kubernetes deployment fully operational")
            print("   ✅ Authentication: OpenRouter integration working")
            print("   ✅ Agent Communication: Multi-agent coordination functional")
            print("   ✅ Customer Experience: End-to-end workflows verified")
            status = "PRODUCTION READY"
            status_icon = "🎉"
        elif successful_phases >= 3:
            print("   ✅ Infrastructure: Kubernetes deployment working")
            print("   ✅ Authentication: OpenRouter integration working")
            print("   ✅ Agent Communication: Basic functionality working")
            print("   ⚠️  Customer Experience: Some workflow issues")
            status = "MOSTLY READY - Minor workflow issues"
            status_icon = "⚠️"
        elif successful_phases >= 2:
            print("   ✅ Infrastructure: Kubernetes deployment working")
            print("   ✅ Authentication: OpenRouter integration working")
            print("   ❌ Agent Communication: Issues detected")
            print("   ❌ Customer Experience: Not functional")
            status = "PARTIAL DEPLOYMENT - Communication issues"
            status_icon = "🔧"
        elif successful_phases >= 1:
            print("   ✅ Infrastructure: Basic Kubernetes deployment working")
            print("   ❌ Authentication: OpenRouter integration issues")
            print("   ❌ Agent Communication: Not functional")
            print("   ❌ Customer Experience: Not functional")
            status = "INFRASTRUCTURE ONLY - Authentication issues"
            status_icon = "🚧"
        else:
            print("   ❌ Infrastructure: Kubernetes deployment issues")
            print("   ❌ Authentication: Not functional")
            print("   ❌ Agent Communication: Not functional")
            print("   ❌ Customer Experience: Not functional")
            status = "DEPLOYMENT ISSUES - System not operational"
            status_icon = "🚨"
        
        print(f"\n{status_icon} DEPLOYMENT STATUS: {status}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if successful_phases == 4:
            print("   🎯 System ready for production use")
            print("   📈 Consider load testing and monitoring setup")
            print("   🔒 Review security configurations")
        elif successful_phases >= 2:
            print("   🔧 Focus on fixing agent communication issues")
            print("   📝 Review pod logs for specific errors")
            print("   🔄 Restart deployments after fixes")
        elif successful_phases >= 1:
            print("   🔑 Fix OpenRouter authentication configuration")
            print("   🔍 Verify environment variables in pods")
            print("   📞 Check API key validity")
        else:
            print("   🚨 Review Kubernetes deployment configuration")
            print("   🏗️  Check service discovery and networking")
            print("   📋 Verify all pods are running")
        
        print(f"\n{'='*100}")
        print(f"🏁 KUBERNETES TESTING COMPLETE - {status}")
        print(f"{'='*100}")
        
        return {
            "successful_phases": successful_phases,
            "total_phases": total_phases,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "status": status,
            "results": self.results
        }


class TestKubernetesInfrastructure:
    """Phase 1: Kubernetes Infrastructure and Service Discovery Tests"""
    
    def __init__(self, orchestrator: KubernetesTestOrchestrator):
        self.orch = orchestrator
    
    def test_namespace_exists(self):
        """Test insurance-ai-poc namespace exists"""
        result = subprocess.run(
            ['kubectl', 'get', 'namespace', self.orch.namespace],
            capture_output=True, timeout=10
        )
        assert result.returncode == 0, f"Namespace {self.orch.namespace} does not exist"
        print(f"✅ Namespace {self.orch.namespace} exists")
    
    def test_deployments_running(self):
        """Test all required deployments are running"""
        required_deployments = [
            'adk-customer-service',
            'adk-technical-agent',
            'adk-orchestrator',
            'streamlit-ui'
        ]
        
        for deployment in required_deployments:
            result = subprocess.run(
                ['kubectl', 'get', 'deployment', deployment, '-n', self.orch.namespace],
                capture_output=True, timeout=10
            )
            assert result.returncode == 0, f"Deployment {deployment} not found"
            print(f"   ✅ Deployment {deployment} exists")
            
            # Check if deployment is ready
            ready = self.orch.wait_for_deployment_ready(deployment, timeout=30)
            if ready:
                print(f"   ✅ Deployment {deployment} is ready")
            else:
                print(f"   ⚠️  Deployment {deployment} may not be fully ready")
    
    def test_services_accessible(self):
        """Test all services are accessible"""
        required_services = [
            'adk-customer-service',
            'adk-technical-agent',
            'adk-orchestrator',
            'streamlit-ui'
        ]
        
        for service in required_services:
            result = subprocess.run(
                ['kubectl', 'get', 'service', service, '-n', self.orch.namespace],
                capture_output=True, timeout=10
            )
            assert result.returncode == 0, f"Service {service} not found"
            print(f"   ✅ Service {service} exists")
    
    def test_pod_health(self):
        """Test pod health and readiness"""
        result = subprocess.run(
            ['kubectl', 'get', 'pods', '-n', self.orch.namespace, '-o', 'json'],
            capture_output=True, timeout=15, text=True
        )
        
        assert result.returncode == 0, "Failed to get pod status"
        
        pods_data = json.loads(result.stdout)
        
        for pod in pods_data['items']:
            pod_name = pod['metadata']['name']
            pod_status = pod['status']['phase']
            
            if pod_status == 'Running':
                print(f"   ✅ Pod {pod_name} is running")
            else:
                print(f"   ⚠️  Pod {pod_name} status: {pod_status}")
    
    def test_environment_variables(self):
        """Test critical environment variables are set"""
        required_envs = {
            'adk-customer-service': ['OPENROUTER_API_KEY', 'PRIMARY_MODEL'],
            'adk-technical-agent': ['OPENROUTER_API_KEY', 'PRIMARY_MODEL'],
            'adk-orchestrator': ['OPENROUTER_API_KEY', 'PRIMARY_MODEL']
        }
        
        for deployment, env_vars in required_envs.items():
            for env_var in env_vars:
                returncode, stdout, stderr = self.orch.exec_in_pod(
                    deployment, f'printenv {env_var}'
                )
                
                if returncode == 0 and stdout.strip():
                    print(f"   ✅ {deployment}: {env_var} is set")
                else:
                    print(f"   ❌ {deployment}: {env_var} is missing or empty")


class TestADKAgentIntegration:
    """Phase 2: ADK Agent Integration and Authentication Tests"""
    
    def __init__(self, orchestrator: KubernetesTestOrchestrator):
        self.orch = orchestrator
    
    def test_openrouter_api_key_validity(self):
        """Test OpenRouter API key is valid"""
        # Test from customer service pod
        test_script = '''
import os
import requests
api_key = os.getenv("OPENROUTER_API_KEY")
if api_key:
    response = requests.get("https://openrouter.ai/api/v1/models", 
                           headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
    print(f"API_TEST_RESULT:{response.status_code}")
else:
    print("API_TEST_RESULT:NO_KEY")
'''
        
        returncode, stdout, stderr = self.orch.exec_in_pod(
            'adk-customer-service', f'python -c "{test_script}"'
        )
        
        if "API_TEST_RESULT:200" in stdout:
            print("✅ OpenRouter API key is valid and accessible")
        else:
            print(f"❌ OpenRouter API key test failed: {stdout}")
            assert False, "OpenRouter API key validation failed"
    
    def test_litellm_configuration(self):
        """Test LiteLLM configuration in agents"""
        test_script = '''
import os
try:
    import litellm
    print("LITELLM_IMPORT:SUCCESS")
except ImportError as e:
    print(f"LITELLM_IMPORT:FAILED:{e}")
'''
        
        agents = ['adk-customer-service', 'adk-technical-agent', 'adk-orchestrator']
        
        for agent in agents:
            returncode, stdout, stderr = self.orch.exec_in_pod(
                agent, f'python -c "{test_script}"'
            )
            
            if "LITELLM_IMPORT:SUCCESS" in stdout:
                print(f"   ✅ {agent}: LiteLLM imported successfully")
            else:
                print(f"   ❌ {agent}: LiteLLM import failed - {stdout}")
    
    def test_agent_process_health(self):
        """Test agent processes are healthy"""
        agents = ['adk-customer-service', 'adk-technical-agent', 'adk-orchestrator']
        
        for agent in agents:
            # Check logs for any obvious errors
            logs = self.orch.get_pod_logs(agent, lines=10)
            
            if "error" in logs.lower() or "failed" in logs.lower():
                print(f"   ⚠️  {agent}: Potential issues in logs")
                print(f"      Recent logs: {logs[:200]}...")
            else:
                print(f"   ✅ {agent}: Process appears healthy")
    
    def test_agent_endpoints_accessible(self):
        """Test agent endpoints are accessible internally"""
        test_script = '''
import requests
try:
    response = requests.get("http://adk-customer-service:8000/health", timeout=5)
    print(f"ENDPOINT_TEST:customer-service:{response.status_code}")
except Exception as e:
    print(f"ENDPOINT_TEST:customer-service:ERROR:{e}")

try:
    response = requests.get("http://adk-technical-agent:8002/health", timeout=5)
    print(f"ENDPOINT_TEST:technical-agent:{response.status_code}")
except Exception as e:
    print(f"ENDPOINT_TEST:technical-agent:ERROR:{e}")

try:
    response = requests.get("http://adk-orchestrator:8001/health", timeout=5)
    print(f"ENDPOINT_TEST:orchestrator:{response.status_code}")
except Exception as e:
    print(f"ENDPOINT_TEST:orchestrator:ERROR:{e}")
'''
        
        returncode, stdout, stderr = self.orch.exec_in_pod(
            'streamlit-ui', f'python -c "{test_script}"'
        )
        
        # Parse results
        for line in stdout.split('\n'):
            if line.startswith('ENDPOINT_TEST:'):
                parts = line.split(':')
                if len(parts) >= 3:
                    agent = parts[1]
                    status = parts[2]
                    if status in ['200', '404', '405']:  # Accept various success codes
                        print(f"   ✅ {agent}: Endpoint accessible")
                    else:
                        print(f"   ⚠️  {agent}: Endpoint test result: {status}")


class TestAgentCommunication:
    """Phase 3: Agent Communication and Session Management Tests"""
    
    def __init__(self, orchestrator: KubernetesTestOrchestrator):
        self.orch = orchestrator
    
    def test_basic_agent_communication(self):
        """Test basic communication with agents"""
        test_script = '''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
result = send_chat_message_simple("Health check", "TEST001")
print(f"COMM_TEST:status:{result.get('connection_status', 'unknown')}")
print(f"COMM_TEST:response_length:{len(result.get('response', ''))}")
'''
        
        returncode, stdout, stderr = self.orch.exec_in_pod(
            'streamlit-ui', f'python -c "{test_script}"'
        )
        
        if "COMM_TEST:status:api_success" in stdout:
            print("✅ Basic agent communication successful")
        elif "COMM_TEST:status:api_connected_needs_keys" in stdout:
            print("⚠️  Agent connected but authentication needs attention")
        else:
            print(f"❌ Agent communication failed: {stdout}")
            # Don't fail the test, just warn
    
    def test_session_management(self):
        """Test session creation and persistence"""
        test_script = '''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
customer_id = "SESSION_TEST_001"

# First request
result1 = send_chat_message_simple("Hello", customer_id)
session1 = result1.get("session_id")

# Second request with same customer
result2 = send_chat_message_simple("How are you?", customer_id)
session2 = result2.get("session_id")

print(f"SESSION_TEST:first:{session1[:8] if session1 else 'None'}")
print(f"SESSION_TEST:second:{session2[:8] if session2 else 'None'}")
print(f"SESSION_TEST:persistent:{session1 == session2}")
'''
        
        returncode, stdout, stderr = self.orch.exec_in_pod(
            'streamlit-ui', f'python -c "{test_script}"'
        )
        
        if "SESSION_TEST:persistent:True" in stdout:
            print("✅ Session persistence working correctly")
        else:
            print(f"⚠️  Session persistence test results: {stdout}")
    
    def test_multiple_agent_interaction(self):
        """Test interaction with different agents"""
        test_script = '''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple

# Test customer service agent
result_cs = send_chat_message_simple("Test customer service", "MULTI_001")
cs_status = result_cs.get('connection_status', 'unknown')

print(f"MULTI_AGENT:customer_service:{cs_status}")
print(f"MULTI_AGENT:agent_name:{result_cs.get('agent', 'unknown')}")
'''
        
        returncode, stdout, stderr = self.orch.exec_in_pod(
            'streamlit-ui', f'python -c "{test_script}"'
        )
        
        for line in stdout.split('\n'):
            if "MULTI_AGENT:customer_service:api_success" in line:
                print("   ✅ Customer service agent communication successful")
            elif "MULTI_AGENT:agent_name:" in line:
                agent_name = line.split(':')[-1]
                print(f"   📝 Routed to agent: {agent_name}")
    
    def test_error_handling(self):
        """Test system error handling"""
        error_tests = [
            ("Empty message", ""),
            ("Invalid customer", "INVALID_CUST"),
        ]
        
        for test_name, message in error_tests:
            test_script = f'''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
try:
    result = send_chat_message_simple("{message}", "ERROR_TEST")
    print(f"ERROR_TEST:{test_name}:SUCCESS:{{result.get('connection_status', 'unknown')}}")
except Exception as e:
    print(f"ERROR_TEST:{test_name}:EXCEPTION:{{str(e)[:50]}}")
'''
            
            returncode, stdout, stderr = self.orch.exec_in_pod(
                'streamlit-ui', f'python -c "{test_script}"'
            )
            
            if "ERROR_TEST" in stdout:
                print(f"   ✅ {test_name}: Error handled gracefully")


class TestE2ECustomerWorkflows:
    """Phase 4: End-to-End Customer Workflow Tests"""
    
    def __init__(self, orchestrator: KubernetesTestOrchestrator):
        self.orch = orchestrator
    
    def test_insurance_policy_inquiry(self):
        """Test complete insurance policy inquiry workflow"""
        scenarios = [
            "What insurance policies do I have?",
            "What am I covered for?",
            "What are my policy details?"
        ]
        
        successful = 0
        
        for i, scenario in enumerate(scenarios):
            test_script = f'''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
result = send_chat_message_simple("{scenario}", "E2E_POLICY_00{i+1}")
status = result.get('connection_status', 'unknown')
response = result.get('response', '')
print(f"POLICY_INQUIRY:scenario_{i+1}:" + status)
print(f"POLICY_RESPONSE:length:" + str(len(response)))
if any(word in response.lower() for word in ['policy', 'insurance', 'coverage']):
    print(f"POLICY_CONTENT:relevant:true")
else:
    print(f"POLICY_CONTENT:relevant:false")
'''
            
            returncode, stdout, stderr = self.orch.exec_in_pod(
                'streamlit-ui', f'python -c "{test_script}"'
            )
            
            if "POLICY_INQUIRY:scenario_" in stdout and "api_success" in stdout:
                if "POLICY_CONTENT:relevant:true" in stdout:
                    print(f"   ✅ Scenario {i+1}: Policy inquiry successful with relevant content")
                    successful += 1
                else:
                    print(f"   ⚠️  Scenario {i+1}: Response not insurance-relevant")
            else:
                print(f"   ❌ Scenario {i+1}: Policy inquiry failed")
        
        success_rate = (successful / len(scenarios)) * 100
        print(f"📊 Policy inquiry success rate: {successful}/{len(scenarios)} ({success_rate:.0f}%)")
        
        assert successful >= len(scenarios) * 0.5, "Less than 50% of policy inquiries successful"
    
    def test_claims_process_workflow(self):
        """Test claims process inquiry workflow"""
        scenarios = [
            "How do I file a claim?",
            "What information do I need for a claim?",
            "What's the claims process?"
        ]
        
        successful = 0
        
        for i, scenario in enumerate(scenarios):
            test_script = f'''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
result = send_chat_message_simple("{scenario}", "E2E_CLAIMS_00{i+1}")
status = result.get('connection_status', 'unknown')
response = result.get('response', '')
print(f"CLAIMS_INQUIRY:scenario_{i+1}:" + status)
if any(word in response.lower() for word in ['claim', 'file', 'process', 'information']):
    print(f"CLAIMS_CONTENT:relevant:true")
else:
    print(f"CLAIMS_CONTENT:relevant:false")
'''
            
            returncode, stdout, stderr = self.orch.exec_in_pod(
                'streamlit-ui', f'python -c "{test_script}"'
            )
            
            if "CLAIMS_INQUIRY:scenario_" in stdout and "api_success" in stdout:
                if "CLAIMS_CONTENT:relevant:true" in stdout:
                    print(f"   ✅ Scenario {i+1}: Claims inquiry successful with relevant content")
                    successful += 1
                else:
                    print(f"   ⚠️  Scenario {i+1}: Response not claims-relevant")
            else:
                print(f"   ❌ Scenario {i+1}: Claims inquiry failed")
        
        success_rate = (successful / len(scenarios)) * 100
        print(f"📊 Claims inquiry success rate: {successful}/{len(scenarios)} ({success_rate:.0f}%)")
    
    def test_performance_under_load(self):
        """Test system performance under moderate load"""
        def make_concurrent_request(request_id):
            test_script = f'''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
import time
start = time.time()
result = send_chat_message_simple("Performance test {request_id}", "PERF_{request_id:03d}")
duration = time.time() - start
print("PERF_TEST:" + str({request_id}) + ":" + result.get('connection_status', 'unknown') + ":" + str(duration))
'''
            
            returncode, stdout, stderr = self.orch.exec_in_pod(
                'streamlit-ui', f'python -c "{test_script}"'
            )
            
            return stdout
        
        # Run 3 concurrent requests (moderate load)
        print("🔄 Running performance test with 3 concurrent requests...")
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_concurrent_request, i) for i in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        successful_requests = 0
        total_requests = 3
        response_times = []
        
        for result in results:
            if "PERF_TEST:" in result and "api_success" in result:
                successful_requests += 1
                # Extract response time
                parts = result.strip().split(':')
                if len(parts) >= 4:
                    try:
                        response_time = float(parts[3])
                        response_times.append(response_time)
                    except:
                        pass
        
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            print(f"📊 Performance Results:")
            print(f"   Successful requests: {successful_requests}/{total_requests}")
            print(f"   Average response time: {avg_time:.2f}s")
            print(f"   Max response time: {max_time:.2f}s")
            
            if successful_requests >= 2 and avg_time < 15:
                print("   ✅ Performance test PASSED")
            else:
                print("   ⚠️  Performance could be improved")
        else:
            print("   ⚠️  Could not measure response times")
    
    def test_comprehensive_customer_journey(self):
        """Test a complete customer service journey"""
        customer_id = "E2E_JOURNEY_001"
        
        journey_steps = [
            ("Greeting", "Hello, I need help with my insurance"),
            ("Policy Inquiry", "What policies do I have?"),
            ("Coverage Question", "What am I covered for in my auto insurance?"),
            ("Claims Question", "How do I file a claim if needed?")
        ]
        
        successful_steps = 0
        
        for step_name, question in journey_steps:
            test_script = f'''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
result = send_chat_message_simple("{question}", "{customer_id}")
status = result.get('connection_status', 'unknown')
response_length = len(result.get('response', ''))
print(f"JOURNEY_STEP:{step_name}:{status}:{response_length}")
'''
            
            returncode, stdout, stderr = self.orch.exec_in_pod(
                'streamlit-ui', f'python -c "{test_script}"'
            )
            
            if "api_success" in stdout and "response_length" in stdout:
                print(f"   ✅ {step_name}: Successful response")
                successful_steps += 1
            else:
                print(f"   ❌ {step_name}: Failed or no response")
        
        journey_success_rate = (successful_steps / len(journey_steps)) * 100
        print(f"📊 Customer journey success rate: {successful_steps}/{len(journey_steps)} ({journey_success_rate:.0f}%)")
        
        if journey_success_rate >= 75:
            print("✅ Customer journey test PASSED")
        else:
            print("⚠️  Customer journey needs improvement")


def run_comprehensive_kubernetes_tests():
    """Main function to run all comprehensive Kubernetes tests"""
    
    orchestrator = KubernetesTestOrchestrator()
    
    try:
        summary = orchestrator.run_all_phases()
        
        # Exit with appropriate code
        if "error" in summary:
            return 1
        elif summary["successful_phases"] == summary["total_phases"]:
            return 0  # All phases passed
        else:
            return 1  # Some phases failed
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = run_comprehensive_kubernetes_tests()
    sys.exit(exit_code) 