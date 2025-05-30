#!/usr/bin/env python3

"""
Modular FastMCP Test Suite

Comprehensive testing for the modular FastMCP implementation with detailed logging.
"""

import asyncio
import sys
import json
import time
import logging
from typing import Dict, Any, List
from pathlib import Path
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    print("❌ FastMCP not available. Please install: pip install fastmcp")
    FASTMCP_AVAILABLE = False

from services.shared.fastmcp_server import ModularFastMCPServer, create_fastmcp_server
from services.shared.fastmcp_data_service import FastMCPDataService

# Setup logging
logger = structlog.get_logger(__name__)


class ModularFastMCPTestRunner:
    """Test runner for modular FastMCP implementation"""
    
    def __init__(self):
        self.test_results = {}
        self.server = None
        
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log a message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_method = getattr(logger, level.lower())
        log_method(f"[{timestamp}] {message}", **kwargs)
    
    async def test_fastmcp_availability(self) -> bool:
        """Test that FastMCP is available and can be imported"""
        try:
            if not FASTMCP_AVAILABLE:
                self.log("FastMCP not available", "ERROR")
                return False
            
            self.log("✅ FastMCP library is available")
            return True
            
        except Exception as e:
            self.log("FastMCP availability test failed", "ERROR", error=str(e))
            return False
    
    async def test_modular_server_creation(self) -> bool:
        """Test modular server creation with all components"""
        try:
            self.log("Testing modular FastMCP server creation...")
            
            # Create server instance
            self.server = ModularFastMCPServer("Test Insurance Server")
            
            if not self.server:
                self.log("Failed to create server instance", "ERROR")
                return False
            
            self.log("✅ Modular server instance created")
            return True
            
        except Exception as e:
            self.log("Modular server creation failed", "ERROR", error=str(e))
            return False
    
    async def test_data_service_initialization(self) -> bool:
        """Test data service initialization"""
        try:
            if not self.server:
                self.log("No server available for data service test", "ERROR")
                return False
            
            self.log("Testing data service initialization...")
            
            # Initialize data service
            success = self.server.initialize_data_service()
            
            if not success:
                self.log("Data service initialization failed", "ERROR")
                return False
            
            # Verify data was loaded
            if not self.server.data_service or not self.server.data_service.data:
                self.log("No data loaded in data service", "ERROR")
                return False
            
            # Log data statistics
            data_stats = {
                "users": len(self.server.data_service.data.get('users', [])),
                "policies": len(self.server.data_service.data.get('policies', [])),
                "claims": len(self.server.data_service.data.get('claims', [])),
                "quotes": len(self.server.data_service.data.get('quotes', []))
            }
            
            self.log("✅ Data service initialized successfully", **data_stats)
            return True
            
        except Exception as e:
            self.log("Data service initialization test failed", "ERROR", error=str(e))
            return False
    
    async def test_mcp_server_creation(self) -> bool:
        """Test FastMCP server instance creation"""
        try:
            if not self.server:
                self.log("No server available for MCP server test", "ERROR")
                return False
            
            self.log("Testing FastMCP server instance creation...")
            
            # Create MCP server
            success = self.server.create_mcp_server()
            
            if not success:
                self.log("FastMCP server creation failed", "ERROR")
                return False
            
            # Verify server instance
            if not self.server.mcp_server:
                self.log("FastMCP server instance not created", "ERROR")
                return False
            
            if not isinstance(self.server.mcp_server, FastMCP):
                self.log("Created object is not FastMCP instance", "ERROR", 
                        type=type(self.server.mcp_server))
                return False
            
            self.log("✅ FastMCP server instance created successfully")
            return True
            
        except Exception as e:
            self.log("FastMCP server creation test failed", "ERROR", error=str(e))
            return False
    
    async def test_tool_modules_initialization(self) -> bool:
        """Test initialization of all tool modules"""
        try:
            if not self.server:
                self.log("No server available for tool modules test", "ERROR")
                return False
            
            self.log("Testing tool modules initialization...")
            
            # Initialize tool modules
            success = self.server.initialize_tool_modules()
            
            if not success:
                self.log("Tool modules initialization failed", "ERROR")
                return False
            
            # Verify tool modules
            if not self.server.tool_modules:
                self.log("No tool modules initialized", "ERROR")
                return False
            
            expected_modules = {"user", "policy", "claims", "analytics", "quote"}
            actual_modules = set(self.server.tool_modules.keys())
            
            if not expected_modules.issubset(actual_modules):
                missing = expected_modules - actual_modules
                self.log("Missing tool modules", "ERROR", missing=list(missing))
                return False
            
            module_count = len(self.server.tool_modules)
            self.log("✅ Tool modules initialized successfully", modules=module_count,
                    module_names=list(self.server.tool_modules.keys()))
            return True
            
        except Exception as e:
            self.log("Tool modules initialization test failed", "ERROR", error=str(e))
            return False
    
    async def test_tool_registration(self) -> bool:
        """Test registration of all tools with FastMCP server"""
        try:
            if not self.server:
                self.log("No server available for tool registration test", "ERROR")
                return False
            
            self.log("Testing tool registration...")
            
            # Register all tools
            success = self.server.register_all_tools()
            
            if not success:
                self.log("Tool registration failed", "ERROR")
                return False
            
            self.log("✅ All tools registered successfully")
            return True
            
        except Exception as e:
            self.log("Tool registration test failed", "ERROR", error=str(e))
            return False
    
    async def test_complete_server_setup(self) -> bool:
        """Test complete server setup process"""
        try:
            self.log("Testing complete server setup...")
            
            # Create fresh server for complete setup test
            test_server = ModularFastMCPServer("Complete Setup Test")
            
            # Run complete setup
            success = test_server.setup()
            
            if not success:
                self.log("Complete server setup failed", "ERROR")
                return False
            
            # Validate setup
            if not test_server.validate_server_setup():
                self.log("Server setup validation failed", "ERROR")
                return False
            
            # Get server info
            info = test_server.get_server_info()
            self.log("✅ Complete server setup successful", **info)
            return True
            
        except Exception as e:
            self.log("Complete server setup test failed", "ERROR", error=str(e))
            return False
    
    async def test_tool_execution(self) -> bool:
        """Test execution of tools through modular system"""
        try:
            if not self.server or not self.server.tool_modules:
                self.log("No server or tool modules available for execution test", "ERROR")
                return False
            
            self.log("Testing tool execution...")
            
            # Test cases for different tool modules
            test_cases = [
                ("user", "get_user", {"user_id": "user_001"}),
                ("user", "list_users", {}),
                ("policy", "get_customer_policies", {"customer_id": "user_003"}),
                ("claims", "get_customer_claims", {"customer_id": "user_003"}),
                ("analytics", "get_market_trends", {}),
                ("quote", "generate_quote", {"customer_id": "user_001", "quote_type": "auto", "coverage_amount": 100000})
            ]
            
            passed_tests = 0
            total_tests = len(test_cases)
            
            for module_name, tool_name, params in test_cases:
                try:
                    self.log(f"Testing {module_name}.{tool_name}...", params=params)
                    
                    # Get tool module
                    tool_module = self.server.tool_modules.get(module_name)
                    if not tool_module:
                        self.log(f"Tool module {module_name} not found", "ERROR")
                        continue
                    
                    # Get tool function
                    tool_func = getattr(tool_module, tool_name, None)
                    if not tool_func:
                        self.log(f"Tool function {tool_name} not found in {module_name}", "ERROR")
                        continue
                    
                    # Execute tool
                    start_time = time.time()
                    result = tool_func(**params)
                    end_time = time.time()
                    
                    execution_time = end_time - start_time
                    
                    # Verify result
                    if result is None:
                        self.log(f"Tool {module_name}.{tool_name} returned None", "ERROR")
                        continue
                    
                    # Parse JSON result
                    try:
                        parsed_result = json.loads(result)
                        if isinstance(parsed_result, dict) and parsed_result.get('success'):
                            self.log(f"✅ {module_name}.{tool_name} executed successfully", 
                                   execution_time=f"{execution_time:.3f}s")
                            passed_tests += 1
                        else:
                            self.log(f"❌ {module_name}.{tool_name} returned failure", 
                                   error=parsed_result.get('error', 'Unknown'))
                    except json.JSONDecodeError:
                        self.log(f"❌ {module_name}.{tool_name} returned invalid JSON", "ERROR")
                    
                except Exception as e:
                    self.log(f"❌ {module_name}.{tool_name} execution failed", "ERROR", error=str(e))
            
            success_rate = (passed_tests / total_tests) * 100
            self.log(f"Tool execution results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
            
            return passed_tests >= (total_tests * 0.8)  # 80% success rate required
            
        except Exception as e:
            self.log("Tool execution test failed", "ERROR", error=str(e))
            return False
    
    async def test_factory_function(self) -> bool:
        """Test the factory function for creating FastMCP servers"""
        try:
            self.log("Testing factory function...")
            
            # Use factory function
            mcp_server = create_fastmcp_server()
            
            if not mcp_server:
                self.log("Factory function returned None", "ERROR")
                return False
            
            if not isinstance(mcp_server, FastMCP):
                self.log("Factory function returned wrong type", "ERROR", type=type(mcp_server))
                return False
            
            self.log("✅ Factory function created FastMCP server successfully")
            return True
            
        except Exception as e:
            self.log("Factory function test failed", "ERROR", error=str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all modular FastMCP tests"""
        self.log("🧪 Starting Modular FastMCP Test Suite")
        self.log("="*60)
        
        results = {}
        
        # Test 1: FastMCP Availability
        self.log("Test 1: FastMCP Availability")
        results["fastmcp_availability"] = await self.test_fastmcp_availability()
        
        if not results["fastmcp_availability"]:
            return {
                "success": False,
                "error": "FastMCP not available",
                "results": results
            }
        
        # Test 2: Modular Server Creation
        self.log("Test 2: Modular Server Creation")
        results["modular_server_creation"] = await self.test_modular_server_creation()
        
        # Test 3: Data Service Initialization
        self.log("Test 3: Data Service Initialization")
        results["data_service_initialization"] = await self.test_data_service_initialization()
        
        # Test 4: FastMCP Server Creation
        self.log("Test 4: FastMCP Server Creation")
        results["mcp_server_creation"] = await self.test_mcp_server_creation()
        
        # Test 5: Tool Modules Initialization
        self.log("Test 5: Tool Modules Initialization")
        results["tool_modules_initialization"] = await self.test_tool_modules_initialization()
        
        # Test 6: Tool Registration
        self.log("Test 6: Tool Registration")
        results["tool_registration"] = await self.test_tool_registration()
        
        # Test 7: Complete Server Setup
        self.log("Test 7: Complete Server Setup")
        results["complete_server_setup"] = await self.test_complete_server_setup()
        
        # Test 8: Tool Execution
        self.log("Test 8: Tool Execution")
        results["tool_execution"] = await self.test_tool_execution()
        
        # Test 9: Factory Function
        self.log("Test 9: Factory Function")
        results["factory_function"] = await self.test_factory_function()
        
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
        print("MODULAR FASTMCP COMPREHENSIVE TEST REPORT")
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
        print("-" * 60)
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<35} {status}")
        
        print("\n" + "="*80)
        
        # Provide recommendations
        if summary.get('success_rate', 0) < 100:
            print("\n🔧 Recommendations:")
            if not results.get('fastmcp_availability', True):
                print("  - Install FastMCP: pip install fastmcp")
            if not results.get('tool_execution', True):
                print("  - Review tool implementations and data service integration")
            if not results.get('complete_server_setup', True):
                print("  - Check server setup process and validation")
        else:
            print("\n🎉 All tests passed! Modular FastMCP is working perfectly.")


async def main():
    """Main test execution"""
    if not FASTMCP_AVAILABLE:
        print("❌ FastMCP not available. Please install: pip install fastmcp")
        sys.exit(1)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    runner = ModularFastMCPTestRunner()
    
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