#!/usr/bin/env python3
"""
Comprehensive Domain Agent API Testing
Tests the Claims Agent with various customer scenarios using A2A protocol
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List
import pytest

class DomainAgentTester:
    """Test suite for Domain Agent API functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """Test domain agent health endpoint"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                result = await response.json()
                return {
                    "status": "PASS" if response.status == 200 else "FAIL",
                    "response_code": response.status,
                    "data": result,
                    "message": "Health check successful" if response.status == 200 else f"Health check failed: {response.status}"
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Health check failed: {e}",
                "error": str(e)
            }
    
    async def send_message(self, message: str, customer_id: str = "CUST-001") -> Dict[str, Any]:
        """Send message to domain agent and get response"""
        try:
            payload = {
                "message": message,
                "customer_id": customer_id,
                "timestamp": time.time()
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/chat", 
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                duration = (time.time() - start_time) * 1000
                result = await response.json()
                
                return {
                    "status": "PASS" if response.status == 200 else "FAIL",
                    "response_code": response.status,
                    "response_time_ms": duration,
                    "message": message,
                    "response": result.get("response", ""),
                    "thinking_steps": result.get("thinking_steps", []),
                    "orchestration_events": result.get("orchestration_events", []),
                    "api_calls": result.get("api_calls", []),
                    "metadata": result.get("metadata", {})
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Message sending failed: {e}",
                "error": str(e)
            }
    
    async def test_policy_inquiry_scenarios(self) -> List[Dict[str, Any]]:
        """Test various policy inquiry scenarios"""
        
        scenarios = [
            {
                "name": "Basic Policy Question",
                "message": "What policies do I have?",
                "expected_intent": "policy_question",
                "expected_actions": ["data_agent"]
            },
            {
                "name": "Policy Details Request",
                "message": "Tell me about my policies",
                "expected_intent": "policy_question", 
                "expected_actions": ["data_agent"]
            },
            {
                "name": "Coverage Question",
                "message": "What insurance policies do I have?",
                "expected_intent": "policy_question",
                "expected_actions": ["data_agent"]
            },
            {
                "name": "Coverage Amount Question",
                "message": "How much coverage do I have on my auto policy?",
                "expected_intent": "policy_question",
                "expected_actions": ["data_agent"]
            },
            {
                "name": "Renewal Question",
                "message": "When does my policy renew?",
                "expected_intent": "policy_question",
                "expected_actions": ["data_agent"]
            }
        ]
        
        results = []
        for scenario in scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            result = await self.send_message(scenario["message"])
            
            # Analyze the response
            analysis = self._analyze_response(result, scenario)
            result.update(analysis)
            results.append(result)
            
            print(f"   Result: {'✅ PASS' if result['analysis']['overall'] == 'PASS' else '❌ FAIL'}")
            if result['analysis']['issues']:
                for issue in result['analysis']['issues']:
                    print(f"   ⚠️ Issue: {issue}")
        
        return results
    
    async def test_claims_scenarios(self) -> List[Dict[str, Any]]:
        """Test claims-related scenarios"""
        
        scenarios = [
            {
                "name": "Check Claim Status",
                "message": "What's the status of my claim?",
                "expected_intent": "check_status",
                "expected_actions": ["data_agent"]
            },
            {
                "name": "File New Claim",
                "message": "I need to file a claim for my car accident",
                "expected_intent": "file_claim",
                "expected_actions": ["data_agent", "notification_agent"]
            },
            {
                "name": "Claims History",
                "message": "Show me my claims history",
                "expected_intent": "check_status",
                "expected_actions": ["data_agent"]
            },
            {
                "name": "Claim Documentation",
                "message": "What documents do I need for my claim?",
                "expected_intent": "general_question",
                "expected_actions": []
            }
        ]
        
        results = []
        for scenario in scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            result = await self.send_message(scenario["message"])
            
            analysis = self._analyze_response(result, scenario)
            result.update(analysis)
            results.append(result)
            
            print(f"   Result: {'✅ PASS' if result['analysis']['overall'] == 'PASS' else '❌ FAIL'}")
            if result['analysis']['issues']:
                for issue in result['analysis']['issues']:
                    print(f"   ⚠️ Issue: {issue}")
        
        return results
    
    async def test_fraud_detection_scenarios(self) -> List[Dict[str, Any]]:
        """Test fraud detection scenarios"""
        
        scenarios = [
            {
                "name": "Suspicious Claim Pattern",
                "message": "I had another accident today, need to file another claim",
                "expected_intent": "file_claim",
                "expected_actions": ["data_agent"]
            },
            {
                "name": "High Value Claim",
                "message": "My $50,000 jewelry was stolen, I need to file a claim",
                "expected_intent": "file_claim",
                "expected_actions": ["data_agent", "notification_agent"]
            }
        ]
        
        results = []
        for scenario in scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            result = await self.send_message(scenario["message"])
            
            analysis = self._analyze_response(result, scenario)
            result.update(analysis)
            results.append(result)
            
            print(f"   Result: {'✅ PASS' if result['analysis']['overall'] == 'PASS' else '❌ FAIL'}")
        
        return results
    
    def _analyze_response(self, result: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response quality and correctness"""
        
        issues = []
        checks = {
            "response_received": bool(result.get("response")),
            "thinking_steps_present": len(result.get("thinking_steps", [])) > 0,
            "orchestration_events": len(result.get("orchestration_events", [])) > 0,
            "api_calls_made": len(result.get("api_calls", [])) > 0,
            "non_generic_response": not self._is_generic_response(result.get("response", ""))
        }
        
        # Check if response is generic/unhelpful
        if self._is_generic_response(result.get("response", "")):
            issues.append("Generic/unhelpful response detected")
        
        # Check if thinking steps show proper reasoning
        thinking_steps = result.get("thinking_steps", [])
        if not thinking_steps:
            issues.append("No thinking steps recorded")
        elif len(thinking_steps) < 2:
            issues.append("Insufficient reasoning depth")
        
        # Check if orchestration events show A2A communication
        orchestration = result.get("orchestration_events", [])
        if not orchestration:
            issues.append("No orchestration events - not communicating with technical agents")
        
        # Check if expected actions were taken - FIXED to detect localhost endpoints
        expected_actions = scenario.get("expected_actions", [])
        if expected_actions:
            api_calls = result.get("api_calls", [])
            called_agents = set()
            for call in api_calls:
                endpoint = call.get("endpoint", "")
                # Updated to detect localhost endpoints
                if "localhost:8004" in endpoint or "data-agent" in endpoint:
                    called_agents.add("data_agent")
                elif "localhost:8005" in endpoint or "notification-agent" in endpoint:
                    called_agents.add("notification_agent")
            
            for expected_agent in expected_actions:
                if expected_agent not in called_agents:
                    issues.append(f"Expected call to {expected_agent} but not made")
        
        # Overall assessment
        critical_checks = ["response_received", "non_generic_response"]
        critical_passed = all(checks[check] for check in critical_checks)
        
        overall_score = sum(checks.values()) / len(checks) * 100
        
        return {
            "analysis": {
                "overall": "PASS" if critical_passed and len(issues) <= 2 else "FAIL",
                "score": overall_score,
                "checks": checks,
                "issues": issues,
                "scenario_name": scenario["name"]
            }
        }
    
    def _is_generic_response(self, response: str) -> bool:
        """Check if response is generic/unhelpful"""
        generic_phrases = [
            "Could you please rephrase your question",
            "I'm here to help with your insurance needs",
            "Could you be more specific",
            "I'd be happy to help",
            "Please provide more details"
        ]
        
        response_lower = response.lower()
        return any(phrase.lower() in response_lower for phrase in generic_phrases)
    
    async def test_template_usage(self) -> Dict[str, Any]:
        """Test if agent uses template-based responses"""
        
        # Send a message that should trigger template usage
        result = await self.send_message("What's the status of my claim?")
        
        response = result.get("response", "")
        
        # Check for template indicators - UPDATED for our actual template format
        template_indicators = [
            "**Current Claims Status",
            "**Active Claims:**",
            "**Primary Claim Status:**",
            "**Estimated Resolution:**",
            "**Next Steps:**",
            "claim(s) currently being processed",
            "standard review process",
            "24-48 hours"
        ]
        
        found_indicators = sum(1 for indicator in template_indicators if indicator in response)
        
        return {
            "status": "PASS" if found_indicators >= 3 else "FAIL",
            "template_indicators_found": found_indicators,
            "total_indicators": len(template_indicators),
            "response_length": len(response),
            "uses_template": found_indicators >= 3,
            "message": f"Found {found_indicators}/{len(template_indicators)} template indicators"
        }
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run all domain agent tests"""
        
        print("🧪 Domain Agent Comprehensive Test Suite")
        print("="*60)
        
        # Test health check
        print("\n🔍 Testing Health Check...")
        health_result = await self.test_health_check()
        print(f"   Health: {'✅ PASS' if health_result['status'] == 'PASS' else '❌ FAIL'}")
        
        # Test template usage
        print("\n🔍 Testing Template Usage...")
        template_result = await self.test_template_usage()
        print(f"   Template: {'✅ PASS' if template_result['status'] == 'PASS' else '❌ FAIL'}")
        
        # Test different scenarios
        print("\n🔍 Testing Policy Inquiry Scenarios...")
        policy_results = await self.test_policy_inquiry_scenarios()
        
        print("\n🔍 Testing Claims Scenarios...")
        claims_results = await self.test_claims_scenarios()
        
        print("\n🔍 Testing Fraud Detection Scenarios...")
        fraud_results = await self.test_fraud_detection_scenarios()
        
        # Calculate overall results
        all_results = policy_results + claims_results + fraud_results
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r.get('analysis', {}).get('overall') == 'PASS')
        
        # Summary
        print("\n" + "="*60)
        print("📊 DOMAIN AGENT TEST SUMMARY")
        print("="*60)
        print(f"Health Check: {'✅ PASS' if health_result['status'] == 'PASS' else '❌ FAIL'}")
        print(f"Template Usage: {'✅ PASS' if template_result['status'] == 'PASS' else '❌ FAIL'}")
        print(f"Scenario Tests: {passed_tests}/{total_tests} passed")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Issues summary
        all_issues = []
        for result in all_results:
            issues = result.get('analysis', {}).get('issues', [])
            all_issues.extend(issues)
        
        if all_issues:
            print(f"\n⚠️ Common Issues Detected:")
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {issue} ({count} times)")
        
        overall_success = (health_result['status'] == 'PASS' and 
                          template_result['status'] == 'PASS' and 
                          passed_tests >= total_tests * 0.7)
        
        print(f"\nOverall Result: {'✅ SUCCESS' if overall_success else '❌ NEEDS IMPROVEMENT'}")
        print("="*60)
        
        return {
            "overall_success": overall_success,
            "health_check": health_result,
            "template_usage": template_result,
            "scenario_results": {
                "policy_scenarios": policy_results,
                "claims_scenarios": claims_results,
                "fraud_scenarios": fraud_results
            },
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
                "common_issues": issue_counts if 'issue_counts' in locals() else {}
            }
        }

async def main():
    """Main test runner"""
    
    # Test with domain agent
    async with DomainAgentTester("http://localhost:8000") as tester:
        results = await tester.run_comprehensive_test_suite()
        
        # Save results
        with open("tests/integration/domain_agent_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: tests/integration/domain_agent_test_results.json")
        
        return results["overall_success"]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 