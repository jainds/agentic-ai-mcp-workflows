#!/usr/bin/env python3
"""
Master Test Runner for Insurance AI POC
Runs all test phases in sequence as requested by the user:
1. Policy Server Tests
2. Technical Agent + Policy Server Integration 
3. Domain/Orchestrator + Technical Agent + Policy Server
4. Complete System Integration (including UI)
"""

import sys
import os
import time
import subprocess
from typing import List, Dict, Any

# Add paths for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'insurance-adk'))

class TestOrchestrator:
    """Orchestrates the execution of all test phases"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    def run_phase(self, phase_num: int, phase_name: str, test_file: str) -> bool:
        """Run a single test phase"""
        print(f"\n{'='*100}")
        print(f"🚀 STARTING PHASE {phase_num}: {phase_name.upper()}")
        print(f"{'='*100}")
        
        phase_start = time.time()
        
        try:
            # Run the test file
            result = subprocess.run(
                [sys.executable, test_file],
                cwd=os.path.dirname(__file__),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout per phase
            )
            
            phase_end = time.time()
            duration = phase_end - phase_start
            
            success = result.returncode == 0
            
            # Store results
            self.results[f"phase_{phase_num}"] = {
                "name": phase_name,
                "success": success,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # Print results
            if success:
                print(f"✅ PHASE {phase_num} COMPLETED SUCCESSFULLY")
                print(f"⏱️  Duration: {duration:.1f} seconds")
            else:
                print(f"❌ PHASE {phase_num} FAILED")
                print(f"⏱️  Duration: {duration:.1f} seconds")
                print(f"📝 Error output:")
                print(result.stderr[-500:] if result.stderr else "No error output")
            
            # Always show stdout for test results
            if result.stdout:
                print("\n📋 Test Output:")
                print(result.stdout)
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ PHASE {phase_num} TIMEOUT (5 minutes)")
            self.results[f"phase_{phase_num}"] = {
                "name": phase_name,
                "success": False,
                "duration": 300,
                "error": "Timeout"
            }
            return False
            
        except Exception as e:
            print(f"💥 PHASE {phase_num} ERROR: {e}")
            self.results[f"phase_{phase_num}"] = {
                "name": phase_name,
                "success": False,
                "duration": 0,
                "error": str(e)
            }
            return False
    
    def cleanup_processes(self):
        """Clean up any running processes between tests"""
        print("\n🧹 Cleaning up processes...")
        
        cleanup_commands = [
            "pkill -f 'python.*main.py'",
            "pkill -f 'streamlit'",
            "pkill -f 'adk.*api_server'",
            "pkill -f 'pytest'"
        ]
        
        for cmd in cleanup_commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            except:
                pass
        
        # Wait for processes to terminate
        time.sleep(2)
        print("✅ Process cleanup complete")
    
    def run_all_phases(self) -> Dict[str, Any]:
        """Run all test phases in sequence"""
        
        print("🎯 INSURANCE AI POC - COMPREHENSIVE TEST SUITE")
        print("="*100)
        print("🔍 Running tests in the sequence requested:")
        print("   Phase 1: Policy Server Tests")
        print("   Phase 2: Technical Agent + Policy Server Integration")
        print("   Phase 3: Domain/Orchestrator + Technical Agent + Policy Server")
        print("   Phase 4: Complete System Integration (including UI)")
        print("="*100)
        
        # Test phases configuration
        phases = [
            (1, "Policy Server Tests", "test_1_policy_server.py"),
            (2, "Technical Agent Integration", "test_2_technical_agent_integration.py"),
            (3, "Full Agent Chain", "test_3_full_agent_chain.py"),
            (4, "Complete System", "test_4_complete_system.py")
        ]
        
        successful_phases = 0
        
        for phase_num, phase_name, test_file in phases:
            # Clean up before each phase
            if phase_num > 1:
                self.cleanup_processes()
                time.sleep(2)
            
            # Run the phase
            success = self.run_phase(phase_num, phase_name, test_file)
            if success:
                successful_phases += 1
            
            # Brief pause between phases
            if phase_num < len(phases):
                print(f"\n⏳ Brief pause before next phase...")
                time.sleep(3)
        
        # Final cleanup
        self.cleanup_processes()
        
        # Generate summary
        return self.generate_summary(successful_phases, len(phases))
    
    def generate_summary(self, successful_phases: int, total_phases: int) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        
        total_duration = time.time() - self.start_time
        
        print(f"\n{'='*100}")
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*100}")
        
        print(f"\n⏱️  EXECUTION TIME:")
        print(f"   Total Duration: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
        
        print(f"\n🎯 PHASE RESULTS:")
        for phase_key, phase_data in self.results.items():
            phase_num = phase_key.split('_')[1]
            success_icon = "✅" if phase_data['success'] else "❌"
            print(f"   Phase {phase_num}: {success_icon} {phase_data['name']} ({phase_data['duration']:.1f}s)")
        
        success_rate = (successful_phases / total_phases) * 100
        print(f"\n📈 OVERALL SUCCESS RATE: {successful_phases}/{total_phases} ({success_rate:.0f}%)")
        
        # Architecture assessment
        print(f"\n🏗️  ARCHITECTURE ASSESSMENT:")
        
        if successful_phases == 4:
            print("   ✅ Policy Server: Fully functional MCP implementation")
            print("   ✅ Technical Agent: ADK + MCP integration working")
            print("   ✅ Agent Chain: Multi-agent coordination operational")
            print("   ✅ Complete System: End-to-end functionality verified")
            status = "PRODUCTION READY"
            status_icon = "🎉"
        elif successful_phases == 3:
            print("   ✅ Policy Server: Fully functional")
            print("   ✅ Technical Agent: Working")
            print("   ✅ Agent Chain: Operational")
            print("   ⚠️  Complete System: Some issues detected")
            status = "MOSTLY READY - Minor issues to address"
            status_icon = "⚠️"
        elif successful_phases == 2:
            print("   ✅ Policy Server: Working")
            print("   ✅ Technical Agent: Basic integration working")
            print("   ❌ Agent Chain: Issues detected")
            print("   ❌ Complete System: Major issues")
            status = "PARTIAL FUNCTIONALITY - Significant work needed"
            status_icon = "🔧"
        elif successful_phases == 1:
            print("   ✅ Policy Server: Basic functionality")
            print("   ❌ Technical Agent: Integration issues")
            print("   ❌ Agent Chain: Not functional")
            print("   ❌ Complete System: Not functional")
            status = "FOUNDATIONAL ONLY - Major development needed"
            status_icon = "🚧"
        else:
            print("   ❌ Policy Server: Critical issues")
            print("   ❌ Technical Agent: Not functional")
            print("   ❌ Agent Chain: Not functional")
            print("   ❌ Complete System: Not functional")
            status = "CRITICAL ISSUES - System not operational"
            status_icon = "🚨"
        
        print(f"\n{status_icon} SYSTEM STATUS: {status}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if successful_phases == 4:
            print("   🎯 Ready for production deployment and user testing")
            print("   📈 Consider performance optimization and scaling")
            print("   🔒 Implement production security measures")
        elif successful_phases >= 2:
            print("   🔧 Focus on fixing failing integration tests")
            print("   📝 Review error logs for specific issues")
            print("   🔄 Re-run tests after fixes")
        else:
            print("   🚨 Address foundational issues first")
            print("   🏗️  Review architecture and configuration")
            print("   📞 Consider architectural consultation")
        
        # Next steps
        print(f"\n🎯 NEXT STEPS:")
        
        if successful_phases == 4:
            print("   1. Deploy to staging environment")
            print("   2. Conduct user acceptance testing")
            print("   3. Prepare production deployment")
        elif successful_phases >= 2:
            print("   1. Review failing test outputs above")
            print("   2. Fix identified issues")
            print("   3. Re-run specific failing tests")
            print("   4. Run complete test suite again")
        else:
            print("   1. Review system architecture")
            print("   2. Fix configuration issues")
            print("   3. Test individual components")
            print("   4. Re-run Phase 1 tests")
        
        print(f"\n{'='*100}")
        print(f"🏁 TESTING COMPLETE - {status}")
        print(f"{'='*100}")
        
        return {
            "successful_phases": successful_phases,
            "total_phases": total_phases,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "status": status,
            "results": self.results
        }

def main():
    """Main test execution function"""
    
    # Check if we're in the right directory
    if not os.path.exists("test_1_policy_server.py"):
        print("❌ Error: Test files not found. Please run from the tests directory.")
        sys.exit(1)
    
    # Create and run test orchestrator
    orchestrator = TestOrchestrator()
    
    try:
        summary = orchestrator.run_all_phases()
        
        # Exit with appropriate code
        if summary["successful_phases"] == summary["total_phases"]:
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        orchestrator.cleanup_processes()
        sys.exit(130)
        
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        orchestrator.cleanup_processes()
        sys.exit(1)

if __name__ == "__main__":
    main() 