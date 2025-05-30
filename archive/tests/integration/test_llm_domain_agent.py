#!/usr/bin/env python3
"""
Test LLM-Powered Domain Agent Architecture
Validates proper LLM reasoning, A2A orchestration, and template usage
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, List

class LLMDomainAgentTester:
    """Test suite for LLM-powered domain agent architecture compliance"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_architecture_compliance(self) -> Dict[str, Any]:
        """Test architecture compliance: LLM reasoning → A2A → Technical agents"""
        
        print("🧠 Testing LLM-Powered Domain Agent Architecture")
        print("="*60)
        
        results = {
            "architecture_compliance": {},
            "llm_reasoning_tests": {},
            "a2a_orchestration_tests": {},
            "template_usage_tests": {},
            "overall_compliance": False
        }
        
        # Test 1: Architecture Understanding
        print("\n🔍 Testing Architecture Understanding...")
        arch_test = await self._test_architecture_understanding()
        results["architecture_compliance"] = arch_test
        print(f"   Architecture: {'✅ PASS' if arch_test['compliant'] else '❌ FAIL'}")
        
        # Test 2: LLM Reasoning 
        print("\n🔍 Testing LLM Reasoning...")
        llm_test = await self._test_llm_reasoning()
        results["llm_reasoning_tests"] = llm_test
        print(f"   LLM Reasoning: {'✅ PASS' if llm_test['llm_powered'] else '❌ FAIL'}")
        
        # Test 3: A2A Orchestration
        print("\n🔍 Testing A2A Orchestration...")
        a2a_test = await self._test_a2a_orchestration()
        results["a2a_orchestration_tests"] = a2a_test
        print(f"   A2A Orchestration: {'✅ PASS' if a2a_test['orchestration_working'] else '❌ FAIL'}")
        
        # Test 4: Template Usage
        print("\n🔍 Testing Template Usage...")
        template_test = await self._test_template_usage()
        results["template_usage_tests"] = template_test
        print(f"   Template Usage: {'✅ PASS' if template_test['template_used'] else '❌ FAIL'}")
        
        # Overall compliance
        compliance_score = (
            arch_test["compliant"] +
            llm_test["llm_powered"] + 
            a2a_test["orchestration_working"] +
            template_test["template_used"]
        )
        
        results["overall_compliance"] = compliance_score >= 3  # At least 3/4 must pass
        
        print("\n" + "="*60)
        print("📊 ARCHITECTURE COMPLIANCE SUMMARY")
        print("="*60)
        print(f"Architecture Understanding: {'✅ PASS' if arch_test['compliant'] else '❌ FAIL'}")
        print(f"LLM Reasoning: {'✅ PASS' if llm_test['llm_powered'] else '❌ FAIL'}")
        print(f"A2A Orchestration: {'✅ PASS' if a2a_test['orchestration_working'] else '❌ FAIL'}")
        print(f"Template Usage: {'✅ PASS' if template_test['template_used'] else '❌ FAIL'}")
        print(f"Compliance Score: {compliance_score}/4")
        print(f"Overall Result: {'✅ ARCHITECTURE COMPLIANT' if results['overall_compliance'] else '❌ ARCHITECTURE VIOLATION'}")
        
        return results
    
    async def _test_architecture_understanding(self) -> Dict[str, Any]:
        """Test if the agent understands the proper architecture"""
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "compliant": True,
                        "agent_type": data.get("agent"),
                        "llm_enabled": data.get("llm_enabled", False),
                        "technical_agents": data.get("technical_agents", []),
                        "architecture_indicators": {
                            "has_technical_agents": len(data.get("technical_agents", [])) > 0,
                            "llm_enabled": data.get("llm_enabled", False),
                            "proper_naming": "LLM" in data.get("agent", "")
                        }
                    }
                else:
                    return {"compliant": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"compliant": False, "error": str(e)}
    
    async def _test_llm_reasoning(self) -> Dict[str, Any]:
        """Test if the agent uses LLM reasoning for intent detection and planning"""
        
        try:
            test_message = "What policies do I have?"
            payload = {"message": test_message, "customer_id": "CUST-001"}
            
            async with self.session.post(f"{self.base_url}/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    thinking_steps = data.get("thinking_steps", [])
                    metadata = data.get("metadata", {})
                    
                    # Check for LLM reasoning indicators
                    llm_indicators = {
                        "llm_powered_metadata": metadata.get("llm_powered", False),
                        "llm_thinking_steps": any("LLM" in step for step in thinking_steps),
                        "intent_confidence": metadata.get("confidence", 0) > 0,
                        "processing_shows_reasoning": len(thinking_steps) > 3
                    }
                    
                    return {
                        "llm_powered": sum(llm_indicators.values()) >= 2,
                        "indicators": llm_indicators,
                        "intent_detected": metadata.get("intent"),
                        "confidence": metadata.get("confidence"),
                        "thinking_steps_count": len(thinking_steps)
                    }
                else:
                    return {"llm_powered": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"llm_powered": False, "error": str(e)}
    
    async def _test_a2a_orchestration(self) -> Dict[str, Any]:
        """Test if the agent properly orchestrates A2A protocol calls"""
        
        try:
            test_message = "Tell me about my policies"
            payload = {"message": test_message, "customer_id": "CUST-001"}
            
            async with self.session.post(f"{self.base_url}/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    orchestration_events = data.get("orchestration_events", [])
                    api_calls = data.get("api_calls", [])
                    thinking_steps = data.get("thinking_steps", [])
                    
                    # Check orchestration indicators
                    orchestration_indicators = {
                        "has_orchestration_events": len(orchestration_events) > 0,
                        "has_api_calls": len(api_calls) > 0,
                        "calls_technical_agents": any("technical_agent_call" in event.get("event", "") for event in orchestration_events),
                        "proper_a2a_endpoints": any("localhost:800" in call.get("endpoint", "") for call in api_calls),
                        "orchestration_planning": any("orchestration" in step.lower() for step in thinking_steps)
                    }
                    
                    return {
                        "orchestration_working": sum(orchestration_indicators.values()) >= 3,
                        "indicators": orchestration_indicators,
                        "orchestration_events_count": len(orchestration_events),
                        "api_calls_count": len(api_calls),
                        "technical_agents_called": list(set(event.get("details", {}).get("agent") for event in orchestration_events if event.get("details", {}).get("agent")))
                    }
                else:
                    return {"orchestration_working": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"orchestration_working": False, "error": str(e)}
    
    async def _test_template_usage(self) -> Dict[str, Any]:
        """Test if the agent uses template-based responses"""
        
        try:
            test_message = "What's the status of my claim?"
            payload = {"message": test_message, "customer_id": "CUST-001"}
            
            async with self.session.post(f"{self.base_url}/chat", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    response_text = data.get("response", "")
                    thinking_steps = data.get("thinking_steps", [])
                    
                    # Check for template usage indicators
                    template_indicators = {
                        "structured_response": "**" in response_text,  # Markdown formatting
                        "professional_sections": response_text.count("**") >= 4,  # Multiple sections
                        "template_thinking": any("template" in step.lower() for step in thinking_steps),
                        "comprehensive_response": len(response_text) > 200,
                        "customer_personalization": "customer" in response_text.lower() or "policy" in response_text.lower()
                    }
                    
                    return {
                        "template_used": sum(template_indicators.values()) >= 3,
                        "indicators": template_indicators,
                        "response_length": len(response_text),
                        "template_indicators_found": sum(template_indicators.values())
                    }
                else:
                    return {"template_used": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"template_used": False, "error": str(e)}
    
    async def test_no_mock_data_violation(self) -> Dict[str, Any]:
        """Test that the agent doesn't use hardcoded mock data inappropriately"""
        
        print("\n🔍 Testing No Mock Data Violation...")
        
        try:
            # Test with different customer IDs to ensure no hardcoded responses
            test_cases = [
                {"customer_id": "CUST-001", "message": "What policies do I have?"},
                {"customer_id": "CUST-999", "message": "What policies do I have?"},
                {"customer_id": "CUST-TEST", "message": "What policies do I have?"}
            ]
            
            responses = []
            for test_case in test_cases:
                async with self.session.post(f"{self.base_url}/chat", json=test_case) as response:
                    if response.status == 200:
                        data = await response.json()
                        responses.append({
                            "customer_id": test_case["customer_id"],
                            "response": data.get("response", ""),
                            "orchestration_events": len(data.get("orchestration_events", [])),
                            "api_calls": len(data.get("api_calls", []))
                        })
            
            # Check if responses are properly orchestrated (not just hardcoded)
            proper_orchestration = all(r["orchestration_events"] > 0 for r in responses)
            attempts_real_calls = all(r["api_calls"] > 0 for r in responses)
            
            return {
                "no_mock_violation": proper_orchestration and attempts_real_calls,
                "proper_orchestration": proper_orchestration,
                "attempts_real_calls": attempts_real_calls,
                "test_cases": len(responses),
                "message": "✅ PASS - Agent properly orchestrates A2A calls" if proper_orchestration and attempts_real_calls else "❌ FAIL - Agent may be using inappropriate mock data"
            }
            
        except Exception as e:
            return {"no_mock_violation": False, "error": str(e)}

async def main():
    """Run the LLM domain agent architecture test"""
    
    async with LLMDomainAgentTester() as tester:
        # Test architecture compliance
        compliance_results = await tester.test_architecture_compliance()
        
        # Test no mock data violation
        mock_test = await tester.test_no_mock_data_violation()
        print(f"   Mock Data Test: {mock_test['message']}")
        
        # Save results
        results = {
            "compliance_results": compliance_results,
            "mock_data_test": mock_test,
            "test_timestamp": time.time()
        }
        
        with open("tests/integration/llm_domain_agent_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: tests/integration/llm_domain_agent_test_results.json")
        
        return compliance_results["overall_compliance"] and mock_test["no_mock_violation"]

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 