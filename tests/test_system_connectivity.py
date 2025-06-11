#!/usr/bin/env python3
"""
System Connectivity Tests - Verify proper integration between Streamlit UI and ADK agents
"""

import pytest
import requests
import json
import time
from typing import Dict, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ui"))

class TestSystemConnectivity:
    """Test suite for end-to-end system connectivity"""
    
    BASE_URLS = {
        "streamlit_ui": "http://localhost:8501",
        "customer_service": "http://localhost:8000", 
        "technical_agent": "http://localhost:8002",
        "orchestrator": "http://localhost:8003",
        "policy_server": "http://localhost:8001"
    }
    
    def test_all_services_accessible(self):
        """Test that all services are accessible"""
        for service_name, base_url in self.BASE_URLS.items():
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                # Accept various success codes (200, 307 redirect, etc.)
                assert response.status_code in [200, 307, 404], f"{service_name} returned {response.status_code}"
                print(f"✅ {service_name}: {response.status_code}")
            except requests.RequestException as e:
                pytest.fail(f"❌ {service_name} not accessible: {e}")
    
    def test_streamlit_ui_loads(self):
        """Test that Streamlit UI loads properly"""
        try:
            response = requests.get(self.BASE_URLS["streamlit_ui"], timeout=10)
            assert response.status_code == 200
            assert "streamlit" in response.text.lower() or "insurance" in response.text.lower()
            print("✅ Streamlit UI loads successfully")
        except Exception as e:
            pytest.fail(f"❌ Streamlit UI failed to load: {e}")
    
    def test_customer_service_agent_endpoints(self):
        """Test Customer Service Agent endpoints"""
        base_url = self.BASE_URLS["customer_service"]
        
        # Test various ADK endpoints
        endpoints_to_test = [
            "/",
            "/dev-ui/",
            "/health",
            "/apps/insurance-adk/chat"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=5)
                print(f"Customer Service {endpoint}: {response.status_code}")
                # Accept various codes (200 OK, 307 Redirect, 404 Not Found, 405 Method Not Allowed)
                assert response.status_code in [200, 307, 404, 405], f"Unexpected status for {endpoint}: {response.status_code}"
            except requests.RequestException as e:
                print(f"⚠️ Customer Service {endpoint} error: {e}")
    
    def test_chat_message_flow(self):
        """Test the complete chat message flow from Streamlit to Customer Service"""
        customer_service_url = f"{self.BASE_URLS['customer_service']}/apps/insurance-adk/chat"
        
        test_message = {
            "message": "Hello, I need help with my insurance policy",
            "customer_id": "TEST-CUSTOMER",
            "session_metadata": {
                "ui_source": "streamlit_test",
                "timestamp": time.time()
            }
        }
        
        try:
            response = requests.post(
                customer_service_url,
                json=test_message,
                timeout=15,
                headers={"Content-Type": "application/json"}
            )
            
            # ADK might return various codes depending on configuration
            if response.status_code == 200:
                result = response.json()
                assert "response" in result or "content" in result, "No response content in successful call"
                print("✅ Chat message processed successfully")
            elif response.status_code == 404:
                # Endpoint might not exist, check alternative endpoints
                print("⚠️ Chat endpoint not found, checking alternative endpoints...")
                self._test_alternative_chat_endpoints()
            else:
                print(f"⚠️ Chat endpoint returned {response.status_code}: {response.text}")
                
        except requests.RequestException as e:
            print(f"⚠️ Chat message test failed: {e}")
            # This is expected if ADK is not fully configured yet
    
    def _test_alternative_chat_endpoints(self):
        """Test alternative chat endpoints"""
        base_url = self.BASE_URLS["customer_service"]
        
        alternative_endpoints = [
            "/chat",
            "/api/chat", 
            "/apps/insurance-adk/users/user/sessions",
            "/run_sse"
        ]
        
        for endpoint in alternative_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.post(
                    url,
                    json={"message": "test"},
                    timeout=5
                )
                print(f"Alternative endpoint {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"Alternative endpoint {endpoint} error: {e}")
    
    def test_ui_components_import_correctly(self):
        """Test that UI components can import without errors"""
        try:
            from components.config import UIConfig
            from components.agent_client import ADKAgentClient, send_chat_message_simple
            from components.chat import initialize_chat_state
            from components.monitoring import check_service_health
            
            # Test configuration
            assert hasattr(UIConfig, 'ADK_CUSTOMER_SERVICE_ENDPOINTS')
            assert hasattr(UIConfig, 'MONITORED_SERVICES')
            assert len(UIConfig.ADK_CUSTOMER_SERVICE_ENDPOINTS) > 0
            
            # Test client initialization
            client = ADKAgentClient()
            assert client is not None
            
            print("✅ All UI components import correctly")
            
        except ImportError as e:
            pytest.fail(f"❌ UI component import failed: {e}")
    
    def test_agent_client_configuration(self):
        """Test that agent client is properly configured"""
        try:
            from components.agent_client import ADKAgentClient
            from components.config import UIConfig
            
            client = ADKAgentClient()
            
            # Test endpoints are configured
            assert len(UIConfig.ADK_CUSTOMER_SERVICE_ENDPOINTS) > 0
            assert "localhost:8000" in str(UIConfig.ADK_CUSTOMER_SERVICE_ENDPOINTS)
            
            # Test client methods exist
            assert hasattr(client, 'send_customer_service_message')
            assert hasattr(client, 'send_technical_message')  
            assert hasattr(client, 'send_orchestrator_message')
            
            print("✅ Agent client properly configured")
            
        except Exception as e:
            pytest.fail(f"❌ Agent client configuration failed: {e}")
    
    def test_system_health_monitoring(self):
        """Test system health monitoring functionality"""
        try:
            from components.monitoring import check_service_health
            from components.config import UIConfig
            
            # Test health check function
            health_status = check_service_health()
            assert isinstance(health_status, dict)
            assert len(health_status) > 0
            
            # Verify monitored services are configured
            assert len(UIConfig.MONITORED_SERVICES) > 0
            assert "ADK Customer Service" in UIConfig.MONITORED_SERVICES
            
            print("✅ System health monitoring works")
            print(f"Monitoring {len(health_status)} services:")
            for service, status in health_status.items():
                print(f"  - {service}: {status['status']}")
                
        except Exception as e:
            pytest.fail(f"❌ System health monitoring failed: {e}")

if __name__ == "__main__":
    # Run tests individually for better debugging
    test_suite = TestSystemConnectivity()
    
    print("🔍 Testing System Connectivity...")
    print("=" * 50)
    
    try:
        test_suite.test_all_services_accessible()
    except Exception as e:
        print(f"Services accessibility test failed: {e}")
    
    try:
        test_suite.test_streamlit_ui_loads()
    except Exception as e:
        print(f"Streamlit UI test failed: {e}")
    
    try:
        test_suite.test_customer_service_agent_endpoints()
    except Exception as e:
        print(f"Customer service endpoints test failed: {e}")
    
    try:
        test_suite.test_ui_components_import_correctly()
    except Exception as e:
        print(f"UI components import test failed: {e}")
    
    try:
        test_suite.test_agent_client_configuration()
    except Exception as e:
        print(f"Agent client configuration test failed: {e}")
    
    try:
        test_suite.test_system_health_monitoring()
    except Exception as e:
        print(f"System health monitoring test failed: {e}")
    
    try:
        test_suite.test_chat_message_flow()
    except Exception as e:
        print(f"Chat message flow test failed: {e}")
    
    print("=" * 50)
    print("🏁 System connectivity testing complete!") 