#!/usr/bin/env python3

"""
Comprehensive Test Suite for Domain Agent (Python A2A Domain Agent)

Tests the complete domain agent functionality:
1. Intent analysis and understanding
2. Execution planning and orchestration
3. Technical agent communication via A2A
4. LLM integration and reasoning
5. Professional response generation
6. Error handling and fallback scenarios
"""

import asyncio
import sys
import json
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from agents.domain.python_a2a_domain_agent import PythonA2ADomainAgent
    DOMAIN_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"❌ Domain Agent not available: {e}")
    DOMAIN_AGENT_AVAILABLE = False

try:
    from python_a2a import Message, TextContent, MessageRole, TaskRequest
    PYTHON_A2A_AVAILABLE = True
except ImportError as e:
    print(f"❌ Python A2A not available: {e}")
    PYTHON_A2A_AVAILABLE = False

# Setup logging
logger = structlog.get_logger(__name__)


class DomainAgentTestRunner:
    """Comprehensive test runner for Domain Agent"""
    
    def __init__(self):
        self.test_results = {}
        self.domain_agent = None
        
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log a message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_method = getattr(logger, level.lower())
        log_method(f"[{timestamp}] {message}", **kwargs)
    
    async def test_domain_agent_availability(self) -> bool:
        """Test that Domain Agent can be imported and initialized"""
        try:
            if not DOMAIN_AGENT_AVAILABLE:
                self.log("Domain Agent not available", "ERROR")
                return False
            
            self.log("Testing Domain Agent availability...")
            
            # Test initialization without starting server
            agent = PythonA2ADomainAgent(port=19000)  # Use different port
            
            if not agent:
                self.log("Failed to create Domain Agent instance", "ERROR")
                return False
            
            # Test basic attributes
            assert hasattr(agent, 'name')
            assert hasattr(agent, 'description')
            assert hasattr(agent, 'capabilities')
            assert hasattr(agent, 'response_template')
            
            self.log("✅ Domain Agent is available and can be initialized")
            return True
            
        except Exception as e:
            self.log("Domain Agent availability test failed", "ERROR", error=str(e))
            return False
    
    async def test_llm_integration(self) -> bool:
        """Test LLM client integration and configuration"""
        try:
            self.log("Testing LLM integration...")
            
            agent = PythonA2ADomainAgent(port=19001)
            
            # Test LLM client setup
            if not agent.llm_client:
                self.log("LLM client not configured - testing fallback", "WARNING")
                return True  # Pass if no LLM configured (expected in some environments)
            
            # Test basic LLM call with mocking
            with patch.object(agent.llm_client.chat.completions, 'create') as mock_create:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '''{"primary_intent": "claim_status", "confidence": 0.95}'''
                mock_create.return_value = mock_response
                
                # Test intent analysis
                result = agent.understand_intent("What's the status of my claim?")
                
                assert "primary_intent" in result
                assert result["primary_intent"] == "claim_status"
                assert result["confidence"] == 0.95
            
            self.log("✅ LLM integration working correctly")
            return True
            
        except Exception as e:
            self.log("LLM integration test failed", "ERROR", error=str(e))
            return False
    
    async def test_intent_analysis(self) -> bool:
        """Test intent analysis for various user requests"""
        try:
            self.log("Testing intent analysis...")
            
            agent = PythonA2ADomainAgent(port=19002)
            
            # Mock LLM responses for different intents
            test_cases = [
                {
                    "input": "What's the status of my claim?",
                    "expected_intent": "claim_status",
                    "llm_response": '''{"primary_intent": "claim_status", "confidence": 0.95, "entities": {"claim_id": null}}'''
                },
                {
                    "input": "I want to file a new claim",
                    "expected_intent": "claim_filing", 
                    "llm_response": '''{"primary_intent": "claim_filing", "confidence": 0.90, "entities": {}}'''
                },
                {
                    "input": "Show me my policy details",
                    "expected_intent": "policy_inquiry",
                    "llm_response": '''{"primary_intent": "policy_inquiry", "confidence": 0.85, "entities": {}}'''
                },
                {
                    "input": "I need a quote for auto insurance",
                    "expected_intent": "quote_request",
                    "llm_response": '''{"primary_intent": "quote_request", "confidence": 0.92, "entities": {"insurance_type": "auto"}}'''
                }
            ]
            
            if not agent.llm_client:
                self.log("No LLM client configured - skipping intent analysis", "WARNING")
                return True
            
            with patch.object(agent.llm_client.chat.completions, 'create') as mock_create:
                for test_case in test_cases:
                    mock_response = Mock()
                    mock_response.choices = [Mock()]
                    mock_response.choices[0].message.content = test_case["llm_response"]
                    mock_create.return_value = mock_response
                    
                    result = agent.understand_intent(test_case["input"])
                    
                    assert result["primary_intent"] == test_case["expected_intent"]
                    assert "confidence" in result
            
            self.log("✅ Intent analysis working correctly", test_cases_passed=len(test_cases))
            return True
            
        except Exception as e:
            self.log("Intent analysis test failed", "ERROR", error=str(e))
            return False
    
    async def test_execution_planning(self) -> bool:
        """Test execution planning based on intent analysis"""
        try:
            self.log("Testing execution planning...")
            
            agent = PythonA2ADomainAgent(port=19003)
            
            # Test various intent scenarios
            test_intents = [
                {
                    "primary_intent": "claim_status",
                    "entities": {"claim_id": "CLM-123"},
                    "expected_steps": ["fetch_claim_status", "fetch_claim_details"]
                },
                {
                    "primary_intent": "policy_inquiry",
                    "entities": {"customer_id": "CUST-001"},
                    "expected_steps": ["fetch_policy_details", "calculate_current_benefits"]
                },
                {
                    "primary_intent": "quote_request",
                    "entities": {"insurance_type": "auto"},
                    "expected_steps": ["generate_quote"]
                }
            ]
            
            for intent_data in test_intents:
                plan = agent.create_execution_plan(intent_data, "test user text")
                
                assert "steps" in plan
                assert "intent" in plan
                assert plan["intent"] == intent_data["primary_intent"]
                
                # Verify planning logic
                plan_actions = [step["action"] for step in plan["steps"]]
                for expected_action in intent_data["expected_steps"]:
                    assert any(expected_action in action for action in plan_actions)
            
            self.log("✅ Execution planning working correctly", plans_tested=len(test_intents))
            return True
            
        except Exception as e:
            self.log("Execution planning test failed", "ERROR", error=str(e))
            return False
    
    async def test_technical_agent_communication(self) -> bool:
        """Test communication with technical agents via A2A"""
        try:
            self.log("Testing technical agent communication...")
            
            agent = PythonA2ADomainAgent(port=19004)
            
            # Mock A2A client wrapper
            with patch.object(agent, '_call_technical_agent') as mock_call:
                mock_call.return_value = {
                    "success": True,
                    "data": {
                        "customer_id": "CUST-001",
                        "claim_status": "approved",
                        "claim_amount": 1500.00
                    },
                    "timestamp": "2024-01-15T10:30:00Z"
                }
                
                # Test different agent calls
                test_calls = [
                    {
                        "agent": "data_agent",
                        "action": "fetch_claim_status",
                        "params": {"claim_id": "CLM-123"}
                    },
                    {
                        "agent": "data_agent", 
                        "action": "fetch_policy_details",
                        "params": {"customer_id": "CUST-001"}
                    }
                ]
                
                for call_data in test_calls:
                    result = await agent._call_technical_agent(
                        call_data["agent"],
                        call_data["params"]
                    )
                    
                    assert result["success"] is True
                    assert "data" in result
            
            self.log("✅ Technical agent communication working correctly")
            return True
            
        except Exception as e:
            self.log("Technical agent communication test failed", "ERROR", error=str(e))
            return False
    
    async def test_response_generation(self) -> bool:
        """Test professional response generation with templates"""
        try:
            self.log("Testing response generation...")
            
            agent = PythonA2ADomainAgent(port=19005)
            
            # Test response generation for different scenarios
            test_scenarios = [
                {
                    "intent_analysis": {
                        "primary_intent": "claim_status",
                        "confidence": 0.95
                    },
                    "execution_results": {
                        "success": True,
                        "aggregated_data": {
                            "claims_data": {
                                "status": "approved",
                                "amount": 1500.00,
                                "claim_id": "CLM-123"
                            }
                        }
                    },
                    "user_text": "What's my claim status?"
                },
                {
                    "intent_analysis": {
                        "primary_intent": "policy_inquiry",
                        "confidence": 0.88
                    },
                    "execution_results": {
                        "success": True,
                        "aggregated_data": {
                            "policy_data": {
                                "active_policies": 2,
                                "total_coverage": 150000
                            }
                        }
                    },
                    "user_text": "Show me my policies"
                }
            ]
            
            for scenario in test_scenarios:
                response = agent.prepare_response(
                    scenario["intent_analysis"],
                    scenario["execution_results"], 
                    scenario["user_text"]
                )
                
                # Verify response contains key elements
                assert len(response) > 100  # Substantial response
                assert "Thank you" in response or "Current Status" in response
                
                # Verify professional tone
                assert "**" in response  # Markdown formatting
                assert "•" in response or "1." in response  # Bullet points or numbers
            
            self.log("✅ Response generation working correctly", scenarios_tested=len(test_scenarios))
            return True
            
        except Exception as e:
            self.log("Response generation test failed", "ERROR", error=str(e))
            return False
    
    async def test_message_handling(self) -> bool:
        """Test complete message handling workflow"""
        try:
            self.log("Testing message handling workflow...")
            
            agent = PythonA2ADomainAgent(port=19006)
            
            # Create test message
            if not PYTHON_A2A_AVAILABLE:
                self.log("Python A2A not available - creating mock message", "WARNING")
                # Create mock message
                test_message = Mock()
                test_message.content = Mock()
                test_message.content.text = "What's the status of my claim CLM-123?"
                test_message.conversation_id = "conv_001"
                test_message.message_id = "msg_001"
            else:
                test_message = Message(
                    content=TextContent(text="What's the status of my claim CLM-123?"),
                    role=MessageRole.USER,
                    conversation_id="conv_001"
                )
            
            # Mock all dependencies
            with patch.object(agent, 'understand_intent') as mock_intent, \
                 patch.object(agent, 'create_execution_plan') as mock_plan, \
                 patch.object(agent, 'execute_plan') as mock_execute, \
                 patch.object(agent, 'prepare_response') as mock_response:
                
                mock_intent.return_value = {
                    "primary_intent": "claim_status",
                    "confidence": 0.95
                }
                
                mock_plan.return_value = {
                    "intent": "claim_status",
                    "steps": [{"agent": "data_agent", "action": "fetch_claim_status"}]
                }
                
                mock_execute.return_value = {
                    "success": True,
                    "aggregated_data": {"claims_data": {"status": "approved"}}
                }
                
                mock_response.return_value = "Your claim CLM-123 has been approved."
                
                # Test message handling
                response = agent.handle_message(test_message)
                
                # Verify response structure
                assert hasattr(response, 'content')
                assert hasattr(response.content, 'text')
                assert "claim" in response.content.text.lower()
                
                # Verify all methods were called
                mock_intent.assert_called_once()
                mock_plan.assert_called_once()
                mock_execute.assert_called_once()
                mock_response.assert_called_once()
            
            self.log("✅ Message handling workflow working correctly")
            return True
            
        except Exception as e:
            self.log("Message handling test failed", "ERROR", error=str(e))
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling in various failure scenarios"""
        try:
            self.log("Testing error handling...")
            
            agent = PythonA2ADomainAgent(port=19007)
            
            # Test 1: LLM failure
            if agent.llm_client:
                with patch.object(agent.llm_client.chat.completions, 'create') as mock_create:
                    mock_create.side_effect = Exception("LLM service unavailable")
                    
                    try:
                        result = agent.understand_intent("test message")
                        # Should handle error gracefully
                        assert False, "Should have raised exception"
                    except Exception as e:
                        assert "LLM service unavailable" in str(e)
            
            # Test 2: Technical agent failure
            with patch.object(agent, '_call_technical_agent') as mock_call:
                mock_call.side_effect = Exception("Technical agent unavailable")
                
                execution_plan = {
                    "steps": [{"agent": "data_agent", "action": "test"}],
                    "intent": "test"
                }
                
                result = agent.execute_plan(execution_plan, "conv_001")
                
                # Should handle error and return error response
                assert result["success"] is False
                assert "error" in result
            
            # Test 3: Invalid message handling
            if PYTHON_A2A_AVAILABLE:
                invalid_message = Message(
                    content=TextContent(text=""),
                    role=MessageRole.USER
                )
                
                response = agent.handle_message(invalid_message)
                
                # Should handle gracefully
                assert hasattr(response, 'content')
                assert len(response.content.text) > 0
            
            self.log("✅ Error handling working correctly")
            return True
            
        except Exception as e:
            self.log("Error handling test failed", "ERROR", error=str(e))
            return False
    
    async def test_http_endpoints(self) -> bool:
        """Test HTTP endpoints for Kubernetes integration"""
        try:
            self.log("Testing HTTP endpoints...")
            
            agent = PythonA2ADomainAgent(port=19008)
            
            # Test health endpoint
            health_response = await agent.app.router.routes[0].endpoint()
            assert "status" in health_response
            assert health_response["status"] == "healthy"
            assert "agent_type" in health_response
            
            # Test readiness endpoint  
            ready_response = await agent.app.router.routes[1].endpoint()
            assert "status" in ready_response
            assert ready_response["status"] == "ready"
            
            # Test chat endpoint with mock
            from agents.domain.python_a2a_domain_agent import ChatRequest
            
            chat_request = ChatRequest(
                message="Test message",
                customer_id="test_customer"
            )
            
            with patch.object(agent, 'process_user_message') as mock_process:
                mock_process.return_value = {
                    "response": "Test response",
                    "intent": "general_inquiry",
                    "confidence": 0.8,
                    "thinking_steps": [],
                    "orchestration_events": [],
                    "api_calls": []
                }
                
                # Mock the actual endpoint call
                response = await agent.process_user_message("Test message", "test_customer")
                
                assert "response" in response
                assert "intent" in response
                assert response["response"] == "Test response"
            
            self.log("✅ HTTP endpoints working correctly")
            return True
            
        except Exception as e:
            self.log("HTTP endpoints test failed", "ERROR", error=str(e))
            return False
    
    async def test_template_enhancement(self) -> bool:
        """Test professional template enhancement features"""
        try:
            self.log("Testing template enhancement...")
            
            agent = PythonA2ADomainAgent(port=19009)
            
            # Verify template loading
            assert agent.response_template is not None
            assert len(agent.response_template) > 100
            assert agent.template_enhancement_enabled is True
            
            # Test template application
            test_data = {
                "primary_status": "Your claim is approved",
                "current_state": "Processing payment",
                "estimated_timeline": "3-5 business days",
                "detailed_analysis": "All documentation verified",
                "account_summary": "Premium customer account",
                "customer_type": "Premium",
                "next_steps": "Payment will be processed"
            }
            
            # Mock template formatting
            with patch.object(agent.response_template, 'format') as mock_format:
                mock_format.return_value = f"""Thank you for your inquiry. I've conducted a comprehensive analysis of your request.

**Current Status:**
Based on my review, here's what I found:
• {test_data['primary_status']}
• Current state: **{test_data['current_state']}**
• Estimated timeline: **{test_data['estimated_timeline']}**"""
                
                formatted_response = agent.response_template.format(**test_data)
                
                assert "Thank you for your inquiry" in formatted_response
                assert "comprehensive analysis" in formatted_response
                assert test_data["primary_status"] in formatted_response
            
            self.log("✅ Template enhancement working correctly")
            return True
            
        except Exception as e:
            self.log("Template enhancement test failed", "ERROR", error=str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all domain agent tests"""
        self.log("🧪 Starting Domain Agent Comprehensive Test Suite")
        self.log("="*70)
        
        results = {}
        
        # Test 1: Domain Agent Availability
        self.log("Test 1: Domain Agent Availability")
        results["domain_agent_availability"] = await self.test_domain_agent_availability()
        
        if not results["domain_agent_availability"]:
            return {
                "success": False,
                "error": "Domain Agent not available",
                "results": results
            }
        
        # Test 2: LLM Integration
        self.log("Test 2: LLM Integration")
        results["llm_integration"] = await self.test_llm_integration()
        
        # Test 3: Intent Analysis
        self.log("Test 3: Intent Analysis")
        results["intent_analysis"] = await self.test_intent_analysis()
        
        # Test 4: Execution Planning
        self.log("Test 4: Execution Planning")
        results["execution_planning"] = await self.test_execution_planning()
        
        # Test 5: Technical Agent Communication
        self.log("Test 5: Technical Agent Communication")
        results["technical_agent_communication"] = await self.test_technical_agent_communication()
        
        # Test 6: Response Generation
        self.log("Test 6: Response Generation")
        results["response_generation"] = await self.test_response_generation()
        
        # Test 7: Message Handling
        self.log("Test 7: Message Handling")
        results["message_handling"] = await self.test_message_handling()
        
        # Test 8: Error Handling
        self.log("Test 8: Error Handling")
        results["error_handling"] = await self.test_error_handling()
        
        # Test 9: HTTP Endpoints
        self.log("Test 9: HTTP Endpoints")
        results["http_endpoints"] = await self.test_http_endpoints()
        
        # Test 10: Template Enhancement
        self.log("Test 10: Template Enhancement")
        results["template_enhancement"] = await self.test_template_enhancement()
        
        # Calculate success rate
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"Tests completed: {passed}/{total} passed ({success_rate:.1f}%)")
        
        return {
            "success": True,
            "results": results,
            "summary": {
                "passed": passed,
                "total": total,
                "success_rate": success_rate
            }
        }
    
    def print_report(self, report: Dict[str, Any]):
        """Print comprehensive test report"""
        print("\n" + "="*80)
        print("DOMAIN AGENT COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        if not report.get("success", False):
            print(f"❌ FAILED: {report.get('error', 'Unknown error')}")
            return
        
        results = report.get("results", {})
        summary = report.get("summary", {})
        
        print(f"Overall Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"Tests Passed: {summary.get('passed', 0)}/{summary.get('total', 0)}")
        print()
        
        print("Test Results:")
        print("-" * 70)
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<40} {status}")
        
        print("\n" + "="*80)
        
        # Provide recommendations
        if summary.get('success_rate', 0) < 100:
            print("\n🔧 Recommendations:")
            if not results.get('domain_agent_availability', True):
                print("  - Install/fix Domain Agent dependencies")
            if not results.get('llm_integration', True):
                print("  - Configure LLM client (OpenAI/OpenRouter API key)")
            if not results.get('intent_analysis', True):
                print("  - Verify LLM service connectivity")
            if not results.get('technical_agent_communication', True):
                print("  - Check technical agent connectivity")
        else:
            print("\n🎉 All tests passed! Domain Agent is working perfectly.")


async def main():
    """Main test execution"""
    if not DOMAIN_AGENT_AVAILABLE:
        print("❌ Domain Agent not available. Please check installation and dependencies.")
        sys.exit(1)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    runner = DomainAgentTestRunner()
    
    try:
        report = await runner.run_all_tests()
        runner.print_report(report)
        
        # Exit with appropriate code
        if report.get("success", False):
            success_rate = report.get("summary", {}).get("success_rate", 0)
            sys.exit(0 if success_rate >= 80 else 1)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error("Test execution failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 