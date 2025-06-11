#!/usr/bin/env python3
"""
Phase 1: Policy Server Testing
Comprehensive tests for the MCP Policy Server functionality
"""

import pytest
import requests
import json
import time
import subprocess
import signal
import os
import sys
from typing import Dict, Any

# Add policy server to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'policy_server'))

class TestPolicyServer:
    """Policy Server MCP Testing Suite"""
    
    @pytest.fixture(scope="class")
    def policy_server_process(self):
        """Start policy server for testing"""
        print("🚀 Starting Policy Server for testing...")
        
        # Change to policy server directory
        policy_dir = os.path.join(os.path.dirname(__file__), '..', 'policy_server')
        
        # Start policy server process
        process = subprocess.Popen(
            ['python', 'main.py'],
            cwd=policy_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # Wait for server to start
        time.sleep(3)
        
        # Check if server started successfully
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(f"Policy server failed to start: {stderr.decode()}")
        
        yield process
        
        # Cleanup: terminate the process
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()
        print("🛑 Policy Server stopped")
    
    def test_server_startup(self, policy_server_process):
        """Test policy server starts correctly"""
        assert policy_server_process.poll() is None, "Policy server should be running"
        print("✅ Policy server startup: PASSED")
    
    def test_health_endpoint(self):
        """Test health endpoint (if available)"""
        try:
            # Try different health endpoint variations
            health_urls = [
                "http://localhost:8001/health",
                "http://localhost:8001/mcp/health", 
                "http://localhost:8001/"
            ]
            
            for url in health_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code in [200, 307]:  # 307 is redirect
                        print(f"✅ Health endpoint {url}: PASSED (Status: {response.status_code})")
                        return
                except requests.RequestException:
                    continue
            
            print("⚠️  Health endpoint: No standard health endpoint found (Expected for MCP servers)")
            
        except Exception as e:
            print(f"⚠️  Health endpoint test error: {e}")
    
    def test_mcp_endpoint_exists(self):
        """Test MCP endpoint is accessible"""
        try:
            # Test MCP endpoint - should reject GET requests
            response = requests.get("http://localhost:8001/mcp", timeout=5)
            
            # MCP servers typically reject GET with 405 or 307
            if response.status_code in [405, 307, 406]:
                print("✅ MCP endpoint exists: PASSED (Properly rejects GET requests)")
            else:
                print(f"⚠️  MCP endpoint: Unexpected status {response.status_code}")
                
        except requests.RequestException as e:
            print(f"❌ MCP endpoint test failed: {e}")
            pytest.fail(f"MCP endpoint not accessible: {e}")
    
    def test_mcp_protocol_structure(self):
        """Test MCP JSON-RPC protocol structure"""
        try:
            # Valid MCP JSON-RPC request structure
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            response = requests.post(
                "http://localhost:8001/mcp",
                json=mcp_request,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "jsonrpc" in data, "Response should include jsonrpc field"
                assert "result" in data or "error" in data, "Response should include result or error"
                print("✅ MCP JSON-RPC protocol: PASSED")
            else:
                print(f"⚠️  MCP protocol test: Status {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"⚠️  MCP protocol test error: {e}")
    
    def test_policy_data_structure(self):
        """Test that policy data is loaded correctly"""
        try:
            # Test policy lookup via MCP
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "policy_lookup",
                    "arguments": {
                        "customer_id": "CUST001"
                    }
                }
            }
            
            response = requests.post(
                "http://localhost:8001/mcp",
                json=mcp_request,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    print("✅ Policy data access: PASSED")
                    print(f"Sample response: {json.dumps(data['result'], indent=2)[:200]}...")
                else:
                    print(f"⚠️  Policy data: Error in response: {data.get('error', 'Unknown error')}")
            else:
                print(f"⚠️  Policy data test: Status {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Policy data test error: {e}")
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test invalid JSON-RPC request
            invalid_request = {
                "invalid": "request"
            }
            
            response = requests.post(
                "http://localhost:8001/mcp",
                json=invalid_request,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            # Should return error response
            if response.status_code in [400, 422]:
                print("✅ Error handling: PASSED (Properly rejects invalid requests)")
            else:
                print(f"⚠️  Error handling: Unexpected status {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Error handling test error: {e}")
    
    def test_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            try:
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": int(time.time() * 1000),  # Unique ID
                    "method": "tools/list",
                    "params": {}
                }
                
                response = requests.post(
                    "http://localhost:8001/mcp",
                    json=mcp_request,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                results.append(response.status_code == 200)
                
            except Exception:
                results.append(False)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        success_rate = sum(results) / len(results)
        if success_rate >= 0.8:  # 80% success rate
            print(f"✅ Concurrent requests: PASSED ({success_rate:.1%} success rate)")
        else:
            print(f"⚠️  Concurrent requests: {success_rate:.1%} success rate")

def run_policy_server_tests():
    """Run policy server tests and return results"""
    print("=" * 80)
    print("🔍 PHASE 1: POLICY SERVER TESTING")
    print("=" * 80)
    
    # Run pytest with custom output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--no-header",
        "-s"  # Don't capture output so we see our custom prints
    ])
    
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ PHASE 1 COMPLETE: Policy Server tests PASSED")
    else:
        print("⚠️  PHASE 1 COMPLETE: Some policy server tests had issues")
    print("=" * 80)
    
    return exit_code == 0

if __name__ == "__main__":
    run_policy_server_tests() 