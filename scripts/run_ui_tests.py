#!/usr/bin/env python3
"""
UI Test Runner for Insurance AI PoC
Handles setup, execution, and reporting of comprehensive UI tests
"""

import os
import sys
import time
import json
import subprocess
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UITestRunner:
    """Manages UI test execution with proper setup and teardown"""
    
    def __init__(self):
        self.project_root = project_root
        self.streamlit_process = None
        self.ui_url = "http://localhost:8501"
        self.results_dir = self.project_root / "test_results"
        
    def setup_test_environment(self):
        """Setup the test environment"""
        logger.info("🔧 Setting up test environment...")
        
        # Create results directory
        self.results_dir.mkdir(exist_ok=True)
        
        # Check if Streamlit is already running
        if self.check_streamlit_running():
            logger.info("✅ Streamlit already running")
            return True
        
        # Start Streamlit app
        return self.start_streamlit_app()
    
    def check_streamlit_running(self):
        """Check if Streamlit is already running"""
        try:
            import requests
            response = requests.get(self.ui_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def start_streamlit_app(self):
        """Start the Streamlit application"""
        try:
            logger.info("🚀 Starting Streamlit application...")
            
            # Change to UI directory
            ui_dir = self.project_root / "ui"
            
            # Start Streamlit
            cmd = [
                sys.executable, "-m", "streamlit", "run", 
                "streamlit_app.py", 
                "--server.port", "8501",
                "--server.address", "0.0.0.0",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ]
            
            self.streamlit_process = subprocess.Popen(
                cmd,
                cwd=ui_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for Streamlit to start
            max_attempts = 30
            for attempt in range(max_attempts):
                if self.check_streamlit_running():
                    logger.info("✅ Streamlit started successfully")
                    return True
                time.sleep(2)
                logger.info(f"⏳ Waiting for Streamlit to start... ({attempt + 1}/{max_attempts})")
            
            logger.error("❌ Failed to start Streamlit within timeout")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error starting Streamlit: {e}")
            return False
    
    def run_selenium_tests(self):
        """Run the comprehensive Selenium tests"""
        try:
            logger.info("🧪 Running Selenium UI tests...")
            
            # Import and run the test suite
            from tests.ui.test_selenium_ui import StreamlitUITester
            
            tester = StreamlitUITester(self.ui_url)
            results = tester.run_comprehensive_test_suite()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.results_dir / f"ui_test_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"💾 Test results saved to: {results_file}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error running Selenium tests: {e}")
            return {
                "status": "ERROR",
                "message": str(e),
                "total_tests": 0,
                "passed": 0,
                "failed": 1,
                "success_rate": 0.0,
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup_test_environment(self):
        """Clean up the test environment"""
        logger.info("🧹 Cleaning up test environment...")
        
        if self.streamlit_process:
            try:
                self.streamlit_process.terminate()
                self.streamlit_process.wait(timeout=10)
                logger.info("✅ Streamlit process terminated")
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()
                logger.warning("⚠️ Streamlit process killed (timeout)")
            except Exception as e:
                logger.error(f"❌ Error stopping Streamlit: {e}")
    
    def print_test_summary(self, results):
        """Print a comprehensive test summary"""
        print("\n" + "="*80)
        print("🧪 INSURANCE AI POC - UI TEST RESULTS")
        print("="*80)
        
        # Overall statistics
        print(f"📊 Test Summary:")
        print(f"   🕐 Timestamp: {results.get('timestamp', 'Unknown')}")
        print(f"   🔢 Total Tests: {results.get('total_tests', 0)}")
        print(f"   ✅ Passed: {results.get('passed', 0)}")
        print(f"   ⚠️ Partial: {results.get('partial', 0)}")
        print(f"   ❌ Failed: {results.get('failed', 0)}")
        print(f"   📈 Success Rate: {results.get('success_rate', 0)}%")
        
        # Feature breakdown
        if "test_results" in results:
            print(f"\n📋 Feature Test Results:")
            
            feature_mapping = {
                "page_load": "🌐 Page Load",
                "authentication": "🔐 Authentication Flow",
                "invalid_auth": "❌ Invalid Authentication",
                "chat_interface": "💬 Chat Interface",
                "agent_orchestration": "🤝 Agent Orchestration",
                "thinking_steps": "🧠 Thinking Steps Display",
                "system_health": "⚕️ System Health Monitor",
                "api_monitor": "📊 API Monitor",
                "tab_navigation": "🔄 Tab Navigation",
                "logout": "🚪 Logout Functionality"
            }
            
            for test_name, result in results["test_results"].items():
                feature_name = feature_mapping.get(test_name, test_name.replace('_', ' ').title())
                status_icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌", "ERROR": "💥"}[result.get('status', 'ERROR')]
                print(f"   {status_icon} {feature_name}: {result.get('message', 'No message')}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if results.get('success_rate', 0) >= 90:
            print("   🎉 Excellent! All core functionality is working properly.")
        elif results.get('success_rate', 0) >= 70:
            print("   👍 Good! Most features working, address failing tests.")
        elif results.get('success_rate', 0) >= 50:
            print("   ⚠️ Moderate issues detected. Review and fix failing components.")
        else:
            print("   🚨 Significant issues detected. Immediate attention required.")
        
        print("="*80)
    
    def run_comprehensive_tests(self, skip_setup=False):
        """Run the complete test suite"""
        try:
            # Setup environment
            if not skip_setup:
                if not self.setup_test_environment():
                    return {"status": "SETUP_FAILED", "message": "Failed to setup test environment"}
            
            # Run tests
            results = self.run_selenium_tests()
            
            # Print summary
            self.print_test_summary(results)
            
            return results
            
        finally:
            # Always cleanup
            if not skip_setup:
                self.cleanup_test_environment()


def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="Insurance AI PoC UI Test Runner")
    parser.add_argument("--skip-setup", action="store_true", 
                       help="Skip Streamlit setup (assume it's already running)")
    parser.add_argument("--url", default="http://localhost:8501",
                       help="Streamlit URL to test against")
    parser.add_argument("--output", help="Output file for test results")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = UITestRunner()
    if args.url != "http://localhost:8501":
        runner.ui_url = args.url
    
    # Run tests
    results = runner.run_comprehensive_tests(skip_setup=args.skip_setup)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results also saved to: {args.output}")
    
    # Exit with appropriate code
    if results.get('success_rate', 0) >= 90:
        sys.exit(0)  # Success
    elif results.get('success_rate', 0) >= 50:
        sys.exit(1)  # Partial success
    else:
        sys.exit(2)  # Failure


if __name__ == "__main__":
    main() 