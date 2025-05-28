#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies all components are working before running tests
"""

import subprocess
import requests
import time
import json
import sys
from typing import Dict, Any, List


class DeploymentVerifier:
    """Verify deployment status and fix common issues"""
    
    def __init__(self):
        self.checks = []
        self.fixes = []
        
    def run_command(self, cmd: str) -> tuple:
        """Run shell command and return (success, output)"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            return False, str(e)
    
    def check_kubernetes_cluster(self) -> Dict[str, Any]:
        """Check if Kubernetes cluster is accessible"""
        print("🔍 Checking Kubernetes cluster...")
        
        success, output = self.run_command("kubectl cluster-info")
        if success:
            success, nodes = self.run_command("kubectl get nodes")
            return {
                "status": "healthy" if success else "degraded",
                "cluster_info": output,
                "nodes": nodes if success else "No nodes found"
            }
        else:
            return {
                "status": "failed",
                "error": output,
                "fix": "Ensure Kubernetes cluster is running (minikube start, k3s, etc.)"
            }
    
    def check_namespace_and_pods(self) -> Dict[str, Any]:
        """Check namespace and pod status"""
        print("🔍 Checking namespace and pods...")
        
        # Check namespace
        success, output = self.run_command("kubectl get namespace insurance-poc")
        if not success:
            return {
                "status": "failed",
                "error": "Namespace insurance-poc not found",
                "fix": "Run: kubectl apply -f k8s/manifests/namespace.yaml"
            }
        
        # Check pods
        success, pods = self.run_command("kubectl get pods -n insurance-poc")
        if not success:
            return {
                "status": "failed", 
                "error": pods,
                "fix": "Deploy agents: cd scripts && ./deploy_k8s.sh"
            }
        
        # Parse pod status
        pod_lines = pods.strip().split('\n')[1:]  # Skip header
        pod_status = {}
        
        for line in pod_lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    pod_name = parts[0]
                    ready = parts[1]
                    status = parts[2]
                    pod_status[pod_name] = {
                        "ready": ready,
                        "status": status,
                        "healthy": status == "Running" and "/" in ready and ready.split("/")[0] == ready.split("/")[1]
                    }
        
        return {
            "status": "healthy" if all(p["healthy"] for p in pod_status.values()) else "degraded",
            "pods": pod_status,
            "raw_output": pods
        }
    
    def check_services_and_nodeports(self) -> Dict[str, Any]:
        """Check services and NodePort accessibility"""
        print("🔍 Checking services and NodePorts...")
        
        success, services = self.run_command("kubectl get services -n insurance-poc")
        if not success:
            return {
                "status": "failed",
                "error": services,
                "fix": "Deploy services: kubectl apply -f k8s/manifests/"
            }
        
        # Test NodePort connectivity
        nodeport_tests = {
            "support-agent": 30005,
            "claims-agent": 30008
        }
        
        connectivity = {}
        for service, port in nodeport_tests.items():
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                connectivity[service] = {
                    "port": port,
                    "accessible": response.status_code == 200,
                    "response": response.json() if response.status_code == 200 else None,
                    "status_code": response.status_code
                }
            except Exception as e:
                connectivity[service] = {
                    "port": port,
                    "accessible": False,
                    "error": str(e)
                }
        
        return {
            "status": "healthy" if all(c["accessible"] for c in connectivity.values()) else "failed",
            "services": services,
            "connectivity": connectivity
        }
    
    def check_secrets_and_config(self) -> Dict[str, Any]:
        """Check secrets and configuration"""
        print("🔍 Checking secrets and configuration...")
        
        # Check secrets
        success, secrets = self.run_command("kubectl get secrets -n insurance-poc")
        if not success or "llm-api-keys" not in secrets:
            return {
                "status": "failed",
                "error": "LLM API keys secret not found",
                "fix": "Create secret: kubectl create secret generic llm-api-keys -n insurance-poc --from-literal=OPENROUTER_API_KEY=your_key"
            }
        
        # Check if API key is set
        success, api_key = self.run_command("kubectl get secret llm-api-keys -n insurance-poc -o jsonpath='{.data.OPENROUTER_API_KEY}' | base64 -d")
        
        if not success or not api_key.strip() or "${" in api_key:
            return {
                "status": "failed",
                "error": "API key not properly set in secret",
                "fix": "Set API key: export OPENROUTER_API_KEY=your_key && kubectl delete secret llm-api-keys -n insurance-poc && kubectl create secret generic llm-api-keys -n insurance-poc --from-literal=OPENROUTER_API_KEY=\"$OPENROUTER_API_KEY\""
            }
        
        return {
            "status": "healthy",
            "secrets": secrets,
            "api_key_length": len(api_key.strip()) if api_key else 0
        }
    
    def test_basic_functionality(self) -> Dict[str, Any]:
        """Test basic agent functionality"""
        print("🔍 Testing basic functionality...")
        
        test_results = {}
        
        # Test simple claim inquiry
        try:
            response = requests.post(
                "http://localhost:30008/execute",
                json={
                    "skill_name": "HandleClaimInquiry",
                    "parameters": {
                        "user_message": "What is my claim status? my claimid is 1002, customer id is 101"
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                test_results["claim_inquiry"] = {
                    "success": result.get("success", False),
                    "workflow": result.get("result", {}).get("workflow"),
                    "has_response": bool(result.get("result", {}).get("response")),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                test_results["claim_inquiry"] = {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response": response.text
                }
                
        except Exception as e:
            test_results["claim_inquiry"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:30008/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                test_results["health_check"] = {
                    "success": True,
                    "agent_name": health_data.get("agent"),
                    "skills_count": len(health_data.get("skills", [])),
                    "status": health_data.get("status")
                }
            else:
                test_results["health_check"] = {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            test_results["health_check"] = {
                "success": False,
                "error": str(e)
            }
        
        overall_success = all(t.get("success", False) for t in test_results.values())
        
        return {
            "status": "healthy" if overall_success else "failed",
            "tests": test_results
        }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all deployment checks"""
        print("🚀 Running Deployment Verification...")
        print("=" * 50)
        
        results = {}
        
        # 1. Kubernetes cluster
        results["kubernetes"] = self.check_kubernetes_cluster()
        
        # 2. Namespace and pods
        results["pods"] = self.check_namespace_and_pods()
        
        # 3. Services and NodePorts
        results["services"] = self.check_services_and_nodeports()
        
        # 4. Secrets and config
        results["secrets"] = self.check_secrets_and_config()
        
        # 5. Basic functionality
        results["functionality"] = self.test_basic_functionality()
        
        return results
    
    def generate_report(self, results: Dict[str, Any]):
        """Generate and display verification report"""
        print("\n" + "=" * 60)
        print("🏁 DEPLOYMENT VERIFICATION REPORT")
        print("=" * 60)
        
        overall_status = "HEALTHY"
        issues = []
        fixes = []
        
        for check_name, result in results.items():
            status = result.get("status", "unknown")
            print(f"\n📊 {check_name.upper()}:")
            
            if status == "healthy":
                print(f"  ✅ PASS - {check_name} is working correctly")
            elif status == "degraded":
                print(f"  ⚠️  WARN - {check_name} has issues but may work")
                overall_status = "DEGRADED"
                if "fix" in result:
                    fixes.append(f"{check_name}: {result['fix']}")
            else:
                print(f"  ❌ FAIL - {check_name} is not working")
                overall_status = "FAILED"
                issues.append(check_name)
                if "fix" in result:
                    fixes.append(f"{check_name}: {result['fix']}")
            
            # Show key details
            if "error" in result:
                print(f"      ❌ Error: {result['error']}")
            if check_name == "functionality" and "tests" in result:
                for test_name, test_result in result["tests"].items():
                    test_status = "✅" if test_result.get("success") else "❌"
                    print(f"      {test_status} {test_name}")
        
        print(f"\n🎯 OVERALL STATUS: {overall_status}")
        
        if overall_status == "HEALTHY":
            print("🎉 All systems are operational! Ready to run tests.")
        elif overall_status == "DEGRADED":
            print("⚠️  Some issues detected but system may work.")
        else:
            print("🚨 Critical issues found. Fix required before testing.")
        
        if fixes:
            print(f"\n🔧 SUGGESTED FIXES:")
            for fix in fixes:
                print(f"  • {fix}")
        
        return overall_status == "HEALTHY"


def main():
    """Main verification function"""
    verifier = DeploymentVerifier()
    results = verifier.run_all_checks()
    
    healthy = verifier.generate_report(results)
    
    # Save detailed results
    with open("deployment_verification.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📝 Detailed results saved to: deployment_verification.json")
    
    if healthy:
        print("\n✅ System is ready! You can now run:")
        print("   python tests/run_integration_tests.py")
        return 0
    else:
        print("\n❌ Fix the issues above before running tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 