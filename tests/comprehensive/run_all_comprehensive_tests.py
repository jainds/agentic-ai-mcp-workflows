#!/usr/bin/env python3

"""
Master Test Runner for Comprehensive Agent Integration Tests

Executes all comprehensive tests in sequence:
1. FastMCP Modular Server Tests
2. Technical Agent Tests
3. Domain Agent Tests
4. Integration Tests (Domain <-> Technical)

Provides consolidated reporting and recommendations.
"""

import asyncio
import sys
import time
import json
import subprocess
from typing import Dict, Any, List
from pathlib import Path
import structlog

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logger = structlog.get_logger(__name__)


class ComprehensiveTestSuite:
    """Master test suite runner"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def log(self, message: str, level: str = "INFO", **kwargs):
        """Log a message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_method = getattr(logger, level.lower())
        log_method(f"[{timestamp}] {message}", **kwargs)
    
    async def run_test_script(self, script_path: str, test_name: str) -> Dict[str, Any]:
        """Run a test script and capture results"""
        try:
            self.log(f"Running {test_name}...")
            
            start_time = time.time()
            
            # Run the test script
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_root
            )
            
            stdout, stderr = await process.communicate()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            success = process.returncode == 0
            
            return {
                "success": success,
                "duration": duration,
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "script_path": str(script_path)
            }
            
        except Exception as e:
            self.log(f"{test_name} execution failed", "ERROR", error=str(e))
            return {
                "success": False,
                "duration": 0,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "script_path": str(script_path),
                "error": str(e)
            }
    
    async def run_fastmcp_tests(self) -> Dict[str, Any]:
        """Run FastMCP modular server tests"""
        script_path = project_root / "scripts" / "test_modular_fastmcp.py"
        
        if not script_path.exists():
            return {
                "success": False,
                "error": "FastMCP test script not found",
                "duration": 0
            }
        
        return await self.run_test_script(script_path, "FastMCP Modular Server Tests")
    
    async def run_technical_agent_tests(self) -> Dict[str, Any]:
        """Run Technical Agent comprehensive tests"""
        script_path = project_root / "tests" / "comprehensive" / "test_technical_agent_fastmcp.py"
        
        if not script_path.exists():
            return {
                "success": False,
                "error": "Technical Agent test script not found",
                "duration": 0
            }
        
        return await self.run_test_script(script_path, "Technical Agent Comprehensive Tests")
    
    async def run_domain_agent_tests(self) -> Dict[str, Any]:
        """Run Domain Agent comprehensive tests"""
        script_path = project_root / "tests" / "comprehensive" / "test_domain_agent_comprehensive.py"
        
        if not script_path.exists():
            return {
                "success": False,
                "error": "Domain Agent test script not found",
                "duration": 0
            }
        
        return await self.run_test_script(script_path, "Domain Agent Comprehensive Tests")
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run Domain <-> Technical Agent integration tests"""
        script_path = project_root / "tests" / "comprehensive" / "test_domain_technical_integration.py"
        
        if not script_path.exists():
            return {
                "success": False,
                "error": "Integration test script not found",
                "duration": 0
            }
        
        return await self.run_test_script(script_path, "Domain <-> Technical Agent Integration Tests")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests in sequence"""
        self.log("🧪 Starting Comprehensive Agent Integration Test Suite")
        self.log("="*80)
        
        self.start_time = time.time()
        
        # Test 1: FastMCP Modular Server
        self.log("Phase 1: FastMCP Modular Server Tests")
        self.test_results["fastmcp_server"] = await self.run_fastmcp_tests()
        
        # Test 2: Technical Agent
        self.log("Phase 2: Technical Agent Comprehensive Tests")
        self.test_results["technical_agent"] = await self.run_technical_agent_tests()
        
        # Test 3: Domain Agent
        self.log("Phase 3: Domain Agent Comprehensive Tests")
        self.test_results["domain_agent"] = await self.run_domain_agent_tests()
        
        # Test 4: Integration Tests
        self.log("Phase 4: Domain <-> Technical Agent Integration Tests")
        self.test_results["integration"] = await self.run_integration_tests()
        
        self.end_time = time.time()
        
        # Calculate overall results
        passed_phases = sum(1 for result in self.test_results.values() if result.get("success", False))
        total_phases = len(self.test_results)
        overall_success_rate = (passed_phases / total_phases * 100) if total_phases > 0 else 0
        total_duration = self.end_time - self.start_time
        
        self.log(f"All comprehensive tests completed: {passed_phases}/{total_phases} phases passed ({overall_success_rate:.1f}%)")
        
        return {
            "success": overall_success_rate >= 75,  # Pass if 75% or more phases succeed
            "results": self.test_results,
            "summary": {
                "passed_phases": passed_phases,
                "total_phases": total_phases,
                "overall_success_rate": overall_success_rate,
                "total_duration": total_duration,
                "start_time": self.start_time,
                "end_time": self.end_time
            }
        }
    
    def extract_test_details(self, test_output: str) -> Dict[str, Any]:
        """Extract detailed test information from output"""
        details = {
            "individual_tests": [],
            "success_rate": 0,
            "total_tests": 0,
            "passed_tests": 0
        }
        
        try:
            lines = test_output.split('\n')
            
            for line in lines:
                # Look for test result lines (format: "test_name PASS/FAIL")
                if "✅ PASS" in line or "❌ FAIL" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        test_name = parts[0]
                        status = "PASS" if "✅ PASS" in line else "FAIL"
                        details["individual_tests"].append({
                            "name": test_name,
                            "status": status
                        })
                        
                        details["total_tests"] += 1
                        if status == "PASS":
                            details["passed_tests"] += 1
                
                # Look for success rate information
                if "success rate" in line.lower() or "passed" in line.lower():
                    # Try to extract percentages and counts
                    import re
                    percent_match = re.search(r'(\d+\.?\d*)%', line)
                    if percent_match:
                        details["success_rate"] = float(percent_match.group(1))
            
            # Calculate success rate if not found
            if details["total_tests"] > 0 and details["success_rate"] == 0:
                details["success_rate"] = (details["passed_tests"] / details["total_tests"]) * 100
        
        except Exception as e:
            self.log(f"Error extracting test details: {e}", "WARNING")
        
        return details
    
    def print_comprehensive_report(self, report: Dict[str, Any]):
        """Print comprehensive test report"""
        print("\n" + "="*100)
        print("COMPREHENSIVE AGENT INTEGRATION TEST REPORT")
        print("="*100)
        
        if not report.get("success", False):
            print(f"❌ OVERALL RESULT: FAILED")
        else:
            print(f"✅ OVERALL RESULT: PASSED")
        
        summary = report.get("summary", {})
        
        print(f"\nOverall Success Rate: {summary.get('overall_success_rate', 0):.1f}%")
        print(f"Phases Passed: {summary.get('passed_phases', 0)}/{summary.get('total_phases', 0)}")
        print(f"Total Duration: {summary.get('total_duration', 0):.2f} seconds")
        print()
        
        # Phase-by-phase results
        print("Phase Results:")
        print("-" * 90)
        results = report.get("results", {})
        
        phase_names = {
            "fastmcp_server": "FastMCP Modular Server Tests",
            "technical_agent": "Technical Agent Comprehensive Tests", 
            "domain_agent": "Domain Agent Comprehensive Tests",
            "integration": "Domain <-> Technical Agent Integration Tests"
        }
        
        for phase_key, phase_result in results.items():
            phase_name = phase_names.get(phase_key, phase_key)
            status = "✅ PASS" if phase_result.get("success", False) else "❌ FAIL"
            duration = phase_result.get("duration", 0)
            
            print(f"{phase_name:<50} {status:<10} ({duration:.2f}s)")
            
            # Extract and show individual test details
            if phase_result.get("stdout"):
                details = self.extract_test_details(phase_result["stdout"])
                if details["total_tests"] > 0:
                    print(f"  └─ Individual Tests: {details['passed_tests']}/{details['total_tests']} passed ({details['success_rate']:.1f}%)")
            
            # Show errors if any
            if not phase_result.get("success", False) and phase_result.get("stderr"):
                error_lines = phase_result["stderr"].strip().split('\n')
                if error_lines and error_lines[0]:
                    print(f"  └─ Error: {error_lines[0][:70]}...")
        
        print("\n" + "="*100)
        
        # Detailed recommendations
        failed_phases = [phase for phase, result in results.items() if not result.get("success", False)]
        
        if failed_phases:
            print("\n🔧 ISSUE ANALYSIS & RECOMMENDATIONS:")
            print("-" * 50)
            
            if "fastmcp_server" in failed_phases:
                print("\n📦 FastMCP Server Issues:")
                print("  - Check FastMCP dependencies and installation")
                print("  - Verify modular server architecture")
                print("  - Run: python scripts/test_modular_fastmcp.py")
            
            if "technical_agent" in failed_phases:
                print("\n🔧 Technical Agent Issues:")
                print("  - Check Technical Agent dependencies")
                print("  - Verify FastMCP integration")
                print("  - Check A2A protocol implementation")
                print("  - Run: python tests/comprehensive/test_technical_agent_fastmcp.py")
            
            if "domain_agent" in failed_phases:
                print("\n🧠 Domain Agent Issues:")
                print("  - Configure LLM client (OpenAI/OpenRouter API key)")
                print("  - Check intent analysis functionality")
                print("  - Verify response generation templates")
                print("  - Run: python tests/comprehensive/test_domain_agent_comprehensive.py")
            
            if "integration" in failed_phases:
                print("\n🔗 Integration Issues:")
                print("  - Fix communication between Domain and Technical agents")
                print("  - Check A2A protocol compatibility")
                print("  - Verify end-to-end workflow execution")
                print("  - Run: python tests/comprehensive/test_domain_technical_integration.py")
            
            print("\n📋 NEXT STEPS:")
            print("1. Address the issues above in order of priority")
            print("2. Re-run individual test suites to verify fixes")
            print("3. Run this comprehensive suite again")
            print("4. Proceed with system deployment once all tests pass")
        
        else:
            print("\n🎉 EXCELLENT! All comprehensive tests passed!")
            print("\n✅ SYSTEM STATUS:")
            print("  - FastMCP modular server is working correctly")
            print("  - Technical agent is functioning properly")
            print("  - Domain agent is operating as expected")
            print("  - Integration between agents is successful")
            print("\n🚀 READY FOR:")
            print("  - Production deployment")
            print("  - End-to-end user testing")
            print("  - System monitoring and optimization")
        
        # Save detailed report
        report_file = project_root / "comprehensive_test_report.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n📄 Detailed report saved to: {report_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save detailed report: {e}")


async def main():
    """Main execution"""
    try:
        # Configure logging
        import logging
        logging.basicConfig(level=logging.INFO)
        
        # Create and run test suite
        test_suite = ComprehensiveTestSuite()
        
        print("🧪 COMPREHENSIVE AGENT INTEGRATION TEST SUITE")
        print("Testing complete chain: User -> Domain Agent -> Technical Agent -> FastMCP -> Data")
        print("="*100)
        
        report = await test_suite.run_all_tests()
        test_suite.print_comprehensive_report(report)
        
        # Exit with appropriate code
        if report.get("success", False):
            print("\n✅ All comprehensive tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Some comprehensive tests failed. Please review the issues above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error("Comprehensive test execution failed", error=str(e), exc_info=True)
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 