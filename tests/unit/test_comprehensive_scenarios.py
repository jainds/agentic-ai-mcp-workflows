#!/usr/bin/env python3

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the parent directory to the Python path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Add the project root to Python path 
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Add domain_agent directory to path
domain_agent_path = os.path.join(project_root, 'domain_agent')
sys.path.insert(0, domain_agent_path)

# Add technical_agent directory to path  
technical_agent_path = os.path.join(project_root, 'technical_agent')
sys.path.insert(0, technical_agent_path)

from domain_agent.main import DomainAgent


class TestComprehensiveScenarios:
    """Comprehensive unit tests for domain agent with various customer ID formats and scenarios"""
    
    @pytest.fixture
    def domain_agent(self):
        """Create a domain agent instance for testing"""
        return DomainAgent()
    
    @pytest.fixture
    def mock_technical_response_cust_001(self):
        """Mock response from technical agent for CUST-001"""
        return {
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
                        "payment_method": "auto_pay",
                        "coverage_amount": 75000,
                        "deductible": 750,
                        "start_date": "2024-01-15T00:00:00Z",
                        "end_date": "2025-01-15T00:00:00Z",
                        "vehicle": {
                            "make": "Honda",
                            "model": "Civic",
                            "year": 2023,
                            "vin": "1HGCM82633A123456"
                        },
                        "coverage_details": {
                            "bodily_injury_liability": "$50,000 per person, $100,000 per accident",
                            "property_damage_liability": "$25,000 per accident",
                            "collision": "Actual Cash Value",
                            "comprehensive": "Actual Cash Value"
                        }
                    },
                    {
                        "policy_id": "POL-2024-LIFE-001",
                        "type": "life",
                        "status": "active", 
                        "premium": 45.00,
                        "billing_cycle": "monthly",
                        "next_payment_due": "2024-06-15T00:00:00Z",
                        "payment_method": "auto_pay",
                        "coverage_amount": 250000,
                        "deductible": 0,
                        "start_date": "2024-01-01T00:00:00Z",
                        "end_date": "2034-01-01T00:00:00Z",
                        "beneficiary": "Spouse",
                        "coverage_details": {
                            "death_benefit": "$250,000",
                            "term_length": "10 years",
                            "riders": ["Accidental Death", "Disability Waiver"]
                        }
                    }
                ],
                "agents": [
                    {
                        "agent_id": "AGENT_001",
                        "name": "Michael Brown",
                        "phone": "+1-555-0123",
                        "email": "michael.brown@insurance.com",
                        "specialization": "Auto and Life Insurance"
                    }
                ]
            }
        }
    
    @pytest.fixture  
    def mock_technical_response_not_found(self):
        """Mock response for customer not found"""
        return {
            "success": False,
            "error": "Customer not found",
            "data": None
        }

    # === Tests for User's Specific Examples ===
    
    @pytest.mark.asyncio
    async def test_general_policies_overview(self, domain_agent, mock_technical_response_cust_001):
        """Test: Tell me about my policies"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**POLICY OVERVIEW:** You have 2 active policies: Auto Insurance and Life Insurance."
            
            result = await domain_agent.ask({
                'user_question': 'Tell me about my policies',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "policy" in result.lower()
            mock_tech.assert_called_once()
            mock_format.assert_called_once()

    @pytest.mark.asyncio
    async def test_policy_expiring_next(self, domain_agent, mock_technical_response_cust_001):
        """Test: Which policy is expiring next?"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "Your auto policy (POL-2024-AUTO-002) expires next on January 15, 2025."
            
            result = await domain_agent.ask({
                'user_question': 'Which policy is expiring next for customer CUST-001?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "auto" in result.lower()
            assert "2025" in result
            
    @pytest.mark.asyncio
    async def test_policy_details_comprehensive(self, domain_agent, mock_technical_response_cust_001):
        """Test: What are my policy details?"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**POLICY DETAILS:** Auto: Honda Civic 2023, $75,000 coverage. Life: $250,000 benefit, 10-year term."
            
            result = await domain_agent.ask({
                'user_question': 'What are my policy details for customer CUST-001?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "honda" in result.lower()
            assert "250,000" in result

    @pytest.mark.asyncio
    async def test_auto_vehicle_details(self, domain_agent, mock_technical_response_cust_001):
        """Test: For my auto policy, can you give me vehicle details?"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**VEHICLE DETAILS:** 2023 Honda Civic, VIN: 1HGCM82633A123456"
            
            result = await domain_agent.ask({
                'user_question': 'For my auto policy, can you give me vehicle details for customer CUST-001?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "honda" in result.lower()
            assert "civic" in result.lower()
            assert "2023" in result

    @pytest.mark.asyncio
    async def test_all_policy_limits(self, domain_agent, mock_technical_response_cust_001):
        """Test: Explain all my policy limits"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**POLICY LIMITS:** Auto: $75,000 total, $50,000 bodily injury. Life: $250,000 death benefit."
            
            result = await domain_agent.ask({
                'user_question': 'Explain all my policy limits for customer CUST-001',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "75,000" in result
            assert "250,000" in result

    # === Tests with Different Customer ID Formats ===
    
    @pytest.mark.asyncio
    async def test_user_format_customer_id(self, domain_agent):
        """Test customer ID in user_### format"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = {"success": True, "data": {"customer_id": "user_003", "policies": []}}
            mock_format.return_value = "Customer user_003 has no active policies."
            
            result = await domain_agent.ask({
                'user_question': 'What policies does user_003 have?',
                'session_data': {'customer_id': 'user_003'}
            })
            
            assert "user_003" in result
            mock_tech.assert_called_once()

    @pytest.mark.asyncio 
    async def test_customer_dash_format(self, domain_agent):
        """Test customer ID in customer-### format"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = {"success": True, "data": {"customer_id": "customer-123", "policies": []}}
            mock_format.return_value = "Customer customer-123 coverage information."
            
            result = await domain_agent.ask({
                'user_question': 'Show me coverage for customer-123',
                'session_data': {'customer_id': 'customer-123'}
            })
            
            assert "customer-123" in result

    @pytest.mark.asyncio
    async def test_mixed_case_customer_id(self, domain_agent):
        """Test mixed case customer ID"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = {"success": True, "data": {"customer_id": "Customer_001", "policies": []}}
            mock_format.return_value = "Payment details for Customer_001."
            
            result = await domain_agent.ask({
                'user_question': 'What are the payment details for Customer_001?',
                'session_data': {'customer_id': 'Customer_001'}
            })
            
            assert "Customer_001" in result

    @pytest.mark.asyncio
    async def test_casual_customer_name(self, domain_agent):
        """Test casual customer name mention"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = {"success": True, "data": {"customer_id": "john", "policies": []}}
            mock_format.return_value = "Policy information for customer john."
            
            result = await domain_agent.ask({
                'user_question': 'Tell me about policies for customer john',
                'session_data': {'customer_id': 'john'}
            })
            
            assert "john" in result

    # === Negative Test Cases ===
    
    @pytest.mark.asyncio
    async def test_nonexistent_customer(self, domain_agent, mock_technical_response_not_found):
        """Test non-existent customer ID handling"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            
            mock_tech.return_value = mock_technical_response_not_found
            
            result = await domain_agent.ask({
                'user_question': 'What policies does CUST-999 have?',
                'session_data': {'customer_id': 'CUST-999'}
            })
            
            assert any(word in result.lower() for word in ["not found", "no policies", "customer not found"])

    @pytest.mark.asyncio
    async def test_invalid_customer_format(self, domain_agent):
        """Test invalid customer ID format"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            
            mock_tech.return_value = {"success": False, "error": "Invalid customer ID format"}
            
            result = await domain_agent.ask({
                'user_question': 'Show me policies for customer @#$%',
                'session_data': {'customer_id': '@#$%'}
            })
            
            assert any(word in result.lower() for word in ["invalid", "error", "not found"])

    @pytest.mark.asyncio
    async def test_empty_customer_id(self, domain_agent):
        """Test empty customer ID"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech:
            
            mock_tech.return_value = {"success": False, "error": "Customer ID is required"}
            
            result = await domain_agent.ask({
                'user_question': "What are my policies for customer ''?",
                'session_data': {'customer_id': ''}
            })
            
            assert any(word in result.lower() for word in ["required", "invalid", "error"])

    @pytest.mark.asyncio
    async def test_no_customer_specified(self, domain_agent):
        """Test query without customer identification"""
        result = await domain_agent.ask({
            'user_question': 'What are my policies?',
            'session_data': {}
        })
        
        assert any(word in result.lower() for word in ["customer", "identify", "specify", "required"])

    # === Edge Cases and Advanced Scenarios ===
    
    @pytest.mark.asyncio
    async def test_policy_comparison(self, domain_agent, mock_technical_response_cust_001):
        """Test policy comparison functionality"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**POLICY COMPARISON:** Auto: $95 quarterly, Life: $45 monthly"
            
            result = await domain_agent.ask({
                'user_question': 'Compare my auto and life policies for CUST-001',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "auto" in result.lower()
            assert "life" in result.lower()
            assert "compare" in result.lower()

    @pytest.mark.asyncio
    async def test_premium_calculation(self, domain_agent, mock_technical_response_cust_001):
        """Test premium calculation across policies"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**ANNUAL PREMIUM:** Total: $920 (Auto: $380, Life: $540)"
            
            result = await domain_agent.ask({
                'user_question': 'Calculate my total annual premium for customer CUST-001',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "annual" in result.lower()
            assert "total" in result.lower()

    @pytest.mark.asyncio
    async def test_emergency_contact_info(self, domain_agent, mock_technical_response_cust_001):
        """Test emergency contact information"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**EMERGENCY CONTACT:** Michael Brown, +1-555-0123"
            
            result = await domain_agent.ask({
                'user_question': 'Who should I contact in an emergency for customer CUST-001?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "michael" in result.lower()
            assert "brown" in result.lower()

    # === Different Query Styles ===
    
    @pytest.mark.asyncio
    async def test_formal_business_style(self, domain_agent, mock_technical_response_cust_001):
        """Test formal business language style"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**COMPREHENSIVE POLICY REVIEW:** Complete analysis of coverage portfolio."
            
            result = await domain_agent.ask({
                'user_question': 'I would like to request a comprehensive review of all insurance policies and associated coverage details for customer identifier CUST-001',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "policy" in result.lower()
            assert "coverage" in result.lower()

    @pytest.mark.asyncio
    async def test_casual_conversational_style(self, domain_agent, mock_technical_response_cust_001):
        """Test casual conversational style"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "Hey! You have auto and life insurance policies."
            
            result = await domain_agent.ask({
                'user_question': "Hey, can you just quickly tell me what kind of insurance I have? I'm customer CUST-001",
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "insurance" in result.lower()

    @pytest.mark.asyncio
    async def test_technical_jargon_handling(self, domain_agent, mock_technical_response_cust_001):
        """Test technical insurance jargon handling"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**ACTUARIAL DATA:** Risk assessment and coverage parameters provided."
            
            result = await domain_agent.ask({
                'user_question': 'Provide actuarial data and risk assessment parameters for policyholder CUST-001',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "data" in result.lower()

    # === Boundary Value Testing ===
    
    @pytest.mark.asyncio
    async def test_very_long_query(self, domain_agent, mock_technical_response_cust_001):
        """Test very long query handling"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "**POLICY INFORMATION:** Comprehensive response to detailed inquiry."
            
            long_query = "I am writing a very long query to test the system's ability to handle extensive customer requests with lots of details and information and I want to know about my policies and coverage and payments and everything else related to my insurance for customer CUST-001 and I hope this works correctly"
            
            result = await domain_agent.ask({
                'user_question': long_query,
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "policy" in result.lower()

    @pytest.mark.asyncio
    async def test_minimal_query(self, domain_agent, mock_technical_response_cust_001):
        """Test minimal query format"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "Auto and Life policies active."
            
            result = await domain_agent.ask({
                'user_question': 'CUST-001 policy?',
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "policy" in result.lower()

    # === Special Characters and Edge Cases ===
    
    @pytest.mark.asyncio
    async def test_special_characters_query(self, domain_agent, mock_technical_response_cust_001):
        """Test special characters in queries"""
        with patch.object(domain_agent, '_call_technical_agent', new_callable=AsyncMock) as mock_tech, \
             patch.object(domain_agent, '_format_with_llm', new_callable=AsyncMock) as mock_format:
            
            mock_tech.return_value = mock_technical_response_cust_001
            mock_format.return_value = "Coverage: $75,000 & $250,000. Payment due: September & June."
            
            result = await domain_agent.ask({
                'user_question': "What's my coverage amount ($) & payment due dates (?) for customer CUST-001???",
                'session_data': {'customer_id': 'CUST-001'}
            })
            
            assert "coverage" in result.lower()
            assert "payment" in result.lower() 