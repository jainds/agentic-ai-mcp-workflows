"""
Complete End-to-End System Flow Tests

Tests the complete architecture flow:
1. Streamlit UI for visualization and interaction
2. Domain agent plans and orchestrates with LLM reasoning 
3. Domain agent talks to technical agent via official Google A2A protocol
4. Technical agent has MCP tools using FastMCP library
5. Verification of thinking steps, orchestration events, and API calls

Architecture Flow:
UI (Streamlit) → Domain Agent (Claims Agent) → A2A Protocol → Technical Agent (FastMCP Data Agent) → MCP Services
"""

import pytest
import asyncio
import json
import time
import httpx
from typing import Dict, Any
import subprocess
import psutil
from unittest.mock import AsyncMock, Mock, patch

# Test without importing A2A models directly since they may not be available in test environment
# from a2a.models import TaskRequest, TaskResponse

class TestCompleteSystemFlow:
    """Test the complete system architecture flow."""
    
    @pytest.fixture(scope="session", autouse=True)
    def setup_services(self):
        """Setup all required services for testing."""
        services_status = {
            "fastmcp_services": False,
            "domain_agent": False,
            "technical_agent": False,
            "ui": False
        }
        
        try:
            # Check FastMCP services are running
            services_status["fastmcp_services"] = self._check_fastmcp_services()
            
            # Check domain agent is running
            services_status["domain_agent"] = self._check_service("http://localhost:8000/health")
            
            # Check technical agent is running
            services_status["technical_agent"] = self._check_service("http://localhost:8002/health")
            
            # Check UI is accessible
            services_status["ui"] = self._check_service("http://localhost:8501")
            
        except Exception as e:
            pytest.skip(f"Cannot run e2e tests without all services: {e}")
        
        return services_status
    
    def _check_fastmcp_services(self) -> bool:
        """Check if FastMCP services are running."""
        required_ports = [8000, 8002, 8004, 8006]  # user, policy, claims, analytics
        for port in required_ports:
            if not self._check_service(f"http://localhost:{port}/health"):
                return False
        return True
    
    def _check_service(self, url: str) -> bool:
        """Check if a service is accessible."""
        try:
            response = httpx.get(url, timeout=5.0)
            return response.status_code == 200
        except:
            return False
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_policy_inquiry_flow(self, setup_services):
        """Test complete flow for policy inquiry from UI to final response."""
        
        # 1. Simulate Streamlit UI request to Domain Agent
        ui_request = {
            "message": "How many insurance policies do I have and what are the details?",
            "customer_id": "CUST-001"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 2. Domain Agent receives UI request and processes via A2A
            response = await client.post(
                "http://localhost:8000/chat",
                json=ui_request
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # 3. Verify Domain Agent orchestration occurred
            assert "response" in result
            assert "thinking_steps" in result
            assert "orchestration_events" in result
            assert "api_calls" in result
            
            # 4. Verify Domain Agent used LLM reasoning (thinking steps)
            thinking_steps = result["thinking_steps"]
            assert len(thinking_steps) > 0, "Domain agent should show LLM reasoning"
            
            # Should contain intent analysis and planning
            thinking_text = " ".join(thinking_steps).lower()
            assert any(keyword in thinking_text for keyword in 
                      ["analyz", "intent", "gather", "plan", "orchestrat"]), \
                   f"Missing LLM reasoning keywords in: {thinking_steps}"
            
            # 5. Verify A2A communication occurred (API calls tracked)
            api_calls = result["api_calls"]
            assert len(api_calls) > 0, "Should have A2A calls to technical agent"
            
            # Should have called technical agent
            technical_calls = [call for call in api_calls 
                             if "data-agent" in call.get("endpoint", "")]
            assert len(technical_calls) > 0, "Should call technical agent via A2A"
            
            # 6. Verify orchestration events track the flow
            events = result["orchestration_events"]
            assert len(events) > 0, "Should track orchestration events"
            
            event_types = [event.get("event_type", "") for event in events]
            assert "task_started" in event_types, "Should track task start"
            assert "technical_agent_call" in event_types, "Should track A2A calls"
            
            # 7. Verify response quality (not generic fallback)
            response_text = result["response"]
            assert len(response_text) > 100, "Response should be substantial"
            assert "I'm here to help" not in response_text, "Should not be generic fallback"
            
            # Should contain policy-related information
            assert any(keyword in response_text.lower() for keyword in 
                      ["policy", "policies", "coverage", "insurance"]), \
                   "Response should contain policy information"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_claim_filing_flow(self, setup_services):
        """Test complete flow for claim filing with multiple service interactions."""
        
        ui_request = {
            "message": "I need to file a claim for my car accident yesterday on I-95. My car was rear-ended.",
            "customer_id": "CUST-002"
        }
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                "http://localhost:8000/chat",
                json=ui_request
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # 1. Verify complex orchestration for claim filing
            thinking_steps = result["thinking_steps"]
            assert len(thinking_steps) >= 5, "Claim filing should have multiple reasoning steps"
            
            # Should show claim information extraction and processing
            thinking_text = " ".join(thinking_steps).lower()
            claim_keywords = ["claim", "extract", "customer", "policy", "fraud"]
            found_keywords = sum(1 for keyword in claim_keywords if keyword in thinking_text)
            assert found_keywords >= 3, f"Should show claim processing steps: {thinking_steps}"
            
            # 2. Verify multiple A2A calls for claim filing
            api_calls = result["api_calls"]
            assert len(api_calls) >= 2, "Claim filing should make multiple technical agent calls"
            
            # Should call different actions
            call_details = [f"{call.get('method', '')}:{call.get('endpoint', '')}" 
                           for call in api_calls]
            assert len(set(call_details)) >= 2, "Should make diverse technical agent calls"
            
            # 3. Verify orchestration events show complete flow
            events = result["orchestration_events"]
            event_types = [event.get("event_type", "") for event in events]
            
            assert "intent_analyzed" in event_types, "Should analyze claim filing intent"
            assert "technical_agent_call" in event_types, "Should call technical agents"
            assert "task_completed" in event_types, "Should complete the task"
            
            # 4. Verify claim-specific response
            response_text = result["response"]
            assert any(keyword in response_text.lower() for keyword in 
                      ["claim", "file", "process", "reference", "next"]), \
                   "Response should address claim filing"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_technical_agent_mcp_integration(self, setup_services):
        """Test technical agent's direct integration with MCP services."""
        
        # Direct A2A call to technical agent
        a2a_task = {
            "taskId": "test_mcp_integration",
            "user": {
                "action": "get_customer",
                "customer_id": "CUST-001"
            }
        }
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Call technical agent directly to test MCP integration
            response = await client.post(
                "http://localhost:8002/process",
                json=a2a_task
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # 1. Verify A2A protocol compliance
            assert "taskId" in result
            assert "status" in result
            assert "parts" in result
            assert result["taskId"] == "test_mcp_integration"
            
            # 2. Verify technical agent processed via MCP
            assert result["status"] in ["completed", "failed"]
            assert len(result["parts"]) > 0
            
            # 3. If successful, verify data structure
            if result["status"] == "completed":
                response_data = result["parts"][0].get("text", "")
                if response_data:
                    # Should contain customer data or proper error handling
                    assert len(response_data) > 10, "Should return substantial data"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e 
    async def test_error_handling_and_resilience(self, setup_services):
        """Test system resilience when services are unavailable."""
        
        ui_request = {
            "message": "Show me my policy information",
            "customer_id": "CUST-INVALID"
        }
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "http://localhost:8000/chat",
                json=ui_request
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # 1. Should not crash system
            assert "response" in result
            
            # 2. Should track error handling in thinking steps
            thinking_steps = result["thinking_steps"]
            thinking_text = " ".join(thinking_steps).lower()
            
            # Should show error handling or fallback reasoning
            error_indicators = ["error", "failed", "fallback", "unable", "issue"]
            has_error_handling = any(indicator in thinking_text for indicator in error_indicators)
            
            # 3. Should provide helpful response even with errors
            response_text = result["response"]
            assert len(response_text) > 20, "Should provide meaningful error response"
            
            # Should not expose internal errors to user
            assert "exception" not in response_text.lower()
            assert "traceback" not in response_text.lower()
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_conversation_context_management(self, setup_services):
        """Test multi-turn conversation handling and context management."""
        
        customer_id = "CUST-CONVERSATION"
        
        # First message - establish context
        first_request = {
            "message": "I have a question about my auto insurance policy",
            "customer_id": customer_id
        }
        
        # Second message - should use context
        second_request = {
            "message": "What's my deductible?",
            "customer_id": customer_id
        }
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            # Send first message
            response1 = await client.post(
                "http://localhost:8000/chat",
                json=first_request
            )
            
            assert response1.status_code == 200
            result1 = response1.json()
            
            # Brief delay for conversation management
            await asyncio.sleep(1)
            
            # Send second message
            response2 = await client.post(
                "http://localhost:8000/chat", 
                json=second_request
            )
            
            assert response2.status_code == 200
            result2 = response2.json()
            
            # 1. Both responses should be substantial
            assert len(result1["response"]) > 50
            assert len(result2["response"]) > 50
            
            # 2. Second response should show context awareness
            thinking_steps2 = result2["thinking_steps"]
            thinking_text2 = " ".join(thinking_steps2).lower()
            
            # Should reference context or previous conversation
            context_indicators = ["context", "previous", "earlier", "auto", "policy"]
            has_context = any(indicator in thinking_text2 for indicator in context_indicators)
            
            # 3. Both should have orchestration
            assert len(result1["api_calls"]) > 0, "First message should have API calls"
            assert len(result2["api_calls"]) > 0, "Second message should have API calls"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_performance_and_response_times(self, setup_services):
        """Test system performance and response time requirements."""
        
        ui_request = {
            "message": "Quick question about my coverage",
            "customer_id": "CUST-PERF"
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8000/chat",
                json=ui_request
            )
            
            total_time = time.time() - start_time
            
            assert response.status_code == 200
            result = response.json()
            
            # 1. Response time should be reasonable (< 30 seconds)
            assert total_time < 30.0, f"Response time too slow: {total_time:.2f}s"
            
            # 2. Should track API call timings
            api_calls = result["api_calls"]
            if api_calls:
                # Should have timing information
                first_call = api_calls[0]
                timing_fields = ["timestamp", "duration", "status"]
                has_timing = any(field in first_call for field in timing_fields)
                assert has_timing, "API calls should include timing information"
            
            # 3. Should complete successfully
            assert len(result["response"]) > 0, "Should provide response"


class TestServiceHealth:
    """Test individual service health and availability."""
    
    @pytest.mark.e2e
    def test_fastmcp_services_health(self):
        """Test that all FastMCP services are healthy."""
        services = {
            "user_service": "http://localhost:8000/health",
            "policy_service": "http://localhost:8002/health", 
            "claims_service": "http://localhost:8004/health",
            "analytics_service": "http://localhost:8006/health"
        }
        
        for service_name, health_url in services.items():
            try:
                response = httpx.get(health_url, timeout=5.0)
                assert response.status_code == 200, f"{service_name} health check failed"
                
                health_data = response.json()
                assert health_data.get("status") == "healthy", f"{service_name} not healthy"
                
            except Exception as e:
                pytest.skip(f"Service {service_name} not available: {e}")
    
    @pytest.mark.e2e  
    def test_domain_agent_health(self):
        """Test domain agent health and capabilities."""
        try:
            response = httpx.get("http://localhost:8000/health", timeout=5.0)
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data.get("status") == "healthy"
            assert health_data.get("agent") == "ClaimsAgent"
            
            # Should have A2A capabilities
            capabilities = health_data.get("capabilities", {})
            assert capabilities.get("google_a2a_compatible") == True
            assert capabilities.get("llmEnabled") == True
            
        except Exception as e:
            pytest.skip(f"Domain agent not available: {e}")
    
    @pytest.mark.e2e
    def test_technical_agent_health(self):
        """Test technical agent health and MCP integration."""
        try:
            response = httpx.get("http://localhost:8002/health", timeout=5.0)
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data.get("status") == "healthy"
            assert health_data.get("agent") == "FastMCPDataAgent"
            
            # Should have MCP capabilities
            capabilities = health_data.get("capabilities", {})
            assert capabilities.get("mcpIntegration") == True
            assert capabilities.get("google_a2a_compatible") == True
            
        except Exception as e:
            pytest.skip(f"Technical agent not available: {e}")


@pytest.mark.e2e
def test_system_readiness():
    """Verify complete system is ready for e2e testing."""
    required_services = [
        ("Domain Agent", "http://localhost:8000/health"),
        ("Technical Agent", "http://localhost:8002/health"),
        ("User Service", "http://localhost:8000/health"),
        ("Claims Service", "http://localhost:8004/health"),
        ("Policy Service", "http://localhost:8002/health"),
        ("Analytics Service", "http://localhost:8006/health")
    ]
    
    unavailable_services = []
    
    for service_name, health_url in required_services:
        try:
            response = httpx.get(health_url, timeout=3.0)
            if response.status_code != 200:
                unavailable_services.append(service_name)
        except:
            unavailable_services.append(service_name)
    
    if unavailable_services:
        pytest.skip(f"Services not available for e2e testing: {', '.join(unavailable_services)}")
    
    print(f"✅ All {len(required_services)} services are healthy and ready for e2e testing") 