import pytest
import asyncio
import httpx
import json
from typing import Dict, Any, List
from datetime import datetime, date


class TestE2EWorkflows:
    """End-to-end integration tests for insurance AI PoC workflows"""
    
    @pytest.fixture(scope="class")
    def base_urls(self):
        """Base URLs for services"""
        return {
            "customer_service": "http://localhost:30000",
            "support_agent": "http://localhost:30005", 
            "claims_agent": "http://localhost:30007",
            "customer_agent": "http://localhost:8010",
            "policy_agent": "http://localhost:8011",
            "claims_data_agent": "http://localhost:8012"
        }
    
    @pytest.fixture(scope="class")
    async def http_client(self):
        """HTTP client for making requests"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client
    
    @pytest.fixture(scope="class")
    def test_customer(self):
        """Test customer data"""
        return {
            "customer_id": 101,
            "name": "Alice Johnson",
            "policy_ids": [202, 203]
        }
    
    @pytest.fixture(scope="class")
    def test_policy(self):
        """Test policy data"""
        return {
            "policy_id": 202,
            "policy_number": "POL-AUTO-202401-001",
            "status": "active"
        }

    async def test_service_health_checks(self, http_client, base_urls):
        """Test that all services are healthy"""
        services = ["customer_service", "support_agent", "claims_agent"]
        
        for service in services:
            url = f"{base_urls[service]}/health"
            response = await http_client.get(url)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data

    async def test_customer_service_basic_operations(self, http_client, base_urls, test_customer):
        """Test customer service basic operations"""
        base_url = base_urls["customer_service"]
        
        # Test get customer
        response = await http_client.get(f"{base_url}/customer/{test_customer['customer_id']}")
        assert response.status_code == 200
        
        customer_data = response.json()
        assert customer_data["customer_id"] == test_customer["customer_id"]
        assert customer_data["first_name"] == "Alice"
        assert customer_data["last_name"] == "Johnson"
        
        # Test customer summary
        response = await http_client.get(f"{base_url}/customer/{test_customer['customer_id']}/summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert summary["full_name"] == test_customer["name"]
        assert summary["policy_count"] == len(test_customer["policy_ids"])

    async def test_policy_status_inquiry_workflow(self, http_client, base_urls, test_customer):
        """Test complete policy status inquiry workflow through support agent"""
        support_url = base_urls["support_agent"]
        
        # Customer asks about policy status
        message = "What is the status of my policies?"
        
        chat_request = {
            "message": message,
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{support_url}/chat", json=chat_request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "response" in result
        assert "policy" in result["response"].lower() or "active" in result["response"].lower()
        assert result["workflow"] == "policy_inquiry"
        
        # Verify data was gathered
        assert "data" in result
        assert "customer" in result["data"]
        assert "policies" in result["data"]
        
        customer_data = result["data"]["customer"]
        assert customer_data["customer_id"] == test_customer["customer_id"]

    async def test_claim_filing_workflow(self, http_client, base_urls, test_customer):
        """Test complete claim filing workflow through claims domain agent"""
        claims_url = base_urls["claims_agent"]
        
        # Customer wants to file a claim
        message = "I want to file a claim for a car accident that happened on January 15th, 2024 at the intersection of Main St and Oak Ave. My car was rear-ended and has damage to the bumper."
        
        chat_request = {
            "message": message,
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{claims_url}/chat", json=chat_request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "response" in result
        
        # Check if claim was filed or if more information is needed
        if result.get("workflow") == "claim_filing":
            if result.get("next_action") == "collect_claim_details":
                # Agent needs more information
                assert "missing_fields" in result
            else:
                # Claim was successfully filed
                assert "data" in result
                assert "claim" in result["data"]
                claim_data = result["data"]["claim"]
                assert "claim_id" in claim_data
                assert "claim_number" in claim_data

    async def test_claim_status_inquiry_workflow(self, http_client, base_urls, test_customer):
        """Test claim status inquiry workflow"""
        claims_url = base_urls["claims_agent"]
        
        # Customer asks about claim status
        message = "What is the status of my claims?"
        
        chat_request = {
            "message": message,
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{claims_url}/chat", json=chat_request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "response" in result
        assert result["workflow"] == "claim_status"
        
        # Check if claims were found
        if "data" in result and "claims" in result["data"]:
            claims = result["data"]["claims"]
            if claims:
                # Verify claim structure
                for claim in claims:
                    assert "claim_id" in claim
                    assert "status" in claim

    async def test_general_support_workflow(self, http_client, base_urls, test_customer):
        """Test general support inquiry workflow"""
        support_url = base_urls["support_agent"]
        
        # Customer asks a general question
        message = "What types of coverage do you offer?"
        
        chat_request = {
            "message": message,
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{support_url}/chat", json=chat_request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "response" in result
        assert result["workflow"] == "general_support"
        
        # Response should be helpful and mention insurance concepts
        response_text = result["response"].lower()
        insurance_terms = ["coverage", "policy", "insurance", "protection", "premium"]
        assert any(term in response_text for term in insurance_terms)

    async def test_agent_skill_discovery(self, http_client, base_urls):
        """Test that agents expose their skills correctly"""
        agents = ["support_agent", "claims_agent"]
        
        for agent in agents:
            url = f"{base_urls[agent]}/skills"
            response = await http_client.get(url)
            assert response.status_code == 200
            
            skills_data = response.json()
            assert "agent" in skills_data
            assert "skills" in skills_data
            
            skills = skills_data["skills"]
            assert isinstance(skills, dict)
            assert len(skills) > 0
            
            # Each skill should have required metadata
            for skill_name, skill_info in skills.items():
                assert "name" in skill_info
                assert "description" in skill_info
                assert "agent" in skill_info

    async def test_a2a_communication(self, http_client, base_urls, test_customer):
        """Test A2A communication between domain and technical agents"""
        support_url = base_urls["support_agent"]
        
        # Execute a skill that requires A2A communication
        execute_request = {
            "skill_name": "CheckPolicyStatus",
            "parameters": {
                "policy_id": 202,
                "customer_id": test_customer["customer_id"]
            },
            "sender": "test_client"
        }
        
        response = await http_client.post(f"{support_url}/execute", json=execute_request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "result" in result
        
        # Verify policy information was retrieved
        policy_info = result["result"]
        assert "policy_id" in policy_info
        assert "status" in policy_info

    async def test_customer_journey_complete_flow(self, http_client, base_urls, test_customer):
        """Test complete customer journey from inquiry to claim filing"""
        support_url = base_urls["support_agent"]
        claims_url = base_urls["claims_agent"]
        
        # Step 1: Customer asks about policies
        policy_request = {
            "message": "Can you tell me about my current policies?",
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{support_url}/chat", json=policy_request)
        assert response.status_code == 200
        
        policy_result = response.json()
        assert policy_result["success"] is True
        assert "policies" in policy_result.get("data", {})
        
        # Step 2: Customer files a claim
        claim_request = {
            "message": "I need to file a claim for water damage in my basement from a burst pipe on January 10th",
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{claims_url}/chat", json=claim_request)
        assert response.status_code == 200
        
        claim_result = response.json()
        assert claim_result["success"] is True
        
        # Step 3: Customer checks claim status (if claim was filed)
        if claim_result.get("data", {}).get("claim_id"):
            claim_id = claim_result["data"]["claim_id"]
            
            status_request = {
                "message": f"What is the status of claim {claim_id}?",
                "customer_id": test_customer["customer_id"],
                "claim_id": claim_id
            }
            
            response = await http_client.post(f"{claims_url}/chat", json=status_request)
            assert response.status_code == 200
            
            status_result = response.json()
            assert status_result["success"] is True

    async def test_error_handling(self, http_client, base_urls):
        """Test error handling in various scenarios"""
        support_url = base_urls["support_agent"]
        
        # Test with invalid customer ID
        invalid_request = {
            "message": "What are my policies?",
            "customer_id": 99999
        }
        
        response = await http_client.post(f"{support_url}/chat", json=invalid_request)
        assert response.status_code == 200
        
        result = response.json()
        # Should handle gracefully, either with success=False or appropriate error message
        if not result.get("success", True):
            assert "error" in result or "not found" in result.get("response", "").lower()

    async def test_concurrent_requests(self, http_client, base_urls, test_customer):
        """Test system behavior under concurrent requests"""
        support_url = base_urls["support_agent"]
        
        # Create multiple concurrent requests
        requests = [
            {
                "message": f"Request {i}: What is my policy status?",
                "customer_id": test_customer["customer_id"]
            }
            for i in range(5)
        ]
        
        # Send all requests concurrently
        tasks = [
            http_client.post(f"{support_url}/chat", json=req)
            for req in requests
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            result = response.json()
            # Should either succeed or fail gracefully
            assert "success" in result

    async def test_data_consistency(self, http_client, base_urls, test_customer, test_policy):
        """Test data consistency across services"""
        customer_url = base_urls["customer_service"]
        support_url = base_urls["support_agent"]
        
        # Get customer data directly from service
        response = await http_client.get(f"{customer_url}/customer/{test_customer['customer_id']}")
        assert response.status_code == 200
        direct_customer = response.json()
        
        # Get customer data through support agent
        chat_request = {
            "message": "What is my account information?",
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{support_url}/chat", json=chat_request)
        assert response.status_code == 200
        
        agent_result = response.json()
        if agent_result.get("success") and "data" in agent_result:
            agent_customer = agent_result["data"].get("customer", {})
            
            # Verify consistency
            if agent_customer:
                assert agent_customer["customer_id"] == direct_customer["customer_id"]

    @pytest.mark.performance
    async def test_response_times(self, http_client, base_urls, test_customer):
        """Test response times for critical workflows"""
        support_url = base_urls["support_agent"]
        
        # Measure response time for policy inquiry
        start_time = datetime.now()
        
        chat_request = {
            "message": "What is my policy status?",
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{support_url}/chat", json=chat_request)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        assert response.status_code == 200
        # Response should be under 10 seconds for normal operation
        assert response_time < 10.0, f"Response time {response_time}s exceeds 10s threshold"

    async def test_system_integration_flow(self, http_client, base_urls, test_customer):
        """Test complete system integration across all components"""
        # This test verifies the entire architecture works together:
        # Customer Service -> Technical Agents -> Domain Agents -> LLM -> A2A -> MCP
        
        support_url = base_urls["support_agent"]
        
        # Complex request that requires multiple service calls
        complex_request = {
            "message": "I'm Alice Johnson, customer ID 101. Can you give me a complete overview of my account including my policies and any recent claims?",
            "customer_id": test_customer["customer_id"]
        }
        
        response = await http_client.post(f"{support_url}/chat", json=complex_request)
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is True
        assert "response" in result
        
        # Response should contain comprehensive information
        response_text = result["response"].lower()
        expected_terms = ["policy", "customer", "account"]
        assert any(term in response_text for term in expected_terms)
        
        # Verify complete data flow worked
        if "data" in result:
            data = result["data"]
            # Should have customer information (from CustomerDataAgent)
            # Should have policy information (from PolicyDataAgent)  
            # Should have integrated this through SupportDomainAgent
            # And generated natural language response via LLM
            assert isinstance(data, dict)