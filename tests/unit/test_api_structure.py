#!/usr/bin/env python3
"""
Unit tests for API Structure and Focused APIs
Tests the individual API endpoints and their data structures
"""

import pytest
import json
from unittest.mock import Mock, patch
from typing import Dict, Any, List

import sys
import os

# Add policy_server to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'policy_server'))

# Import the actual functions from the policy server
from main import (
    get_policies, get_agent, get_policy_types, get_policy_list,
    get_payment_information, get_coverage_information, get_policy_details,
    get_deductibles, get_recommendations, get_customer_policies
)

class TestAPIStructure:
    """Test API structure and focused endpoint functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_customer_id = "CUST-001"

    def test_get_policies_basic(self):
        """Test basic policy list retrieval"""
        result = get_policies(self.test_customer_id)
        
        assert isinstance(result, list)
        if result:  # If customer has policies
            policy = result[0]
            assert "id" in policy
            assert "type" in policy
            assert "status" in policy

    def test_get_agent_information(self):
        """Test agent contact information retrieval"""
        result = get_agent(self.test_customer_id)
        
        assert isinstance(result, dict)
        # Should have either valid agent info or error message
        if "error" not in result:
            assert "name" in result
            assert "email" in result

    def test_get_policy_types(self):
        """Test policy type categories"""
        result = get_policy_types(self.test_customer_id)
        
        assert isinstance(result, list)
        # Should be a list of policy type strings
        for policy_type in result:
            assert isinstance(policy_type, str)

    def test_get_policy_list_detailed(self):
        """Test detailed policy list with more information"""
        result = get_policy_list(self.test_customer_id)
        
        assert isinstance(result, list)
        if result:  # If customer has policies
            policy = result[0]
            assert "id" in policy
            assert "type" in policy
            assert "status" in policy
            assert "premium" in policy

    def test_get_payment_information(self):
        """Test payment and billing information"""
        result = get_payment_information(self.test_customer_id)
        
        assert isinstance(result, list)
        if result:  # If customer has payment info
            payment = result[0]
            assert "policy_id" in payment
            assert "premium" in payment

    def test_get_coverage_information(self):
        """Test coverage details"""
        result = get_coverage_information(self.test_customer_id)
        
        assert isinstance(result, list)
        if result:  # If customer has coverage
            coverage = result[0]
            assert "policy_id" in coverage
            assert "coverage_amount" in coverage

    def test_get_policy_details_specific(self):
        """Test specific policy details"""
        policies = get_policies(self.test_customer_id)
        if policies:
            policy_id = policies[0]["id"]
            result = get_policy_details(policy_id)
            
            assert isinstance(result, dict)
            if "error" not in result:
                assert "id" in result
                assert "type" in result

    def test_get_deductibles(self):
        """Test deductible information"""
        result = get_deductibles(self.test_customer_id)
        
        assert isinstance(result, list)
        if result:  # If customer has deductibles
            deductible = result[0]
            assert "policy_id" in deductible
            assert "deductible" in deductible

    def test_get_recommendations(self):
        """Test personalized recommendations"""
        result = get_recommendations(self.test_customer_id)
        
        assert isinstance(result, list)
        # Recommendations should be a list
        for rec in result:
            assert isinstance(rec, dict)

    def test_invalid_customer_id(self):
        """Test handling of invalid customer ID"""
        result = get_policies("INVALID-ID")
        
        # Should return empty list for invalid customer
        assert isinstance(result, list)
        assert len(result) == 0

    def test_api_data_consistency(self):
        """Test that APIs return consistent customer data"""
        # Get data from multiple APIs for the same customer
        policies = get_policies(self.test_customer_id)
        agent = get_agent(self.test_customer_id)
        payment_info = get_payment_information(self.test_customer_id)
        
        # All should handle the same customer appropriately
        assert isinstance(policies, list)
        assert isinstance(agent, dict)
        assert isinstance(payment_info, list)

    def test_api_response_size_comparison(self):
        """Test that focused APIs return smaller data than comprehensive API"""
        # Get comprehensive data
        comprehensive = get_customer_policies(self.test_customer_id)
        comprehensive_size = len(json.dumps(comprehensive))
        
        # Get focused data
        policies = get_policies(self.test_customer_id)
        policies_size = len(json.dumps(policies))
        
        agent = get_agent(self.test_customer_id)
        agent_size = len(json.dumps(agent))
        
        # Focused APIs should be smaller than comprehensive
        assert policies_size <= comprehensive_size
        assert agent_size <= comprehensive_size
        
        # Calculate efficiency if there's actual data
        if comprehensive_size > 0:
            combined_focused = policies_size + agent_size
            efficiency_ratio = combined_focused / comprehensive_size
            
            # Should be more efficient when only specific data is needed
            print(f"Efficiency ratio: {efficiency_ratio:.2f}")
            # Allow up to 100% ratio since focused APIs might be similar for small datasets
            assert efficiency_ratio <= 1.0

class TestAPIValidation:
    """Test API parameter validation and error handling"""
    
    def test_empty_customer_id(self):
        """Test handling of empty customer ID"""
        result = get_policies("")
        
        # Should return empty list for empty customer ID
        assert isinstance(result, list)
        assert len(result) == 0

    def test_policy_details_with_invalid_policy_id(self):
        """Test policy details with invalid policy ID"""
        result = get_policy_details("INVALID-POLICY")
        
        # Should return error or empty result
        assert isinstance(result, dict)
        if "error" in result:
            assert "not found" in result["error"].lower()

    def test_api_parameter_types(self):
        """Test that APIs handle different parameter types correctly"""
        # Test string customer ID (normal case)
        result = get_policies("CUST-001")
        assert isinstance(result, list)
        
        # Test with different customer IDs
        for customer_id in ["CUST-002", "CUST-003", "NONEXISTENT"]:
            result = get_policies(customer_id)
            assert isinstance(result, list)  # Should always return list

class TestAPIBusinessLogic:
    """Test business logic within APIs"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_customer_id = "CUST-001"

    def test_recommendations_structure(self):
        """Test that recommendations have proper structure"""
        result = get_recommendations(self.test_customer_id)
        
        assert isinstance(result, list)
        # Each recommendation should be a dictionary
        for rec in result:
            assert isinstance(rec, dict)

    def test_policy_types_consistency(self):
        """Test that policy types are consistent with actual policies"""
        policies = get_policies(self.test_customer_id)
        policy_types = get_policy_types(self.test_customer_id)
        
        if policies:
            # Policy types should match the types in the actual policies
            actual_types = set(p["type"] for p in policies if "type" in p)
            returned_types = set(policy_types)
            
            # All actual types should be in the returned types
            assert actual_types.issubset(returned_types) or len(actual_types) == 0

    def test_coverage_completeness(self):
        """Test that coverage information relates to policies"""
        policies = get_policies(self.test_customer_id)
        coverage = get_coverage_information(self.test_customer_id)
        
        # Coverage should relate to existing policies
        if policies and coverage:
            policy_ids = set(p["id"] for p in policies)
            coverage_policy_ids = set(c["policy_id"] for c in coverage if "policy_id" in c)
            
            # Coverage should be for valid policy IDs
            assert coverage_policy_ids.issubset(policy_ids) or len(coverage_policy_ids) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 