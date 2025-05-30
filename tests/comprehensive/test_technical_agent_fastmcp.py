#!/usr/bin/env python3

"""
Comprehensive Test Suite for Technical Agent (FastMCP Data Agent)

Tests the complete technical agent functionality:
1. FastMCP integration and tool discovery
2. A2A protocol compliance and communication
3. Data service interactions
4. Error handling and resilience  
5. Performance characteristics
6. Integration with modular FastMCP server
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


class TechnicalAgentTestRunner:
    """Comprehensive test runner for Technical Agent"""
    
    def __init__(self):
        self.test_results = {}
        self.technical_agent = None
        self.fastmcp_server = None
        
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log a message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_method = getattr(logger, level.lower())
        log_method(f"[{timestamp}] {message}", **kwargs)
    
    async def test_technical_agent_availability(self) -> bool:
        """Test that Technical Agent can be imported and initialized"""
        try:
            if not TECHNICAL_AGENT_AVAILABLE:
                self.log("Technical Agent not available", "ERROR")
                return False
            
            self.log("Testing Technical Agent availability...")
            
            # Test initialization without starting server
            agent = FastMCPDataAgent(port=18002)  # Use different port
            
            if not agent:
                self.log("Failed to create Technical Agent instance", "ERROR")
                return False
            
            # Test basic attributes
            assert hasattr(agent, 'service_urls')
            assert hasattr(agent, 'client')
            assert hasattr(agent, 'available_tools')
            
            # Clean up
            await agent.close()
            
            self.log("✅ Technical Agent is available and can be initialized")
            return True
            
        except Exception as e:
            self.log("Technical Agent availability test failed", "ERROR", error=str(e))
            return False
    
    async def test_fastmcp_server_integration(self) -> bool:
        """Test integration with modular FastMCP server"""
        try:
            if not FASTMCP_SERVER_AVAILABLE:
                self.log("FastMCP Server not available", "ERROR")
                return False
            
            self.log("Testing FastMCP server integration...")
            
            # Create FastMCP server
            mcp_server = create_fastmcp_server()
            
            if not mcp_server:
                self.log("Failed to create FastMCP server", "ERROR")
                return False
            
            self.log("✅ FastMCP server integration working")
            return True
            
        except Exception as e:
            self.log("FastMCP server integration test failed", "ERROR", error=str(e))
            return False
    
    async def test_tool_discovery(self) -> bool:
        """Test tool discovery from FastMCP services"""
        try:
            self.log("Testing tool discovery...")
            
            # Create technical agent
            agent = FastMCPDataAgent(port=18003)
            
            # Mock HTTP responses for tool discovery
            with patch.object(agent.client, 'post') as mock_post:
                # Mock successful tool discovery response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "tools": [
                        {"name": "get_user", "description": "Get user information"},
                        {"name": "list_users", "description": "List all users"},
                        {"name": "create_user", "description": "Create new user"}
                    ]
                }
                mock_post.return_value = mock_response
                
                # Test tool discovery
                await agent._discover_service_tools("user", "http://localhost:8000")
                
                # Verify tools were discovered
                user_tools = agent.available_tools.get("user", [])
                assert len(user_tools) == 3
                
                tool_names = [tool["name"] for tool in user_tools]
                assert "get_user" in tool_names
                assert "list_users" in tool_names
                assert "create_user" in tool_names
            
            await agent.close()
            
            self.log("✅ Tool discovery working correctly", tools_discovered=len(user_tools))
            return True
            
        except Exception as e:
            self.log("Tool discovery test failed", "ERROR", error=str(e))
            return False
    
    async def test_tool_execution(self) -> bool:
        """Test execution of FastMCP tools"""
        try:
            self.log("Testing tool execution...")
            
            agent = FastMCPDataAgent(port=18004)
            
            # Mock successful tool execution
            with patch.object(agent.client, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
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
                mock_post.return_value = mock_response
                
                # Test tool execution
                result = await agent.call_tool("user", "get_user", {"user_id": "user_001"})
                
                # Verify result
                assert result["success"] is True
                assert "data" in result
                assert result["data"]["user_id"] == "user_001"
                assert result["data"]["name"] == "John Smith"
            
            await agent.close()
            
            self.log("✅ Tool execution working correctly")
            return True
            
        except Exception as e:
            self.log("Tool execution test failed", "ERROR", error=str(e))
            return False
    
    async def test_a2a_task_handling(self) -> bool:
        """Test A2A task request handling"""
        try:
            self.log("Testing A2A task handling...")
            
            # Create mock A2A task request
            from python_a2a import TaskRequest
            
            mock_task = TaskRequest(
                taskId="test_task_001",
                user={
                    "action": "get_customer",
                    "customer_id": "CUST-001"
                }
            )
            
            agent = FastMCPDataAgent(port=18005)
            
            # Mock tool execution for the task
            with patch.object(agent, '_handle_get_customer') as mock_handler:
                mock_handler.return_value = {
                    "success": True,
                    "customer_id": "CUST-001",
                    "customer_info": {"name": "John Smith", "email": "john@example.com"},
                    "policies": [],
                    "claims": []
                }
                
                # Handle the task
                response = agent.handle_task(mock_task)
                
                # Verify response
                assert response.taskId == "test_task_001"
                assert response.status == "completed"
                assert len(response.parts) > 0
                assert response.parts[0]["type"] == "data_response"
                
                # Verify handler was called
                mock_handler.assert_called_once()
            
            await agent.close()
            
            self.log("✅ A2A task handling working correctly")
            return True
            
        except Exception as e:
            self.log("A2A task handling test failed", "ERROR", error=str(e))
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling for various failure scenarios"""
        try:
            self.log("Testing error handling...")
            
            agent = FastMCPDataAgent(port=18006)
            
            # Test 1: Service unavailable
            with patch.object(agent.client, 'post') as mock_post:
                mock_post.side_effect = httpx.ConnectError("Connection failed")
                
                result = await agent.call_tool("user", "get_user", {"user_id": "test"})
                
                assert result["success"] is False
                assert "error" in result
                assert "Connection failed" in result["error"]
            
            # Test 2: HTTP error response
            with patch.object(agent.client, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_post.return_value = mock_response
                
                result = await agent.call_tool("user", "get_user", {"user_id": "test"})
                
                assert result["success"] is False
                assert "HTTP 500" in result["error"]
            
            # Test 3: Invalid task action
            from python_a2a import TaskRequest
            
            invalid_task = TaskRequest(
                taskId="invalid_task",
                user={"action": "unknown_action"}
            )
            
            response = agent.handle_task(invalid_task)
            
            assert response.status == "failed"
            assert "Unknown action" in response.parts[0]["text"]
            
            await agent.close()
            
            self.log("✅ Error handling working correctly")
            return True
            
        except Exception as e:
            self.log("Error handling test failed", "ERROR", error=str(e))
            return False
    
    async def test_data_aggregation(self) -> bool:
        """Test data aggregation across multiple services"""
        try:
            self.log("Testing data aggregation...")
            
            agent = FastMCPDataAgent(port=18007)
            
            # Mock responses from different services
            with patch.object(agent, 'call_tool') as mock_call_tool:
                # Setup different responses for different calls
                def side_effect(service, tool, args):
                    if service == "user" and tool == "get_user":
                        return {
                            "success": True,
                            "data": {"user_id": "CUST-001", "name": "John Smith"}
                        }
                    elif service == "policy" and tool == "list_policies":
                        return {
                            "success": True,
                            "policies": [
                                {"policy_id": "POL-001", "type": "auto", "premium": 1200}
                            ]
                        }
                    elif service == "claims" and tool == "list_claims":
                        return {
                            "success": True,
                            "claims": [
                                {"claim_id": "CLM-001", "status": "approved", "amount": 500}
                            ]
                        }
                    return {"success": False, "error": "Unknown call"}
                
                mock_call_tool.side_effect = side_effect
                
                # Test customer data aggregation
                result = await agent.get_customer_data("CUST-001")
                
                # Verify aggregated data
                assert result["success"] is True
                assert result["customer_id"] == "CUST-001"
                assert "customer_info" in result
                assert "policies" in result
                assert "claims" in result
                
                # Verify multiple service calls were made
                assert mock_call_tool.call_count == 3
            
            await agent.close()
            
            self.log("✅ Data aggregation working correctly")
            return True
            
        except Exception as e:
            self.log("Data aggregation test failed", "ERROR", error=str(e))
            return False
    
    async def test_performance_characteristics(self) -> bool:
        """Test performance characteristics of technical agent"""
        try:
            self.log("Testing performance characteristics...")
            
            agent = FastMCPDataAgent(port=18008)
            
            # Test response times
            with patch.object(agent.client, 'post') as mock_post:
                # Fast response mock
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "result": {
                        "content": [{"text": json.dumps({"success": True, "data": "test"})}]
                    }
                }
                mock_post.return_value = mock_response
                
                # Measure execution time
                start_time = time.time()
                result = await agent.call_tool("user", "get_user", {"user_id": "test"})
                end_time = time.time()
                
                execution_time = end_time - start_time
                
                # Verify reasonable performance (should be very fast with mocking)
                assert execution_time < 1.0  # Less than 1 second
                assert result["success"] is True
            
            # Test concurrent requests
            with patch.object(agent.client, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "result": {
                        "content": [{"text": json.dumps({"success": True, "data": "concurrent"})}]
                    }
                }
                mock_post.return_value = mock_response
                
                # Execute multiple concurrent requests
                start_time = time.time()
                tasks = [
                    agent.call_tool("user", "get_user", {"user_id": f"user_{i}"})
                    for i in range(5)
                ]
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                concurrent_time = end_time - start_time
                
                # All requests should succeed
                assert len(results) == 5
                assert all(result["success"] for result in results)
                
                # Concurrent execution should be efficient
                assert concurrent_time < 2.0  # Should complete quickly
            
            await agent.close()
            
            self.log("✅ Performance characteristics acceptable", 
                   single_request_time=f"{execution_time:.3f}s",
                   concurrent_requests_time=f"{concurrent_time:.3f}s")
            return True
            
        except Exception as e:
            self.log("Performance test failed", "ERROR", error=str(e))
            return False
    
    async def test_service_communication(self) -> bool:
        """Test communication with different FastMCP services"""
        try:
            self.log("Testing service communication...")
            
            agent = FastMCPDataAgent(port=18009)
            
            # Test communication with each service type
            services_to_test = [
                ("user", "get_user", {"user_id": "test"}),
                ("policy", "get_policy", {"policy_id": "test"}),
                ("claims", "get_claim", {"claim_id": "test"}),
                ("analytics", "get_market_trends", {})
            ]
            
            with patch.object(agent.client, 'post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "result": {
                        "content": [{"text": json.dumps({"success": True, "service": "test"})}]
                    }
                }
                mock_post.return_value = mock_response
                
                for service, tool, params in services_to_test:
                    result = await agent.call_tool(service, tool, params)
                    
                    assert result["success"] is True
                    assert "service" in result
                    
                    # Verify correct URL was called
                    expected_url = f"{agent.service_urls[service]}/mcp/call"
                    mock_post.assert_called_with(expected_url, json={
                        "method": "tools/call",
                        "params": {
                            "name": tool,
                            "arguments": params
                        }
                    })
            
            await agent.close()
            
            self.log("✅ Service communication working correctly", services_tested=len(services_to_test))
            return True
            
        except Exception as e:
            self.log("Service communication test failed", "ERROR", error=str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all technical agent tests"""
        self.log("🧪 Starting Technical Agent Comprehensive Test Suite")
        self.log("="*70)
        
        results = {}
        
        # Test 1: Technical Agent Availability
        self.log("Test 1: Technical Agent Availability")
        results["technical_agent_availability"] = await self.test_technical_agent_availability()
        
        if not results["technical_agent_availability"]:
            return {
                "success": False,
                "error": "Technical Agent not available",
                "results": results
            }
        
        # Test 2: FastMCP Server Integration
        self.log("Test 2: FastMCP Server Integration")
        results["fastmcp_server_integration"] = await self.test_fastmcp_server_integration()
        
        # Test 3: Tool Discovery
        self.log("Test 3: Tool Discovery")
        results["tool_discovery"] = await self.test_tool_discovery()
        
        # Test 4: Tool Execution
        self.log("Test 4: Tool Execution")
        results["tool_execution"] = await self.test_tool_execution()
        
        # Test 5: A2A Task Handling
        self.log("Test 5: A2A Task Handling")
        results["a2a_task_handling"] = await self.test_a2a_task_handling()
        
        # Test 6: Error Handling
        self.log("Test 6: Error Handling")
        results["error_handling"] = await self.test_error_handling()
        
        # Test 7: Data Aggregation
        self.log("Test 7: Data Aggregation")
        results["data_aggregation"] = await self.test_data_aggregation()
        
        # Test 8: Performance Characteristics
        self.log("Test 8: Performance Characteristics")
        results["performance_characteristics"] = await self.test_performance_characteristics()
        
        # Test 9: Service Communication
        self.log("Test 9: Service Communication")
        results["service_communication"] = await self.test_service_communication()
        
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
        print("TECHNICAL AGENT COMPREHENSIVE TEST REPORT")
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
            if not results.get('technical_agent_availability', True):
                print("  - Install/fix Technical Agent dependencies")
            if not results.get('fastmcp_server_integration', True):
                print("  - Verify FastMCP server setup and integration")
            if not results.get('tool_discovery', True):
                print("  - Check FastMCP service connectivity")
            if not results.get('a2a_task_handling', True):
                print("  - Review A2A protocol implementation")
        else:
            print("\n🎉 All tests passed! Technical Agent is working perfectly.")


async def main():
    """Main test execution"""
    if not TECHNICAL_AGENT_AVAILABLE:
        print("❌ Technical Agent not available. Please check installation and dependencies.")
        sys.exit(1)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    runner = TechnicalAgentTestRunner()
    
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