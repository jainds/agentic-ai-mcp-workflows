#!/usr/bin/env python3
"""
UI Test Runner for Insurance AI Streamlit Interface
Handles port forwarding and runs Selenium tests
"""

import subprocess
import time
import requests
import os
import signal
import sys
from pathlib import Path

class UITestRunner:
    def __init__(self):
        self.port_forward_process = None
        self.base_url = "http://localhost:8501"
        self.namespace = "cursor-insurance-ai-poc"
        
    def setup_port_forwarding(self):
        """Set up kubectl port forwarding to Streamlit service"""
        print("🔗 Setting up port forwarding to Streamlit UI...")
        
        cmd = [
            "kubectl", "port-forward", "svc/streamlit-ui", "8501:8501", 
            "-n", self.namespace
        ]
        
        try:
            self.port_forward_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Wait for port forwarding to be established
            time.sleep(5)
            
            # Check if it's working
            for attempt in range(10):
                try:
                    response = requests.get(f"{self.base_url}/_stcore/health", timeout=5)
                    if response.status_code == 200:
                        print(f"✅ Port forwarding established successfully")
                        return True
                except requests.RequestException:
                    time.sleep(2)
                    continue
            
            print("❌ Failed to establish port forwarding")
            return False
            
        except Exception as e:
            print(f"❌ Error setting up port forwarding: {e}")
            return False
    
    def cleanup_port_forwarding(self):
        """Clean up port forwarding process"""
        if self.port_forward_process:
            print("🧹 Cleaning up port forwarding...")
            try:
                # Kill the entire process group
                os.killpg(os.getpgid(self.port_forward_process.pid), signal.SIGTERM)
                self.port_forward_process.wait(timeout=10)
            except:
                try:
                    # Force kill if needed
                    os.killpg(os.getpgid(self.port_forward_process.pid), signal.SIGKILL)
                except:
                    pass
            self.port_forward_process = None
    
    def wait_for_streamlit(self):
        """Wait for Streamlit to be ready"""
        print("⏳ Waiting for Streamlit to be ready...")
        
        for attempt in range(30):
            try:
                response = requests.get(f"{self.base_url}/_stcore/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Streamlit is ready!")
                    return True
            except requests.RequestException:
                pass
            
            time.sleep(2)
            print(f"   Attempt {attempt + 1}/30...")
        
        print("❌ Streamlit not ready after 60 seconds")
        return False
    
    def run_selenium_tests(self, test_pattern="tests/ui/test_*.py", headless=True):
        """Run Selenium tests using pytest"""
        print("🧪 Running Selenium UI tests...")
        
        # Set environment variables
        env = os.environ.copy()
        env["STREAMLIT_URL"] = self.base_url
        env["HEADLESS"] = "true" if headless else "false"
        
        # Prepare pytest command
        cmd = [
            "python", "-m", "pytest",
            test_pattern,
            "-v",
            "--tb=short",
            "--html=tests/ui/selenium_report.html",
            "--self-contained-html",
            "-x"  # Stop on first failure for debugging
        ]
        
        try:
            result = subprocess.run(cmd, env=env, cwd=".", capture_output=True, text=True)
            
            print("\n" + "="*60)
            print("🧪 SELENIUM TEST RESULTS")
            print("="*60)
            print(result.stdout)
            
            if result.stderr:
                print("\n🔍 Test Warnings/Errors:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("\n✅ All UI tests passed!")
            else:
                print(f"\n❌ Some tests failed (exit code: {result.returncode})")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    def check_kubernetes_deployment(self):
        """Check if Kubernetes deployment is ready"""
        print("🔍 Checking Kubernetes deployment...")
        
        try:
            # Check if deployment exists and is ready
            result = subprocess.run([
                "kubectl", "get", "deployment", "streamlit-ui", 
                "-n", self.namespace, "-o", "json"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Streamlit deployment found")
                
                # Check pod status
                pod_result = subprocess.run([
                    "kubectl", "get", "pods", "-l", "app=streamlit-ui",
                    "-n", self.namespace, "--no-headers"
                ], capture_output=True, text=True, timeout=10)
                
                if pod_result.returncode == 0:
                    pods = pod_result.stdout.strip()
                    if "Running" in pods:
                        print("✅ Streamlit pods are running")
                        return True
                    else:
                        print(f"⚠️ Streamlit pods not ready: {pods}")
                        return False
                
            print("❌ Streamlit deployment not found")
            return False
            
        except Exception as e:
            print(f"❌ Error checking deployment: {e}")
            return False
    
    def run_full_test_suite(self, headless=True):
        """Run complete UI test suite"""
        print("🚀 Starting Insurance AI UI Test Suite")
        print("="*50)
        
        success = True
        
        try:
            # Step 1: Check Kubernetes deployment
            if not self.check_kubernetes_deployment():
                print("❌ Kubernetes deployment check failed")
                return False
            
            # Step 2: Setup port forwarding
            if not self.setup_port_forwarding():
                print("❌ Port forwarding setup failed")
                return False
            
            # Step 3: Wait for Streamlit
            if not self.wait_for_streamlit():
                print("❌ Streamlit readiness check failed")
                return False
            
            # Step 4: Run authentication tests
            print("\n🔐 Running Authentication Tests...")
            auth_success = self.run_selenium_tests("tests/ui/test_authentication.py", headless)
            
            # Step 5: Run chat interface tests
            print("\n💬 Running Chat Interface Tests...")
            chat_success = self.run_selenium_tests("tests/ui/test_chat_interface.py", headless)
            
            # Step 6: Run advanced features tests
            print("\n🔧 Running Advanced Features Tests...")
            advanced_success = self.run_selenium_tests("tests/ui/test_advanced_features.py", headless)
            
            # Summary
            print("\n" + "="*60)
            print("📊 TEST SUMMARY")
            print("="*60)
            print(f"Authentication Tests: {'✅ PASSED' if auth_success else '❌ FAILED'}")
            print(f"Chat Interface Tests: {'✅ PASSED' if chat_success else '❌ FAILED'}")
            print(f"Advanced Features Tests: {'✅ PASSED' if advanced_success else '❌ FAILED'}")
            
            overall_success = auth_success and chat_success and advanced_success
            print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
            
            return overall_success
            
        except KeyboardInterrupt:
            print("\n🛑 Tests interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return False
        finally:
            self.cleanup_port_forwarding()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Insurance AI UI Tests")
    parser.add_argument("--headless", action="store_true", default=True,
                      help="Run tests in headless mode (default: True)")
    parser.add_argument("--visible", action="store_true", 
                      help="Run tests with visible browser")
    parser.add_argument("--test", choices=["auth", "chat", "advanced", "all"], 
                      default="all", help="Which tests to run")
    
    args = parser.parse_args()
    
    # Handle visibility setting
    headless = args.headless and not args.visible
    
    runner = UITestRunner()
    
    try:
        if args.test == "all":
            success = runner.run_full_test_suite(headless)
        else:
            # Setup for individual test runs
            if not runner.setup_port_forwarding():
                return 1
            if not runner.wait_for_streamlit():
                return 1
            
            test_file_map = {
                "auth": "tests/ui/test_authentication.py",
                "chat": "tests/ui/test_chat_interface.py", 
                "advanced": "tests/ui/test_advanced_features.py"
            }
            
            success = runner.run_selenium_tests(test_file_map[args.test], headless)
            runner.cleanup_port_forwarding()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Test run interrupted")
        runner.cleanup_port_forwarding()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 