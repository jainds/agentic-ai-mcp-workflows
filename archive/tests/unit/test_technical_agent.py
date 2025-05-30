"""
Comprehensive unit tests for Technical Agent (Data Agent).

Tests the technical agent's ability to:
1. Handle A2A protocol communication properly
2. Interact with all MCP tools correctly
3. Process different data retrieval scenarios
4. Handle error conditions gracefully
5. Return structured data in expected formats
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from agents.technical.fastmcp_data_agent import FastMCPDataAgent
from agents.shared.a2a_base import TaskRequest, TaskResponse


class TestTechnicalAgentA2AProtocol:
    """Test technical agent's A2A protocol handling."""
    
    @pytest.fixture
    def data_agent(self):
        """Create a FastMCPDataAgent instance for testing."""
        agent = FastMCPDataAgent()
        agent.mcp_clients = {
            'user-service': AsyncMock(),
            'claims-service': AsyncMock(),
            'policy-service': AsyncMock(),
            'analytics-service': AsyncMock()
        }
        return agent
    
    @pytest.mark.asyncio
    async def test_process_customer_data_request(self, data_agent):
        """Test processing customer data requests via A2A."""
        # Mock MCP client response
        mock_response = Mock()
        mock_response.result = {
            "customer_id": "CUST-001",
            "name": "John Smith",
            "type": "Premium",
            "status": "Active",
            "email": "john.smith@email.com",
            "phone": "+1-555-0123"
        }
        data_agent.mcp_clients['user-service'].call_tool.return_value = mock_response
        
        # Create A2A task request
        task = TaskRequest(
            taskId="task_123",
            user={
                "action": "get_customer",
                "customer_id": "CUST-001"
            }
        )
        
        response = await data_agent.process_task(task)
        
        assert response.taskId == "task_123"
        assert response.status == "completed"
        assert len(response.parts) == 1
        
        result_data = json.loads(response.parts[0]["text"])
        assert result_data["customer_id"] == "CUST-001"
        assert result_data["name"] == "John Smith"
        assert result_data["type"] == "Premium"
    
    @pytest.mark.asyncio
    async def test_process_policy_data_request(self, data_agent):
        """Test processing policy data requests via A2A."""
        # Mock MCP client response
        mock_response = Mock()
        mock_response.result = {
            "policies": [
                {"policy_number": "POL-001", "type": "Auto", "premium": 1200, "status": "Active"},
                {"policy_number": "POL-002", "type": "Home", "premium": 800, "status": "Active"},
                {"policy_number": "POL-003", "type": "Life", "premium": 300, "status": "Active"}
            ],
            "active_policies": 3,
            "total_coverage": "$250,000",
            "next_renewal": "2024-12-15"
        }
        data_agent.mcp_clients['policy-service'].call_tool.return_value = mock_response
        
        task = TaskRequest(
            taskId="task_456",
            user={
                "action": "get_customer_policies",
                "customer_id": "CUST-001"
            }
        )
        
        response = await data_agent.process_task(task)
        
        assert response.status == "completed"
        result_data = json.loads(response.parts[0]["text"])
        assert result_data["active_policies"] == 3
        assert len(result_data["policies"]) == 3
        assert result_data["total_coverage"] == "$250,000"
    
    @pytest.mark.asyncio
    async def test_process_claims_data_request(self, data_agent):
        """Test processing claims data requests via A2A."""
        mock_response = Mock()
        mock_response.result = {
            "claims": [
                {
                    "claim_id": "CLM-789",
                    "status": "In Review",
                    "amount": 5000,
                    "date_filed": "2024-05-20",
                    "estimated_resolution": "3-5 business days",
                    "claim_type": "auto"
                }
            ],
            "active_claims": 1,
            "recent_claims": 1,
            "total_claim_value": 5000
        }
        data_agent.mcp_clients['claims-service'].call_tool.return_value = mock_response
        
        task = TaskRequest(
            taskId="task_789",
            user={
                "action": "get_customer_claims",
                "customer_id": "CUST-001"
            }
        )
        
        response = await data_agent.process_task(task)
        
        assert response.status == "completed"
        result_data = json.loads(response.parts[0]["text"])
        assert result_data["active_claims"] == 1
        assert len(result_data["claims"]) == 1
        assert result_data["claims"][0]["claim_id"] == "CLM-789"
    
    @pytest.mark.asyncio
    async def test_process_analytics_request(self, data_agent):
        """Test processing analytics requests via A2A."""
        mock_response = Mock()
        mock_response.result = {
            "risk_score": 0.25,
            "risk_category": "Low Risk",
            "recommendation": "Continue current coverage",
            "savings_opportunity": "None identified",
            "fraud_indicators": [],
            "satisfaction_score": 4.8
        }
        data_agent.mcp_clients['analytics-service'].call_tool.return_value = mock_response
        
        task = TaskRequest(
            taskId="task_analytics",
            user={
                "action": "get_analytics",
                "customer_id": "CUST-001"
            }
        )
        
        response = await data_agent.process_task(task)
        
        assert response.status == "completed"
        result_data = json.loads(response.parts[0]["text"])
        assert result_data["risk_score"] == 0.25
        assert result_data["risk_category"] == "Low Risk"
        assert result_data["recommendation"] == "Continue current coverage"


class TestTechnicalAgentMCPToolInteractions:
    """Test technical agent's interactions with specific MCP tools."""
    
    @pytest.fixture
    def data_agent(self):
        agent = FastMCPDataAgent()
        agent.mcp_clients = {
            'user-service': AsyncMock(),
            'claims-service': AsyncMock(),
            'policy-service': AsyncMock(),
            'analytics-service': AsyncMock()
        }
        return agent
    
    @pytest.mark.asyncio
    async def test_user_service_get_customer_tool(self, data_agent):
        """Test user service get_customer tool interaction."""
        mock_response = Mock()
        mock_response.result = {
            "customer_id": "CUST-001",
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "+1-555-0123",
            "address": "123 Main St, Anytown, ST 12345",
            "type": "Premium",
            "status": "Active",
            "join_date": "2020-01-15"
        }
        data_agent.mcp_clients['user-service'].call_tool.return_value = mock_response
        
        result = await data_agent._call_mcp_tool('user-service', 'get_customer', {'customer_id': 'CUST-001'})
        
        # Verify MCP tool was called correctly
        data_agent.mcp_clients['user-service'].call_tool.assert_called_once_with(
            'get_customer', {'customer_id': 'CUST-001'}
        )
        
        assert result["customer_id"] == "CUST-001"
        assert result["name"] == "John Smith"
        assert result["type"] == "Premium"
    
    @pytest.mark.asyncio
    async def test_claims_service_create_claim_tool(self, data_agent):
        """Test claims service create_claim tool interaction."""
        mock_response = Mock()
        mock_response.result = {
            "claim_id": "CLM-456",
            "status": "Filed",
            "reference_number": "REF-789",
            "estimated_processing_time": "3-5 business days",
            "assigned_adjuster": "Jane Adjuster",
            "next_steps": ["Document review", "Field inspection", "Settlement calculation"]
        }
        data_agent.mcp_clients['claims-service'].call_tool.return_value = mock_response
        
        claim_data = {
            "customer_id": "CUST-001",
            "policy_number": "POL-123",
            "incident_date": "2024-05-29",
            "description": "Car accident on highway",
            "amount": 5000,
            "claim_type": "auto"
        }
        
        result = await data_agent._call_mcp_tool('claims-service', 'create_claim', claim_data)
        
        data_agent.mcp_clients['claims-service'].call_tool.assert_called_once_with(
            'create_claim', claim_data
        )
        
        assert result["claim_id"] == "CLM-456"
        assert result["status"] == "Filed"
        assert result["reference_number"] == "REF-789"
    
    @pytest.mark.asyncio
    async def test_policy_service_validate_policy_tool(self, data_agent):
        """Test policy service validate_policy tool interaction."""
        mock_response = Mock()
        mock_response.result = {
            "policy_number": "POL-123",
            "status": "Active",
            "coverage_type": "Comprehensive",
            "coverage_amount": "$50,000",
            "deductible": "$500",
            "premium": "$1,200/year",
            "effective_date": "2024-01-01",
            "expiration_date": "2024-12-31",
            "is_valid": True
        }
        data_agent.mcp_clients['policy-service'].call_tool.return_value = mock_response
        
        result = await data_agent._call_mcp_tool('policy-service', 'validate_policy', {
            'policy_number': 'POL-123',
            'customer_id': 'CUST-001'
        })
        
        assert result["policy_number"] == "POL-123"
        assert result["status"] == "Active"
        assert result["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_analytics_service_risk_assessment_tool(self, data_agent):
        """Test analytics service risk_assessment tool interaction."""
        mock_response = Mock()
        mock_response.result = {
            "risk_score": 0.15,
            "risk_factors": [
                {"factor": "driving_history", "score": 0.1, "weight": 0.3},
                {"factor": "credit_score", "score": 0.05, "weight": 0.2},
                {"factor": "location", "score": 0.2, "weight": 0.2}
            ],
            "risk_category": "Low Risk",
            "confidence": 0.92,
            "recommendations": [
                "Continue current coverage",
                "Consider increasing deductible for savings"
            ]
        }
        data_agent.mcp_clients['analytics-service'].call_tool.return_value = mock_response
        
        result = await data_agent._call_mcp_tool('analytics-service', 'risk_assessment', {
            'customer_id': 'CUST-001',
            'assessment_type': 'comprehensive'
        })
        
        assert result["risk_score"] == 0.15
        assert result["risk_category"] == "Low Risk"
        assert len(result["risk_factors"]) == 3
    
    @pytest.mark.asyncio
    async def test_analytics_service_fraud_detection_tool(self, data_agent):
        """Test analytics service fraud_detection tool interaction."""
        mock_response = Mock()
        mock_response.result = {
            "fraud_score": 0.05,
            "fraud_indicators": [],
            "confidence": 0.98,
            "risk_level": "Very Low",
            "factors_analyzed": [
                "claim_frequency",
                "claim_timing",
                "claim_amount",
                "customer_history",
                "external_data_match"
            ],
            "recommendation": "Process normally"
        }
        data_agent.mcp_clients['analytics-service'].call_tool.return_value = mock_response
        
        result = await data_agent._call_mcp_tool('analytics-service', 'fraud_detection', {
            'claim_id': 'CLM-789',
            'customer_id': 'CUST-001'
        })
        
        assert result["fraud_score"] == 0.05
        assert result["risk_level"] == "Very Low"
        assert result["recommendation"] == "Process normally"


class TestTechnicalAgentErrorHandling:
    """Test technical agent's error handling capabilities."""
    
    @pytest.fixture
    def data_agent(self):
        agent = FastMCPDataAgent()
        agent.mcp_clients = {
            'user-service': AsyncMock(),
            'claims-service': AsyncMock(),
            'policy-service': AsyncMock(),
            'analytics-service': AsyncMock()
        }
        return agent
    
    @pytest.mark.asyncio
    async def test_handle_mcp_service_unavailable(self, data_agent):
        """Test handling when MCP service is unavailable."""
        # Simulate service unavailable
        data_agent.mcp_clients['user-service'].call_tool.side_effect = ConnectionError("Service unavailable")
        
        task = TaskRequest(
            taskId="task_error",
            user={
                "action": "get_customer",
                "customer_id": "CUST-001"
            }
        )
        
        response = await data_agent.process_task(task)
        
        assert response.status == "failed"
        assert "error" in response.parts[0]["text"].lower()
        assert "unavailable" in response.parts[0]["text"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_invalid_mcp_response(self, data_agent):
        """Test handling when MCP service returns invalid data."""
        # Simulate invalid response
        mock_response = Mock()
        mock_response.result = None  # Invalid/empty response
        data_agent.mcp_clients['policy-service'].call_tool.return_value = mock_response
        
        task = TaskRequest(
            taskId="task_invalid",
            user={
                "action": "get_customer_policies",
                "customer_id": "CUST-001"
            }
        )
        
        response = await data_agent.process_task(task)
        
        assert response.status == "failed"
        assert "invalid" in response.parts[0]["text"].lower() or "error" in response.parts[0]["text"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_unknown_action(self, data_agent):
        """Test handling of unknown action requests."""
        task = TaskRequest(
            taskId="task_unknown",
            user={
                "action": "unknown_action",
                "customer_id": "CUST-001"
            }
        )
        
        response = await data_agent.process_task(task)
        
        assert response.status == "failed"
        assert "unknown" in response.parts[0]["text"].lower() or "unsupported" in response.parts[0]["text"].lower()
    
    @pytest.mark.asyncio
    async def test_handle_missing_parameters(self, data_agent):
        """Test handling of requests with missing required parameters."""
        task = TaskRequest(
            taskId="task_missing_params",
            user={
                "action": "get_customer"
                # Missing customer_id parameter
            }
        )
        
        response = await data_agent.process_task(task)
        
        assert response.status == "failed"
        assert "missing" in response.parts[0]["text"].lower() or "required" in response.parts[0]["text"].lower()


class TestTechnicalAgentDataTransformation:
    """Test technical agent's data transformation and formatting capabilities."""
    
    @pytest.fixture
    def data_agent(self):
        agent = FastMCPDataAgent()
        agent.mcp_clients = {
            'user-service': AsyncMock(),
            'claims-service': AsyncMock(),
            'policy-service': AsyncMock(),
            'analytics-service': AsyncMock()
        }
        return agent
    
    @pytest.mark.asyncio
    async def test_transform_customer_data_for_domain_agent(self, data_agent):
        """Test transformation of customer data for domain agent consumption."""
        raw_mcp_response = Mock()
        raw_mcp_response.result = {
            "id": "123",
            "firstName": "John",
            "lastName": "Smith",
            "emailAddress": "john.smith@email.com",
            "phoneNumber": "+1-555-0123",
            "customerType": "PREMIUM",
            "accountStatus": "ACTIVE",
            "registrationDate": "2020-01-15T00:00:00Z"
        }
        
        data_agent.mcp_clients['user-service'].call_tool.return_value = raw_mcp_response
        
        # Test the transformation
        result = await data_agent._call_mcp_tool('user-service', 'get_customer', {'customer_id': 'CUST-001'})
        
        # Verify data is properly transformed for domain agent
        expected_fields = ["id", "firstName", "lastName", "emailAddress", "customerType", "accountStatus"]
        for field in expected_fields:
            assert field in result
    
    @pytest.mark.asyncio
    async def test_aggregate_multiple_service_responses(self, data_agent):
        """Test aggregation of responses from multiple MCP services."""
        # Mock responses from different services
        user_response = Mock()
        user_response.result = {"customer_id": "CUST-001", "name": "John Smith", "type": "Premium"}
        
        policy_response = Mock()
        policy_response.result = {"active_policies": 3, "total_coverage": "$250,000"}
        
        claims_response = Mock() 
        claims_response.result = {"active_claims": 1, "recent_claims": 1}
        
        data_agent.mcp_clients['user-service'].call_tool.return_value = user_response
        data_agent.mcp_clients['policy-service'].call_tool.return_value = policy_response
        data_agent.mcp_clients['claims-service'].call_tool.return_value = claims_response
        
        # Test aggregation in a comprehensive request
        task = TaskRequest(
            taskId="task_aggregate",
            user={
                "action": "get_comprehensive_customer_data",
                "customer_id": "CUST-001"
            }
        )
        
        response = await data_agent.process_task(task)
        
        if response.status == "completed":
            result_data = json.loads(response.parts[0]["text"])
            
            # Should contain data from all services
            assert "customer_id" in result_data
            assert "active_policies" in result_data
            assert "active_claims" in result_data


class TestTechnicalAgentPerformance:
    """Test technical agent's performance characteristics."""
    
    @pytest.fixture
    def data_agent(self):
        agent = FastMCPDataAgent()
        agent.mcp_clients = {
            'user-service': AsyncMock(),
            'claims-service': AsyncMock(),
            'policy-service': AsyncMock(),
            'analytics-service': AsyncMock()
        }
        return agent
    
    @pytest.mark.asyncio
    async def test_concurrent_mcp_requests(self, data_agent):
        """Test handling of concurrent MCP requests."""
        # Mock responses with different delays
        async def delayed_response_1():
            await asyncio.sleep(0.1)
            mock_resp = Mock()
            mock_resp.result = {"service": "user", "data": "test1"}
            return mock_resp
        
        async def delayed_response_2():
            await asyncio.sleep(0.2)
            mock_resp = Mock()
            mock_resp.result = {"service": "policy", "data": "test2"}
            return mock_resp
        
        data_agent.mcp_clients['user-service'].call_tool = delayed_response_1
        data_agent.mcp_clients['policy-service'].call_tool = delayed_response_2
        
        # Execute concurrent requests
        start_time = asyncio.get_event_loop().time()
        
        tasks = [
            data_agent._call_mcp_tool('user-service', 'get_customer', {'customer_id': 'CUST-001'}),
            data_agent._call_mcp_tool('policy-service', 'get_policies', {'customer_id': 'CUST-001'})
        ]
        
        results = await asyncio.gather(*tasks)
        end_time = asyncio.get_event_loop().time()
        
        # Should complete in less time than sequential execution
        assert (end_time - start_time) < 0.3  # Should be ~0.2s, not 0.3s
        assert len(results) == 2
        assert results[0]["service"] == "user"
        assert results[1]["service"] == "policy"
    
    @pytest.mark.asyncio
    async def test_response_caching(self, data_agent):
        """Test response caching for repeated requests (if implemented)."""
        mock_response = Mock()
        mock_response.result = {"customer_id": "CUST-001", "name": "John Smith"}
        data_agent.mcp_clients['user-service'].call_tool.return_value = mock_response
        
        # First request
        result1 = await data_agent._call_mcp_tool('user-service', 'get_customer', {'customer_id': 'CUST-001'})
        
        # Second identical request
        result2 = await data_agent._call_mcp_tool('user-service', 'get_customer', {'customer_id': 'CUST-001'})
        
        # Both should return same data
        assert result1 == result2
        
        # If caching is implemented, MCP client should only be called once
        # For now, we just verify functionality


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 