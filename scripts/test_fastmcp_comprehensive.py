#!/usr/bin/env python3
"""
Comprehensive FastMCP Test Runner
Starts FastMCP server, runs all tests, validates MCP protocol compliance
"""

import asyncio
import aiohttp
import json
import subprocess
import sys
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import signal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import structlog

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastMCPTestRunner:
    """Comprehensive test runner for FastMCP with proper SSE protocol"""
    
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:9000"
        self.test_results = {}
        self.session_id = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        getattr(logger, level.lower())(f"[{timestamp}] {message}")
    
    async def start_server(self) -> bool:
        """Start the FastMCP server"""
        try:
            self.log("Starting FastMCP server...")
            
            # Start server in background
            self.server_process = subprocess.Popen([
                sys.executable, "-m", "services.shared.fastmcp_standalone_server",
                "--port", "9000"
            ], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd=".",
            env={"PYTHONPATH": "."})
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Check if server is running
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                self.log(f"Server failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}", "ERROR")
                return False
            
            # Test health endpoint
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.base_url}/health", timeout=5) as response:
                        if response.status == 200:
                            health_data = await response.json()
                            self.log(f"Server health check passed: {health_data}")
                            return True
                        else:
                            self.log(f"Health check failed with status {response.status}", "ERROR")
                            return False
                except Exception as e:
                    self.log(f"Health check failed: {e}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"Failed to start server: {e}", "ERROR")
            return False
    
    def stop_server(self):
        """Stop the FastMCP server"""
        if self.server_process:
            self.log("Stopping FastMCP server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log("Server didn't stop gracefully, forcing kill", "WARNING")
                self.server_process.kill()
                self.server_process.wait()
            finally:
                self.server_process = None
    
    async def test_json_data_loading(self) -> bool:
        """Test if JSON data loads correctly"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        tools_count = data.get("tools_available", 0)
                        if tools_count > 0:
                            self.log(f"JSON data loaded successfully, {tools_count} tools available")
                            return True
                        else:
                            self.log("No tools available", "ERROR")
                            return False
                    else:
                        self.log(f"Failed to get server info: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"JSON data loading test failed: {e}", "ERROR")
            return False
    
    async def test_sse_connection(self) -> bool:
        """Test SSE connection establishment"""
        try:
            self.log("Testing SSE connection...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/sse") as response:
                    if response.status == 200:
                        # Read initial SSE data
                        async for line in response.content:
                            line_str = line.decode().strip()
                            if line_str.startswith("event: endpoint"):
                                # Extract session endpoint
                                data_line = await response.content.readline()
                                data_str = data_line.decode().strip()
                                if data_str.startswith("data: "):
                                    endpoint = data_str[6:]  # Remove "data: " prefix
                                    self.log(f"SSE connection established, endpoint: {endpoint}")
                                    # Extract session ID from endpoint
                                    if "session_id=" in endpoint:
                                        self.session_id = endpoint.split("session_id=")[1].split("&")[0]
                                        self.log(f"Session ID: {self.session_id}")
                                    return True
                                break
                        else:
                            self.log("No SSE endpoint received", "ERROR")
                            return False
                    else:
                        self.log(f"SSE connection failed: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"SSE connection test failed: {e}", "ERROR")
            return False
    
    async def test_mcp_initialization(self) -> bool:
        """Test MCP protocol initialization"""
        if not self.session_id:
            self.log("No session ID available for MCP testing", "ERROR")
            return False
        
        try:
            self.log("Testing MCP initialization...")
            
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages/?session_id={self.session_id}",
                    json=init_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log(f"MCP initialization successful: {result}")
                        return True
                    else:
                        self.log(f"MCP initialization failed: {response.status}", "ERROR")
                        return False
                        
        except Exception as e:
            self.log(f"MCP initialization test failed: {e}", "ERROR")
            return False
    
    async def test_tools_list(self) -> bool:
        """Test MCP tools/list request"""
        if not self.session_id:
            self.log("No session ID available for tools list testing", "ERROR")
            return False
        
        try:
            self.log("Testing MCP tools/list...")
            
            # Send tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages/?session_id={self.session_id}",
                    json=tools_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        tools = result.get("result", {}).get("tools", [])
                        self.log(f"Tools list received: {len(tools)} tools")
                        for tool in tools[:3]:  # Show first 3 tools
                            self.log(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                        return len(tools) > 0
                    else:
                        self.log(f"Tools list failed: {response.status}", "ERROR")
                        return False
                        
        except Exception as e:
            self.log(f"Tools list test failed: {e}", "ERROR")
            return False
    
    async def test_tool_call(self) -> bool:
        """Test MCP tool call"""
        if not self.session_id:
            self.log("No session ID available for tool call testing", "ERROR")
            return False
        
        try:
            self.log("Testing MCP tool call...")
            
            # Test get_user tool
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_user",
                    "arguments": {
                        "user_id": "user_001"
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/messages/?session_id={self.session_id}",
                    json=tool_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.log(f"Tool call successful: {result}")
                        return True
                    else:
                        self.log(f"Tool call failed: {response.status}", "ERROR")
                        return False
                        
        except Exception as e:
            self.log(f"Tool call test failed: {e}", "ERROR")
            return False
    
    async def test_health_endpoints(self) -> bool:
        """Test health and info endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test health
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status != 200:
                        self.log(f"Health endpoint failed: {response.status}", "ERROR")
                        return False
                
                # Test root
                async with session.get(f"{self.base_url}/") as response:
                    if response.status != 200:
                        self.log(f"Root endpoint failed: {response.status}", "ERROR")
                        return False
                        
                self.log("Health endpoints working correctly")
                return True
                
        except Exception as e:
            self.log(f"Health endpoints test failed: {e}", "ERROR")
            return False
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        self.log("Starting comprehensive FastMCP tests...")
        
        # Start server
        if not await self.start_server():
            return {"success": False, "error": "Failed to start server"}
        
        try:
            results = {}
            
            # Test 1: JSON Data Loading
            self.log("Test 1: JSON Data Loading")
            results["json_data_loading"] = await self.test_json_data_loading()
            
            # Test 2: Health Endpoints
            self.log("Test 2: Health Endpoints")
            results["health_endpoints"] = await self.test_health_endpoints()
            
            # Test 3: SSE Connection
            self.log("Test 3: SSE Connection")
            results["sse_connection"] = await self.test_sse_connection()
            
            # Test 4: MCP Initialization (requires SSE)
            if results["sse_connection"]:
                self.log("Test 4: MCP Initialization")
                results["mcp_initialization"] = await self.test_mcp_initialization()
                
                # Test 5: Tools List (requires MCP init)
                if results["mcp_initialization"]:
                    self.log("Test 5: MCP Tools List")
                    results["mcp_tools_list"] = await self.test_tools_list()
                    
                    # Test 6: Tool Call (requires tools list)
                    if results["mcp_tools_list"]:
                        self.log("Test 6: MCP Tool Call")
                        results["mcp_tool_call"] = await self.test_tool_call()
            
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
            
        finally:
            self.stop_server()
    
    def print_report(self, report: Dict[str, Any]):
        """Print a comprehensive test report"""
        print("\n" + "="*60)
        print("FASTMCP COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        if not report.get("success", False):
            print(f"❌ FAILED: {report.get('error', 'Unknown error')}")
            return
        
        results = report.get("results", {})
        summary = report.get("summary", {})
        
        print(f"Overall Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"Tests Passed: {summary.get('passed', 0)}/{summary.get('total', 0)}")
        print()
        
        print("Test Results:")
        print("-" * 40)
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:25} {status}")
        
        print("\n" + "="*60)


async def main():
    """Main test execution"""
    runner = FastMCPTestRunner()
    
    def signal_handler(sig, frame):
        print("\nShutting down tests...")
        runner.stop_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        report = await runner.run_comprehensive_tests()
        runner.print_report(report)
        
        # Exit with appropriate code
        if report.get("success", False):
            success_rate = report.get("summary", {}).get("success_rate", 0)
            sys.exit(0 if success_rate >= 80 else 1)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        runner.stop_server()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 