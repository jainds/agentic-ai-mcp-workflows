#!/usr/bin/env python3
"""
Comprehensive Test Runner for Insurance AI POC

This script ensures the complete architecture is tested:
1. Streamlit UI for visualization
2. Domain agent plans and orchestrates with LLM reasoning
3. Domain agent talks to technical agent via official Google A2A protocol
4. Technical agent has MCP tools using FastMCP library

Test Flow:
Unit Tests → Integration Tests → End-to-End Tests → Cleanup
"""

import os
import sys
import subprocess
import time
import asyncio
import httpx
import signal
from typing import List, Dict, Any
import json
from pathlib import Path

class ComprehensiveTestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {
            "unit_tests": {"status": "pending", "details": {}},
            "integration_tests": {"status": "pending", "details": {}},
            "e2e_tests": {"status": "pending", "details": {}},
            "service_health": {"status": "pending", "details": {}},
            "architecture_validation": {"status": "pending", "details": {}}
        }
        self.started_processes = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def cleanup_processes(self):
        """Clean up any started processes."""
        for process in self.started_processes:
            try:
                if process.poll() is None:  # Process is still running
                    self.log(f"Terminating process {process.pid}")
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
            except Exception as e:
                self.log(f"Error cleaning up process: {e}", "ERROR")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for clean shutdown."""
        def signal_handler(signum, frame):
            self.log("Received shutdown signal, cleaning up...")
            self.cleanup_processes()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def check_service_health(self, url: str, timeout: int = 5) -> bool:
        """Check if a service is healthy."""
        try:
            response = httpx.get(url, timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    def _check_fastmcp_services(self) -> bool:
        """Check if FastMCP services are running."""
        # FastMCP services use dynamic ports, so check common port ranges
        potential_ports = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007]
        healthy_services = 0
        
        for port in potential_ports:
            if self.check_service_health(f"http://localhost:{port}/health"):
                healthy_services += 1
        
        # We need at least 4 services (user, claims, policy, analytics)
        return healthy_services >= 4
    
    def discover_service_ports(self) -> Dict[str, int]:
        """Discover which ports the FastMCP services are running on."""
        service_ports = {}
        potential_ports = [8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007]
        
        for port in potential_ports:
            try:
                response = httpx.get(f"http://localhost:{port}/health", timeout=3.0)
                if response.status_code == 200:
                    health_data = response.json()
                    service_name = health_data.get("service", "unknown")
                    service_ports[service_name] = port
                    self.log(f"Discovered {service_name} on port {port}")
            except:
                continue
                
        return service_ports
    
    def start_fastmcp_services(self) -> bool:
        """Start FastMCP services if not already running."""
        self.log("Starting FastMCP services...")
        
        # Check if we already have enough services running
        if self._check_fastmcp_services():
            self.log("Sufficient FastMCP services already running")
            return True
        
        # Start services
        try:
            process = subprocess.Popen([
                sys.executable, "scripts/start_fastmcp_services.py"
            ], cwd=self.project_root)
            self.started_processes.append(process)
            
            # Wait for services to start with dynamic port discovery
            max_wait = 45  # Increased timeout
            wait_time = 0
            
            while wait_time < max_wait:
                if self._check_fastmcp_services():
                    # Discover actual ports
                    service_ports = self.discover_service_ports()
                    self.log(f"All FastMCP services started successfully with ports: {service_ports}")
                    return True
                
                time.sleep(3)  # Increased check interval
                wait_time += 3
            
            self.log("FastMCP services failed to start within timeout", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"Failed to start FastMCP services: {e}", "ERROR")
            return False
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests and return results."""
        self.log("Running unit tests...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/unit/", 
                "-v", 
                "--tb=short",
                "--json-report",
                "--json-report-file=test_results_unit.json"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            success = result.returncode == 0
            
            # Try to read detailed results
            details = {"stdout": result.stdout, "stderr": result.stderr}
            try:
                with open(self.project_root / "test_results_unit.json") as f:
                    details["json_report"] = json.load(f)
            except:
                pass
            
            self.test_results["unit_tests"] = {
                "status": "passed" if success else "failed",
                "details": details
            }
            
            if success:
                self.log("✅ Unit tests passed")
            else:
                self.log("❌ Unit tests failed", "ERROR")
                self.log(f"STDOUT: {result.stdout}")
                self.log(f"STDERR: {result.stderr}")
            
            return self.test_results["unit_tests"]
            
        except Exception as e:
            self.log(f"Error running unit tests: {e}", "ERROR")
            self.test_results["unit_tests"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            return self.test_results["unit_tests"]
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests and return results."""
        self.log("Running integration tests...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/integration/", 
                "-v", 
                "--tb=short",
                "-m", "integration",
                "--json-report",
                "--json-report-file=test_results_integration.json"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            success = result.returncode == 0
            
            details = {"stdout": result.stdout, "stderr": result.stderr}
            try:
                with open(self.project_root / "test_results_integration.json") as f:
                    details["json_report"] = json.load(f)
            except:
                pass
            
            self.test_results["integration_tests"] = {
                "status": "passed" if success else "failed",
                "details": details
            }
            
            if success:
                self.log("✅ Integration tests passed")
            else:
                self.log("❌ Integration tests failed", "ERROR")
                self.log(f"STDOUT: {result.stdout}")
                self.log(f"STDERR: {result.stderr}")
            
            return self.test_results["integration_tests"]
            
        except Exception as e:
            self.log(f"Error running integration tests: {e}", "ERROR")
            self.test_results["integration_tests"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            return self.test_results["integration_tests"]
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests and return results."""
        self.log("Running end-to-end tests...")
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/e2e/", 
                "-v", 
                "--tb=short",
                "-m", "e2e",
                "--json-report",
                "--json-report-file=test_results_e2e.json"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            success = result.returncode == 0
            
            details = {"stdout": result.stdout, "stderr": result.stderr}
            try:
                with open(self.project_root / "test_results_e2e.json") as f:
                    details["json_report"] = json.load(f)
            except:
                pass
            
            self.test_results["e2e_tests"] = {
                "status": "passed" if success else "failed",
                "details": details
            }
            
            if success:
                self.log("✅ End-to-end tests passed")
            else:
                self.log("❌ End-to-end tests failed", "ERROR")
                self.log(f"STDOUT: {result.stdout}")
                self.log(f"STDERR: {result.stderr}")
            
            return self.test_results["e2e_tests"]
            
        except Exception as e:
            self.log(f"Error running e2e tests: {e}", "ERROR")
            self.test_results["e2e_tests"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            return self.test_results["e2e_tests"]
    
    def validate_architecture(self) -> Dict[str, Any]:
        """Validate the complete architecture is working."""
        self.log("Validating architecture components...")
        
        validation_results = {
            "fastmcp_services": False,
            "domain_agent": False,
            "technical_agent": False,
            "a2a_protocol": False,
            "ui_communication": False
        }
        
        try:
            # 1. Check FastMCP services (dynamic ports)
            validation_results["fastmcp_services"] = self._check_fastmcp_services()
            service_ports = self.discover_service_ports()
            self.log(f"FastMCP services discovery: {service_ports}")
            
            # 2. Check Domain Agent (should be on port 8000 or discovered port)
            domain_ports = [8000] + [port for port in range(8001, 8010)]
            domain_healthy = False
            domain_port = None
            
            for port in domain_ports:
                try:
                    response = httpx.get(f"http://localhost:{port}/health", timeout=5.0)
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data.get("agent") == "ClaimsAgent":
                            domain_healthy = True
                            domain_port = port
                            self.log(f"Found Domain Agent (ClaimsAgent) on port {port}")
                            break
                except:
                    continue
            
            validation_results["domain_agent"] = domain_healthy
            
            # 3. Check Technical Agent (should be on port 8002 or discovered port)
            technical_ports = [8002] + [port for port in range(8001, 8010)]
            technical_healthy = False
            technical_port = None
            
            for port in technical_ports:
                try:
                    response = httpx.get(f"http://localhost:{port}/health", timeout=5.0)
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data.get("agent") == "FastMCPDataAgent":
                            technical_healthy = True
                            technical_port = port
                            self.log(f"Found Technical Agent (FastMCPDataAgent) on port {port}")
                            break
                except:
                    continue
            
            validation_results["technical_agent"] = technical_healthy
            
            # 4. Test A2A protocol communication
            if domain_healthy and technical_healthy:
                validation_results["a2a_protocol"] = self._test_a2a_communication(technical_port)
            
            # 5. Test UI communication
            if domain_healthy:
                validation_results["ui_communication"] = self._test_ui_communication(domain_port)
            
            all_valid = all(validation_results.values())
            
            self.test_results["architecture_validation"] = {
                "status": "passed" if all_valid else "failed",
                "details": validation_results
            }
            
            if all_valid:
                self.log("✅ Architecture validation passed")
            else:
                self.log("❌ Architecture validation failed", "ERROR")
                for component, status in validation_results.items():
                    status_icon = "✅" if status else "❌"
                    self.log(f"  {status_icon} {component}")
            
            return self.test_results["architecture_validation"]
            
        except Exception as e:
            self.log(f"Error validating architecture: {e}", "ERROR")
            self.test_results["architecture_validation"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            return self.test_results["architecture_validation"]
    
    def _test_a2a_communication(self, technical_port: int = 8002) -> bool:
        """Test A2A protocol communication between agents."""
        try:
            # Test direct A2A call to technical agent
            task_data = {
                "taskId": "test_a2a_validation",
                "user": {
                    "action": "health_check",
                    "customer_id": "TEST-001"
                }
            }
            
            response = httpx.post(
                f"http://localhost:{technical_port}/process",
                json=task_data,
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return (result.get("taskId") == "test_a2a_validation" and
                        result.get("status") in ["completed", "failed"])
            
            return False
            
        except Exception as e:
            self.log(f"A2A communication test failed: {e}")
            return False
    
    def _test_ui_communication(self, domain_port: int = 8000) -> bool:
        """Test UI communication with domain agent."""
        try:
            ui_request = {
                "message": "Test message for architecture validation",
                "customer_id": "TEST-001"
            }
            
            response = httpx.post(
                f"http://localhost:{domain_port}/chat",
                json=ui_request,
                timeout=15.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return ("response" in result and
                        "thinking_steps" in result and
                        "orchestration_events" in result and
                        "api_calls" in result)
            
            return False
            
        except Exception as e:
            self.log(f"UI communication test failed: {e}")
            return False
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        self.log("Generating test report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "passed",
            "results": self.test_results
        }
        
        # Determine overall status
        for test_type, result in self.test_results.items():
            if result["status"] in ["failed", "error"]:
                report["overall_status"] = "failed"
                break
        
        # Write report
        with open(self.project_root / "test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        overall_icon = "✅" if report["overall_status"] == "passed" else "❌"
        print(f"Overall Status: {overall_icon} {report['overall_status'].upper()}")
        print()
        
        for test_type, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"{status_icon} {test_type.replace('_', ' ').title()}: {result['status']}")
        
        print()
        print("Architecture Components:")
        if "architecture_validation" in self.test_results:
            details = self.test_results["architecture_validation"].get("details", {})
            if isinstance(details, dict) and "fastmcp_services" in details:
                for component, status in details.items():
                    status_icon = "✅" if status else "❌"
                    print(f"  {status_icon} {component.replace('_', ' ').title()}")
        
        print("="*80)
        print(f"Detailed report saved to: {self.project_root / 'test_report.json'}")
        
        return report
    
    def run_all_tests(self):
        """Run the complete test suite."""
        self.log("Starting comprehensive test suite...")
        self.setup_signal_handlers()
        
        try:
            # 1. Start FastMCP services
            if not self.start_fastmcp_services():
                self.log("Failed to start FastMCP services, aborting tests", "ERROR")
                return False
            
            # 2. Validate architecture
            self.validate_architecture()
            
            # 3. Run unit tests
            self.run_unit_tests()
            
            # 4. Run integration tests
            self.run_integration_tests()
            
            # 5. Run end-to-end tests
            self.run_e2e_tests()
            
            # 6. Generate report
            report = self.generate_report()
            
            return report["overall_status"] == "passed"
            
        except KeyboardInterrupt:
            self.log("Tests interrupted by user")
            return False
        except Exception as e:
            self.log(f"Unexpected error during test execution: {e}", "ERROR")
            return False
        finally:
            self.cleanup_processes()


def main():
    """Main entry point."""
    runner = ComprehensiveTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 