#!/usr/bin/env python3
"""
Test script to validate auto policy response fixes
"""

import json
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'domain_agent'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'technical_agent'))

def test_mock_data_integrity():
    """Test that mock data has correct vehicle information"""
    print("=== Testing Mock Data Integrity ===")
    
    with open('data/mock_data.json', 'r') as f:
        data = json.load(f)
    
    cust_001_policies = [p for p in data['policies'] if p['customer_id'] == 'CUST-001']
    
    print(f"Found {len(cust_001_policies)} policies for CUST-001:")
    
    for policy in cust_001_policies:
        print(f"\nPolicy {policy['id']}:")
        print(f"  Type: {policy['type']}")
        print(f"  Status: {policy['status']}")
        print(f"  Coverage: ${policy['coverage_amount']:,.2f}")
        
        if 'details' in policy and 'vehicle' in policy['details']:
            vehicle = policy['details']['vehicle']
            print(f"  Vehicle: {vehicle['year']} {vehicle['make']} {vehicle['model']}")
            print(f"  VIN: {vehicle['vin']}")
            
            # Verify correct vehicle data
            if vehicle['make'] == 'Honda' and vehicle['model'] == 'Civic':
                print("  ✅ Correct vehicle data: Honda Civic")
            else:
                print(f"  ❌ Unexpected vehicle data: {vehicle['make']} {vehicle['model']}")

def test_response_formatter_template_selection():
    """Test template selection logic"""
    print("\n=== Testing Template Selection ===")
    
    try:
        from response_formatter import ResponseFormatter
        
        formatter = ResponseFormatter()
        
        test_cases = [
            ("Show me my auto policy details", "auto_policy_template"),
            ("What's my vehicle information?", "auto_policy_template"),
            ("Tell me about my car insurance", "auto_policy_template"),
            ("Show me my life insurance", "life_policy_template"),
            ("Who are my beneficiaries?", "life_policy_template"),
            ("What are all my policies?", "policy_response_template"),
            ("What are my payment dates?", "payment_due_template"),
        ]
        
        for question, expected_template in test_cases:
            selected_template = formatter._get_template_key_for_intent_and_question("policy_inquiry", question)
            status = "✅" if selected_template == expected_template else "❌"
            print(f"  {status} '{question}' → {selected_template} (expected: {expected_template})")
            
    except ImportError as e:
        print(f"  ❌ Could not import ResponseFormatter: {e}")

def test_prompt_improvements():
    """Test that prompts include the new filtering rules"""
    print("\n=== Testing Prompt Improvements ===")
    
    try:
        from prompt_loader import PromptLoader
        
        prompts = PromptLoader()
        formatting_prompt = prompts.prompts.get("llm_formatting", {}).get("format_response_prompt", "")
        
        required_elements = [
            "POLICY TYPE FILTERING RULES",
            "DO NOT change Honda Civic to Honda City",
            "DO NOT mention vehicles that are not in the customer's actual policy data",
            "focus your response on that policy type only"
        ]
        
        for element in required_elements:
            if element in formatting_prompt:
                print(f"  ✅ Found: '{element}'")
            else:
                print(f"  ❌ Missing: '{element}'")
                
    except ImportError as e:
        print(f"  ❌ Could not import PromptLoader: {e}")

def simulate_auto_policy_query():
    """Simulate what should happen with an auto policy query"""
    print("\n=== Simulating Auto Policy Query ===")
    
    # Mock technical response (what would come from technical agent)
    mock_technical_response = json.dumps({
        "customer_id": "CUST-001",
        "total_policies": 2,
        "policies": [
            {
                "id": "POL-2024-AUTO-002",
                "type": "auto",
                "status": "active",
                "premium": 95.00,
                "coverage_amount": 75000.00,
                "deductible": 750.00,
                "billing_cycle": "quarterly",
                "next_payment_due": "2024-09-01T00:00:00Z",
                "details": {
                    "vehicle": {
                        "make": "Honda",
                        "model": "Civic",
                        "year": 2019,
                        "vin": "2HGFC2F59KH123456"
                    },
                    "coverage_types": ["liability", "collision", "comprehensive"]
                }
            }
        ]
    }, indent=2)
    
    print("Expected response should:")
    print("  ✅ Focus on AUTO policy only")
    print("  ✅ Show Honda Civic (NOT Honda City)")
    print("  ✅ Not mention life insurance prominently")
    print("  ✅ Include vehicle details: 2019 Honda Civic")
    print("  ✅ Include coverage types: liability, collision, comprehensive")
    print("\nMock technical response preview:")
    print(mock_technical_response[:200] + "...")

if __name__ == "__main__":
    print("🔧 Testing Auto Policy Response Fixes\n")
    
    test_mock_data_integrity()
    test_response_formatter_template_selection()
    test_prompt_improvements()
    simulate_auto_policy_query()
    
    print("\n🎯 Summary:")
    print("The fixes should now:")
    print("1. Use auto_policy_template when 'auto' is mentioned in question")
    print("2. Never change Honda Civic to Honda City")
    print("3. Focus only on auto policy when specifically requested")
    print("4. Not make up vehicle information")
    print("\nTo test fully, run the system and ask: 'Show me my auto policy for CUST-001'") 