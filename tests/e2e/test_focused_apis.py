#!/usr/bin/env python3
"""
End-to-end tests for Focused APIs
Tests real customer service scenarios demonstrating business value of focused APIs
"""

import pytest
import asyncio
import json
import time
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

class TestFocusedAPIsE2E:
    """End-to-end tests for focused API business scenarios"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_customer_id = "CUST-001"

    def test_customer_service_quick_policy_lookup(self):
        """Test: Customer calls asking 'What policies do I have?'"""
        
        # Customer service agent needs quick policy overview
        start_time = time.time()
        
        # Using focused API
        policies = get_policies(self.test_customer_id)
        
        lookup_time = time.time() - start_time
        
        # Verify business value
        assert isinstance(policies, list)
        assert lookup_time < 1.0  # Should be fast for customer service
        
        # Agent can quickly tell customer their policies
        if policies:
            policy_types = [p["type"] for p in policies]
            print(f"✅ Customer has {len(policies)} policies: {', '.join(policy_types)}")
        
        # Measure data efficiency vs comprehensive API
        comprehensive_data = get_customer_policies(self.test_customer_id)
        focused_data_size = len(json.dumps(policies))
        comprehensive_data_size = len(json.dumps(comprehensive_data))
        
        if comprehensive_data_size > 0:
            efficiency = (comprehensive_data_size - focused_data_size) / comprehensive_data_size
            print(f"✅ Data efficiency: {efficiency:.1%} reduction in data transfer")
            assert efficiency >= 0  # Should be at least as efficient

    def test_billing_inquiry_scenario(self):
        """Test: Customer calls asking 'When is my next payment due?'"""
        
        # Customer service needs billing information only
        payment_info = get_payment_information(self.test_customer_id)
        
        # Verify payment info structure
        assert isinstance(payment_info, list)
        
        if payment_info:
            # Should have payment details
            payment = payment_info[0]
            assert isinstance(payment, dict)
            print(f"✅ Payment information available")

    def test_agent_contact_request(self):
        """Test: Customer asks 'Who is my insurance agent?'"""
        
        # Customer needs agent contact information
        agent_info = get_agent(self.test_customer_id)
        
        # Verify agent information structure
        assert isinstance(agent_info, dict)
        
        if "error" not in agent_info and agent_info.get("name"):
            print(f"✅ Agent: {agent_info['name']}")
            
            # Verify this is much smaller than full customer data
            agent_data_size = len(json.dumps(agent_info))
            comprehensive_data = get_customer_policies(self.test_customer_id)
            comprehensive_size = len(json.dumps(comprehensive_data))
            
            if comprehensive_size > 0:
                efficiency = agent_data_size / comprehensive_size
                assert efficiency <= 1.0  # Agent info should be <= comprehensive data

    def test_coverage_verification_scenario(self):
        """Test: Customer asks 'What am I covered for in my auto policy?'"""
        
        # Get customer's policies first
        policies = get_policies(self.test_customer_id)
        auto_policies = [p for p in policies if p.get("type") == "Auto"]
        
        if auto_policies:
            # Get detailed coverage for auto policy
            coverage_info = get_coverage_information(self.test_customer_id)
            auto_coverage = [c for c in coverage_info if c.get("policy_id") == auto_policies[0].get("id")]
            
            # Verify coverage details available
            assert isinstance(coverage_info, list)
            
            if auto_coverage:
                coverage_types = [c.get("coverage_type", "Unknown") for c in auto_coverage]
                print(f"✅ Auto coverage includes: {', '.join(coverage_types)}")

    def test_new_customer_recommendations(self):
        """Test: New customer asks 'What other insurance should I consider?'"""
        
        # Get personalized recommendations
        recommendations = get_recommendations(self.test_customer_id)
        
        # Verify recommendations structure
        assert isinstance(recommendations, list)
        
        if recommendations:
            print(f"✅ Found {len(recommendations)} recommendations")

    def test_multi_api_customer_overview(self):
        """Test: Agent needs complete customer overview for call"""
        
        # Simulate agent preparing for customer call
        start_time = time.time()
        
        # Get key information using multiple focused APIs
        policies = get_policies(self.test_customer_id)
        agent_info = get_agent(self.test_customer_id)
        payment_info = get_payment_information(self.test_customer_id)
        recommendations = get_recommendations(self.test_customer_id)
        
        preparation_time = time.time() - start_time
        
        # Verify all APIs returned data
        assert isinstance(policies, list)
        assert isinstance(agent_info, dict)
        assert isinstance(payment_info, list)
        assert isinstance(recommendations, list)
        
        # Calculate total data size
        total_focused_size = (
            len(json.dumps(policies)) +
            len(json.dumps(agent_info)) +
            len(json.dumps(payment_info)) +
            len(json.dumps(recommendations))
        )
        
        # Compare with comprehensive API
        comprehensive_data = get_customer_policies(self.test_customer_id)
        comprehensive_size = len(json.dumps(comprehensive_data))
        
        # Even multiple focused APIs should be reasonable
        if comprehensive_size > 0:
            efficiency = total_focused_size / comprehensive_size
            print(f"✅ Multi-API efficiency: {efficiency:.1%} of comprehensive data")
            print(f"✅ Preparation time: {preparation_time:.3f}s")
            
            # Should be reasonably efficient
            assert efficiency <= 2.0  # Allow some overhead for multiple calls
            assert preparation_time < 5.0  # Fast enough for customer service

    def test_policy_renewal_workflow(self):
        """Test: Customer calls about renewing their home insurance"""
        
        # Customer service workflow for renewal
        policies = get_policies(self.test_customer_id)
        home_policies = [p for p in policies if p.get("type") == "Home"]
        
        if home_policies:
            home_policy_id = home_policies[0].get("id")
            
            # Get detailed information for renewal discussion
            policy_details = get_policy_details(home_policy_id)
            coverage_info = get_coverage_information(self.test_customer_id)
            home_coverage = [c for c in coverage_info if c.get("policy_id") == home_policy_id]
            
            # Verify agent has information for renewal
            assert isinstance(policy_details, dict)
            assert isinstance(coverage_info, list)
            
            if "error" not in policy_details and home_coverage:
                print(f"✅ Home policy renewal information available")

    def test_claims_preparation_scenario(self):
        """Test: Customer about to file a claim needs deductible information"""
        
        # Customer needs to know their deductibles before filing claim
        deductibles = get_deductibles(self.test_customer_id)
        
        # Verify deductible information is available
        assert isinstance(deductibles, list)
        
        if deductibles:
            # Group deductibles by policy type
            by_type = {}
            for ded in deductibles:
                policy_type = ded.get("type", "Unknown")
                if policy_type not in by_type:
                    by_type[policy_type] = []
                by_type[policy_type].append(ded)
            
            print(f"✅ Deductibles available for {len(by_type)} policy types")
            
            # Customer can make informed decision about filing claim
            for policy_type, deductible_list in by_type.items():
                print(f"  {policy_type}: {len(deductible_list)} policies")

class TestAPIPerformanceComparison:
    """Performance comparison tests between focused and comprehensive APIs"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_customer_id = "CUST-001"

    def test_response_time_comparison(self):
        """Compare response times between focused and comprehensive APIs"""
        
        # Test comprehensive API timing
        start_time = time.time()
        comprehensive_data = get_customer_policies(self.test_customer_id)
        comprehensive_time = time.time() - start_time
        
        # Test focused API timing
        start_time = time.time()
        focused_data = get_policies(self.test_customer_id)
        focused_time = time.time() - start_time
        
        print(f"✅ Comprehensive API: {comprehensive_time:.4f}s")
        print(f"✅ Focused API: {focused_time:.4f}s")
        
        # Focused API should be faster or similar
        assert focused_time <= comprehensive_time * 2.0  # Allow reasonable margin

    def test_data_transfer_efficiency(self):
        """Measure data transfer efficiency across different scenarios"""
        
        scenarios = [
            ("Quick Policy Check", lambda: get_policies(self.test_customer_id)),
            ("Agent Contact", lambda: get_agent(self.test_customer_id)),
            ("Payment Info", lambda: get_payment_information(self.test_customer_id)),
            ("Policy Types", lambda: get_policy_types(self.test_customer_id)),
        ]
        
        # Get baseline comprehensive data size
        comprehensive_data = get_customer_policies(self.test_customer_id)
        baseline_size = len(json.dumps(comprehensive_data))
        
        if baseline_size > 0:
            print(f"Baseline comprehensive data: {baseline_size} bytes")
            
            for scenario_name, api_call in scenarios:
                focused_data = api_call()
                focused_size = len(json.dumps(focused_data))
                efficiency = (baseline_size - focused_size) / baseline_size
                
                print(f"✅ {scenario_name}: {efficiency:.1%} reduction ({focused_size} bytes)")
                assert efficiency >= -1.0  # Allow focused APIs to be larger in some cases

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 