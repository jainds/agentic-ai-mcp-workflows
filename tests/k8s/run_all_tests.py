#!/usr/bin/env python3
"""
Master Test Runner for Kubernetes Insurance AI Deployment
Runs all tests in the correct sequence: unit -> integration -> e2e
"""

import sys
import time
import subprocess
from typing import Dict, Any, List, Tuple

def run_test_script(script_path: str, test_name: str) -> Tuple[bool, str]:
    """Run a test script and return success status and output"""
    try:
        print(f"\n{'='*60}")
        print(f"🧪 Running {test_name}")
        print(f"{'='*60}")
        
        result = subprocess.run([
            sys.executable, script_path, "--k8s"
        ], capture_output=True, text=True, timeout=300)
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        return success, result.stdout + result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"❌ {test_name} timed out after 5 minutes")
        return False, "Test timed out"
    except Exception as e:
        print(f"❌ {test_name} failed to run: {e}")
        return False, str(e)

def check_kubernetes_deployment() -> bool:
    """Check if Kubernetes deployment is ready"""
    try:
        print("🔍 Checking Kubernetes deployment status...")
        
        # Check if namespace exists
        result = subprocess.run([
            "kubectl", "get", "namespace", "insurance-ai-agentic"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Namespace 'insurance-ai-agentic' not found")
            return False
        
        # Check if pods are running
        result = subprocess.run([
            "kubectl", "get", "pods", "-n", "insurance-ai-agentic", 
            "--field-selector=status.phase=Running"
        ], capture_output=True, text=True)
        
        if "insurance-ai-poc" not in result.stdout:
            print("❌ Insurance AI pods are not running")
            print("Current pod status:")
            subprocess.run([
                "kubectl", "get", "pods", "-n", "insurance-ai-agentic"
            ])
            return False
        
        print("✅ Kubernetes deployment appears to be ready")
        return True
        
    except Exception as e:
        print(f"❌ Failed to check Kubernetes deployment: {e}")
        return False

def main():
    """Main test execution"""
    print("🚀 Insurance AI Kubernetes Test Suite")
    print("Testing deployment in namespace: insurance-ai-agentic")
    print("=" * 60)
    
    # Check deployment readiness
    if not check_kubernetes_deployment():
        print("\n❌ Kubernetes deployment is not ready. Please ensure:")
        print("   1. Helm chart is deployed: helm install insurance-ai-poc ./k8s/insurance-ai-poc")
        print("   2. All pods are running: kubectl get pods -n insurance-ai-agentic")
        print("   3. Services are available: kubectl get svc -n insurance-ai-agentic")
        sys.exit(1)
    
    # Define test sequence
    tests = [
        ("tests/k8s/test_policy_server.py", "Policy Server Component Tests"),
        ("tests/k8s/test_technical_agent.py", "Technical Agent Component Tests"),
        ("tests/k8s/test_domain_agent.py", "Domain Agent Component Tests"),
        ("tests/k8s/test_streamlit_ui.py", "Streamlit UI Component Tests"),
        ("tests/k8s/test_integration.py", "Integration Tests"),
        ("tests/k8s/test_e2e.py", "End-to-End Tests")
    ]
    
    # Track results
    results = {}
    start_time = time.time()
    
    # Run tests in sequence
    for script_path, test_name in tests:
        success, output = run_test_script(script_path, test_name)
        results[test_name] = success
        
        if not success:
            print(f"\n⚠️  {test_name} failed. Continuing with remaining tests...")
        
        # Brief pause between tests
        time.sleep(2)
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{'='*60}")
    print("📊 FINAL TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"⏱️  Total execution time: {duration:.1f} seconds")
    print()
    
    passed_tests = []
    failed_tests = []
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        
        if success:
            passed_tests.append(test_name)
        else:
            failed_tests.append(test_name)
    
    print(f"\n📈 Results: {len(passed_tests)}/{len(results)} tests passed")
    
    if len(passed_tests) == len(results):
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Insurance AI Assistant is fully functional in Kubernetes!")
        print("\n🔗 Access your application:")
        print("   Streamlit UI: http://localhost:8080")
        print("   (Run: kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-streamlit-ui 8080:80)")
        print("\n🧪 Individual component access:")
        print("   Domain Agent: kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-domain-agent 8003:8003")
        print("   Technical Agent: kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-technical-agent 8002:8002")
        print("   Policy Server: kubectl port-forward -n insurance-ai-agentic service/insurance-ai-poc-policy-server 8001:8001")
        sys.exit(0)
    
    elif len(passed_tests) >= len(results) * 0.7:  # 70% pass rate
        print("\n⚠️  MOSTLY FUNCTIONAL")
        print("Most tests passed, but some issues detected.")
        if failed_tests:
            print("\n❌ Failed tests:")
            for test in failed_tests:
                print(f"   • {test}")
        print("\n🔗 You can still try accessing:")
        print("   Streamlit UI: http://localhost:8080")
        sys.exit(1)
    
    else:
        print("\n❌ CRITICAL ISSUES DETECTED")
        print("Multiple test failures indicate system problems.")
        if failed_tests:
            print("\n❌ Failed tests:")
            for test in failed_tests:
                print(f"   • {test}")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Check pod logs: kubectl logs -n insurance-ai-agentic -l app.kubernetes.io/name=insurance-ai-poc")
        print("   2. Verify services: kubectl get svc -n insurance-ai-agentic")
        print("   3. Check pod status: kubectl get pods -n insurance-ai-agentic")
        print("   4. Review ConfigMap: kubectl get configmap -n insurance-ai-agentic")
        sys.exit(1)

if __name__ == "__main__":
    main() 