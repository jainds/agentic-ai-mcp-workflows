#!/usr/bin/env python3
"""
Comprehensive Test Report Generator for Insurance AI PoC

This script runs the complete test suite and generates detailed reports
including unit tests, integration tests, coverage analysis, and performance metrics.
"""

import subprocess
import sys
import os
import time
import json
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import argparse

# Rich for beautiful output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich not available, using basic output")


@dataclass
class TestResult:
    name: str
    status: str  # passed, failed, skipped, error
    duration: float
    details: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class TestSuite:
    name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    coverage: Optional[float] = None
    results: List[TestResult] = None

    def __post_init__(self):
        if self.results is None:
            self.results = []

    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100


@dataclass
class TestReport:
    timestamp: str
    total_duration: float
    suites: List[TestSuite]
    overall_coverage: Optional[float] = None
    environment_info: Dict[str, str] = None
    service_health: Dict[str, bool] = None

    def __post_init__(self):
        if self.suites is None:
            self.suites = []
        if self.environment_info is None:
            self.environment_info = {}
        if self.service_health is None:
            self.service_health = {}

    @property
    def total_tests(self) -> int:
        return sum(suite.total_tests for suite in self.suites)

    @property
    def total_passed(self) -> int:
        return sum(suite.passed for suite in self.suites)

    @property
    def total_failed(self) -> int:
        return sum(suite.failed for suite in self.suites)

    @property
    def total_skipped(self) -> int:
        return sum(suite.skipped for suite in self.suites)

    @property
    def overall_success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.total_passed / self.total_tests) * 100


class TestRunner:
    """Comprehensive test runner and reporter"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.console = Console() if RICH_AVAILABLE else None
        self.report = TestReport(
            timestamp=datetime.now().isoformat(),
            total_duration=0.0,
            suites=[],
            environment_info=self._get_environment_info()
        )

    def _get_environment_info(self) -> Dict[str, str]:
        """Get environment information"""
        return {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": str(self.project_root),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _print(self, message: str, style: str = None):
        """Print with rich formatting if available"""
        if self.console and RICH_AVAILABLE:
            if style:
                self.console.print(message, style=style)
            else:
                self.console.print(message)
        else:
            print(message)

    def _run_command(self, command: List[str], cwd: Path = None) -> Dict[str, Any]:
        """Run a command and capture output"""
        if cwd is None:
            cwd = self.project_root

        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            duration = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out after 5 minutes",
                "duration": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": time.time() - start_time
            }

    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output for test statistics"""
        lines = output.split('\n')
        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 0.0
        }

        for line in lines:
            line = line.strip()
            
            # Look for the summary line
            if "passed" in line and ("failed" in line or "error" in line or "skipped" in line):
                # Parse lines like: "22 passed, 6 warnings in 0.15s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        stats["passed"] = int(parts[i-1])
                    elif part == "failed" and i > 0:
                        stats["failed"] = int(parts[i-1])
                    elif part == "skipped" and i > 0:
                        stats["skipped"] = int(parts[i-1])
                    elif part == "error" and i > 0:
                        stats["errors"] = int(parts[i-1])
                    elif "s" in part and "in" in parts[i-1]:
                        # Duration like "0.15s"
                        try:
                            stats["duration"] = float(part.replace('s', ''))
                        except ValueError:
                            pass

            # Alternative format: "=== X passed in Y seconds ==="
            elif "passed in" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        stats["passed"] = int(part)
                        break

        stats["total"] = stats["passed"] + stats["failed"] + stats["skipped"] + stats["errors"]
        return stats

    def run_unit_tests(self) -> TestSuite:
        """Run unit tests"""
        self._print("\n🧪 Running Unit Tests", "bold blue")
        
        command = [
            sys.executable, "-m", "pytest", 
            "tests/unit/", 
            "-v", "--tb=short",
            "--durations=10"
        ]

        result = self._run_command(command)
        stats = self._parse_pytest_output(result["stdout"])

        suite = TestSuite(
            name="Unit Tests",
            total_tests=stats["total"],
            passed=stats["passed"],
            failed=stats["failed"],
            skipped=stats["skipped"],
            errors=stats["errors"],
            duration=stats["duration"]
        )

        if result["success"]:
            self._print(f"✅ Unit tests completed: {stats['passed']}/{stats['total']} passed", "green")
        else:
            self._print(f"❌ Unit tests failed: {stats['failed']} failures, {stats['errors']} errors", "red")
            if result["stderr"]:
                self._print(f"Error details: {result['stderr'][:500]}...", "red")

        return suite

    def run_unit_tests_with_coverage(self) -> TestSuite:
        """Run unit tests with coverage analysis"""
        self._print("\n📊 Running Unit Tests with Coverage", "bold blue")
        
        command = [
            sys.executable, "-m", "pytest", 
            "tests/unit/", 
            "--cov=agents", "--cov=services",
            "--cov-report=term-missing",
            "--cov-report=json:coverage.json",
            "-v", "--tb=short"
        ]

        result = self._run_command(command)
        stats = self._parse_pytest_output(result["stdout"])

        # Try to parse coverage from output
        coverage_percentage = None
        for line in result["stdout"].split('\n'):
            if "TOTAL" in line and "%" in line:
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        try:
                            coverage_percentage = float(part.replace('%', ''))
                            break
                        except ValueError:
                            pass

        suite = TestSuite(
            name="Unit Tests (with Coverage)",
            total_tests=stats["total"],
            passed=stats["passed"],
            failed=stats["failed"],
            skipped=stats["skipped"],
            errors=stats["errors"],
            duration=stats["duration"],
            coverage=coverage_percentage
        )

        if result["success"]:
            coverage_msg = f" (Coverage: {coverage_percentage}%)" if coverage_percentage else ""
            self._print(f"✅ Unit tests with coverage completed: {stats['passed']}/{stats['total']} passed{coverage_msg}", "green")
        else:
            self._print(f"❌ Unit tests with coverage failed", "red")

        return suite

    async def check_service_health(self) -> Dict[str, bool]:
        """Check if services are running for integration tests"""
        services = {
            "customer-service": "http://localhost:30000/health",
            "policy-service": "http://localhost:30001/health", 
            "claims-service": "http://localhost:30002/health",
            "support-agent": "http://localhost:30005/health",
            "claims-agent": "http://localhost:30007/health"
        }

        health_status = {}
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for service_name, url in services.items():
                try:
                    response = await client.get(url)
                    health_status[service_name] = response.status_code == 200
                except Exception:
                    health_status[service_name] = False

        return health_status

    def run_integration_tests(self) -> TestSuite:
        """Run integration tests if services are available"""
        self._print("\n🔗 Checking Integration Test Prerequisites", "bold blue")
        
        # Check if services are running
        health_status = asyncio.run(self.check_service_health())
        services_available = any(health_status.values())

        if not services_available:
            self._print("⚠️  No services detected running, skipping integration tests", "yellow")
            self._print("   Run './scripts/deploy.sh' or 'python scripts/run_local.py start' first", "yellow")
            
            return TestSuite(
                name="Integration Tests",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=1,
                errors=0,
                duration=0.0
            )

        self._print("🚀 Services detected, running integration tests", "green")
        
        command = [
            sys.executable, "-m", "pytest", 
            "tests/integration/", 
            "-v", "--tb=short",
            "-x"  # Stop on first failure for integration tests
        ]

        result = self._run_command(command)
        stats = self._parse_pytest_output(result["stdout"])

        suite = TestSuite(
            name="Integration Tests",
            total_tests=stats["total"],
            passed=stats["passed"],
            failed=stats["failed"],
            skipped=stats["skipped"],
            errors=stats["errors"],
            duration=stats["duration"]
        )

        if result["success"]:
            self._print(f"✅ Integration tests completed: {stats['passed']}/{stats['total']} passed", "green")
        else:
            self._print(f"❌ Integration tests failed: {stats['failed']} failures", "red")

        return suite

    def run_performance_tests(self) -> TestSuite:
        """Run performance tests"""
        self._print("\n⚡ Running Performance Tests", "bold blue")
        
        command = [
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-m", "performance",
            "-v", "--tb=short"
        ]

        result = self._run_command(command)
        stats = self._parse_pytest_output(result["stdout"])

        suite = TestSuite(
            name="Performance Tests",
            total_tests=stats["total"],
            passed=stats["passed"],
            failed=stats["failed"],
            skipped=stats["skipped"],
            errors=stats["errors"],
            duration=stats["duration"]
        )

        if stats["total"] == 0:
            self._print("⚠️  No performance tests found", "yellow")
        elif result["success"]:
            self._print(f"✅ Performance tests completed: {stats['passed']}/{stats['total']} passed", "green")
        else:
            self._print(f"❌ Performance tests failed", "red")

        return suite

    def generate_summary_table(self):
        """Generate summary table"""
        if not RICH_AVAILABLE:
            self._print("\n=== TEST SUMMARY ===")
            for suite in self.report.suites:
                self._print(f"{suite.name}: {suite.passed}/{suite.total_tests} passed ({suite.success_rate:.1f}%)")
            self._print(f"Overall: {self.report.total_passed}/{self.report.total_tests} passed ({self.report.overall_success_rate:.1f}%)")
            return

        table = Table(title="Test Results Summary")
        table.add_column("Test Suite", style="cyan")
        table.add_column("Total", style="magenta")
        table.add_column("Passed", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Skipped", style="yellow")
        table.add_column("Success Rate", style="blue")
        table.add_column("Duration", style="white")
        table.add_column("Coverage", style="purple")

        for suite in self.report.suites:
            coverage_str = f"{suite.coverage:.1f}%" if suite.coverage else "N/A"
            table.add_row(
                suite.name,
                str(suite.total_tests),
                str(suite.passed),
                str(suite.failed),
                str(suite.skipped),
                f"{suite.success_rate:.1f}%",
                f"{suite.duration:.2f}s",
                coverage_str
            )

        # Add totals row
        total_coverage = self.report.overall_coverage or "N/A"
        if isinstance(total_coverage, float):
            total_coverage = f"{total_coverage:.1f}%"
        
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{self.report.total_tests}[/bold]",
            f"[bold green]{self.report.total_passed}[/bold green]",
            f"[bold red]{self.report.total_failed}[/bold red]",
            f"[bold yellow]{self.report.total_skipped}[/bold yellow]",
            f"[bold blue]{self.report.overall_success_rate:.1f}%[/bold blue]",
            f"[bold]{self.report.total_duration:.2f}s[/bold]",
            f"[bold purple]{total_coverage}[/bold purple]"
        )

        self.console.print("\n")
        self.console.print(table)

    def generate_detailed_report(self):
        """Generate detailed test report"""
        if not RICH_AVAILABLE:
            self._print("\n=== DETAILED REPORT ===")
            self._print(f"Test run completed at: {self.report.timestamp}")
            self._print(f"Total duration: {self.report.total_duration:.2f} seconds")
            return

        # Main summary panel
        summary_text = f"""
**Test Execution Summary**

- **Total Tests**: {self.report.total_tests}
- **Passed**: {self.report.total_passed} ✅
- **Failed**: {self.report.total_failed} ❌  
- **Skipped**: {self.report.total_skipped} ⏭️
- **Success Rate**: {self.report.overall_success_rate:.1f}%
- **Total Duration**: {self.report.total_duration:.2f} seconds
- **Timestamp**: {self.report.timestamp}
        """

        summary_panel = Panel(
            Markdown(summary_text),
            title="🎯 Insurance AI PoC Test Results",
            border_style="blue"
        )
        
        self.console.print(summary_panel)

        # Environment info
        if self.report.environment_info:
            env_text = "\n".join([f"- **{k}**: {v}" for k, v in self.report.environment_info.items()])
            env_panel = Panel(
                Markdown(env_text),
                title="🔧 Environment Information",
                border_style="cyan"
            )
            self.console.print(env_panel)

        # Service health status
        if self.report.service_health:
            health_items = []
            for service, is_healthy in self.report.service_health.items():
                status = "✅ Healthy" if is_healthy else "❌ Unavailable"
                health_items.append(f"- **{service}**: {status}")
            
            health_text = "\n".join(health_items)
            health_panel = Panel(
                Markdown(health_text),
                title="🏥 Service Health Status",
                border_style="green" if any(self.report.service_health.values()) else "red"
            )
            self.console.print(health_panel)

    def save_json_report(self, filename: str = "test_report.json"):
        """Save detailed report as JSON"""
        output_path = self.project_root / filename
        
        with open(output_path, 'w') as f:
            json.dump(asdict(self.report), f, indent=2)
        
        self._print(f"📄 Detailed JSON report saved to: {output_path}")

    def save_html_report(self, filename: str = "test_report.html"):
        """Save HTML report"""
        output_path = self.project_root / filename
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Insurance AI PoC Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .skipped {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Insurance AI PoC Test Report</h1>
        <p><strong>Generated:</strong> {self.report.timestamp}</p>
        <p><strong>Total Duration:</strong> {self.report.total_duration:.2f} seconds</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Tests</td><td>{self.report.total_tests}</td></tr>
            <tr><td>Passed</td><td class="passed">{self.report.total_passed}</td></tr>
            <tr><td>Failed</td><td class="failed">{self.report.total_failed}</td></tr>
            <tr><td>Skipped</td><td class="skipped">{self.report.total_skipped}</td></tr>
            <tr><td>Success Rate</td><td>{self.report.overall_success_rate:.1f}%</td></tr>
        </table>
    </div>
    
    <div class="suites">
        <h2>Test Suites</h2>
        {''.join([f'''
        <div class="suite">
            <h3>{suite.name}</h3>
            <p><strong>Tests:</strong> {suite.total_tests} | 
               <strong>Passed:</strong> <span class="passed">{suite.passed}</span> | 
               <strong>Failed:</strong> <span class="failed">{suite.failed}</span> | 
               <strong>Skipped:</strong> <span class="skipped">{suite.skipped}</span> | 
               <strong>Success Rate:</strong> {suite.success_rate:.1f}% | 
               <strong>Duration:</strong> {suite.duration:.2f}s
               {f' | <strong>Coverage:</strong> {suite.coverage:.1f}%' if suite.coverage else ''}
            </p>
        </div>
        ''' for suite in self.report.suites])}
    </div>
</body>
</html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        self._print(f"🌐 HTML report saved to: {output_path}")

    async def run_all_tests(self, include_coverage: bool = True, include_integration: bool = True, include_performance: bool = False):
        """Run all test suites and generate comprehensive report"""
        start_time = time.time()
        
        self._print("🚀 Starting Comprehensive Test Suite", "bold green")
        self._print("=" * 60)

        # Check service health for integration tests
        if include_integration:
            self.report.service_health = await self.check_service_health()

        # Run test suites
        if include_coverage:
            unit_suite = self.run_unit_tests_with_coverage()
            self.report.overall_coverage = unit_suite.coverage
        else:
            unit_suite = self.run_unit_tests()
        
        self.report.suites.append(unit_suite)

        if include_integration:
            integration_suite = self.run_integration_tests()
            self.report.suites.append(integration_suite)

        if include_performance:
            performance_suite = self.run_performance_tests()
            self.report.suites.append(performance_suite)

        # Calculate total duration
        self.report.total_duration = time.time() - start_time

        # Generate reports
        self._print("\n" + "=" * 60)
        self.generate_summary_table()
        self.generate_detailed_report()

        # Save reports
        self.save_json_report()
        self.save_html_report()

        # Final status
        if self.report.total_failed == 0:
            self._print("\n🎉 All tests passed! System is ready for deployment.", "bold green")
            return True
        else:
            self._print(f"\n⚠️  {self.report.total_failed} test(s) failed. Please review and fix issues.", "bold red")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run comprehensive test suite for Insurance AI PoC")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage analysis")
    parser.add_argument("--no-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--performance", action="store_true", help="Include performance tests")
    parser.add_argument("--output-dir", default=".", help="Output directory for reports")
    
    args = parser.parse_args()

    # Change to output directory
    if args.output_dir != ".":
        os.chdir(args.output_dir)

    runner = TestRunner()
    
    try:
        success = asyncio.run(runner.run_all_tests(
            include_coverage=not args.no_coverage,
            include_integration=not args.no_integration,
            include_performance=args.performance
        ))
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test run failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()