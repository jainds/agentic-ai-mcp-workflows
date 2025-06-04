#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Insurance AI POC
Executes unit, integration, and E2E tests and records results
"""

import subprocess
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
import pytest
import coverage

class TestSuiteRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "pending",
            "test_categories": {
                "unit": {"status": "pending", "results": {}},
                "integration": {"status": "pending", "results": {}},
                "e2e": {"status": "pending", "results": {}},
                "system": {"status": "pending", "results": {}},
                "ui": {"status": "pending", "results": {}}
            },
            "coverage": {},
            "metrics": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration": 0
            }
        }
        self.start_time = time.time()
        
    def run_command(self, command, cwd=None, capture_output=True):
        """Run a shell command and return result"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def run_unit_tests(self):
        """Run unit tests"""
        print("🧪 Running Unit Tests...")
        
        # Run all unit tests that exist
        unit_test_commands = [
            "python -m pytest tests/unit/ -v --tb=short --json-report --json-report-file=test_results_unit.json"
        ]
        
        unit_results = {}
        for i, cmd in enumerate(unit_test_commands):
            component = "all_unit_tests"
            print(f"  Testing {component}...")
            result = self.run_command(cmd)
            unit_results[component] = {
                "command": cmd,
                "success": result["success"],
                "output": result["stdout"],
                "errors": result["stderr"]
            }
        
        self.results["test_categories"]["unit"]["results"] = unit_results
        self.results["test_categories"]["unit"]["status"] = "completed"
        
    def run_integration_tests(self):
        """Run integration tests"""
        print("🔗 Running Integration Tests...")
        
        integration_commands = [
            "python -m pytest tests/integration/ -v --tb=short --json-report --json-report-file=test_results_integration.json"
        ]
        
        integration_results = {}
        for i, cmd in enumerate(integration_commands):
            component = "all_integration_tests"
            print(f"  Testing {component}...")
            result = self.run_command(cmd)
            integration_results[component] = {
                "command": cmd,
                "success": result["success"],
                "output": result["stdout"],
                "errors": result["stderr"]
            }
        
        self.results["test_categories"]["integration"]["results"] = integration_results
        self.results["test_categories"]["integration"]["status"] = "completed"
        
    def run_e2e_tests(self):
        """Run E2E tests"""
        print("🎯 Running E2E Tests...")
        
        e2e_commands = [
            "python -m pytest tests/e2e/ -v --tb=short --json-report --json-report-file=test_results_e2e.json"
        ]
        
        e2e_results = {}
        for i, cmd in enumerate(e2e_commands):
            component = "all_e2e_tests"
            print(f"  Testing {component}...")
            result = self.run_command(cmd)
            e2e_results[component] = {
                "command": cmd,
                "success": result["success"],
                "output": result["stdout"],
                "errors": result["stderr"]
            }
        
        self.results["test_categories"]["e2e"]["results"] = e2e_results
        self.results["test_categories"]["e2e"]["status"] = "completed"
        
    def run_system_tests(self):
        """Run system tests"""
        print("🏗️ Running System Tests...")
        
        system_commands = [
            "python -m pytest tests/k8s/ -v --tb=short --json-report --json-report-file=test_results_system.json"
        ]
        
        system_results = {}
        for i, cmd in enumerate(system_commands):
            component = "k8s_system_tests"
            print(f"  Testing {component}...")
            result = self.run_command(cmd)
            system_results[component] = {
                "command": cmd,
                "success": result["success"],
                "output": result["stdout"],
                "errors": result["stderr"]
            }
        
        self.results["test_categories"]["system"]["results"] = system_results
        self.results["test_categories"]["system"]["status"] = "completed"
        
    def run_ui_tests(self):
        """Run UI tests"""
        print("🖥️ Running UI Tests...")
        
        ui_commands = [
            "python -m pytest tests/ui/ -v --tb=short --json-report --json-report-file=test_results_ui.json"
        ]
        
        ui_results = {}
        for i, cmd in enumerate(ui_commands):
            component = "all_ui_tests"
            print(f"  Testing {component}...")
            result = self.run_command(cmd)
            ui_results[component] = {
                "command": cmd,
                "success": result["success"],
                "output": result["stdout"],
                "errors": result["stderr"]
            }
        
        self.results["test_categories"]["ui"]["results"] = ui_results
        self.results["test_categories"]["ui"]["status"] = "completed"
        
    def generate_coverage_report(self):
        """Generate code coverage report"""
        print("📊 Generating Coverage Report...")
        
        # Run coverage analysis
        coverage_cmd = "python -m coverage run -m pytest tests/ && python -m coverage report --format=json"
        result = self.run_command(coverage_cmd)
        
        if result["success"]:
            try:
                # Parse coverage.json if it exists
                if os.path.exists("coverage.json"):
                    with open("coverage.json", "r") as f:
                        coverage_data = json.load(f)
                    self.results["coverage"] = coverage_data
                else:
                    self.results["coverage"] = {"error": "Coverage file not found"}
            except Exception as e:
                self.results["coverage"] = {"error": str(e)}
        else:
            self.results["coverage"] = {
                "error": "Coverage generation failed",
                "details": result["stderr"]
            }
    
    def collect_metrics(self):
        """Collect overall test metrics"""
        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        
        # List of JSON report files to check
        json_files = [
            "test_results_unit.json",
            "test_results_integration.json", 
            "test_results_e2e.json",
            "test_results_system.json",
            "test_results_ui.json"
        ]
        
        for json_file in json_files:
            if os.path.exists(json_file):
                try:
                    with open(json_file, "r") as f:
                        test_data = json.load(f)
                    if "summary" in test_data:
                        summary = test_data["summary"]
                        total_tests += summary.get("total", 0)
                        passed += summary.get("passed", 0) 
                        failed += summary.get("failed", 0)
                        skipped += summary.get("skipped", 0)
                except:
                    pass  # Continue if JSON parsing fails
        
        self.results["metrics"]["total_tests"] = total_tests
        self.results["metrics"]["passed"] = passed
        self.results["metrics"]["failed"] = failed
        self.results["metrics"]["skipped"] = skipped
        self.results["metrics"]["duration"] = time.time() - self.start_time
        
        # Determine overall status
        if failed > 0:
            self.results["overall_status"] = "failed"
        elif total_tests == 0:
            self.results["overall_status"] = "no_tests"
        else:
            self.results["overall_status"] = "passed"
    
    def save_results(self, filename):
        """Save test results to file"""
        self.collect_metrics()
        
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📋 Test results saved to: {filename}")
        print(f"📊 Summary:")
        print(f"   Total Tests: {self.results['metrics']['total_tests']}")
        print(f"   Passed: {self.results['metrics']['passed']}")
        print(f"   Failed: {self.results['metrics']['failed']}")
        print(f"   Skipped: {self.results['metrics']['skipped']}")
        print(f"   Duration: {self.results['metrics']['duration']:.2f}s")
        print(f"   Overall Status: {self.results['overall_status']}")
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Comprehensive Test Suite...")
        print("=" * 60)
        
        try:
            self.run_unit_tests()
            self.run_integration_tests()
            self.run_e2e_tests()
            self.run_system_tests()
            self.run_ui_tests()
            self.generate_coverage_report()
            
        except KeyboardInterrupt:
            print("\n⚠️  Test suite interrupted by user")
            self.results["overall_status"] = "interrupted"
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            self.results["overall_status"] = "error"
            self.results["error"] = str(e)
        
        return self.results

def main():
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    else:
        output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    runner = TestSuiteRunner()
    results = runner.run_all_tests()
    runner.save_results(output_file)
    
    # Exit with appropriate code
    if results["overall_status"] in ["passed", "no_tests"]:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 