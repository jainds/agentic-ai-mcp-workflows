#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Agent Communication
Tests to prevent similar issues across all agents
"""

import pytest
import asyncio
import httpx
import json
import time
from typing import Dict, Any, List
from datetime import datetime


class AgentIntegrationTests:
    """Integration tests for multi-agent system"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.agent_ports = {
            "support-agent": 30005,
            "claims-agent": 30008,
            "customer-agent": 8010,
            "policy-agent": 8011,
            "claims-data-agent": 8012,
        }
        
    async def test_agent_health_checks(self) -> Dict[str, bool]:
        """Test all agents are healthy and responding"""
        results = {}
        
        async with httpx.AsyncClient() as client:
            for agent_name, port in self.agent_ports.items():
                try:
                    # External agents (NodePort)
                    if port >= 30000:
                        url = f"{self.base_url}:{port}/health"
                    else:
                        # Internal agents - test via kubectl exec
                        continue
                    
                    response = await client.get(url, timeout=10.0)
                    response.raise_for_status()
                    
                    health_data = response.json()
                    results[agent_name] = {
                        "healthy": health_data.get("status") == "healthy",
                        "response_time": response.elapsed.total_seconds(),
                        "skills_count": len(health_data.get("skills", [])),
                        "agent_type": health_data.get("agent_type")
                    }
                    
                except Exception as e:
                    results[agent_name] = {
                        "healthy": False,
                        "error": str(e)
                    }
        
        return results
    
    async def test_claim_inquiry_end_to_end(self) -> Dict[str, Any]:
        """Test complete claim inquiry workflow"""
        test_cases = [
            {
                "name": "claim_status_with_ids",
                "message": "What is my claim status? my claimid is 1002, customer id is 101",
                "expected_claim_id": 1002,
                "expected_customer_id": 101,
                "expected_workflow": "claim_status"
            },
            {
                "name": "claim_status_different_format",
                "message": "I need to check claim #1001 for customer 101",
                "expected_claim_id": 1001,
                "expected_customer_id": 101,
                "expected_workflow": "claim_status"
            },
            {
                "name": "general_claim_question",
                "message": "How do I file a new claim?",
                "expected_workflow": "general_claims_support"
            }
        ]
        
        results = {}
        
        async with httpx.AsyncClient() as client:
            for test_case in test_cases:
                try:
                    payload = {
                        "skill_name": "HandleClaimInquiry",
                        "parameters": {
                            "user_message": test_case["message"]
                        }
                    }
                    
                    start_time = time.time()
                    response = await client.post(
                        f"{self.base_url}:30008/execute",
                        json=payload,
                        timeout=60.0
                    )
                    response_time = time.time() - start_time
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    # Analyze response
                    success = result.get("success", False)
                    agent_result = result.get("result", {})
                    workflow = agent_result.get("workflow")
                    
                    # Check ID extraction (if expected)
                    claim_data = agent_result.get("data", {}).get("claim", {})
                    extracted_claim_id = claim_data.get("claim_id")
                    
                    results[test_case["name"]] = {
                        "success": success,
                        "agent_success": agent_result.get("success", False),
                        "workflow": workflow,
                        "extracted_claim_id": extracted_claim_id,
                        "response_time": response_time,
                        "has_response": bool(agent_result.get("response")),
                        "expected_workflow_match": workflow == test_case.get("expected_workflow"),
                        "expected_claim_id_match": extracted_claim_id == test_case.get("expected_claim_id"),
                        "raw_response": result
                    }
                    
                except Exception as e:
                    results[test_case["name"]] = {
                        "success": False,
                        "error": str(e)
                    }
        
        return results
    
    async def test_id_extraction_accuracy(self) -> Dict[str, Any]:
        """Test ID extraction from various message formats"""
        test_messages = [
            {"message": "claimid is 1002", "expected_claim": 1002, "expected_customer": None},
            {"message": "customer id is 101", "expected_claim": None, "expected_customer": 101},
            {"message": "claim #1001", "expected_claim": 1001, "expected_customer": None},
            {"message": "my claim 2001 status", "expected_claim": 2001, "expected_customer": None},
            {"message": "customer 12345 claim 2002", "expected_claim": 2002, "expected_customer": 12345},
            {"message": "CLM-AUTO-20240115-001", "expected_claim": 1, "expected_customer": None},  # Should extract numbers
            {"message": "no numbers here", "expected_claim": None, "expected_customer": None},
        ]
        
        results = {}
        
        for i, test in enumerate(test_messages):
            try:
                # Test via the simple inquiry to see extraction
                payload = {
                    "skill_name": "HandleClaimInquiry", 
                    "parameters": {"user_message": test["message"]}
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}:30008/execute",
                        json=payload,
                        timeout=30.0
                    )
                    result = response.json()
                    
                    # Look for extracted IDs in the response or logs
                    claim_data = result.get("result", {}).get("data", {}).get("claim", {})
                    extracted_claim = claim_data.get("claim_id")
                    
                    results[f"test_{i}_{test['message'][:20]}"] = {
                        "message": test["message"],
                        "expected_claim": test["expected_claim"],
                        "expected_customer": test["expected_customer"],
                        "extracted_claim": extracted_claim,
                        "claim_match": extracted_claim == test["expected_claim"],
                        "success": result.get("success", False)
                    }
                    
            except Exception as e:
                results[f"test_{i}_error"] = {
                    "message": test["message"],
                    "error": str(e)
                }
        
        return results
    
    async def test_technical_agent_connectivity(self) -> Dict[str, Any]:
        """Test connectivity between domain and technical agents"""
        test_calls = [
            {
                "agent": "claims-data-agent",
                "skill": "GetClaimStatus",
                "params": {"claim_id": 1002},
                "expected_fields": ["claim_id", "status", "claim_number"]
            },
            {
                "agent": "claims-data-agent", 
                "skill": "GetCustomerClaims",
                "params": {"customer_id": 101},
                "expected_fields": ["claims"]
            }
        ]
        
        results = {}
        
        # Test direct technical agent calls
        for test in test_calls:
            try:
                # We can't directly test internal agents, but we can test via domain agent
                payload = {
                    "skill_name": "GetClaimStatus",
                    "parameters": test["params"]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}:30008/execute",
                        json=payload,
                        timeout=30.0
                    )
                    result = response.json()
                    
                    success = result.get("success", False)
                    agent_result = result.get("result", {})
                    
                    # Check if expected fields are present
                    has_expected_fields = all(
                        field in str(agent_result) for field in test["expected_fields"]
                    )
                    
                    results[f"{test['agent']}_{test['skill']}"] = {
                        "success": success,
                        "agent_success": agent_result.get("success", False),
                        "has_expected_fields": has_expected_fields,
                        "response_present": bool(agent_result)
                    }
                    
            except Exception as e:
                results[f"{test['agent']}_{test['skill']}_error"] = {
                    "error": str(e)
                }
        
        return results
    
    async def test_llm_integration(self) -> Dict[str, Any]:
        """Test LLM API integration and fallbacks"""
        test_scenarios = [
            {
                "name": "intent_detection",
                "message": "I want to check my claim status",
                "expected_intent": "claim_status"
            },
            {
                "name": "claim_filing_intent", 
                "message": "I need to file a new insurance claim",
                "expected_intent": "claim_filing"
            },
            {
                "name": "general_support",
                "message": "What is your phone number?",
                "expected_intent": "general_support"
            }
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            try:
                payload = {
                    "skill_name": "HandleClaimInquiry",
                    "parameters": {"user_message": scenario["message"]}
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}:30008/execute",
                        json=payload,
                        timeout=60.0
                    )
                    result = response.json()
                    
                    agent_result = result.get("result", {})
                    workflow = agent_result.get("workflow")
                    has_response = bool(agent_result.get("response"))
                    
                    results[scenario["name"]] = {
                        "success": result.get("success", False),
                        "workflow": workflow,
                        "intent_match": workflow == scenario["expected_intent"],
                        "has_response": has_response,
                        "response_length": len(agent_result.get("response", "")),
                    }
                    
            except Exception as e:
                results[scenario["name"]] = {
                    "error": str(e),
                    "success": False
                }
        
        return results
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and recovery"""
        error_tests = [
            {
                "name": "invalid_claim_id",
                "skill": "GetClaimStatus", 
                "params": {"claim_id": 99999},
                "expect_graceful_failure": True
            },
            {
                "name": "invalid_customer_id",
                "skill": "HandleClaimInquiry",
                "params": {"user_message": "claim status for customer 99999"},
                "expect_graceful_failure": True
            },
            {
                "name": "malformed_request",
                "skill": "NonExistentSkill",
                "params": {},
                "expect_graceful_failure": True
            }
        ]
        
        results = {}
        
        for test in error_tests:
            try:
                payload = {
                    "skill_name": test["skill"],
                    "parameters": test["params"]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}:30008/execute",
                        json=payload,
                        timeout=30.0
                    )
                    
                    # Should get a response even for errors
                    result = response.json()
                    
                    # Check for graceful error handling
                    has_error_message = bool(
                        result.get("result", {}).get("response") or 
                        result.get("error")
                    )
                    
                    results[test["name"]] = {
                        "http_success": response.status_code == 200,
                        "has_error_message": has_error_message,
                        "graceful_failure": has_error_message and response.status_code == 200,
                        "result": result
                    }
                    
            except Exception as e:
                results[test["name"]] = {
                    "http_success": False,
                    "exception": str(e)
                }
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🧪 Running Comprehensive Agent Integration Tests...")
        
        all_results = {}
        
        # Test 1: Health checks
        print("\n1️⃣ Testing agent health...")
        all_results["health_checks"] = await self.test_agent_health_checks()
        
        # Test 2: End-to-end claim inquiry
        print("2️⃣ Testing end-to-end claim inquiry...")
        all_results["claim_inquiry_e2e"] = await self.test_claim_inquiry_end_to_end()
        
        # Test 3: ID extraction accuracy
        print("3️⃣ Testing ID extraction accuracy...")
        all_results["id_extraction"] = await self.test_id_extraction_accuracy()
        
        # Test 4: Technical agent connectivity
        print("4️⃣ Testing technical agent connectivity...")
        all_results["technical_connectivity"] = await self.test_technical_agent_connectivity()
        
        # Test 5: LLM integration
        print("5️⃣ Testing LLM integration...")
        all_results["llm_integration"] = await self.test_llm_integration()
        
        # Test 6: Error handling
        print("6️⃣ Testing error handling...")
        all_results["error_handling"] = await self.test_error_handling()
        
        return all_results


async def main():
    """Run the integration tests"""
    tester = AgentIntegrationTests()
    results = await tester.run_all_tests()
    
    # Generate summary report
    print("\n" + "="*60)
    print("🏁 INTEGRATION TEST SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, tests in results.items():
        print(f"\n📊 {category.upper().replace('_', ' ')}:")
        
        if isinstance(tests, dict):
            for test_name, result in tests.items():
                total_tests += 1
                
                if isinstance(result, dict):
                    success = result.get("success", result.get("healthy", result.get("graceful_failure", False)))
                    status = "✅ PASS" if success else "❌ FAIL"
                    
                    if success:
                        passed_tests += 1
                    
                    print(f"  {status} {test_name}")
                    
                    # Show key metrics
                    if "response_time" in result:
                        print(f"      ⏱️  Response time: {result['response_time']:.2f}s")
                    if "workflow" in result:
                        print(f"      🔄 Workflow: {result['workflow']}")
                    if "error" in result:
                        print(f"      ❌ Error: {result['error']}")
    
    # Overall success rate
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\n🎯 OVERALL SUCCESS RATE: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT! System is performing well.")
    elif success_rate >= 75:
        print("⚠️  GOOD: Some issues need attention.")
    else:
        print("🚨 CRITICAL: Multiple failures detected.")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"test_results_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📝 Detailed results saved to: test_results_{timestamp}.json")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 