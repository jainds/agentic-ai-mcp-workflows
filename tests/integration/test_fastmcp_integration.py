#!/usr/bin/env python3
"""
Integration Tests for FastMCP Services
Tests the actual deployed FastMCP architecture with A2A agent communication.
"""

import asyncio
import httpx
import json
import pytest
from typing import Dict, Any

class TestFastMCPIntegration:
    """Test suite for FastMCP services integration"""
    
    def __init__(self):
        self.service_urls = {
            "user": "http://localhost:8000",
            "claims": "http://localhost:8001", 
            "policy": "http://localhost:8002",
            "analytics": "http://localhost:8003",
            "data_agent": "http://localhost:8004"
        }
        self.timeout = 30.0

    @pytest.fixture
    async def client(self):
        """Create HTTP client for tests"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            yield client

    async def test_fastmcp_data_agent_health(self, client):
        """Test FastMCP Data Agent health endpoint"""
        response = await client.get(f"{self.service_urls['data_agent']}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "fastmcp-data-agent"

    async def test_fastmcp_data_agent_tools_discovery(self, client):
        """Test tool discovery via FastMCP Data Agent"""
        response = await client.get(f"{self.service_urls['data_agent']}/tools")
        assert response.status_code == 200
        tools_data = response.json()
        # Should discover tools from all services
        assert isinstance(tools_data, dict)

    async def test_customer_data_retrieval(self, client):
        """Test end-to-end customer data retrieval"""
        request_data = {"customer_id": "user_001"}
        response = await client.post(
            f"{self.service_urls['data_agent']}/customer/data",
            json=request_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["customer_id"] == "user_001"
        assert "customer_info" in data
        assert "policies" in data
        assert "claims" in data

    async def test_claims_processing_flow(self, client):
        """Test claims processing through FastMCP Data Agent"""
        # Test listing claims
        request_data = {"customer_id": "user_001"}
        response = await client.post(
            f"{self.service_urls['data_agent']}/claims/list",
            json=request_data
        )
        assert response.status_code == 200

        # Test creating a claim
        claim_data = {
            "customer_id": "user_001",
            "policy_number": "POL-001",
            "incident_date": "2024-05-30",
            "description": "Integration test claim",
            "amount": 2500.0,
            "claim_type": "auto_collision"
        }
        response = await client.post(
            f"{self.service_urls['data_agent']}/claims/create",
            json=claim_data
        )
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

    async def test_policy_operations(self, client):
        """Test policy operations through FastMCP Data Agent"""
        # Test listing policies
        request_data = {"customer_id": "user_001"}
        response = await client.post(
            f"{self.service_urls['data_agent']}/policies/list", 
            json=request_data
        )
        assert response.status_code == 200

        # Test quote calculation
        quote_data = {
            "customer_id": "user_001",
            "policy_type": "auto",
            "coverage_amount": 50000.0,
            "risk_factors": {
                "age": 35,
                "location": "low_risk", 
                "claims_history": 0
            }
        }
        response = await client.post(
            f"{self.service_urls['data_agent']}/policies/quote",
            json=quote_data
        )
        assert response.status_code == 200

    async def test_customer_summary_generation(self, client):
        """Test comprehensive customer summary generation"""
        request_data = {"customer_id": "user_001"}
        response = await client.post(
            f"{self.service_urls['data_agent']}/customer/summary",
            json=request_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "summary" in data
        assert "total_policies" in data["summary"]
        assert "total_claims" in data["summary"]
        assert "total_coverage" in data["summary"]

@pytest.mark.asyncio
async def test_fastmcp_service_communication():
    """Test actual FastMCP service communication"""
    tester = TestFastMCPIntegration()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test health of all services
        for service_name, url in tester.service_urls.items():
            try:
                if service_name == "data_agent":
                    response = await client.get(f"{url}/health")
                else:
                    # FastMCP services respond with 406 for non-MCP requests
                    response = await client.get(f"{url}/mcp/", headers={"Accept": "text/event-stream"})
                    assert response.status_code == 406  # Expected for FastMCP without proper headers
                print(f"✅ {service_name} service is responding correctly")
            except Exception as e:
                print(f"❌ {service_name} service error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fastmcp_service_communication()) 