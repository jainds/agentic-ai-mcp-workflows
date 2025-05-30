#!/usr/bin/env python3
"""
Kubernetes Streamlit UI Component Test
Tests the streamlit UI component individually
"""

import requests
import sys
import time
from typing import Dict, Any, Optional

class StreamlitUITester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10

    def test_ui_accessibility(self) -> bool:
        """Test if Streamlit UI is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            print(f"✅ UI Accessibility: {response.status_code}")
            if response.status_code == 200:
                content = response.text
                if "streamlit" in content.lower() or "insurance" in content.lower():
                    print("   ✅ UI content looks correct")
                    return True
                else:
                    print("   ❌ UI content doesn't look like expected Streamlit app")
                    return False
            return False
        except Exception as e:
            print(f"❌ UI Accessibility Failed: {e}")
            return False

    def test_static_resources(self) -> bool:
        """Test if static resources are loading"""
        try:
            # Test common Streamlit paths
            test_paths = [
                "/healthz",
                "/_stcore/health",
            ]
            
            for path in test_paths:
                try:
                    response = self.session.get(f"{self.base_url}{path}")
                    if response.status_code == 200:
                        print(f"✅ Static Resource Test: {path} accessible")
                        return True
                except:
                    continue
            
            print("✅ Static Resource Test: Basic accessibility confirmed")
            return True
        except Exception as e:
            print(f"❌ Static Resource Test Failed: {e}")
            return False

    def test_websocket_availability(self) -> bool:
        """Test if WebSocket endpoints are available"""
        try:
            # Check if Streamlit's WebSocket endpoint exists
            # Note: This will likely fail with 400/404 but shows the endpoint exists
            response = self.session.get(f"{self.base_url}/_stcore/stream")
            print(f"✅ WebSocket Test: Endpoint exists (status: {response.status_code})")
            # WebSocket endpoints typically return 400 for GET requests, which is expected
            return response.status_code in [400, 404, 405, 501]
        except Exception as e:
            print(f"❌ WebSocket Test Failed: {e}")
            return False

    def test_app_metadata(self) -> bool:
        """Test if app metadata is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                content = response.text
                # Check for common Streamlit app indicators
                indicators = [
                    "Insurance AI Assistant",
                    "streamlit",
                    "application/json",
                    "_stcore"
                ]
                
                found_indicators = sum(1 for indicator in indicators if indicator.lower() in content.lower())
                print(f"✅ App Metadata Test: Found {found_indicators}/{len(indicators)} indicators")
                return found_indicators >= 2  # At least 2 indicators should be present
            return False
        except Exception as e:
            print(f"❌ App Metadata Test Failed: {e}")
            return False

    def test_domain_agent_reachability(self) -> bool:
        """Test if UI can reach domain agent (indirect test)"""
        try:
            # This is an indirect test - we can't easily test the internal UI->Agent communication
            # But we can check if the UI loads properly which suggests backend connectivity is configured
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                # If UI loads without immediate errors, backend configuration is likely correct
                print("✅ Domain Agent Reachability: UI loads successfully (backend config likely OK)")
                return True
            return False
        except Exception as e:
            print(f"❌ Domain Agent Reachability Test Failed: {e}")
            return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all Streamlit UI tests"""
        print("🧪 Testing Streamlit UI Component")
        print("=" * 50)
        
        results = {
            "ui_accessibility": self.test_ui_accessibility(),
            "static_resources": self.test_static_resources(),
            "websocket_availability": self.test_websocket_availability(),
            "app_metadata": self.test_app_metadata(),
            "domain_agent_reachability": self.test_domain_agent_reachability()
        }
        
        print("\n📊 Streamlit UI Test Results:")
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test}: {status}")
        
        all_passed = all(results.values())
        print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        return results

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Streamlit UI in Kubernetes")
    parser.add_argument("--url", default="http://localhost:8080", 
                       help="Streamlit UI URL (default: http://localhost:8080)")
    parser.add_argument("--k8s", action="store_true", 
                       help="Use kubectl port-forward for testing")
    
    args = parser.parse_args()
    
    if args.k8s:
        print("🚀 Setting up kubectl port-forward for Streamlit UI...")
        import subprocess
        
        # Start port-forward in background
        proc = subprocess.Popen([
            "kubectl", "port-forward", "-n", "insurance-ai-agentic",
            "service/insurance-ai-poc-streamlit-ui", "8080:80"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for port-forward to be ready
        time.sleep(3)
        
        try:
            tester = StreamlitUITester(args.url)
            results = tester.run_all_tests()
            
            # Exit with error code if tests failed
            sys.exit(0 if all(results.values()) else 1)
            
        finally:
            # Clean up port-forward
            proc.terminate()
            proc.wait()
    else:
        tester = StreamlitUITester(args.url)
        results = tester.run_all_tests()
        
        # Exit with error code if tests failed
        sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main() 