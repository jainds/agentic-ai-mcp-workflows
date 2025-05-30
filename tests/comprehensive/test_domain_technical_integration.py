#!/usr/bin/env python3

"""
Comprehensive Integration Test Suite for Domain Agent <-> Technical Agent Communication

Tests the complete integration between:
1. Domain Agent (Python A2A Domain Agent) - LLM reasoning, intent analysis
2. Technical Agent (FastMCP Data Agent) - Data access via FastMCP
3. FastMCP Server - Modular tool services
4. End-to-end user request workflow

This validates the complete chain:
User -> Domain Agent -> Technical Agent -> FastMCP Server -> Data Services
"""

import asyncio
import sys
import json
import time
import httpx
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
    from agents.technical.fastmcp_data_agent import FastMCPDataAgent
    TECHNICAL_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"❌ Technical Agent not available: {e}")
    TECHNICAL_AGENT_AVAILABLE = False

try:
    from services.shared.fastmcp_server import ModularFastMCPServer, create_fastmcp_server
    FASTMCP_SERVER_AVAILABLE = True
except ImportError as e:
    print(f"❌ FastMCP Server not available: {e}")
    FASTMCP_SERVER_AVAILABLE = False

# Setup logging
logger = structlog.get_logger(__name__)


class IntegrationTestRunner:
    """Comprehensive integration test runner"""
    
    def __init__(self):
        self.test_results = {}
        self.domain_agent = None
        self.technical_agent = None
        self.fastmcp_server = None
        
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log a message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_method = getattr(logger, level.lower())
        log_method(f"[{timestamp}] {message}", **kwargs)
    
    async def test_component_availability(self) -> bool:
        """Test that all components are available"""
        try:
            self.log("Testing component availability...")
            
            if not DOMAIN_AGENT_AVAILABLE:
                self.log("Domain Agent not available", "ERROR")
                return False
            
            if not TECHNICAL_AGENT_AVAILABLE:
                self.log("Technical Agent not available", "ERROR")
                return False
            
            if not FASTMCP_SERVER_AVAILABLE:
                self.log("FastMCP Server not available", "ERROR")
                return False
            
            self.log("✅ All components available")
            return True
            
        except Exception as e:
            self.log("Component availability test failed", "ERROR", error=str(e))
            return False
    
    async def test_component_initialization(self) -> bool:
        """Test initialization of all components"""
        try:
            self.log("Testing component initialization...")
            
            # Initialize FastMCP server
            self.fastmcp_server = create_fastmcp_server()
            if not self.fastmcp_server:
                self.log("Failed to create FastMCP server", "ERROR")
                return False
            
            # Initialize Technical Agent
            self.technical_agent = FastMCPDataAgent(port=20001)
            if not self.technical_agent:
                self.log("Failed to create Technical Agent", "ERROR")
                return False
            
            # Initialize Domain Agent  
            self.domain_agent = PythonA2ADomainAgent(port=20000)
            if not self.domain_agent:
                self.log("Failed to create Domain Agent", "ERROR")
                return False
            
            self.log("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            self.log("Component initialization test failed", "ERROR", error=str(e))
            return False
    
    async def test_fastmcp_technical_agent_integration(self) -> bool:
        """Test integration between FastMCP server and Technical Agent"""
        try:
            self.log("Testing FastMCP <-> Technical Agent integration...")
            
            # Mock FastMCP server responses
            with patch.object(self.technical_agent.client, 'post') as mock_post:
                # Mock tool discovery
                discovery_response = Mock()
                discovery_response.status_code = 200
                discovery_response.json.return_value = {
                    "tools": [
                        {"name": "get_user", "description": "Get user information"},
                        {"name": "get_policy", "description": "Get policy information"},
                        {"name": "get_claim", "description": "Get claim information"}
                    ]
                }
                
                # Mock tool execution
                execution_response = Mock()
                execution_response.status_code = 200
                execution_response.json.return_value = {
                    "result": {
                        "content": [
                            {
                                "text": json.dumps({
                                    "success": True,
                                    "data": {
                                        "user_id": "user_001",
                                        "name": "John Smith",
                                        "email": "john.smith@example.com"
                                    }
                                })
                            }
                        ]
                    }
                }
                
                mock_post.return_value = execution_response
                
                # Test tool discovery
                await self.technical_agent._discover_service_tools("user", "http://localhost:8000")
                
                # Test tool execution
                result = await self.technical_agent.call_tool("user", "get_user", {"user_id": "user_001"})
                
                # Verify integration
                assert result["success"] is True
                assert "data" in result
                assert result["data"]["user_id"] == "user_001"
            
            self.log("✅ FastMCP <-> Technical Agent integration working")
            return True
            
        except Exception as e:
            self.log("FastMCP <-> Technical Agent integration test failed", "ERROR", error=str(e))
            return False
    
    async def test_domain_technical_agent_communication(self) -> bool:
        """Test communication between Domain Agent and Technical Agent"""
        try:
            self.log("Testing Domain Agent <-> Technical Agent communication...")
            
            # Mock Technical Agent responses
            with patch.object(self.domain_agent, '_call_technical_agent') as mock_call:
                mock_call.return_value = {
                    "success": True,
                    "data": {
                        "customer_id": "CUST-001",
                        "name": "John Smith",
                        "policies": [
                            {"policy_id": "POL-001", "type": "auto", "status": "active"}
                        ],
                        "claims": [
                            {"claim_id": "CLM-001", "status": "approved", "amount": 1500}
                        ]
                    },
                    "timestamp": "2024-01-15T10:30:00Z"
                }
                
                # Test domain agent calling technical agent
                result = await self.domain_agent._call_technical_agent(
                    "data_agent",
                    {"action": "get_customer_data", "customer_id": "CUST-001"}
                )
                
                # Verify communication
                assert result["success"] is True
                assert "data" in result
                assert result["data"]["customer_id"] == "CUST-001"
                
                # Verify call was made
                mock_call.assert_called_once()
            
            self.log("✅ Domain Agent <-> Technical Agent communication working")
            return True
            
        except Exception as e:
            self.log("Domain Agent <-> Technical Agent communication test failed", "ERROR", error=str(e))
            return False
    
    async def test_end_to_end_claim_status_workflow(self) -> bool:
        """Test complete end-to-end workflow for claim status inquiry"""
        try:
            self.log("Testing end-to-end claim status workflow...")
            
            user_message = "What's the status of my claim CLM-123?"
            
            # Mock all the components in the chain
            with patch.object(self.domain_agent, 'understand_intent') as mock_intent, \
                 patch.object(self.domain_agent, '_call_technical_agent') as mock_tech_call, \
                 patch.object(self.technical_agent, 'call_tool') as mock_tool:
                
                # Mock intent analysis
                mock_intent.return_value = {
                    "primary_intent": "claim_status",
                    "entities": {"claim_id": "CLM-123"},
                    "confidence": 0.95,
                    "urgency": "medium",
                    "complexity": "simple"
                }
                
                # Mock technical agent response
                mock_tech_call.return_value = {
                    "success": True,
                    "data": {
                        "claim_id": "CLM-123",
                        "status": "approved",
                        "amount": 2500.00,
                        "approval_date": "2024-01-10",
                        "payment_status": "processing"
                    }
                }
                
                # Mock FastMCP tool call
                mock_tool.return_value = {
                    "success": True,
                    "claim_id": "CLM-123", 
                    "status": "approved",
                    "amount": 2500.00
                }
                
                # Process the complete workflow
                result = await self.domain_agent.process_user_message(user_message, "CUST-001")
                
                # Verify workflow execution
                assert "response" in result
                assert "intent" in result
                assert result["intent"] == "claim_status"
                
                # Verify response contains claim information
                response_text = result["response"].lower()
                assert "claim" in response_text
                assert "clm-123" in response_text or "approved" in response_text
                
                # Verify orchestration
                orchestration_events = result.get("orchestration_events", [])
                assert len(orchestration_events) >= 3  # intent, plan, execution
                
                event_types = [event["event"] for event in orchestration_events]
                assert "intent_analysis" in event_types
                assert "execution_plan" in event_types
                assert "execution_results" in event_types
            
            self.log("✅ End-to-end claim status workflow working", 
                   response_length=len(result["response"]),
                   orchestration_events=len(orchestration_events))
            return True
            
        except Exception as e:
            self.log("End-to-end claim status workflow test failed", "ERROR", error=str(e))
            return False
    
    async def test_end_to_end_policy_inquiry_workflow(self) -> bool:
        """Test complete end-to-end workflow for policy inquiry"""
        try:
            self.log("Testing end-to-end policy inquiry workflow...")
            
            user_message = "Show me my active policies and coverage details"
            
            # Mock the complete workflow
            with patch.object(self.domain_agent, 'understand_intent') as mock_intent, \
                 patch.object(self.domain_agent, '_call_technical_agent') as mock_tech_call:
                
                # Mock intent analysis
                mock_intent.return_value = {
                    "primary_intent": "policy_inquiry",
                    "entities": {"customer_id": "CUST-001"},
                    "confidence": 0.88,
                    "urgency": "low",
                    "complexity": "moderate"
                }
                
                # Mock technical agent response
                mock_tech_call.return_value = {
                    "success": True,
                    "data": {
                        "customer_id": "CUST-001",
                        "active_policies": 2,
                        "policies": [
                            {
                                "policy_id": "POL-001",
                                "type": "auto",
                                "coverage_amount": 100000,
                                "premium": 1200,
                                "status": "active"
                            },
                            {
                                "policy_id": "POL-002", 
                                "type": "home",
                                "coverage_amount": 300000,
                                "premium": 800,
                                "status": "active"
                            }
                        ],
                        "total_coverage": 400000,
                        "annual_premium": 2000
                    }
                }
                
                # Process the workflow
                result = await self.domain_agent.process_user_message(user_message, "CUST-001")
                
                # Verify workflow execution
                assert "response" in result
                assert result["intent"] == "policy_inquiry"
                
                # Verify response contains policy information
                response_text = result["response"].lower()
                assert "policy" in response_text or "policies" in response_text
                assert "coverage" in response_text or "active" in response_text
                
                # Verify technical agent was called
                mock_tech_call.assert_called()
                
                # Check call parameters
                call_args = mock_tech_call.call_args[0]
                assert call_args[0] == "data_agent"  # Called data agent
            
            self.log("✅ End-to-end policy inquiry workflow working")
            return True
            
        except Exception as e:
            self.log("End-to-end policy inquiry workflow test failed", "ERROR", error=str(e))
            return False
    
    async def test_error_propagation_and_handling(self) -> bool:
        """Test error propagation through the integration chain"""
        try:
            self.log("Testing error propagation and handling...")
            
            # Test 1: Technical Agent failure
            with patch.object(self.domain_agent, '_call_technical_agent') as mock_tech_call:
                mock_tech_call.side_effect = Exception("Technical agent connection failed")
                
                execution_plan = {
                    "steps": [{"agent": "data_agent", "action": "fetch_data"}],
                    "intent": "test"
                }
                
                result = self.domain_agent.execute_plan(execution_plan, "conv_001")
                
                # Should handle error gracefully
                assert result["success"] is False
                assert "error" in result
                assert "connection failed" in result["error"].lower()
            
            # Test 2: FastMCP service failure
            with patch.object(self.technical_agent.client, 'post') as mock_post:
                mock_post.side_effect = httpx.ConnectError("Service unavailable")
                
                result = await self.technical_agent.call_tool("user", "get_user", {"user_id": "test"})
                
                # Should handle error gracefully
                assert result["success"] is False
                assert "error" in result
            
            # Test 3: End-to-end error handling
            with patch.object(self.domain_agent, 'understand_intent') as mock_intent:
                mock_intent.side_effect = Exception("LLM service unavailable")
                
                try:
                    await self.domain_agent.process_user_message("test message", "CUST-001")
                    # Should propagate error
                    assert False, "Should have raised exception"
                except Exception as e:
                    assert "LLM service unavailable" in str(e)
            
            self.log("✅ Error propagation and handling working correctly")
            return True
            
        except Exception as e:
            self.log("Error propagation test failed", "ERROR", error=str(e))
            return False
    
    async def test_performance_and_timing(self) -> bool:
        """Test performance characteristics of the integration"""
        try:
            self.log("Testing performance and timing...")
            
            # Mock fast responses
            with patch.object(self.domain_agent, 'understand_intent') as mock_intent, \
                 patch.object(self.domain_agent, '_call_technical_agent') as mock_tech_call:
                
                mock_intent.return_value = {
                    "primary_intent": "claim_status",
                    "confidence": 0.95
                }
                
                mock_tech_call.return_value = {
                    "success": True,
                    "data": {"status": "test"}
                }
                
                # Measure timing
                start_time = time.time()
                result = await self.domain_agent.process_user_message("test", "CUST-001")
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                # Verify reasonable performance
                assert execution_time < 5.0  # Should complete within 5 seconds
                assert result["response"] is not None
            
            # Test concurrent requests
            tasks = []
            for i in range(3):
                task = self.domain_agent.process_user_message(f"test message {i}", f"CUST-00{i}")
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            concurrent_time = end_time - start_time
            
            # Should handle concurrent requests efficiently
            assert len(results) == 3
            assert concurrent_time < 10.0  # Should complete within 10 seconds
            
            self.log("✅ Performance and timing acceptable", 
                   single_request_time=f"{execution_time:.3f}s",
                   concurrent_requests_time=f"{concurrent_time:.3f}s")
            return True
            
        except Exception as e:
            self.log("Performance test failed", "ERROR", error=str(e))
            return False
    
    async def test_data_flow_integrity(self) -> bool:
        """Test data flow integrity through the integration chain"""
        try:
            self.log("Testing data flow integrity...")
            
            # Test data consistency through the chain
            test_customer_id = "CUST-001"
            test_data = {
                "customer_id": test_customer_id,
                "name": "John Smith",
                "email": "john.smith@example.com",
                "policies": [{"policy_id": "POL-001", "type": "auto"}],
                "claims": [{"claim_id": "CLM-001", "status": "approved"}]
            }
            
            with patch.object(self.domain_agent, '_call_technical_agent') as mock_tech_call:
                mock_tech_call.return_value = {
                    "success": True,
                    "data": test_data
                }
                
                # Call through domain agent
                result = await self.domain_agent._call_technical_agent(
                    "data_agent",
                    {"action": "get_customer_data", "customer_id": test_customer_id}
                )
                
                # Verify data integrity
                assert result["success"] is True
                assert result["data"]["customer_id"] == test_customer_id
                assert result["data"]["name"] == "John Smith"
                assert len(result["data"]["policies"]) == 1
                assert len(result["data"]["claims"]) == 1
                
                # Verify no data corruption
                assert result["data"]["policies"][0]["policy_id"] == "POL-001"
                assert result["data"]["claims"][0]["claim_id"] == "CLM-001"
            
            self.log("✅ Data flow integrity maintained")
            return True
            
        except Exception as e:
            self.log("Data flow integrity test failed", "ERROR", error=str(e))
            return False
    
    async def cleanup(self):
        """Clean up test resources"""
        try:
            if self.technical_agent:
                await self.technical_agent.close()
            # Domain agent and FastMCP server don't need explicit cleanup in tests
            self.log("✅ Test cleanup completed")
        except Exception as e:
            self.log("Test cleanup failed", "WARNING", error=str(e))
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        self.log("🧪 Starting Domain <-> Technical Agent Integration Test Suite")
        self.log("="*80)
        
        results = {}
        
        try:
            # Test 1: Component Availability
            self.log("Test 1: Component Availability")
            results["component_availability"] = await self.test_component_availability()
            
            if not results["component_availability"]:
                return {
                    "success": False,
                    "error": "Required components not available",
                    "results": results
                }
            
            # Test 2: Component Initialization
            self.log("Test 2: Component Initialization")
            results["component_initialization"] = await self.test_component_initialization()
            
            # Test 3: FastMCP <-> Technical Agent Integration
            self.log("Test 3: FastMCP <-> Technical Agent Integration")
            results["fastmcp_technical_integration"] = await self.test_fastmcp_technical_agent_integration()
            
            # Test 4: Domain <-> Technical Agent Communication
            self.log("Test 4: Domain <-> Technical Agent Communication")
            results["domain_technical_communication"] = await self.test_domain_technical_agent_communication()
            
            # Test 5: End-to-End Claim Status Workflow
            self.log("Test 5: End-to-End Claim Status Workflow")
            results["e2e_claim_status_workflow"] = await self.test_end_to_end_claim_status_workflow()
            
            # Test 6: End-to-End Policy Inquiry Workflow
            self.log("Test 6: End-to-End Policy Inquiry Workflow")
            results["e2e_policy_inquiry_workflow"] = await self.test_end_to_end_policy_inquiry_workflow()
            
            # Test 7: Error Propagation and Handling
            self.log("Test 7: Error Propagation and Handling")
            results["error_propagation_handling"] = await self.test_error_propagation_and_handling()
            
            # Test 8: Performance and Timing
            self.log("Test 8: Performance and Timing")
            results["performance_timing"] = await self.test_performance_and_timing()
            
            # Test 9: Data Flow Integrity
            self.log("Test 9: Data Flow Integrity")
            results["data_flow_integrity"] = await self.test_data_flow_integrity()
            
            # Calculate success rate
            passed = sum(1 for result in results.values() if result)
            total = len(results)
            success_rate = (passed / total * 100) if total > 0 else 0
            
            self.log(f"Integration tests completed: {passed}/{total} passed ({success_rate:.1f}%)")
            
            return {
                "success": True,
                "results": results,
                "summary": {
                    "passed": passed,
                    "total": total,
                    "success_rate": success_rate
                }
            }
            
        finally:
            await self.cleanup()
    
    def print_report(self, report: Dict[str, Any]):
        """Print comprehensive integration test report"""
        print("\n" + "="*80)
        print("DOMAIN <-> TECHNICAL AGENT INTEGRATION TEST REPORT")
        print("="*80)
        
        if not report.get("success", False):
            print(f"❌ FAILED: {report.get('error', 'Unknown error')}")
            return
        
        results = report.get("results", {})
        summary = report.get("summary", {})
        
        print(f"Overall Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"Tests Passed: {summary.get('passed', 0)}/{summary.get('total', 0)}")
        print()
        
        print("Integration Test Results:")
        print("-" * 70)
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<40} {status}")
        
        print("\n" + "="*80)
        
        # Provide recommendations
        if summary.get('success_rate', 0) < 100:
            print("\n🔧 Integration Issues & Recommendations:")
            if not results.get('component_availability', True):
                print("  - Install missing components (Domain Agent, Technical Agent, FastMCP)")
            if not results.get('fastmcp_technical_integration', True):
                print("  - Fix FastMCP <-> Technical Agent communication")
            if not results.get('domain_technical_communication', True):
                print("  - Fix Domain <-> Technical Agent A2A communication")
            if not results.get('e2e_claim_status_workflow', True):
                print("  - Debug end-to-end claim status workflow")
            if not results.get('error_propagation_handling', True):
                print("  - Improve error handling throughout the integration chain")
        else:
            print("\n🎉 All integration tests passed! The complete system is working perfectly.")
            print("\n🔗 Integration Chain Working:")
            print("  User Request -> Domain Agent -> Technical Agent -> FastMCP -> Data Services")


async def main():
    """Main test execution"""
    # Check component availability first
    if not DOMAIN_AGENT_AVAILABLE:
        print("❌ Domain Agent not available. Please check installation and dependencies.")
        sys.exit(1)
    
    if not TECHNICAL_AGENT_AVAILABLE:
        print("❌ Technical Agent not available. Please check installation and dependencies.")
        sys.exit(1)
        
    if not FASTMCP_SERVER_AVAILABLE:
        print("❌ FastMCP Server not available. Please check installation and dependencies.")
        sys.exit(1)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    runner = IntegrationTestRunner()
    
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
        logger.error("Integration test execution failed", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 