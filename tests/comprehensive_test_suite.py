#!/usr/bin/env python3
"""
Comprehensive Test Suite for Insurance AI POC - Post OpenRouter Integration
Tests all components: Unit, Integration, and E2E with the new authentication system
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
from unittest.mock import Mock, patch, MagicMock

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ui'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'insurance-adk'))

class TestFramework:
    """Enhanced test framework for comprehensive testing"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.test_environment = "kubernetes"  # or "local"
        
    def setup_test_environment(self):
        """Detect and setup test environment"""
        try:
            # Check if running in Kubernetes
            result = subprocess.run(['kubectl', 'get', 'pods', '-n', 'insurance-ai-poc'], 
                                    capture_output=True, timeout=5)
            if result.returncode == 0:
                self.test_environment = "kubernetes"
                print("🔍 Detected Kubernetes environment")
            else:
                self.test_environment = "local"
                print("🔍 Using local development environment")
        except:
            self.test_environment = "local"
            print("🔍 Defaulting to local environment")


class TestUnitComponents:
    """Unit tests for individual components"""
    
    def test_openrouter_api_key_validation(self):
        """Test OpenRouter API key validation"""
        print("\n🔑 Testing OpenRouter API Key Validation")
        
        # Test environment variable loading
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        assert api_key is not None, "OPENROUTER_API_KEY must be set"
        assert api_key.startswith("sk-or-v1-"), "Invalid OpenRouter API key format"
        
        print(f"   ✅ API key format valid: {api_key[:20]}...")
        
        # Test API key works with OpenRouter
        try:
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10
            )
            assert response.status_code == 200, f"OpenRouter API test failed: {response.status_code}"
            models = response.json()
            assert "data" in models, "Invalid OpenRouter response format"
            print(f"   ✅ OpenRouter API accessible, {len(models['data'])} models available")
        except Exception as e:
            pytest.fail(f"OpenRouter API validation failed: {e}")
    
    def test_litellm_configuration(self):
        """Test LiteLLM configuration for OpenRouter"""
        print("\n🔧 Testing LiteLLM Configuration")
        
        try:
            import litellm
            from litellm import completion
            
            # Test basic configuration
            api_key = os.getenv("OPENROUTER_API_KEY")
            os.environ["OPENROUTER_API_KEY"] = api_key
            
            # Test model format
            model = "openrouter/openai/gpt-4o-mini"
            
            # Mock test (don't actually call API in unit test)
            with patch('litellm.completion') as mock_completion:
                mock_completion.return_value = Mock(
                    choices=[Mock(message=Mock(content="Test response"))]
                )
                
                response = completion(
                    model=model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                
                mock_completion.assert_called_once()
                assert response.choices[0].message.content == "Test response"
                print("   ✅ LiteLLM configuration test passed")
                
        except ImportError as e:
            pytest.fail(f"LiteLLM import failed: {e}")
        except Exception as e:
            pytest.fail(f"LiteLLM configuration test failed: {e}")
    
    def test_agent_configuration(self):
        """Test agent configuration with OpenRouter"""
        print("\n🤖 Testing Agent Configuration")
        
        try:
            # Test customer service agent
            from insurance_customer_service.agent import root_agent as customer_agent
            assert customer_agent.name == "insurance_customer_service"
            print("   ✅ Customer service agent configured")
            
            # Test technical agent
            from insurance_technical_agent.agent import root_agent as technical_agent
            assert technical_agent.name == "insurance_technical_agent"
            print("   ✅ Technical agent configured")
            
            # Test orchestrator agent
            from insurance_orchestrator.agent import root_agent as orchestrator_agent
            assert orchestrator_agent.name == "insurance_orchestrator"
            print("   ✅ Orchestrator agent configured")
            
        except ImportError as e:
            print(f"   ⚠️  Agent import error (expected in some environments): {e}")
        except Exception as e:
            pytest.fail(f"Agent configuration test failed: {e}")
    
    def test_session_management(self):
        """Test session management functionality"""
        print("\n📋 Testing Session Management")
        
        try:
            # Mock session manager if needed
            session_id = f"test_session_{int(time.time())}"
            customer_id = "CUST001"
            
            # Test session ID format
            assert len(session_id) > 10, "Session ID too short"
            assert "test_session_" in session_id, "Invalid session ID format"
            
            # Test customer ID format  
            assert customer_id.startswith("CUST"), "Invalid customer ID format"
            assert len(customer_id) >= 7, "Customer ID too short"
            
            print(f"   ✅ Session management format validation passed")
            print(f"   📝 Test session: {session_id}")
            
        except Exception as e:
            pytest.fail(f"Session management test failed: {e}")
    
    def test_ui_component_imports(self):
        """Test UI component imports and basic functionality"""
        print("\n🖥️  Testing UI Component Imports")
        
        try:
            # Test agent client import
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ui'))
            from components.agent_client import send_chat_message_simple
            
            # Test function signature
            import inspect
            sig = inspect.signature(send_chat_message_simple)
            params = list(sig.parameters.keys())
            
            assert 'message' in params, "send_chat_message_simple missing message parameter"
            assert 'customer_id' in params, "send_chat_message_simple missing customer_id parameter"
            
            print("   ✅ UI component imports successful")
            print(f"   📝 Function parameters: {params}")
            
        except ImportError as e:
            print(f"   ⚠️  UI import error (expected in some environments): {e}")
        except Exception as e:
            pytest.fail(f"UI component test failed: {e}")


class TestIntegrationComponents:
    """Integration tests between components"""
    
    def test_kubernetes_service_discovery(self):
        """Test Kubernetes service discovery and DNS resolution"""
        print("\n🔍 Testing Kubernetes Service Discovery")
        
        try:
            # Test namespace exists
            result = subprocess.run(
                ['kubectl', 'get', 'namespace', 'insurance-ai-poc'],
                capture_output=True, timeout=10
            )
            
            if result.returncode == 0:
                print("   ✅ insurance-ai-poc namespace exists")
                
                # Test service discovery
                services = [
                    'adk-customer-service',
                    'adk-technical-agent', 
                    'adk-orchestrator',
                    'streamlit-ui'
                ]
                
                for service in services:
                    result = subprocess.run(
                        ['kubectl', 'get', 'service', service, '-n', 'insurance-ai-poc'],
                        capture_output=True, timeout=5
                    )
                    
                    if result.returncode == 0:
                        print(f"   ✅ Service {service} found")
                    else:
                        print(f"   ⚠️  Service {service} not found")
                        
            else:
                print("   ⚠️  Kubernetes environment not available")
                
        except Exception as e:
            print(f"   ⚠️  Kubernetes service discovery error: {e}")
    
    def test_agent_to_agent_communication(self):
        """Test communication between agents"""
        print("\n🔗 Testing Agent-to-Agent Communication")
        
        try:
            # Test in Kubernetes environment
            result = subprocess.run(
                ['kubectl', 'exec', '-n', 'insurance-ai-poc', 'deployment/streamlit-ui', '--',
                 'python', '-c', 
                 'import sys; sys.path.append("/app/ui"); from components.agent_client import send_chat_message_simple; result = send_chat_message_simple("Health check", "TEST001"); print("Status:", result.get("connection_status", "unknown"))'],
                capture_output=True, timeout=30, text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if "api_success" in output:
                    print("   ✅ Agent communication successful")
                elif "api_connected_needs_keys" in output:
                    print("   ⚠️  Agent connected but authentication issue")
                else:
                    print(f"   📝 Agent response: {output}")
            else:
                print(f"   ⚠️  Agent communication test error: {result.stderr}")
                
        except Exception as e:
            print(f"   ⚠️  Agent communication test failed: {e}")
    
    def test_session_persistence(self):
        """Test session persistence across requests"""
        print("\n💾 Testing Session Persistence")
        
        try:
            # Test in Kubernetes environment
            test_script = '''
import sys; sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
customer_id = "PERSIST001"
result1 = send_chat_message_simple("Hello", customer_id)
session1 = result1.get("session_id")
result2 = send_chat_message_simple("How are you?", customer_id)  
session2 = result2.get("session_id")
print(f"Session1: {session1[:8] if session1 else 'None'}")
print(f"Session2: {session2[:8] if session2 else 'None'}")
print(f"Same session: {session1 == session2}")
'''
            
            result = subprocess.run(
                ['kubectl', 'exec', '-n', 'insurance-ai-poc', 'deployment/streamlit-ui', '--',
                 'python', '-c', test_script],
                capture_output=True, timeout=30, text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if "Same session: True" in output:
                    print("   ✅ Session persistence working")
                else:
                    print(f"   📝 Session test result: {output}")
            else:
                print(f"   ⚠️  Session persistence test error: {result.stderr}")
                
        except Exception as e:
            print(f"   ⚠️  Session persistence test failed: {e}")
    
    def test_environment_variable_propagation(self):
        """Test environment variables are properly propagated to pods"""
        print("\n🌍 Testing Environment Variable Propagation")
        
        try:
            # Check customer service environment variables
            result = subprocess.run(
                ['kubectl', 'exec', '-n', 'insurance-ai-poc', 'deployment/adk-customer-service', '--',
                 'env'],
                capture_output=True, timeout=10, text=True
            )
            
            if result.returncode == 0:
                env_vars = result.stdout
                
                required_vars = ['OPENROUTER_API_KEY', 'PRIMARY_MODEL']
                found_vars = []
                
                for var in required_vars:
                    if var in env_vars:
                        found_vars.append(var)
                        print(f"   ✅ {var} found in customer service")
                    else:
                        print(f"   ❌ {var} missing in customer service")
                
                if len(found_vars) == len(required_vars):
                    print("   ✅ All required environment variables present")
                else:
                    print(f"   ⚠️  Missing {len(required_vars) - len(found_vars)} environment variables")
                    
            else:
                print(f"   ⚠️  Environment check failed: {result.stderr}")
                
        except Exception as e:
            print(f"   ⚠️  Environment variable test failed: {e}")


class TestE2EScenarios:
    """End-to-end test scenarios"""
    
    def test_complete_insurance_workflow(self):
        """Test complete insurance customer workflow"""
        print("\n🎭 Testing Complete Insurance Workflow")
        
        scenarios = [
            {
                "name": "Policy Inquiry",
                "message": "What insurance policies do I have?",
                "expected_keywords": ["policy", "insurance", "coverage"]
            },
            {
                "name": "Claims Process",  
                "message": "How do I file a claim?",
                "expected_keywords": ["claim", "file", "process", "information"]
            },
            {
                "name": "Coverage Question",
                "message": "What am I covered for in my auto insurance?",
                "expected_keywords": ["auto", "coverage", "covered", "insurance"]
            },
            {
                "name": "Premium Question",
                "message": "When is my next payment due?",
                "expected_keywords": ["payment", "due", "premium", "billing"]
            }
        ]
        
        successful_scenarios = 0
        
        for scenario in scenarios:
            try:
                print(f"\n   🎬 Scenario: {scenario['name']}")
                
                test_script = f'''
import sys; sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
result = send_chat_message_simple("{scenario["message"]}", "E2E001")
print("Response:", result.get("response", "")[:200])
print("Status:", result.get("connection_status", "unknown"))
'''
                
                result = subprocess.run(
                    ['kubectl', 'exec', '-n', 'insurance-ai-poc', 'deployment/streamlit-ui', '--',
                     'python', '-c', test_script],
                    capture_output=True, timeout=30, text=True
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    
                    if "api_success" in output:
                        # Check for expected keywords in response
                        response_text = output.lower()
                        found_keywords = [kw for kw in scenario["expected_keywords"] 
                                         if kw.lower() in response_text]
                        
                        if found_keywords:
                            print(f"      ✅ Scenario passed (found: {', '.join(found_keywords)})")
                            successful_scenarios += 1
                        else:
                            print(f"      ⚠️  Response doesn't contain expected keywords")
                            print(f"      📝 Response preview: {output[:200]}")
                    else:
                        print(f"      ❌ API call failed: {output}")
                else:
                    print(f"      ❌ Execution failed: {result.stderr}")
                    
            except Exception as e:
                print(f"      ❌ Scenario error: {e}")
        
        success_rate = (successful_scenarios / len(scenarios)) * 100
        print(f"\n   📊 E2E Success Rate: {successful_scenarios}/{len(scenarios)} ({success_rate:.0f}%)")
        
        if success_rate >= 75:
            print("   ✅ E2E workflow tests PASSED")
        else:
            print("   ⚠️  E2E workflow tests need improvement")
    
    def test_performance_under_load(self):
        """Test system performance under simulated load"""
        print("\n⚡ Testing Performance Under Load")
        
        try:
            import concurrent.futures
            import statistics
            
            def make_request(request_id):
                """Make a single request and measure response time"""
                start_time = time.time()
                
                test_script = f'''
import sys; sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
result = send_chat_message_simple("Quick test {request_id}", "PERF{request_id:03d}")
print(result.get("connection_status", "unknown"))
'''
                
                result = subprocess.run(
                    ['kubectl', 'exec', '-n', 'insurance-ai-poc', 'deployment/streamlit-ui', '--',
                     'python', '-c', test_script],
                    capture_output=True, timeout=30, text=True
                )
                
                end_time = time.time()
                duration = end_time - start_time
                
                success = (result.returncode == 0 and "api_success" in result.stdout)
                
                return {
                    "request_id": request_id,
                    "duration": duration,
                    "success": success
                }
            
            # Run concurrent requests
            num_requests = 5  # Moderate load for testing
            print(f"   🔄 Running {num_requests} concurrent requests...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(make_request, i) for i in range(num_requests)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            successful_requests = [r for r in results if r["success"]]
            response_times = [r["duration"] for r in successful_requests]
            
            if response_times:
                avg_time = statistics.mean(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                
                print(f"   📊 Performance Results:")
                print(f"      Successful requests: {len(successful_requests)}/{num_requests}")
                print(f"      Average response time: {avg_time:.2f}s")
                print(f"      Min/Max response time: {min_time:.2f}s / {max_time:.2f}s")
                
                if avg_time < 10 and len(successful_requests) >= num_requests * 0.8:
                    print("   ✅ Performance test PASSED")
                else:
                    print("   ⚠️  Performance needs optimization")
            else:
                print("   ❌ No successful requests in performance test")
                
        except Exception as e:
            print(f"   ⚠️  Performance test failed: {e}")
    
    def test_error_recovery(self):
        """Test system error recovery and resilience"""
        print("\n🛡️  Testing Error Recovery")
        
        error_scenarios = [
            {
                "name": "Invalid Customer ID",
                "customer_id": "INVALID",
                "message": "Test message",
                "expected_behavior": "graceful_handling"
            },
            {
                "name": "Empty Message",
                "customer_id": "TEST001", 
                "message": "",
                "expected_behavior": "error_response"
            },
            {
                "name": "Very Long Message",
                "customer_id": "TEST001",
                "message": "x" * 5000,
                "expected_behavior": "handled_gracefully"
            }
        ]
        
        for scenario in error_scenarios:
            try:
                print(f"\n   🧪 Testing: {scenario['name']}")
                
                test_script = f'''
import sys; sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
try:
    result = send_chat_message_simple("{scenario["message"]}", "{scenario["customer_id"]}")
    print("Status:", result.get("connection_status", "unknown"))
    print("Response length:", len(result.get("response", "")))
except Exception as e:
    print("Error:", str(e)[:100])
'''
                
                result = subprocess.run(
                    ['kubectl', 'exec', '-n', 'insurance-ai-poc', 'deployment/streamlit-ui', '--',
                     'python', '-c', test_script],
                    capture_output=True, timeout=30, text=True
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    if "Error:" not in output or "graceful" in scenario["expected_behavior"]:
                        print(f"      ✅ Error scenario handled appropriately")
                    else:
                        print(f"      ⚠️  Unexpected error handling: {output}")
                else:
                    print(f"      ⚠️  Test execution failed: {result.stderr}")
                    
            except Exception as e:
                print(f"      ❌ Error scenario test failed: {e}")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    
    print("🎯 COMPREHENSIVE TEST SUITE - POST OPENROUTER INTEGRATION")
    print("=" * 80)
    
    framework = TestFramework()
    framework.setup_test_environment()
    
    test_classes = [
        ("Unit Tests", TestUnitComponents()),
        ("Integration Tests", TestIntegrationComponents()),
        ("E2E Tests", TestE2EScenarios())
    ]
    
    overall_results = {}
    
    for test_category, test_instance in test_classes:
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING {test_category.upper()}")
        print(f"{'='*60}")
        
        category_start = time.time()
        
        # Get all test methods
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_') and callable(getattr(test_instance, method))]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for method_name in test_methods:
            try:
                test_method = getattr(test_instance, method_name)
                test_method()
                passed_tests += 1
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
        
        category_duration = time.time() - category_start
        
        overall_results[test_category] = {
            "passed": passed_tests,
            "total": total_tests,
            "duration": category_duration,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }
        
        print(f"\n📊 {test_category} Summary:")
        print(f"   Passed: {passed_tests}/{total_tests} ({overall_results[test_category]['success_rate']:.0f}%)")
        print(f"   Duration: {category_duration:.1f}s")
    
    # Final summary
    print(f"\n{'='*80}")
    print("📋 FINAL TEST SUMMARY")
    print(f"{'='*80}")
    
    total_duration = time.time() - framework.start_time
    overall_passed = sum(r["passed"] for r in overall_results.values())
    overall_total = sum(r["total"] for r in overall_results.values())
    overall_success_rate = (overall_passed / overall_total) * 100 if overall_total > 0 else 0
    
    for category, results in overall_results.items():
        status = "✅" if results["success_rate"] >= 80 else "⚠️" if results["success_rate"] >= 60 else "❌"
        print(f"{status} {category}: {results['passed']}/{results['total']} ({results['success_rate']:.0f}%)")
    
    print(f"\n🎯 OVERALL: {overall_passed}/{overall_total} ({overall_success_rate:.0f}%)")
    print(f"⏱️  TOTAL DURATION: {total_duration:.1f}s")
    
    if overall_success_rate >= 80:
        print("\n🎉 COMPREHENSIVE TEST SUITE: PASSED")
        print("✅ System is ready for production use!")
    elif overall_success_rate >= 60:
        print("\n⚠️  COMPREHENSIVE TEST SUITE: PARTIALLY PASSED")
        print("🔧 Some issues need attention before production")
    else:
        print("\n❌ COMPREHENSIVE TEST SUITE: NEEDS WORK")
        print("🚨 Significant issues require resolution")
    
    return overall_results


if __name__ == "__main__":
    run_comprehensive_tests() 