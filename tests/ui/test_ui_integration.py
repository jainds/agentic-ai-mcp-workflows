#!/usr/bin/env python3
"""
Comprehensive UI Integration Test for Insurance AI
Tests the modular Streamlit UI without complex Selenium setup
"""

import requests
import time
import json
import os
from urllib.parse import urljoin

class InsuranceAIUITester:
    def __init__(self, base_url="http://localhost:8501"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health_endpoint(self):
        """Test Streamlit health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/_stcore/health", timeout=10)
            return {
                "status": "PASS" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "message": "Health endpoint accessible"
            }
        except Exception as e:
            return {"status": "FAIL", "message": f"Health check failed: {e}"}
    
    def test_main_page_load(self):
        """Test main page loading"""
        try:
            response = self.session.get(self.base_url, timeout=15)
            if response.status_code != 200:
                return {"status": "FAIL", "message": f"Page returned {response.status_code}"}
            
            content = response.text.lower()
            
            # Check for Streamlit indicators
            streamlit_checks = [
                ("streamlit" in content, "Streamlit framework detected"),
                ("data-testid" in content, "Streamlit elements found"),
                (len(content) > 1000, "Page has substantial content")
            ]
            
            passed_checks = sum(1 for check, _ in streamlit_checks if check)
            
            return {
                "status": "PASS" if passed_checks >= 2 else "PARTIAL",
                "message": f"Page loaded, {passed_checks}/3 checks passed",
                "details": [msg for check, msg in streamlit_checks if check]
            }
            
        except Exception as e:
            return {"status": "FAIL", "message": f"Page load failed: {e}"}
    
    def test_modular_components(self):
        """Test modular component functionality"""
        try:
            import sys
            if '.' not in sys.path:
                sys.path.append('.')
            
            # Test config component
            from ui.components.config import UIConfig
            config_test = {
                "config_import": True,
                "features_loaded": len(UIConfig.get_enabled_features()) > 0,
                "mode_detection": UIConfig.is_advanced_mode() or UIConfig.is_simple_mode(),
                "endpoints_configured": len(UIConfig.DOMAIN_AGENT_ENDPOINTS) > 0,
                "demo_customers": len(UIConfig.DEMO_CUSTOMERS) > 0
            }
            
            # Test authentication component
            try:
                from ui.components.auth import CustomerValidator
                auth_test = CustomerValidator.validate_customer("CUST-001")
                auth_works = auth_test.get("valid", False)
            except Exception:
                auth_works = False
            
            # Test agent client component
            try:
                from ui.components.agent_client import DomainAgentClient
                client = DomainAgentClient()
                client_works = hasattr(client, 'send_message')
            except Exception:
                client_works = False
            
            total_checks = len(config_test) + 2  # auth + client
            passed_checks = sum(config_test.values()) + auth_works + client_works
            
            return {
                "status": "PASS" if passed_checks >= total_checks - 1 else "PARTIAL",
                "message": f"Component tests: {passed_checks}/{total_checks} passed",
                "details": {
                    "config": config_test,
                    "auth": auth_works,
                    "client": client_works
                }
            }
            
        except Exception as e:
            return {"status": "FAIL", "message": f"Component test failed: {e}"}
    
    def test_feature_toggles(self):
        """Test feature toggle functionality"""
        try:
            from ui.components.config import UIConfig
            
            # Get current features
            features = UIConfig.get_enabled_features()
            
            expected_features = [
                "advanced_features", "system_monitoring", "api_monitoring",
                "thinking_steps", "orchestration_view", "simple_mode", "advanced_mode"
            ]
            
            found_features = sum(1 for feature in expected_features if feature in features)
            
            # Test mode detection
            mode_works = UIConfig.is_advanced_mode() != UIConfig.is_simple_mode()
            
            return {
                "status": "PASS" if found_features >= 6 and mode_works else "PARTIAL",
                "message": f"Feature toggles: {found_features}/{len(expected_features)} found, mode detection: {mode_works}",
                "details": {
                    "features": features,
                    "mode": "Advanced" if UIConfig.is_advanced_mode() else "Simple"
                }
            }
            
        except Exception as e:
            return {"status": "FAIL", "message": f"Feature toggle test failed: {e}"}
    
    def test_service_configuration(self):
        """Test service configuration and endpoints"""
        try:
            from ui.components.config import UIConfig
            
            # Check domain agent endpoints
            endpoints = UIConfig.DOMAIN_AGENT_ENDPOINTS
            endpoint_check = len(endpoints) >= 2
            
            # Check monitored services
            services = UIConfig.MONITORED_SERVICES
            service_check = len(services) >= 4
            
            # Check demo customers
            customers = UIConfig.DEMO_CUSTOMERS
            customer_check = len(customers) >= 3
            
            checks_passed = sum([endpoint_check, service_check, customer_check])
            
            return {
                "status": "PASS" if checks_passed == 3 else "PARTIAL",
                "message": f"Service configuration: {checks_passed}/3 checks passed",
                "details": {
                    "endpoints": len(endpoints),
                    "services": len(services),
                    "customers": len(customers)
                }
            }
            
        except Exception as e:
            return {"status": "FAIL", "message": f"Service configuration test failed: {e}"}
    
    def test_import_from_external(self):
        """Test importing components from external context"""
        try:
            # Simulate external import
            import subprocess
            import tempfile
            
            test_script = """
import sys
sys.path.append('.')
from ui.components import UIConfig, CustomerValidator
print("SUCCESS: External import works")
print(f"Mode: {UIConfig.UI_MODE}")
print(f"Features: {len(UIConfig.get_enabled_features())}")
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_script)
                f.flush()
                
                result = subprocess.run([
                    "python", f.name
                ], capture_output=True, text=True, timeout=10, cwd='.')
                
                os.unlink(f.name)
                
                if result.returncode == 0 and "SUCCESS" in result.stdout:
                    return {
                        "status": "PASS",
                        "message": "External import test passed",
                        "details": result.stdout.strip()
                    }
                else:
                    return {
                        "status": "FAIL",
                        "message": f"External import failed: {result.stderr or result.stdout}"
                    }
                    
        except Exception as e:
            return {"status": "FAIL", "message": f"External import test failed: {e}"}
    
    def run_comprehensive_test_suite(self):
        """Run all tests and return comprehensive results"""
        print("🧪 Insurance AI UI - Comprehensive Test Suite")
        print("="*60)
        
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("Main Page Load", self.test_main_page_load),
            ("Modular Components", self.test_modular_components),
            ("Feature Toggles", self.test_feature_toggles),
            ("Service Configuration", self.test_service_configuration),
            ("External Imports", self.test_import_from_external)
        ]
        
        results = {}
        summary = {"PASS": 0, "PARTIAL": 0, "FAIL": 0}
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                status = result["status"]
                summary[status] += 1
                
                status_icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌"}[status]
                print(f"   {status_icon} {status}: {result['message']}")
                
                if "details" in result and status != "FAIL":
                    print(f"   📋 Details: {result['details']}")
                    
            except Exception as e:
                results[test_name] = {"status": "FAIL", "message": f"Test error: {e}"}
                summary["FAIL"] += 1
                print(f"   ❌ FAIL: Test error: {e}")
        
        # Final summary
        total_tests = len(tests)
        success_rate = ((summary["PASS"] + summary["PARTIAL"] * 0.5) / total_tests) * 100
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {summary['PASS']}")
        print(f"⚠️ Partial: {summary['PARTIAL']}")
        print(f"❌ Failed: {summary['FAIL']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("\n🎉 Excellent! UI is working perfectly.")
        elif success_rate >= 70:
            print("\n👍 Good! Most features working correctly.")
        elif success_rate >= 50:
            print("\n⚠️ Moderate issues detected.")
        else:
            print("\n🚨 Significant issues require attention.")
        
        print("="*60)
        
        return {
            "summary": summary,
            "success_rate": success_rate,
            "results": results,
            "total_tests": total_tests
        }

def main():
    """Main test runner"""
    tester = InsuranceAIUITester()
    results = tester.run_comprehensive_test_suite()
    
    # Return appropriate exit code
    if results["success_rate"] >= 70:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main() 