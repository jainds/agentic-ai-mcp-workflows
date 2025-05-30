#!/usr/bin/env python3
"""
Integration test for Streamlit UI accessibility and domain agent connectivity.

This test was helpful for verifying the UI is working properly after fixing
the domain agent endpoint configuration issue.
"""

import pytest
import requests
import time
import subprocess
import json


class TestUIAccessibility:
    """Test UI accessibility and basic functionality."""
    
    def test_ui_health_check(self):
        """Test if the UI is accessible via port forward."""
        try:
            print("🔍 Testing UI accessibility...")
            response = requests.get("http://localhost:8501", timeout=10)
            if response.status_code == 200:
                print("✅ UI is accessible")
                assert True
            else:
                pytest.fail(f"UI returned status code: {response.status_code}")
        except requests.RequestException as e:
            pytest.skip(f"UI not accessible (likely no port forwarding): {e}")
    
    def test_ui_service_exists(self):
        """Test if the UI service exists in Kubernetes."""
        try:
            result = subprocess.run([
                'kubectl', 'get', 'service', 'streamlit-ui',
                '-n', 'cursor-insurance-ai-poc',
                '-o', 'json'
            ], capture_output=True, text=True, check=True)
            
            service_data = json.loads(result.stdout)
            assert service_data['metadata']['name'] == 'streamlit-ui'
            print("✅ Streamlit UI service exists")
            
        except subprocess.CalledProcessError:
            pytest.fail("Streamlit UI service not found")
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON response from kubectl")
    
    def test_ui_deployment_ready(self):
        """Test if the UI deployment is ready."""
        try:
            result = subprocess.run([
                'kubectl', 'get', 'deployment', 'streamlit-ui',
                '-n', 'cursor-insurance-ai-poc',
                '-o', 'json'
            ], capture_output=True, text=True, check=True)
            
            deployment_data = json.loads(result.stdout)
            status = deployment_data.get('status', {})
            ready_replicas = status.get('readyReplicas', 0)
            replicas = status.get('replicas', 0)
            
            assert ready_replicas == replicas, f"Only {ready_replicas}/{replicas} replicas ready"
            print(f"✅ UI deployment ready: {ready_replicas}/{replicas} replicas")
            
        except subprocess.CalledProcessError:
            pytest.fail("Streamlit UI deployment not found")
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON response from kubectl")
    
    def test_ui_pods_running(self):
        """Test if UI pods are running."""
        try:
            result = subprocess.run([
                'kubectl', 'get', 'pods',
                '-n', 'cursor-insurance-ai-poc',
                '-l', 'app=streamlit-ui',
                '-o', 'json'
            ], capture_output=True, text=True, check=True)
            
            pods_data = json.loads(result.stdout)
            pods = pods_data.get('items', [])
            
            assert len(pods) > 0, "No UI pods found"
            
            for pod in pods:
                status = pod.get('status', {})
                phase = status.get('phase')
                assert phase == 'Running', f"Pod {pod['metadata']['name']} is {phase}"
            
            print(f"✅ {len(pods)} UI pod(s) running")
            
        except subprocess.CalledProcessError:
            pytest.fail("Failed to get UI pods")
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON response from kubectl")


def manual_ui_test_instructions():
    """
    Print manual test instructions for comprehensive UI testing.
    This function provides step-by-step instructions that were used
    to verify the UI fix was working properly.
    """
    print("\n" + "=" * 60)
    print("📋 MANUAL UI TEST INSTRUCTIONS")
    print("=" * 60)
    print("To fully test the UI functionality:")
    print()
    print("1. Set up port forwarding (if not already done):")
    print("   kubectl port-forward svc/streamlit-ui 8501:8501 -n cursor-insurance-ai-poc")
    print()
    print("2. Open http://localhost:8501 in your browser")
    print()
    print("3. Test Authentication:")
    print("   - In the sidebar, enter Customer ID: CUST-001")
    print("   - Click 'Authenticate'")
    print("   - Verify you see 'Welcome, John Smith' message")
    print()
    print("4. Test Chat Interface:")
    print("   - Go to the 'Chat Interface' tab")
    print("   - Send message: 'Tell me about my policies?'")
    print("   - Verify you get a response from the domain agent")
    print("   - Check that conversation history is displayed")
    print()
    print("5. Test System Health:")
    print("   - Go to the 'System Health' tab")
    print("   - Verify domain agent shows as available")
    print("   - Check that other services are listed")
    print()
    print("6. Test Other Features:")
    print("   - Check 'Thinking & Orchestration' tab")
    print("   - Check 'API Monitor' tab")
    print("   - Verify all tabs load without errors")
    print()
    print("Expected Results:")
    print("✅ UI loads and responds")
    print("✅ Authentication works")
    print("✅ Domain agent responds to chat messages")
    print("✅ System health shows services as available")
    print("✅ No error messages in the UI")


if __name__ == "__main__":
    # Can be run as a standalone script for manual testing
    manual_ui_test_instructions()
    
    print("\n" + "=" * 60)
    print("🚀 Running Automated UI Tests")
    print("=" * 60)
    
    # Run pytest programmatically for this file
    import sys
    pytest.main([__file__, "-v", "-s"]) 