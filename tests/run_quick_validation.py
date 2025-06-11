#!/usr/bin/env python3
"""
Quick Validation Script for Insurance AI POC
Focuses on core functionality and provides rapid feedback
"""

import subprocess
import time
import json
import sys

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_result(test_name, success, details=""):
    """Print test result"""
    icon = "✅" if success else "❌"
    print(f"{icon} {test_name}")
    if details:
        print(f"    {details}")

def check_kubernetes_environment():
    """Check if Kubernetes environment is ready"""
    print_header("KUBERNETES ENVIRONMENT CHECK")
    
    try:
        # Check namespace
        result = subprocess.run(
            ['kubectl', 'get', 'namespace', 'insurance-ai-poc'],
            capture_output=True, timeout=10
        )
        print_result("Namespace exists", result.returncode == 0)
        
        # Check deployments
        deployments = ['adk-customer-service', 'adk-technical-agent', 'adk-orchestrator', 'streamlit-ui']
        deployment_ready = 0
        
        for deployment in deployments:
            result = subprocess.run(
                ['kubectl', 'get', 'deployment', deployment, '-n', 'insurance-ai-poc'],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                deployment_ready += 1
                print_result(f"Deployment {deployment}", True)
            else:
                print_result(f"Deployment {deployment}", False)
        
        print(f"\n📊 Deployments Ready: {deployment_ready}/{len(deployments)}")
        return deployment_ready == len(deployments)
        
    except Exception as e:
        print_result("Kubernetes check", False, str(e))
        return False

def check_api_connectivity():
    """Check API connectivity and authentication"""
    print_header("API CONNECTIVITY CHECK")
    
    try:
        # Test basic agent communication
        test_script = '''
import sys
sys.path.append("/app/ui")
try:
    from components.agent_client import send_chat_message_simple
    result = send_chat_message_simple("Hello", "VALIDATION_001")
    status = result.get("connection_status", "unknown")
    response_length = len(result.get("response", ""))
    print(f"STATUS:{status}")
    print(f"RESPONSE_LENGTH:{response_length}")
except Exception as e:
    print(f"ERROR:{str(e)[:100]}")
'''
        
        result = subprocess.run(
            ['kubectl', 'exec', '-n', 'insurance-ai-poc', 'deployment/streamlit-ui', '--',
             'python', '-c', test_script],
            capture_output=True, timeout=30, text=True
        )
        
        if result.returncode == 0:
            output = result.stdout
            if "STATUS:api_success" in output:
                print_result("Agent Communication", True, "API calls successful")
                if "RESPONSE_LENGTH:" in output:
                    length = output.split("RESPONSE_LENGTH:")[1].split()[0]
                    print_result("Response Quality", int(length) > 10, f"Response length: {length} chars")
                return True
            elif "STATUS:api_connected_needs_keys" in output:
                print_result("Agent Communication", False, "Connected but authentication issue")
                return False
            else:
                print_result("Agent Communication", False, f"Unexpected status: {output}")
                return False
        else:
            print_result("Agent Communication", False, f"Execution failed: {result.stderr}")
            return False
            
    except Exception as e:
        print_result("API connectivity check", False, str(e))
        return False

def check_environment_variables():
    """Check critical environment variables"""
    print_header("ENVIRONMENT VARIABLES CHECK")
    
    agents = ['adk-customer-service', 'adk-technical-agent', 'adk-orchestrator']
    env_vars = ['OPENROUTER_API_KEY', 'PRIMARY_MODEL']
    
    all_good = True
    
    for agent in agents:
        agent_good = True
        for env_var in env_vars:
            try:
                result = subprocess.run(
                    ['kubectl', 'exec', '-n', 'insurance-ai-poc', f'deployment/{agent}', '--',
                     'printenv', env_var],
                    capture_output=True, timeout=5, text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    print_result(f"{agent}: {env_var}", True)
                else:
                    print_result(f"{agent}: {env_var}", False, "Missing or empty")
                    agent_good = False
                    all_good = False
            except Exception as e:
                print_result(f"{agent}: {env_var}", False, str(e))
                agent_good = False
                all_good = False
        
        print(f"    📝 {agent}: {'✅ All vars set' if agent_good else '❌ Missing vars'}")
    
    return all_good

def test_basic_scenarios():
    """Test basic customer scenarios"""
    print_header("BASIC CUSTOMER SCENARIOS")
    
    scenarios = [
        ("Greeting", "Hello"),
        ("Policy Question", "What policies do I have?"),
        ("Simple Help", "Can you help me?")
    ]
    
    successful = 0
    
    for scenario_name, message in scenarios:
        try:
            test_script = f'''
import sys
sys.path.append("/app/ui")
from components.agent_client import send_chat_message_simple
result = send_chat_message_simple("{message}", "SCENARIO_TEST")
status = result.get("connection_status", "unknown")
response = result.get("response", "")
print("STATUS:" + status)
print("LENGTH:" + str(len(response)))
'''
            
            result = subprocess.run(
                ['kubectl', 'exec', '-n', 'insurance-ai-poc', 'deployment/streamlit-ui', '--',
                 'python', '-c', test_script],
                capture_output=True, timeout=30, text=True
            )
            
            if result.returncode == 0 and "STATUS:api_success" in result.stdout:
                print_result(scenario_name, True)
                successful += 1
            else:
                print_result(scenario_name, False)
                
        except Exception as e:
            print_result(scenario_name, False, str(e))
    
    success_rate = (successful / len(scenarios)) * 100
    print(f"\n📊 Scenario Success Rate: {successful}/{len(scenarios)} ({success_rate:.0f}%)")
    
    return success_rate >= 60  # 60% threshold

def run_quick_validation():
    """Run quick validation of the system"""
    
    print("🎯 INSURANCE AI POC - QUICK VALIDATION")
    print("="*60)
    print("🔍 Running essential system checks...")
    
    start_time = time.time()
    
    # Run checks
    checks = [
        ("Kubernetes Environment", check_kubernetes_environment),
        ("Environment Variables", check_environment_variables),
        ("API Connectivity", check_api_connectivity),
        ("Basic Scenarios", test_basic_scenarios)
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_function in checks:
        try:
            success = check_function()
            if success:
                passed_checks += 1
        except Exception as e:
            print_result(check_name, False, f"Exception: {e}")
    
    # Summary
    duration = time.time() - start_time
    success_rate = (passed_checks / total_checks) * 100
    
    print_header("VALIDATION SUMMARY")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📊 Checks Passed: {passed_checks}/{total_checks} ({success_rate:.0f}%)")
    
    if success_rate >= 75:
        status = "✅ SYSTEM OPERATIONAL"
        print(f"\n🎉 {status}")
        print("✅ Core functionality verified")
        print("✅ Ready for user testing")
        return 0
    elif success_rate >= 50:
        status = "⚠️  SYSTEM PARTIALLY OPERATIONAL"
        print(f"\n⚠️  {status}")
        print("🔧 Some issues detected but core features working")
        print("📝 Review detailed test results for specific issues")
        return 1
    else:
        status = "❌ SYSTEM ISSUES DETECTED"
        print(f"\n🚨 {status}")
        print("🔧 Significant issues require attention")
        print("📞 Review deployment and configuration")
        return 2

if __name__ == "__main__":
    exit_code = run_quick_validation()
    sys.exit(exit_code) 