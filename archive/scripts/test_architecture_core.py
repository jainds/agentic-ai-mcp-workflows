#!/usr/bin/env python3
"""
Core Architecture Test Script

This script tests the fundamental architecture components without requiring
all services to be running. It focuses on:

1. Unit testing the domain agent's LLM reasoning and orchestration
2. Unit testing the technical agent's A2A and MCP integration
3. Integration testing the key flows
4. Validating the architecture design principles

Architecture Focus:
- Streamlit UI interactions with domain agent
- Domain agent LLM reasoning and planning
- Domain agent to technical agent A2A communication
- Technical agent MCP tool integration
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any

class CoreArchitectureTestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {
            "domain_agent_unit_tests": {"status": "pending", "details": {}},
            "technical_agent_unit_tests": {"status": "pending", "details": {}},
            "a2a_integration_tests": {"status": "pending", "details": {}},
            "architecture_compliance": {"status": "pending", "details": {}}
        }

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_domain_agent_unit_tests(self) -> Dict[str, Any]:
        """Test domain agent's LLM reasoning and orchestration capabilities."""
        self.log("Testing Domain Agent unit capabilities...")
        
        try:
            # Run specific domain agent tests
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/unit/test_domain_agent.py",
                "-v",
                "--tb=short",
                "-k", "test_analyze or test_orchestrat or test_handle_task"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            success = result.returncode == 0
            details = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "focus": "LLM reasoning, intent analysis, orchestration planning"
            }
            
            self.test_results["domain_agent_unit_tests"] = {
                "status": "passed" if success else "failed",
                "details": details
            }
            
            if success:
                self.log("✅ Domain Agent unit tests passed")
            else:
                self.log("❌ Domain Agent unit tests failed", "ERROR")
                
            return self.test_results["domain_agent_unit_tests"]
            
        except Exception as e:
            self.log(f"Error running domain agent tests: {e}", "ERROR")
            self.test_results["domain_agent_unit_tests"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            return self.test_results["domain_agent_unit_tests"]

    def run_technical_agent_unit_tests(self) -> Dict[str, Any]:
        """Test technical agent's A2A and MCP integration capabilities."""
        self.log("Testing Technical Agent unit capabilities...")
        
        try:
            # Run specific technical agent tests
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/unit/test_technical_agent.py",
                "-v",
                "--tb=short",
                "-k", "test_a2a or test_mcp or test_protocol"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            success = result.returncode == 0
            details = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "focus": "A2A protocol compliance, MCP tool integration"
            }
            
            self.test_results["technical_agent_unit_tests"] = {
                "status": "passed" if success else "failed",
                "details": details
            }
            
            if success:
                self.log("✅ Technical Agent unit tests passed")
            else:
                self.log("❌ Technical Agent unit tests failed", "ERROR")
                
            return self.test_results["technical_agent_unit_tests"]
            
        except Exception as e:
            self.log(f"Error running technical agent tests: {e}", "ERROR")
            self.test_results["technical_agent_unit_tests"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            return self.test_results["technical_agent_unit_tests"]

    def run_a2a_integration_tests(self) -> Dict[str, Any]:
        """Test A2A integration between domain and technical agents."""
        self.log("Testing A2A protocol integration...")
        
        try:
            # Run A2A-specific integration tests
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "tests/integration/test_domain_technical_agent_integration.py",
                "-v",
                "--tb=short",
                "-k", "test_a2a or test_protocol"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            success = result.returncode == 0
            details = {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "focus": "Domain-to-Technical agent A2A communication"
            }
            
            self.test_results["a2a_integration_tests"] = {
                "status": "passed" if success else "failed",
                "details": details
            }
            
            if success:
                self.log("✅ A2A integration tests passed")
            else:
                self.log("❌ A2A integration tests failed", "ERROR")
                
            return self.test_results["a2a_integration_tests"]
            
        except Exception as e:
            self.log(f"Error running A2A integration tests: {e}", "ERROR")
            self.test_results["a2a_integration_tests"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            return self.test_results["a2a_integration_tests"]

    def validate_architecture_compliance(self) -> Dict[str, Any]:
        """Validate that the architecture follows the required design principles."""
        self.log("Validating architecture compliance...")
        
        compliance_checks = {
            "domain_agent_has_llm_reasoning": False,
            "domain_agent_orchestrates_technical": False,
            "technical_agent_has_a2a_protocol": False,
            "technical_agent_has_mcp_tools": False,
            "streamlit_ui_integration": False,
            "official_google_a2a_library": False
        }
        
        try:
            # Check 1: Domain agent has LLM reasoning
            domain_agent_file = self.project_root / "agents" / "domain" / "claims_agent.py"
            if domain_agent_file.exists():
                content = domain_agent_file.read_text()
                if "openai" in content.lower() and "analyze_user_intent" in content:
                    compliance_checks["domain_agent_has_llm_reasoning"] = True
                if "_call_technical_agent" in content and "orchestrat" in content.lower():
                    compliance_checks["domain_agent_orchestrates_technical"] = True
            
            # Check 2: Technical agent has A2A protocol
            technical_agent_file = self.project_root / "agents" / "technical" / "fastmcp_data_agent.py"
            if technical_agent_file.exists():
                content = technical_agent_file.read_text()
                if "A2AAgent" in content and "TaskRequest" in content:
                    compliance_checks["technical_agent_has_a2a_protocol"] = True
                if "mcp" in content.lower() and "tool" in content.lower():
                    compliance_checks["technical_agent_has_mcp_tools"] = True
            
            # Check 3: Official Google A2A library usage
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                content = requirements_file.read_text()
                if "a2a-sdk" in content:
                    compliance_checks["official_google_a2a_library"] = True
            
            # Check 4: Streamlit UI integration
            ui_files = list((self.project_root / "ui").glob("*.py"))
            if ui_files:
                ui_content = ""
                for ui_file in ui_files:
                    ui_content += ui_file.read_text()
                if "streamlit" in ui_content.lower() and "chat" in ui_content.lower():
                    compliance_checks["streamlit_ui_integration"] = True
            
            # Calculate compliance score
            total_checks = len(compliance_checks)
            passed_checks = sum(compliance_checks.values())
            compliance_score = passed_checks / total_checks
            
            all_compliant = compliance_score >= 0.8  # 80% threshold
            
            self.test_results["architecture_compliance"] = {
                "status": "passed" if all_compliant else "failed",
                "details": {
                    "compliance_score": compliance_score,
                    "checks": compliance_checks,
                    "summary": f"{passed_checks}/{total_checks} compliance checks passed"
                }
            }
            
            if all_compliant:
                self.log(f"✅ Architecture compliance validated ({compliance_score:.1%})")
            else:
                self.log(f"❌ Architecture compliance failed ({compliance_score:.1%})", "ERROR")
                for check, status in compliance_checks.items():
                    status_icon = "✅" if status else "❌"
                    self.log(f"  {status_icon} {check.replace('_', ' ').title()}")
            
            return self.test_results["architecture_compliance"]
            
        except Exception as e:
            self.log(f"Error validating architecture compliance: {e}", "ERROR")
            self.test_results["architecture_compliance"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
            return self.test_results["architecture_compliance"]

    def generate_core_report(self):
        """Generate a focused architecture test report."""
        self.log("Generating architecture test report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_focus": "Core Architecture Validation",
            "architecture_flow": "UI → Domain Agent (LLM) → A2A → Technical Agent (MCP) → Services",
            "overall_status": "passed",
            "results": self.test_results
        }
        
        # Determine overall status
        failed_tests = []
        for test_type, result in self.test_results.items():
            if result["status"] in ["failed", "error"]:
                failed_tests.append(test_type)
                report["overall_status"] = "failed"
        
        # Write report
        with open(self.project_root / "architecture_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("CORE ARCHITECTURE TEST REPORT")
        print("="*80)
        print("Architecture: Streamlit UI → Domain Agent (LLM) → A2A → Technical Agent (MCP)")
        print()
        
        overall_icon = "✅" if report["overall_status"] == "passed" else "❌"
        print(f"Overall Status: {overall_icon} {report['overall_status'].upper()}")
        
        if failed_tests:
            print(f"Failed components: {', '.join(failed_tests)}")
        
        print()
        
        for test_type, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "passed" else "❌"
            test_name = test_type.replace('_', ' ').title()
            print(f"{status_icon} {test_name}: {result['status']}")
        
        # Show architecture compliance details
        if "architecture_compliance" in self.test_results:
            details = self.test_results["architecture_compliance"].get("details", {})
            if "checks" in details:
                print("\nArchitecture Compliance Details:")
                for check, status in details["checks"].items():
                    status_icon = "✅" if status else "❌"
                    check_name = check.replace('_', ' ').title()
                    print(f"  {status_icon} {check_name}")
                
                score = details.get("compliance_score", 0)
                print(f"\nCompliance Score: {score:.1%}")
        
        print("="*80)
        print(f"Detailed report: {self.project_root / 'architecture_test_report.json'}")
        
        return report

    def run_core_tests(self):
        """Run the core architecture tests."""
        self.log("Starting core architecture validation...")
        self.log("Focus: Domain Agent LLM reasoning, A2A protocol, Technical Agent MCP integration")
        
        try:
            # 1. Test domain agent capabilities
            self.run_domain_agent_unit_tests()
            
            # 2. Test technical agent capabilities
            self.run_technical_agent_unit_tests()
            
            # 3. Test A2A integration
            self.run_a2a_integration_tests()
            
            # 4. Validate architecture compliance
            self.validate_architecture_compliance()
            
            # 5. Generate report
            report = self.generate_core_report()
            
            return report["overall_status"] == "passed"
            
        except Exception as e:
            self.log(f"Unexpected error during core testing: {e}", "ERROR")
            return False


def main():
    """Main entry point."""
    runner = CoreArchitectureTestRunner()
    success = runner.run_core_tests()
    
    if success:
        print("\n🎉 Core architecture validation completed successfully!")
        print("✅ Domain agent LLM reasoning capabilities verified")
        print("✅ Technical agent A2A and MCP integration verified")
        print("✅ Architecture design principles validated")
    else:
        print("\n⚠️  Core architecture validation found issues")
        print("Please review the detailed report for specific failures")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 