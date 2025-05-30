#!/usr/bin/env python3
"""
Comprehensive tests for domain agent connectivity and functionality.
Tests the full chain: UI -> Domain Agent -> A2A -> Technical Agents
"""

import requests
import json
import time
import pytest
from typing import Dict, Any
import subprocess


class TestDomainAgentConnectivity:
    """Test domain agent network connectivity and endpoints"""
    
    @pytest.fixture
    def domain_agent_url(self):
        return "http://claims-agent:8000"
    
    @pytest.fixture 
    def streamlit_ui_pod(self):
        """Get a running streamlit UI pod name"""
        result = subprocess.run([
            "kubectl", "get", "pods", "-n", "cursor-insurance-ai-poc", 
            "-l", "app=streamlit-ui", "-o", "jsonpath={.items[0].metadata.name}"
        ], capture_output=True, text=True)
        return result.stdout.strip()
    
    def test_domain_agent_pods_running(self):
        """Test that domain agent pods are running"""
        result = subprocess.run([
            "kubectl", "get", "pods", "-n", "cursor-insurance-ai-poc",
            "-l", "app=claims-agent", "--no-headers"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get pods: {result.stderr}"
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 1, "No domain agent pods found"
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                status = parts[2]
                assert status == "Running", f"Pod not running: {line}"
        
        print(f"✅ Domain agent pods running: {len(lines)}")
    
    def test_domain_agent_service_exists(self):
        """Test that domain agent service exists and has endpoints"""
        result = subprocess.run([
            "kubectl", "get", "svc", "claims-agent", "-n", "cursor-insurance-ai-poc",
            "-o", "json"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Service not found: {result.stderr}"
        
        service = json.loads(result.stdout)
        assert service['spec']['ports'][0]['port'] == 8000
        
        # Check endpoints
        result = subprocess.run([
            "kubectl", "get", "endpoints", "claims-agent", "-n", "cursor-insurance-ai-poc",
            "-o", "json"
        ], capture_output=True, text=True)
        
        endpoints = json.loads(result.stdout)
        assert len(endpoints['subsets']) > 0, "No service endpoints found"
        assert len(endpoints['subsets'][0]['addresses']) > 0, "No ready endpoints"
        
        print(f"✅ Service exists with {len(endpoints['subsets'][0]['addresses'])} endpoints")
    
    def test_domain_agent_health_from_cluster(self, streamlit_ui_pod):
        """Test domain agent health endpoint from within cluster"""
        cmd = [
            "kubectl", "exec", "-n", "cursor-insurance-ai-poc", streamlit_ui_pod, "--",
            "python", "-c", 
            "import requests; r=requests.get('http://claims-agent:8000/health', timeout=5); print('STATUS:', r.status_code); print('RESPONSE:', r.json())"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0, f"Health check failed: {result.stderr}"
        assert "STATUS: 200" in result.stdout, f"Wrong status code: {result.stdout}"
        assert "healthy" in result.stdout, f"Unhealthy response: {result.stdout}"
        
        print(f"✅ Health check successful from cluster")
    
    def test_domain_agent_chat_from_cluster(self, streamlit_ui_pod):
        """Test domain agent chat endpoint from within cluster"""
        cmd = [
            "kubectl", "exec", "-n", "cursor-insurance-ai-poc", streamlit_ui_pod, "--",
            "python", "-c", 
            """
import requests, json
payload = {'message': 'test message', 'customer_id': 'TEST-001'}
r = requests.post('http://claims-agent:8000/chat', json=payload, timeout=10)
print('STATUS:', r.status_code)
print('RESPONSE:', r.json())
"""
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0, f"Chat test failed: {result.stderr}"
        assert "STATUS: 200" in result.stdout, f"Wrong status code: {result.stdout}"
        assert "response" in result.stdout, f"No response field: {result.stdout}"
        
        print(f"✅ Chat endpoint successful from cluster")
    
    def test_streamlit_ui_domain_agent_client(self, streamlit_ui_pod):
        """Test the actual DomainAgentClient class from Streamlit UI"""
        cmd = [
            "kubectl", "exec", "-n", "cursor-insurance-ai-poc", streamlit_ui_pod, "--",
            "python", "-c", 
            """
import sys
sys.path.append('/app')
from streamlit_app import DomainAgentClient

# Test the actual client used by UI
client = DomainAgentClient()
print('BASE_URL:', client.base_url)
print('ENDPOINTS:', client.possible_endpoints)

if client.base_url:
    print('✅ Domain agent client found active endpoint')
    result = client.send_message('test', 'TEST-001')
    print('MESSAGE_RESULT:', result)
else:
    print('❌ Domain agent client found no active endpoint')
"""
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"DomainAgentClient Test Output:\n{result.stdout}")
        if result.stderr:
            print(f"DomainAgentClient Test Errors:\n{result.stderr}")
        
        # This test reveals what the actual UI code is experiencing
        assert result.returncode == 0, f"DomainAgentClient test failed: {result.stderr}"
    
    def test_dns_resolution_in_cluster(self, streamlit_ui_pod):
        """Test DNS resolution for claims-agent from UI pod"""
        cmd = [
            "kubectl", "exec", "-n", "cursor-insurance-ai-poc", streamlit_ui_pod, "--",
            "nslookup", "claims-agent"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"DNS Resolution Output:\n{result.stdout}")
        
        # Check if claims-agent resolves to an IP
        assert "Name:" in result.stdout or "Address:" in result.stdout, \
            f"DNS resolution failed: {result.stdout}"
    
    def test_network_connectivity_detailed(self, streamlit_ui_pod):
        """Detailed network connectivity test"""
        tests = [
            ("ping", ["ping", "-c", "2", "claims-agent"]),
            ("telnet", ["timeout", "5", "telnet", "claims-agent", "8000"]),
            ("curl_verbose", ["curl", "-v", "-m", "10", "http://claims-agent:8000/health"])
        ]
        
        for test_name, cmd in tests:
            full_cmd = ["kubectl", "exec", "-n", "cursor-insurance-ai-poc", streamlit_ui_pod, "--"] + cmd
            result = subprocess.run(full_cmd, capture_output=True, text=True)
            
            print(f"\n{test_name.upper()} Test:")
            print(f"Command: {' '.join(cmd)}")
            print(f"Return code: {result.returncode}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")


class TestDomainAgentFunctionality:
    """Test domain agent internal functionality"""
    
    def test_domain_agent_logs_for_errors(self):
        """Check domain agent logs for errors"""
        result = subprocess.run([
            "kubectl", "logs", "-n", "cursor-insurance-ai-poc", 
            "deployment/claims-agent", "--tail=50"
        ], capture_output=True, text=True)
        
        logs = result.stdout.lower()
        
        # Check for common error patterns
        error_patterns = ["error", "exception", "traceback", "failed", "timeout"]
        found_errors = []
        
        for pattern in error_patterns:
            if pattern in logs:
                found_errors.append(pattern)
        
        print(f"Domain Agent Logs (last 50 lines):\n{result.stdout}")
        
        if found_errors:
            print(f"⚠️ Found potential errors in logs: {found_errors}")
        else:
            print("✅ No obvious errors in domain agent logs")
    
    def test_domain_agent_endpoints_list(self):
        """Test what endpoints the domain agent actually exposes"""
        # Get a domain agent pod
        result = subprocess.run([
            "kubectl", "get", "pods", "-n", "cursor-insurance-ai-poc",
            "-l", "app=claims-agent", "-o", "jsonpath={.items[0].metadata.name}"
        ], capture_output=True, text=True)
        
        pod_name = result.stdout.strip()
        assert pod_name, "No domain agent pod found"
        
        # Test various endpoints
        endpoints_to_test = [
            "/health",
            "/chat", 
            "/.well-known/agent.json",
            "/tasks/send",
            "/docs",
            "/"
        ]
        
        for endpoint in endpoints_to_test:
            cmd = [
                "kubectl", "exec", "-n", "cursor-insurance-ai-poc", pod_name, "--",
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
                f"http://localhost:8000{endpoint}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            status_code = result.stdout.strip()
            
            print(f"Endpoint {endpoint}: HTTP {status_code}")


class TestStreamlitUIBehavior:
    """Test Streamlit UI specific behavior and state"""
    
    def test_streamlit_ui_logs_for_connection_attempts(self):
        """Check Streamlit UI logs for connection attempts and errors"""
        result = subprocess.run([
            "kubectl", "logs", "-n", "cursor-insurance-ai-poc", 
            "deployment/streamlit-ui", "--tail=100"
        ], capture_output=True, text=True)
        
        logs = result.stdout
        print(f"Streamlit UI Logs (last 100 lines):\n{logs}")
        
        # Look for connection-related messages
        connection_patterns = [
            "domain agent",
            "connection",
            "endpoint", 
            "health",
            "claims-agent",
            "timeout",
            "refused"
        ]
        
        for pattern in connection_patterns:
            if pattern.lower() in logs.lower():
                print(f"Found connection-related log: '{pattern}'")
    
    def test_streamlit_session_state(self):
        """Test if Streamlit is maintaining incorrect session state"""
        # This would require accessing the Streamlit session, 
        # which is complex to do externally
        print("⚠️ Session state test requires manual browser testing")
        print("Recommendations:")
        print("1. Clear browser cache and cookies")
        print("2. Try incognito mode")
        print("3. Check browser developer tools network tab")


if __name__ == "__main__":
    # Run tests directly
    import sys
    
    # Initialize test classes
    connectivity_tests = TestDomainAgentConnectivity()
    functionality_tests = TestDomainAgentFunctionality()
    ui_tests = TestStreamlitUIBehavior()
    
    print("🧪 Running Domain Agent Connectivity Tests")
    print("=" * 50)
    
    try:
        # Get required fixtures
        streamlit_pod = None
        result = subprocess.run([
            "kubectl", "get", "pods", "-n", "cursor-insurance-ai-poc", 
            "-l", "app=streamlit-ui", "-o", "jsonpath={.items[0].metadata.name}"
        ], capture_output=True, text=True)
        streamlit_pod = result.stdout.strip()
        
        if not streamlit_pod:
            print("❌ No Streamlit UI pod found")
            sys.exit(1)
        
        print(f"Using Streamlit pod: {streamlit_pod}")
        
        # Run connectivity tests
        print("\n🔗 Testing Basic Connectivity...")
        connectivity_tests.test_domain_agent_pods_running()
        connectivity_tests.test_domain_agent_service_exists()
        
        print("\n🏥 Testing Health Endpoints...")
        connectivity_tests.test_domain_agent_health_from_cluster(streamlit_pod)
        connectivity_tests.test_domain_agent_chat_from_cluster(streamlit_pod)
        
        print("\n🎯 Testing Actual UI Client...")
        connectivity_tests.test_streamlit_ui_domain_agent_client(streamlit_pod)
        
        print("\n🌐 Testing Network Layer...")
        connectivity_tests.test_dns_resolution_in_cluster(streamlit_pod)
        connectivity_tests.test_network_connectivity_detailed(streamlit_pod)
        
        print("\n🔧 Testing Domain Agent Functionality...")
        functionality_tests.test_domain_agent_logs_for_errors()
        functionality_tests.test_domain_agent_endpoints_list()
        
        print("\n🖥️ Testing Streamlit UI Behavior...")
        ui_tests.test_streamlit_ui_logs_for_connection_attempts()
        ui_tests.test_streamlit_session_state()
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n✅ All tests completed. Check output above for issues.") 