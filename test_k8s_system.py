#!/usr/bin/env python3
"""
Test Kubernetes System End-to-End
Tests the deployed system through the Streamlit UI
"""

import requests
import json
import time

def test_streamlit_ui():
    """Test that Streamlit UI is accessible"""
    print("🧪 Testing Streamlit UI accessibility...")
    
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit UI is accessible on http://localhost:8501")
            return True
        else:
            print(f"❌ Streamlit UI returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to Streamlit UI: {e}")
        return False

def test_kubernetes_pods():
    """Test that all Kubernetes pods are running"""
    print("\n🧪 Testing Kubernetes pod status...")
    
    import subprocess
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "insurance-ai-poc", "-o", "json"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            pods_data = json.loads(result.stdout)
            pods = pods_data.get("items", [])
            
            all_ready = True
            for pod in pods:
                name = pod["metadata"]["name"]
                status = pod["status"]
                
                # Check if pod is ready
                conditions = status.get("conditions", [])
                ready_condition = next((c for c in conditions if c["type"] == "Ready"), None)
                
                if ready_condition and ready_condition["status"] == "True":
                    print(f"✅ Pod {name}: Ready")
                else:
                    print(f"❌ Pod {name}: Not Ready")
                    all_ready = False
            
            return all_ready
        else:
            print(f"❌ Failed to get pod status: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking pods: {e}")
        return False

def test_service_connectivity():
    """Test inter-service connectivity within Kubernetes"""
    print("\n🧪 Testing inter-service connectivity...")
    
    import subprocess
    tests = [
        {
            "name": "Domain Agent → Technical Agent",
            "command": ["kubectl", "exec", "-n", "insurance-ai-poc", 
                       "deployment/insurance-ai-poc-domain-agent", "--",
                       "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                       "http://insurance-ai-poc-technical-agent:8002/a2a/agent.json"]
        },
        {
            "name": "Technical Agent → Policy Server", 
            "command": ["kubectl", "exec", "-n", "insurance-ai-poc",
                       "deployment/insurance-ai-poc-technical-agent", "--",
                       "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                       "http://insurance-ai-poc-policy-server:8001/mcp/"]
        }
    ]
    
    all_passed = True
    for test in tests:
        try:
            result = subprocess.run(test["command"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                status_code = result.stdout.strip().replace('%', '')
                if status_code in ['200', '406']:  # 406 is expected for GET to MCP
                    print(f"✅ {test['name']}: Connected (HTTP {status_code})")
                else:
                    print(f"❌ {test['name']}: Unexpected status {status_code}")
                    all_passed = False
            else:
                print(f"❌ {test['name']}: Connection failed - {result.stderr}")
                all_passed = False
        except Exception as e:
            print(f"❌ {test['name']}: Error - {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🚀 Testing Kubernetes-deployed Insurance AI System")
    print("=" * 60)
    
    # Run tests
    ui_test = test_streamlit_ui()
    pods_test = test_kubernetes_pods()
    connectivity_test = test_service_connectivity()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    if ui_test:
        print("✅ Streamlit UI: PASSED")
        tests_passed += 1
    else:
        print("❌ Streamlit UI: FAILED")
    
    if pods_test:
        print("✅ Kubernetes Pods: PASSED")
        tests_passed += 1
    else:
        print("❌ Kubernetes Pods: FAILED")
    
    if connectivity_test:
        print("✅ Service Connectivity: PASSED")
        tests_passed += 1
    else:
        print("❌ Service Connectivity: FAILED")
    
    print(f"\n🎯 Overall Result: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Your system is deployed and ready!")
        print("\n🌐 Access your Insurance AI system at:")
        print("   http://localhost:8501")
        print("\n💡 The system features:")
        print("   • LLM-only intent processing (no fallbacks)")
        print("   • Multi-intent support")
        print("   • Session-based authentication")
        print("   • Langfuse monitoring")
        print("   • High availability with multiple replicas")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) failed. Please check the system configuration.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 