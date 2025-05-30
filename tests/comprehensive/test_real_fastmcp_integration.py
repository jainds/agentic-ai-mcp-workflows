#!/usr/bin/env python3
"""
REAL FastMCP Integration Tests - NO MOCKING
Tests actual Technical Agent ↔ FastMCP service integration using real connections.
All errors will be visible to help debug actual integration issues.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.technical.fastmcp_data_agent import FastMCPDataAgent, TaskRequest

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class RealFastMCPIntegrationTester:
    """Test REAL Technical Agent ↔ FastMCP integration with NO MOCKING"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.agent = None
        
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log with structured data"""
        timestamp = datetime.utcnow().isoformat()
        getattr(logger, level.lower())(message, timestamp=timestamp, **kwargs)
        print(f"[{timestamp}] {level}: {message}")
        if kwargs:
            print(f"  Details: {kwargs}")
    
    async def test_agent_creation(self) -> bool:
        """Test REAL agent creation"""
        try:
            self.log("Testing REAL Technical Agent creation")
            self.agent = FastMCPDataAgent(port=8004)
            
            # Check agent properties
            assert self.agent.name == "FastMCPDataAgent"
            assert self.agent.port == 8004
            assert "fastmcp_client" in self.agent.capabilities
            assert len(self.agent.service_urls) == 4
            
            self.log("✅ REAL Technical Agent created successfully", 
                    services=list(self.agent.service_urls.keys()),
                    capabilities=self.agent.capabilities)
            return True
            
        except Exception as e:
            self.log("❌ REAL Technical Agent creation failed", 
                    level="ERROR",
                    error=str(e),
                    error_type=type(e).__name__)
            return False
    
    async def test_agent_initialization(self) -> bool:
        """Test REAL agent initialization with FastMCP services"""
        try:
            self.log("Testing REAL agent initialization")
            
            if not self.agent:
                raise ValueError("Agent not created")
            
            # This will attempt REAL connections to FastMCP services
            await self.agent.initialize()
            
            # Check initialization results
            self.log("✅ REAL agent initialization completed", 
                    initialized=self.agent.initialized,
                    connected_services=len(self.agent.mcp_clients),
                    total_tools=sum(len(tools) for tools in self.agent.available_tools.values()),
                    available_tools=self.agent.available_tools)
            
            return self.agent.initialized
            
        except Exception as e:
            self.log("❌ REAL agent initialization failed", 
                    level="ERROR",
                    error=str(e),
                    error_type=type(e).__name__)
            return False
    
    async def test_service_connection(self, service_name: str) -> bool:
        """Test REAL connection to specific FastMCP service"""
        try:
            self.log(f"Testing REAL connection to {service_name} service")
            
            if service_name not in self.agent.mcp_clients:
                self.log(f"❌ No client available for {service_name}")
                return False
            
            client = self.agent.mcp_clients[service_name]
            
            # Try to list tools from the service
            tools_response = await client.list_tools()
            
            self.log(f"✅ REAL connection to {service_name} successful", 
                    response_type=type(tools_response).__name__,
                    tools_count=len(tools_response.tools) if hasattr(tools_response, 'tools') else 0)
            
            return True
            
        except Exception as e:
            self.log(f"❌ REAL connection to {service_name} failed", 
                    level="ERROR",
                    error=str(e),
                    error_type=type(e).__name__)
            return False
    
    async def test_tool_discovery(self) -> bool:
        """Test REAL tool discovery from all services"""
        try:
            self.log("Testing REAL tool discovery")
            
            total_tools = 0
            for service_name, tools in self.agent.available_tools.items():
                tool_count = len(tools)
                total_tools += tool_count
                
                self.log(f"Service {service_name} tools", 
                        count=tool_count,
                        tools=[tool.get("name", "unknown") for tool in tools])
            
            self.log("✅ REAL tool discovery completed", 
                    total_services=len(self.agent.available_tools),
                    total_tools=total_tools)
            
            return total_tools > 0
            
        except Exception as e:
            self.log("❌ REAL tool discovery failed", 
                    level="ERROR",
                    error=str(e),
                    error_type=type(e).__name__)
            return False
    
    async def test_real_tool_call(self, service_name: str, tool_name: str, arguments: dict) -> bool:
        """Test REAL tool call to FastMCP service"""
        try:
            self.log(f"Testing REAL tool call: {service_name}.{tool_name}", 
                    arguments=arguments)
            
            # Make REAL tool call
            result = await self.agent.call_tool(service_name, tool_name, arguments)
            
            self.log(f"✅ REAL tool call successful: {service_name}.{tool_name}", 
                    result_type=type(result).__name__,
                    success=result.get("success", "unknown"),
                    result_keys=list(result.keys()) if isinstance(result, dict) else "non-dict")
            
            return result.get("success", True) if isinstance(result, dict) else True
            
        except Exception as e:
            self.log(f"❌ REAL tool call failed: {service_name}.{tool_name}", 
                    level="ERROR",
                    error=str(e),
                    error_type=type(e).__name__,
                    arguments=arguments)
            return False
    
    async def test_a2a_task_handling(self) -> bool:
        """Test REAL A2A task handling"""
        try:
            self.log("Testing REAL A2A task handling")
            
            # Create a real A2A task
            task = TaskRequest(
                taskId="test_get_customer_123",
                user={
                    "action": "get_customer",
                    "customer_id": "CUST001"
                }
            )
            
            # Process task with REAL FastMCP calls
            response = self.agent.handle_task(task)
            
            self.log("✅ REAL A2A task handling completed", 
                    task_id=response.taskId,
                    status=response.status,
                    parts_count=len(response.parts),
                    metadata=response.metadata)
            
            return response.status == "completed"
            
        except Exception as e:
            self.log("❌ REAL A2A task handling failed", 
                    level="ERROR",
                    error=str(e),
                    error_type=type(e).__name__)
            return False
    
    async def test_error_handling(self) -> bool:
        """Test REAL error handling with invalid requests"""
        try:
            self.log("Testing REAL error handling")
            
            # Test with invalid service
            result1 = await self.agent.call_tool("invalid_service", "test_tool", {})
            
            # Test with invalid tool
            result2 = await self.agent.call_tool("user", "invalid_tool", {})
            
            # Test with missing parameters
            task = TaskRequest(
                taskId="test_error",
                user={"action": "get_customer"}  # Missing customer_id
            )
            response = self.agent.handle_task(task)
            
            self.log("✅ REAL error handling tests completed", 
                    invalid_service_error=result1.get("error", "no error"),
                    invalid_tool_error=result2.get("error", "no error"),
                    missing_param_status=response.status)
            
            return True
            
        except Exception as e:
            self.log("❌ REAL error handling test failed", 
                    level="ERROR",
                    error=str(e),
                    error_type=type(e).__name__)
            return False
    
    async def run_all_tests(self) -> dict:
        """Run all REAL integration tests"""
        self.start_time = datetime.utcnow()
        self.log("Starting REAL FastMCP Integration Tests", 
                test_time=self.start_time.isoformat())
        
        tests = [
            ("agent_creation", self.test_agent_creation),
            ("agent_initialization", self.test_agent_initialization),
            ("service_connections", self.test_service_connections),
            ("tool_discovery", self.test_tool_discovery),
            ("tool_calls", self.test_tool_calls),
            ("a2a_task_handling", self.test_a2a_task_handling),
            ("error_handling", self.test_error_handling)
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                self.log(f"Running test: {test_name}")
                result = await test_func()
                results[test_name] = {
                    "passed": result,
                    "error": None
                }
                if result:
                    passed += 1
                    
            except Exception as e:
                self.log(f"Test {test_name} threw exception", 
                        level="ERROR",
                        error=str(e),
                        error_type=type(e).__name__)
                results[test_name] = {
                    "passed": False,
                    "error": str(e)
                }
        
        # Final cleanup
        if self.agent:
            try:
                await self.agent.close()
            except Exception as e:
                self.log("Error during cleanup", level="WARNING", error=str(e))
        
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        self.log("REAL FastMCP Integration Tests completed", 
                passed=passed,
                total=total,
                success_rate=f"{(passed/total)*100:.1f}%",
                duration_seconds=duration,
                results=results)
        
        return {
            "summary": {
                "passed": passed,
                "total": total,
                "success_rate": (passed/total)*100,
                "duration_seconds": duration
            },
            "results": results,
            "timestamp": end_time.isoformat()
        }
    
    async def test_service_connections(self) -> bool:
        """Test connections to all services"""
        if not self.agent or not self.agent.mcp_clients:
            return False
        
        success_count = 0
        for service_name in self.agent.service_urls.keys():
            if await self.test_service_connection(service_name):
                success_count += 1
        
        return success_count > 0
    
    async def test_tool_calls(self) -> bool:
        """Test various tool calls"""
        test_calls = [
            ("user", "get_user", {"user_id": "CUST001"}),
            ("claims", "list_claims", {"customer_id": "CUST001"}),
            ("policy", "list_policies", {"customer_id": "CUST001"})
        ]
        
        success_count = 0
        for service, tool, args in test_calls:
            if service in self.agent.mcp_clients:
                if await self.test_real_tool_call(service, tool, args):
                    success_count += 1
        
        return success_count > 0


async def main():
    """Run REAL integration tests"""
    print("=" * 80)
    print("REAL FastMCP Integration Tests - NO MOCKING")
    print("All errors will be visible to help debug integration issues")
    print("=" * 80)
    
    tester = RealFastMCPIntegrationTester()
    results = await tester.run_all_tests()
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS:")
    print(f"Tests Passed: {results['summary']['passed']}/{results['summary']['total']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Duration: {results['summary']['duration_seconds']:.2f} seconds")
    
    print("\nDetailed Results:")
    for test_name, result in results['results'].items():
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result['error']:
            print(f"    Error: {result['error']}")
    
    print("=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if results['summary']['passed'] == results['summary']['total'] else 1)


if __name__ == "__main__":
    asyncio.run(main()) 