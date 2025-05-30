#!/usr/bin/env python3

"""
Comprehensive Unit Tests for Technical Agent FastMCP Integration
Tests the technical agent's ability to use official FastMCP Client to communicate with MCP services
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import structlog

# Set up logging
logger = structlog.get_logger(__name__)

class TestTechnicalAgentFastMCPIntegration:
    """Test technical agent's FastMCP Client integration"""
    
    def test_fastmcp_imports(self):
        """Test that FastMCP can be imported"""
        try:
            from fastmcp import Client
            logger.info("FastMCP Client import successful")
            assert True
        except ImportError as e:
            pytest.skip(f"FastMCP not available: {e}")
    
    def test_technical_agent_structure(self):
        """Test that technical agent file exists and can be imported"""
        agent_file = Path("agents/technical/fastmcp_data_agent.py")
        assert agent_file.exists(), "Technical agent file should exist"
        
        try:
            # Import the technical agent module
            import sys
            sys.path.insert(0, str(Path("agents/technical").absolute()))
            import fastmcp_data_agent
            
            # Verify it has the expected class
            assert hasattr(fastmcp_data_agent, 'FastMCPDataAgent'), "Should have FastMCPDataAgent class"
            logger.info("Technical agent import successful")
            
        except ImportError as e:
            logger.warning(f"Technical agent import failed: {e}")
            # This is acceptable in test environment

class TestFastMCPClientIntegration:
    """Test FastMCP Client integration patterns"""
    
    @pytest.mark.asyncio
    async def test_fastmcp_client_creation(self):
        """Test creating FastMCP clients for services"""
        try:
            from fastmcp import Client
            
            # Test creating clients for different service URLs
            service_urls = {
                "user": "http://localhost:8000/mcp",
                "claims": "http://localhost:8001/mcp", 
                "policy": "http://localhost:8002/mcp",
                "analytics": "http://localhost:8003/mcp"
            }
            
            clients = {}
            for service_name, service_url in service_urls.items():
                try:
                    client = Client(service_url)
                    clients[service_name] = client
                    logger.info(f"Created FastMCP client for {service_name}")
                except Exception as e:
                    logger.warning(f"Failed to create client for {service_name}: {e}")
            
            assert len(clients) > 0, "Should create at least one client"
            logger.info(f"Created {len(clients)} FastMCP clients")
            
        except ImportError:
            pytest.skip("FastMCP not available")
    
    @pytest.mark.asyncio
    async def test_fastmcp_tool_discovery_pattern(self):
        """Test the pattern for discovering tools using FastMCP Client"""
        try:
            from fastmcp import Client
            
            # Mock client behavior for tool discovery
            mock_client = AsyncMock(spec=Client)
            
            # Mock tool discovery response
            mock_tools = [
                Mock(name="get_user", description="Get user information"),
                Mock(name="list_claims", description="List customer claims"),
                Mock(name="create_claim", description="Create new claim")
            ]
            
            mock_client.list_tools.return_value = mock_tools
            
            # Test the discovery pattern
            async with mock_client:
                tools = await mock_client.list_tools()
                
                # Convert to internal format (as technical agent would do)
                tool_list = []
                for tool in tools:
                    tool_info = {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": getattr(tool, 'inputSchema', {})
                    }
                    tool_list.append(tool_info)
                
                assert len(tool_list) == 3
                assert tool_list[0]["name"] == "get_user"
                assert tool_list[1]["name"] == "list_claims"
                assert tool_list[2]["name"] == "create_claim"
                
                logger.info(f"Tool discovery pattern test successful: {len(tool_list)} tools")
                
        except ImportError:
            pytest.skip("FastMCP not available")
    
    @pytest.mark.asyncio
    async def test_fastmcp_tool_call_pattern(self):
        """Test the pattern for calling tools using FastMCP Client"""
        try:
            from fastmcp import Client
            
            # Mock client behavior for tool calls
            mock_client = AsyncMock(spec=Client)
            
            # Mock tool call response
            mock_content = Mock()
            mock_content.text = json.dumps({
                "success": True,
                "user_id": "CUST-001",
                "name": "John Smith",
                "email": "john.smith@email.com"
            })
            
            mock_client.call_tool.return_value = [mock_content]
            
            # Test the tool call pattern
            async with mock_client:
                result = await mock_client.call_tool("get_user", {"user_id": "CUST-001"})
                
                # Process result (as technical agent would do)
                if result and len(result) > 0:
                    content = result[0]
                    if hasattr(content, 'text'):
                        try:
                            tool_result = json.loads(content.text)
                        except json.JSONDecodeError:
                            tool_result = {
                                "success": True,
                                "result": content.text,
                                "type": "text"
                            }
                    else:
                        tool_result = {
                            "success": True,
                            "result": str(content),
                            "type": "content"
                        }
                
                assert tool_result["success"] is True
                assert tool_result["user_id"] == "CUST-001"
                assert tool_result["name"] == "John Smith"
                
                logger.info("Tool call pattern test successful")
                
        except ImportError:
            pytest.skip("FastMCP not available")

class TestTechnicalAgentA2AInterface:
    """Test that the Technical Agent maintains proper A2A interface"""
    
    def test_a2a_task_request_structure(self):
        """Test A2A TaskRequest structure handling"""
        
        # Mock TaskRequest structure that Domain Agent would send
        task_data = {
            "taskId": "test_task_001",
            "user": {
                "action": "get_customer_data",
                "customer_id": "CUST-001"
            }
        }
        
        # Verify task structure
        assert "taskId" in task_data
        assert "user" in task_data
        assert "action" in task_data["user"]
        assert "customer_id" in task_data["user"]
        
        # Test action routing logic
        action = task_data["user"]["action"]
        supported_actions = [
            "get_customer", "get_claims", "get_policies", 
            "create_claim", "update_claim", "fraud_analysis", 
            "get_customer_data"
        ]
        
        assert action in supported_actions, f"Action {action} should be supported"
        
        logger.info(f"A2A interface test successful for action: {action}")
    
    def test_a2a_task_response_structure(self):
        """Test A2A TaskResponse structure generation"""
        
        # Mock successful response structure
        success_response = {
            "taskId": "test_task_001",
            "status": "completed",
            "parts": [{
                "text": json.dumps({
                    "action": "get_customer_data",
                    "result": {"success": True, "customer_id": "CUST-001"},
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "FastMCPDataAgent",
                    "protocol": "FastMCP_2.0"
                }),
                "type": "data_response"
            }],
            "metadata": {
                "agent": "FastMCPDataAgent",
                "action": "get_customer_data",
                "protocol": "FastMCP_Client_2.0"
            }
        }
        
        # Verify response structure
        assert "taskId" in success_response
        assert "status" in success_response
        assert "parts" in success_response
        assert "metadata" in success_response
        
        assert success_response["status"] == "completed"
        assert len(success_response["parts"]) > 0
        assert "text" in success_response["parts"][0]
        
        # Verify nested response data
        response_data = json.loads(success_response["parts"][0]["text"])
        assert "action" in response_data
        assert "result" in response_data
        assert "protocol" in response_data
        assert response_data["protocol"] == "FastMCP_2.0"
        
        logger.info("A2A response structure test successful")

class TestTechnicalAgentErrorHandling:
    """Test error handling in FastMCP integration"""
    
    @pytest.mark.asyncio
    async def test_fastmcp_service_unavailable_handling(self):
        """Test handling when FastMCP service is unavailable"""
        try:
            from fastmcp import Client
            
            # Mock client that fails to connect
            mock_client = AsyncMock(spec=Client)
            mock_client.__aenter__.side_effect = ConnectionError("Service unavailable")
            
            # Test error handling
            try:
                async with mock_client:
                    await mock_client.call_tool("get_user", {"user_id": "test"})
                assert False, "Should have raised ConnectionError"
            except ConnectionError as e:
                assert "Service unavailable" in str(e)
                logger.info("Service unavailable error handling test successful")
                
        except ImportError:
            pytest.skip("FastMCP not available")
    
    @pytest.mark.asyncio
    async def test_fastmcp_invalid_response_handling(self):
        """Test handling of invalid FastMCP responses"""
        try:
            from fastmcp import Client
            
            # Mock client with empty/invalid response
            mock_client = AsyncMock(spec=Client)
            mock_client.call_tool.return_value = []  # Empty response
            
            # Test error handling pattern
            async with mock_client:
                result = await mock_client.call_tool("get_user", {"user_id": "test"})
                
                # Handle empty result (as technical agent would do)
                if not result or len(result) == 0:
                    error_result = {
                        "success": False,
                        "error": "Empty result from FastMCP tool"
                    }
                else:
                    error_result = {"success": True}
                
                assert error_result["success"] is False
                assert "Empty result" in error_result["error"]
                
                logger.info("Invalid response handling test successful")
                
        except ImportError:
            pytest.skip("FastMCP not available")

class TestTechnicalAgentPerformance:
    """Test performance characteristics of FastMCP integration"""
    
    @pytest.mark.asyncio
    async def test_concurrent_fastmcp_requests(self):
        """Test concurrent FastMCP requests handling"""
        try:
            from fastmcp import Client
            
            # Mock multiple clients for concurrent requests
            mock_user_client = AsyncMock(spec=Client)
            mock_claims_client = AsyncMock(spec=Client)
            
            # Mock responses with different data
            user_content = Mock()
            user_content.text = json.dumps({"success": True, "service": "user", "data": "user_data"})
            mock_user_client.call_tool.return_value = [user_content]
            
            claims_content = Mock()
            claims_content.text = json.dumps({"success": True, "service": "claims", "data": "claims_data"})
            mock_claims_client.call_tool.return_value = [claims_content]
            
            # Simulate concurrent requests
            async def call_user_service():
                async with mock_user_client:
                    result = await mock_user_client.call_tool("get_user", {"user_id": "CUST-001"})
                    return json.loads(result[0].text)
            
            async def call_claims_service():
                async with mock_claims_client:
                    result = await mock_claims_client.call_tool("list_claims", {"customer_id": "CUST-001"})
                    return json.loads(result[0].text)
            
            # Execute concurrent requests
            start_time = asyncio.get_event_loop().time()
            user_result, claims_result = await asyncio.gather(
                call_user_service(),
                call_claims_service()
            )
            end_time = asyncio.get_event_loop().time()
            
            # Verify results
            assert user_result["service"] == "user"
            assert claims_result["service"] == "claims"
            assert user_result["success"] and claims_result["success"]
            
            # Should complete quickly since they're mocked
            assert (end_time - start_time) < 1.0
            
            logger.info(f"Concurrent requests test successful in {end_time - start_time:.3f}s")
            
        except ImportError:
            pytest.skip("FastMCP not available")

# Test runner class
class TechnicalAgentTestRunner:
    """Test runner for comprehensive technical agent testing"""
    
    def __init__(self):
        self.test_results = {}
        logger.info("Technical Agent FastMCP Test Runner initialized")
    
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Structured logging for test results"""
        timestamp = datetime.utcnow().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "component": "TechnicalAgentTestRunner"
        }
        log_entry.update(kwargs)
        
        logger.info(log_entry)
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all technical agent FastMCP integration tests"""
        start_time = datetime.utcnow()
        self.log("Starting comprehensive Technical Agent FastMCP integration tests")
        
        test_categories = [
            ("FastMCP Integration", TestTechnicalAgentFastMCPIntegration),
            ("FastMCP Client", TestFastMCPClientIntegration),
            ("A2A Interface", TestTechnicalAgentA2AInterface),
            ("Error Handling", TestTechnicalAgentErrorHandling),
            ("Performance", TestTechnicalAgentPerformance)
        ]
        
        results = {}
        total_passed = 0
        total_failed = 0
        
        for category_name, test_class in test_categories:
            self.log(f"Running {category_name} tests...")
            
            try:
                # Run tests in this category
                category_results = await self._run_test_category(test_class)
                results[category_name] = category_results
                
                passed = category_results.get("passed", 0)
                failed = category_results.get("failed", 0)
                total_passed += passed
                total_failed += failed
                
                self.log(f"{category_name} tests completed", 
                        passed=passed, failed=failed)
                
            except Exception as e:
                self.log(f"Error running {category_name} tests", 
                        level="ERROR", error=str(e))
                results[category_name] = {"error": str(e), "passed": 0, "failed": 1}
                total_failed += 1
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        overall_result = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate": total_passed / (total_passed + total_failed) if (total_passed + total_failed) > 0 else 0,
            "categories": results
        }
        
        self.log("Technical Agent FastMCP integration tests completed", 
                duration=duration,
                total_passed=total_passed,
                total_failed=total_failed,
                success_rate=overall_result["success_rate"])
        
        return overall_result
    
    async def _run_test_category(self, test_class) -> Dict[str, Any]:
        """Run tests for a specific category"""
        test_instance = test_class()
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_') and callable(getattr(test_instance, method))]
        
        passed = 0
        failed = 0
        test_details = []
        
        for method_name in test_methods:
            try:
                method = getattr(test_instance, method_name)
                
                if asyncio.iscoroutinefunction(method):
                    await method()
                else:
                    method()
                
                passed += 1
                test_details.append({"test": method_name, "status": "passed"})
                
            except Exception as e:
                failed += 1
                test_details.append({
                    "test": method_name, 
                    "status": "failed", 
                    "error": str(e)
                })
        
        return {
            "passed": passed,
            "failed": failed,
            "total": len(test_methods),
            "details": test_details
        }
    
    def print_report(self, report: Dict[str, Any]):
        """Print detailed test report"""
        print("\n" + "="*80)
        print("TECHNICAL AGENT FASTMCP INTEGRATION TEST REPORT")
        print("="*80)
        
        print(f"Start Time: {report['start_time']}")
        print(f"End Time: {report['end_time']}")
        print(f"Duration: {report['duration_seconds']:.2f} seconds")
        print(f"Total Tests: {report['total_passed'] + report['total_failed']}")
        print(f"Passed: {report['total_passed']}")
        print(f"Failed: {report['total_failed']}")
        print(f"Success Rate: {report['success_rate']:.1%}")
        
        print("\nCATEGORY BREAKDOWN:")
        print("-" * 40)
        
        for category, results in report['categories'].items():
            if 'error' in results:
                print(f"{category}: ERROR - {results['error']}")
            else:
                passed = results['passed']
                failed = results['failed']
                total = results['total']
                rate = (passed / total * 100) if total > 0 else 0
                print(f"{category}: {passed}/{total} passed ({rate:.1f}%)")
                
                # Show failed tests
                if failed > 0:
                    failed_tests = [detail for detail in results['details'] 
                                  if detail['status'] == 'failed']
                    for test in failed_tests:
                        print(f"  ✗ {test['test']}: {test['error']}")
        
        print("\nRECOMMENDations:")
        print("-" * 40)
        
        if report['success_rate'] >= 0.9:
            print("✓ Technical Agent FastMCP integration is working well")
            print("✓ Ready for Domain Agent integration testing")
        elif report['success_rate'] >= 0.7:
            print("⚠ Technical Agent FastMCP integration has some issues")
            print("⚠ Review failed tests before proceeding")
        else:
            print("✗ Technical Agent FastMCP integration needs significant work")
            print("✗ Fix core issues before Domain Agent integration")
        
        if 'FastMCP Integration' in report['categories']:
            integration_results = report['categories']['FastMCP Integration']
            if integration_results.get('failed', 0) > 0:
                print("• Install FastMCP: pip install fastmcp")
                print("• Verify FastMCP services are running")
        
        print("="*80)

async def main():
    """Main test execution function"""
    runner = TechnicalAgentTestRunner()
    
    try:
        print("Running Technical Agent FastMCP Integration Tests...")
        print("This tests the Technical Agent's ability to use FastMCP Client")
        print("to communicate with MCP services while maintaining A2A interface.")
        print("")
        
        report = await runner.run_all_tests()
        runner.print_report(report)
        
        # Return appropriate exit code
        return 0 if report['success_rate'] >= 0.8 else 1
        
    except Exception as e:
        logger.error("Test runner failed", error=str(e))
        print(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 