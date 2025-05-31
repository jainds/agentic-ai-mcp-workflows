#!/usr/bin/env python3

import pytest
import asyncio
import json
import os
import sys
from unittest.mock import patch, AsyncMock
import time

# Add the parent directory to the Python path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from domain_agent.main import DomainAgent
from technical_agent.main import TechnicalAgent
from python_a2a import A2AClient


class TestComprehensiveIntegration:
    """Integration tests for the complete insurance AI system flow"""
    
    @pytest.fixture
    def domain_agent(self):
        """Create a domain agent instance for testing"""
        return DomainAgent()
    
    @pytest.fixture  
    def technical_agent(self):
        """Create a technical agent instance for testing"""
        return TechnicalAgent()

    # === Basic Integration Tests ===
    
    @pytest.mark.asyncio
    async def test_domain_technical_integration_valid_customer(self, domain_agent, technical_agent):
        """Test integration between domain and technical agent with valid customer"""
        with patch.object(technical_agent, '_call_mcp_server', new_callable=AsyncMock) as mock_mcp:
            # Mock MCP response
            mock_mcp.return_value = {
                "success": True,
                "data": {
                    "customer_id": "CUST-001",
                    "policies": [
                        {
                            "policy_id": "POL-2024-AUTO-002",
                            "type": "auto",
                            "status": "active",
                            "premium": 95.00,
                            "billing_cycle": "quarterly",
                            "next_payment_due": "2024-09-01T00:00:00Z",
                            "coverage_amount": 75000
                        }
                    ]
                }
            }
            
            # Test through technical agent
            tech_result = await technical_agent.ask({
                'user_question': 'What policies does CUST-001 have?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert isinstance(tech_result, dict)
            assert tech_result.get("success") is True
            assert "policies" in tech_result.get("data", {})
            
            # Test through domain agent (with mocked technical call)
            with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
                mock_tech.return_value = tech_result
                
                domain_result = await domain_agent.ask({
                    'user_question': 'What policies does CUST-001 have?',
                    'session_data': {'customer_id': 'CUST-001'}
                })
                
                assert isinstance(domain_result, str)
                assert len(domain_result) > 0
                mock_tech.assert_called_once()

    @pytest.mark.asyncio
    async def test_domain_technical_integration_invalid_customer(self, domain_agent, technical_agent):
        """Test integration with invalid customer ID"""
        with patch.object(technical_agent, '_call_mcp_server', new_callable=AsyncMock) as mock_mcp:
            # Mock MCP error response
            mock_mcp.return_value = {
                "success": False,
                "error": "Customer not found",
                "data": None
            }
            
            # Test through technical agent
            tech_result = await technical_agent.ask({
                'user_question': 'What policies does INVALID-999 have?',
                'session_data': {'customer_id': 'INVALID-999'}
            })
            
            assert isinstance(tech_result, dict)
            assert tech_result.get("success") is False
            assert "error" in tech_result
            
            # Test through domain agent
            with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
                mock_tech.return_value = tech_result
                
                domain_result = await domain_agent.ask({
                    'user_question': 'What policies does INVALID-999 have?',
                    'session_data': {'customer_id': 'INVALID-999'}
                })
                
                assert isinstance(domain_result, str)
                assert any(word in domain_result.lower() for word in ["not found", "error", "invalid"])

    # === User's Specific Example Tests ===
    
    @pytest.mark.asyncio
    async def test_tell_me_about_policies_integration(self, domain_agent):
        """Integration test: Tell me about my policies"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [
                    {"type": "auto", "status": "active", "coverage_amount": 75000},
                    {"type": "life", "status": "active", "coverage_amount": 250000}
                ]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'Tell me about my policies',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "policy" in result.lower()
            assert any(word in result.lower() for word in ["auto", "life"])

    @pytest.mark.asyncio
    async def test_policy_expiring_next_integration(self, domain_agent):
        """Integration test: Which policy is expiring next?"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [
                    {
                        "type": "auto",
                        "end_date": "2025-01-15T00:00:00Z",
                        "policy_id": "POL-2024-AUTO-002"
                    },
                    {
                        "type": "life", 
                        "end_date": "2034-01-01T00:00:00Z",
                        "policy_id": "POL-2024-LIFE-001"
                    }
                ]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'Which policy is expiring next for customer CUST-001?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert any(word in result.lower() for word in ["expire", "expiring", "next"])

    @pytest.mark.asyncio
    async def test_auto_vehicle_details_integration(self, domain_agent):
        """Integration test: For my auto policy, can you give me vehicle details?"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [
                    {
                        "type": "auto",
                        "vehicle": {
                            "make": "Honda",
                            "model": "Civic", 
                            "year": 2023,
                            "vin": "1HGCM82633A123456"
                        }
                    }
                ]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'For my auto policy, can you give me vehicle details for customer CUST-001?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert any(word in result.lower() for word in ["vehicle", "auto"])

    @pytest.mark.asyncio
    async def test_policy_limits_explanation_integration(self, domain_agent):
        """Integration test: Explain all my policy limits"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [
                    {
                        "type": "auto",
                        "coverage_amount": 75000,
                        "coverage_details": {
                            "bodily_injury_liability": "$50,000 per person"
                        }
                    },
                    {
                        "type": "life",
                        "coverage_amount": 250000,
                        "coverage_details": {
                            "death_benefit": "$250,000"
                        }
                    }
                ]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'Explain all my policy limits for customer CUST-001',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert any(word in result.lower() for word in ["limit", "coverage"])

    # === Different Customer ID Format Tests ===
    
    @pytest.mark.asyncio
    async def test_user_format_integration(self, domain_agent):
        """Integration test: Customer ID in user_### format"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "user_003",
                "policies": []
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'What policies does user_003 have?',
                'session_data': {'customer_id': 'user_003'}
            })
            
            assert "user_003" in result or "user" in result.lower()

    @pytest.mark.asyncio
    async def test_customer_dash_format_integration(self, domain_agent):
        """Integration test: Customer ID in customer-### format"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "customer-123",
                "policies": []
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'Show me coverage for customer-123',
                'session_data': {'customer_id': 'customer-123'}
            })
            
            assert "customer-123" in result or "customer" in result.lower()

    # === Error Handling Integration Tests ===
    
    @pytest.mark.asyncio
    async def test_mcp_server_timeout_integration(self, domain_agent):
        """Integration test: MCP server timeout handling"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.side_effect = asyncio.TimeoutError("MCP server timeout")
            
            result = await domain_agent.ask({
                'user_question': 'What policies does CUST-001 have?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert any(word in result.lower() for word in ["timeout", "error", "unavailable", "try again"])

    @pytest.mark.asyncio
    async def test_technical_agent_error_integration(self, domain_agent):
        """Integration test: Technical agent error handling"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = {"success": False, "error": "Database connection failed"}
            
            result = await domain_agent.ask({
                'user_question': 'What policies does CUST-001 have?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert any(word in result.lower() for word in ["error", "failed", "unavailable"])

    # === Performance and Stress Integration Tests ===
    
    @pytest.mark.asyncio
    async def test_complex_multi_query_integration(self, domain_agent):
        """Integration test: Complex multi-part query"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [
                    {
                        "type": "auto",
                        "premium": 95.00,
                        "next_payment_due": "2024-09-01T00:00:00Z",
                        "coverage_amount": 75000,
                        "vehicle": {"make": "Honda", "model": "Civic"}
                    }
                ],
                "agents": [
                    {"name": "Michael Brown", "phone": "+1-555-0123"}
                ]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'For customer CUST-001, tell me about all policies, payment dates, coverage limits, agent contact, and vehicle details',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            # Should contain multiple pieces of information
            result_lower = result.lower()
            keyword_count = sum(1 for word in ["policy", "payment", "coverage", "agent", "vehicle"] if word in result_lower)
            assert keyword_count >= 3  # Should contain most requested information types

    @pytest.mark.asyncio
    async def test_concurrent_requests_integration(self, domain_agent):
        """Integration test: Concurrent request handling"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [{"type": "auto", "status": "active"}]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            # Run multiple concurrent requests
            tasks = []
            for i in range(5):
                task = domain_agent.ask({
                    'user_question': f'What policies does CUST-001 have? Request {i}',
                    'session_data': {'customer_id': 'CUST-001'}
                })
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should succeed
            for result in results:
                assert isinstance(result, str)
                assert len(result) > 0
                assert "policy" in result.lower()

    # === Query Style Integration Tests ===
    
    @pytest.mark.asyncio
    async def test_formal_style_integration(self, domain_agent):
        """Integration test: Formal business language style"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [
                    {"type": "auto", "coverage_amount": 75000},
                    {"type": "life", "coverage_amount": 250000}
                ]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'I would like to request a comprehensive review of all insurance policies and associated coverage details for customer identifier CUST-001',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert any(word in result.lower() for word in ["policy", "coverage", "insurance"])

    @pytest.mark.asyncio
    async def test_casual_style_integration(self, domain_agent):
        """Integration test: Casual conversational style"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [
                    {"type": "auto"},
                    {"type": "life"}
                ]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': "Hey, can you just quickly tell me what kind of insurance I have? I'm customer CUST-001",
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "insurance" in result.lower() or "policy" in result.lower()

    # === Boundary Value Integration Tests ===
    
    @pytest.mark.asyncio
    async def test_minimal_query_integration(self, domain_agent):
        """Integration test: Minimal query format"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [{"type": "auto"}, {"type": "life"}]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            result = await domain_agent.ask({
                'user_question': 'CUST-001 policy?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "policy" in result.lower()

    @pytest.mark.asyncio
    async def test_very_long_query_integration(self, domain_agent):
        """Integration test: Very long query handling"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [{"type": "auto"}, {"type": "life"}]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            long_query = "I am writing a very long query to test the system's ability to handle extensive customer requests with lots of details and information and I want to know about my policies and coverage and payments and everything else related to my insurance for customer CUST-001 and I hope this works correctly"
            
            result = await domain_agent.ask({
                'user_question': long_query,
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert any(word in result.lower() for word in ["policy", "insurance", "coverage"])

    # === Response Time Integration Tests ===
    
    @pytest.mark.asyncio
    async def test_response_time_integration(self, domain_agent):
        """Integration test: Response time measurement"""
        mock_response = {
            "success": True,
            "data": {
                "customer_id": "CUST-001",
                "policies": [{"type": "auto"}]
            }
        }
        
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            mock_tech.return_value = mock_response
            
            start_time = time.time()
            
            result = await domain_agent.ask({
                'user_question': 'What policies does CUST-001 have?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Response should be fast (mocked)
            assert response_time < 5.0  # Should complete within 5 seconds
            assert isinstance(result, str)
            assert len(result) > 0 