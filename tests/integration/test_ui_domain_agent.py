#!/usr/bin/env python3
"""
Test the actual DomainAgentClient used by Streamlit UI to find the root cause.
"""

import subprocess
import sys


def test_domain_agent_client_direct():
    """Test the DomainAgentClient directly in the Streamlit UI container"""
    
    # Get streamlit pod
    result = subprocess.run([
        "kubectl", "get", "pods", "-n", "cursor-insurance-ai-poc", 
        "-l", "app=streamlit-ui", "-o", "jsonpath={.items[0].metadata.name}"
    ], capture_output=True, text=True)
    
    streamlit_pod = result.stdout.strip()
    if not streamlit_pod:
        print("❌ No Streamlit UI pod found")
        return False
    
    print(f"Testing DomainAgentClient in pod: {streamlit_pod}")
    
    # Test script to run in the container
    test_script = """
import sys
sys.path.append('/app/ui')
try:
    from streamlit_app import DomainAgentClient
    print('SUCCESS: Imported DomainAgentClient')
    
    client = DomainAgentClient()
    print('CLIENT_CREATED: True')
    print('BASE_URL:', client.base_url)
    print('ENDPOINTS:', client.possible_endpoints)
    
    # Test endpoint discovery
    client._find_active_endpoint()
    print('ENDPOINT_DISCOVERY_COMPLETE: True')
    print('FINAL_BASE_URL:', client.base_url)
    
    if client.base_url:
        print('STATUS: Domain agent client found active endpoint')
        try:
            result = client.send_message('test message', 'TEST-001')
            print('SEND_MESSAGE_SUCCESS: True')
            print('RESULT:', result)
        except Exception as e:
            print('SEND_MESSAGE_ERROR:', str(e))
    else:
        print('STATUS: Domain agent client found NO active endpoint')
        print('REASON: All endpoints failed connection')
        
except ImportError as e:
    print('IMPORT_ERROR:', str(e))
except Exception as e:
    print('GENERAL_ERROR:', str(e))
    import traceback
    traceback.print_exc()
"""
    
    # Run the test in the container
    cmd = [
        "kubectl", "exec", "-n", "cursor-insurance-ai-poc", streamlit_pod, "--",
        "python", "-c", test_script
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("=" * 60)
    print("DOMAIN AGENT CLIENT TEST RESULTS:")
    print("=" * 60)
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nRETURN CODE: {result.returncode}")
    print("=" * 60)
    
    return result.returncode == 0


def test_manual_connection_from_ui():
    """Test manual connection to domain agent from UI pod"""
    
    # Get streamlit pod
    result = subprocess.run([
        "kubectl", "get", "pods", "-n", "cursor-insurance-ai-poc", 
        "-l", "app=streamlit-ui", "-o", "jsonpath={.items[0].metadata.name}"
    ], capture_output=True, text=True)
    
    streamlit_pod = result.stdout.strip()
    
    test_script = """
import requests
import time

endpoints = [
    'http://claims-agent:8000',
    'http://localhost:8000', 
    'http://127.0.0.1:8000'
]

for endpoint in endpoints:
    try:
        print(f'TESTING: {endpoint}/health')
        response = requests.get(f'{endpoint}/health', timeout=3)
        print(f'SUCCESS: {endpoint} - Status: {response.status_code}')
        print(f'RESPONSE: {response.json()}')
        break
    except Exception as e:
        print(f'FAILED: {endpoint} - Error: {str(e)}')
"""
    
    cmd = [
        "kubectl", "exec", "-n", "cursor-insurance-ai-poc", streamlit_pod, "--",
        "python", "-c", test_script
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("=" * 60)
    print("MANUAL CONNECTION TEST RESULTS:")
    print("=" * 60)
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print("=" * 60)


if __name__ == "__main__":
    print("🔍 DIAGNOSTIC: Testing Streamlit UI -> Domain Agent Connection")
    print("=" * 70)
    
    print("\n1️⃣ Testing DomainAgentClient directly...")
    success1 = test_domain_agent_client_direct()
    
    print("\n2️⃣ Testing manual connection...")
    test_manual_connection_from_ui()
    
    print(f"\n📊 SUMMARY:")
    print(f"DomainAgentClient Test: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print("Manual Connection Test: See output above")
    
    if not success1:
        sys.exit(1) 