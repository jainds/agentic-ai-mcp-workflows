"""
Comprehensive Selenium UI Tests for Insurance AI PoC Streamlit App
Tests all features: Authentication, Chat, Thinking Steps, System Health, API Monitor
"""

import pytest
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamlitUITester:
    """Comprehensive Selenium tester for Streamlit UI"""
    
    def __init__(self, base_url="http://localhost:8501"):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        self.test_results = {}
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("✅ Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize WebDriver: {e}")
            return False
    
    def teardown_driver(self):
        """Clean up WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("🧹 WebDriver cleaned up")
    
    def wait_for_streamlit_load(self):
        """Wait for Streamlit app to fully load"""
        try:
            # Wait for Streamlit's main container
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "main")))
            
            # Wait for any loading spinners to disappear
            time.sleep(2)
            
            # Check if the app title is loaded
            title_element = self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            if "Insurance AI PoC" in title_element.text:
                logger.info("✅ Streamlit app loaded successfully")
                return True
            else:
                logger.error("❌ App title not found")
                return False
                
        except TimeoutException:
            logger.error("❌ Timeout waiting for Streamlit to load")
            return False
    
    def test_page_load(self):
        """Test if the main page loads correctly"""
        try:
            self.driver.get(self.base_url)
            
            if self.wait_for_streamlit_load():
                # Check for key elements
                title = self.driver.find_element(By.TAG_NAME, "h1")
                assert "Insurance AI PoC" in title.text
                
                # Check for authentication section
                auth_section = self.driver.find_element(By.XPATH, "//h3[contains(text(), 'Customer Authentication')]")
                assert auth_section is not None
                
                logger.info("✅ Page load test passed")
                return {"status": "PASS", "message": "Page loaded successfully"}
            else:
                return {"status": "FAIL", "message": "Page failed to load"}
                
        except Exception as e:
            logger.error(f"❌ Page load test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_authentication_flow(self):
        """Test customer authentication functionality"""
        try:
            # Find customer ID input
            customer_input = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Enter your Customer ID']"))
            )
            
            # Test with valid customer ID
            customer_input.clear()
            customer_input.send_keys("CUST-001")
            
            # Click authenticate button
            auth_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Authenticate')]")
            auth_button.click()
            
            # Wait for authentication to complete
            time.sleep(3)
            
            # Check for success message
            try:
                success_element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Welcome, John Smith')]"))
                )
                logger.info("✅ Authentication successful")
                
                # Check if tabs are now visible
                tabs = self.driver.find_elements(By.XPATH, "//button[@role='tab']")
                if len(tabs) >= 4:  # Should have 4 tabs: Chat, Thinking Steps, System Health, API Monitor
                    logger.info("✅ All tabs visible after authentication")
                    return {"status": "PASS", "message": "Authentication flow working correctly"}
                else:
                    return {"status": "FAIL", "message": f"Expected 4 tabs, found {len(tabs)}"}
                    
            except TimeoutException:
                return {"status": "FAIL", "message": "Authentication success message not found"}
                
        except Exception as e:
            logger.error(f"❌ Authentication test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_invalid_authentication(self):
        """Test authentication with invalid credentials"""
        try:
            # First, logout if authenticated
            try:
                logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
                logout_button.click()
                time.sleep(2)
            except NoSuchElementException:
                pass  # Not authenticated, continue
            
            # Find customer ID input
            customer_input = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Enter your Customer ID']"))
            )
            
            # Test with invalid customer ID
            customer_input.clear()
            customer_input.send_keys("INVALID-ID")
            
            # Click authenticate button
            auth_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Authenticate')]")
            auth_button.click()
            
            # Wait for error message
            time.sleep(2)
            
            # Check for error message
            try:
                error_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Authentication failed')]")
                logger.info("✅ Invalid authentication properly rejected")
                return {"status": "PASS", "message": "Invalid authentication properly handled"}
            except NoSuchElementException:
                return {"status": "FAIL", "message": "Error message not displayed for invalid authentication"}
                
        except Exception as e:
            logger.error(f"❌ Invalid authentication test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_chat_interface(self):
        """Test chat interface functionality"""
        try:
            # First ensure we're authenticated
            if not self.ensure_authenticated():
                return {"status": "FAIL", "message": "Could not authenticate for chat test"}
            
            # Click on Chat Interface tab
            chat_tab = self.driver.find_element(By.XPATH, "//button[@role='tab'][contains(text(), 'Chat Interface')]")
            chat_tab.click()
            time.sleep(2)
            
            # Find message input area
            message_input = self.wait.until(
                EC.element_to_be_clickable((By.TAG_NAME, "textarea"))
            )
            
            # Send a test message
            test_message = "I need help with my policy coverage"
            message_input.clear()
            message_input.send_keys(test_message)
            
            # Click send button
            send_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Send')]")
            send_button.click()
            
            # Wait for processing to complete (should show spinner)
            time.sleep(5)
            
            # Check for conversation history
            try:
                user_message = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{test_message}')]"))
                )
                
                # Check for agent response
                agent_response = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Domain Agent')]"))
                )
                
                logger.info("✅ Chat interface working correctly")
                return {"status": "PASS", "message": "Chat interface functional"}
                
            except TimeoutException:
                return {"status": "FAIL", "message": "Chat response not received"}
                
        except Exception as e:
            logger.error(f"❌ Chat interface test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_agent_orchestration_display(self):
        """Test agent orchestration functionality"""
        try:
            # Ensure we're authenticated and have sent a message
            if not self.ensure_authenticated():
                return {"status": "FAIL", "message": "Could not authenticate for agent orchestration test"}
            
            # Click on Agent Orchestration tab
            orchestration_tab = self.driver.find_element(By.XPATH, "//button[@role='tab'][contains(text(), 'Agent Orchestration')]")
            orchestration_tab.click()
            time.sleep(2)
            
            # Check if orchestration interface is displayed
            try:
                # Look for orchestration header
                orchestration_header = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Agent Orchestration')]"))
                )
                
                # Check for domain and technical agent sections
                try:
                    domain_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Domain Agent Thought Process')]")
                    technical_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Technical Agent Work')]")
                    
                    # Check for orchestration summary
                    orchestration_summary = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Orchestration Summary')]")
                    
                    logger.info("✅ Agent orchestration interface displaying all components")
                    return {"status": "PASS", "message": "Agent orchestration display fully functional"}
                    
                except NoSuchElementException:
                    return {"status": "PARTIAL", "message": "Orchestration header found but sections missing"}
                    
            except TimeoutException:
                return {"status": "FAIL", "message": "Agent orchestration section not found"}
                
        except Exception as e:
            logger.error(f"❌ Agent orchestration test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_thinking_steps_display(self):
        """Test thinking steps and orchestration display"""
        try:
            # Ensure we're authenticated and have sent a message
            if not self.ensure_authenticated():
                return {"status": "FAIL", "message": "Could not authenticate for thinking steps test"}
            
            # Click on Thinking Steps tab
            thinking_tab = self.driver.find_element(By.XPATH, "//button[@role='tab'][contains(text(), 'Thinking Steps')]")
            thinking_tab.click()
            time.sleep(2)
            
            # Check if thinking steps are displayed
            try:
                # Look for thinking step elements
                steps_header = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Recent Processing Steps')]"))
                )
                
                # Check for expandable step elements
                step_expanders = self.driver.find_elements(By.XPATH, "//summary[contains(@class, 'streamlit-expander')]")
                
                if len(step_expanders) > 0:
                    # Click on first expander to test functionality
                    step_expanders[0].click()
                    time.sleep(1)
                    
                    logger.info(f"✅ Found {len(step_expanders)} thinking steps")
                    return {"status": "PASS", "message": f"Thinking steps display working - {len(step_expanders)} steps found"}
                else:
                    return {"status": "PARTIAL", "message": "Thinking steps header found but no steps displayed"}
                    
            except TimeoutException:
                return {"status": "FAIL", "message": "Thinking steps section not found"}
                
        except Exception as e:
            logger.error(f"❌ Thinking steps test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_system_health_monitor(self):
        """Test system health monitoring functionality"""
        try:
            # Ensure we're authenticated
            if not self.ensure_authenticated():
                return {"status": "FAIL", "message": "Could not authenticate for system health test"}
            
            # Click on System Health tab
            health_tab = self.driver.find_element(By.XPATH, "//button[@role='tab'][contains(text(), 'System Health')]")
            health_tab.click()
            time.sleep(2)
            
            # Check for system health elements
            try:
                # Check for UI Service status
                ui_service = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'UI Service')]"))
                )
                
                # Check for FastMCP Agent status
                fastmcp_service = self.driver.find_element(By.XPATH, "//*[contains(text(), 'FastMCP Agent')]")
                
                # Check for Kubernetes status
                k8s_service = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Kubernetes')]")
                
                # Check for service details table
                service_table = self.driver.find_element(By.XPATH, "//table")
                
                logger.info("✅ System health monitor displaying all components")
                return {"status": "PASS", "message": "System health monitor fully functional"}
                
            except NoSuchElementException as e:
                return {"status": "FAIL", "message": f"Missing system health component: {e}"}
                
        except Exception as e:
            logger.error(f"❌ System health test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_api_monitor_display(self):
        """Test API monitoring functionality"""
        try:
            # Ensure we're authenticated
            if not self.ensure_authenticated():
                return {"status": "FAIL", "message": "Could not authenticate for API monitor test"}
            
            # Click on API Monitor tab
            api_tab = self.driver.find_element(By.XPATH, "//button[@role='tab'][contains(text(), 'API Monitor')]")
            api_tab.click()
            time.sleep(2)
            
            # Check for API monitor elements
            try:
                # Check for API call statistics
                total_calls_metric = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Total API Calls')]"))
                )
                
                success_rate_metric = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Success Rate')]")
                response_time_metric = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Avg Response Time')]")
                recent_calls_metric = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Calls (Last 1min)')]")
                
                # Check for recent API calls section
                try:
                    recent_calls_header = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Recent API Calls')]")
                    
                    # Look for API call expanders
                    api_call_expanders = self.driver.find_elements(By.XPATH, "//summary[contains(text(), 'Service')]")
                    
                    if len(api_call_expanders) > 0:
                        # Test expanding an API call
                        api_call_expanders[0].click()
                        time.sleep(1)
                        
                        logger.info(f"✅ API monitor displaying {len(api_call_expanders)} API calls")
                        return {"status": "PASS", "message": f"API monitor fully functional - {len(api_call_expanders)} calls tracked"}
                    else:
                        return {"status": "PARTIAL", "message": "API monitor header found but no API calls displayed"}
                        
                except NoSuchElementException:
                    return {"status": "PARTIAL", "message": "API metrics found but call details missing"}
                    
            except TimeoutException:
                return {"status": "FAIL", "message": "API monitor metrics not found"}
                
        except Exception as e:
            logger.error(f"❌ API monitor test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_tab_navigation(self):
        """Test navigation between all tabs"""
        try:
            # Ensure we're authenticated
            if not self.ensure_authenticated():
                return {"status": "FAIL", "message": "Could not authenticate for tab navigation test"}
            
            # Get all tabs
            tabs = self.driver.find_elements(By.XPATH, "//button[@role='tab']")
            
            if len(tabs) < 5:
                return {"status": "FAIL", "message": f"Expected 5 tabs, found {len(tabs)}"}
            
            # Test clicking each tab
            tab_names = ["Chat Interface", "Agent Orchestration", "Thinking Steps", "System Health", "API Monitor"]
            successful_navigations = 0
            
            for i, tab_name in enumerate(tab_names):
                try:
                    tab = self.driver.find_element(By.XPATH, f"//button[@role='tab'][contains(text(), '{tab_name}')]")
                    tab.click()
                    time.sleep(1)
                    
                    # Verify the tab is active/selected
                    if "selected" in tab.get_attribute("class") or "active" in tab.get_attribute("class"):
                        successful_navigations += 1
                        logger.info(f"✅ Successfully navigated to {tab_name}")
                    else:
                        logger.warning(f"⚠️ Navigation to {tab_name} may not be working")
                        
                except NoSuchElementException:
                    logger.error(f"❌ Tab {tab_name} not found")
            
            if successful_navigations >= 4:  # Allow for some tolerance
                return {"status": "PASS", "message": f"Tab navigation working - {successful_navigations}/5 tabs functional"}
            else:
                return {"status": "FAIL", "message": f"Tab navigation issues - only {successful_navigations}/5 tabs working"}
                
        except Exception as e:
            logger.error(f"❌ Tab navigation test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def test_logout_functionality(self):
        """Test logout functionality"""
        try:
            # Ensure we're authenticated
            if not self.ensure_authenticated():
                return {"status": "FAIL", "message": "Could not authenticate for logout test"}
            
            # Find and click logout button
            logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
            logout_button.click()
            time.sleep(2)
            
            # Check that we're back to unauthenticated state
            try:
                # Should see authentication input again
                customer_input = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Enter your Customer ID']"))
                )
                
                # Tabs should be hidden
                tabs = self.driver.find_elements(By.XPATH, "//button[@role='tab']")
                
                if len(tabs) == 0:
                    logger.info("✅ Logout successful - returned to unauthenticated state")
                    return {"status": "PASS", "message": "Logout functionality working correctly"}
                else:
                    return {"status": "FAIL", "message": "Tabs still visible after logout"}
                    
            except TimeoutException:
                return {"status": "FAIL", "message": "Authentication input not found after logout"}
                
        except Exception as e:
            logger.error(f"❌ Logout test failed: {e}")
            return {"status": "FAIL", "message": str(e)}
    
    def ensure_authenticated(self):
        """Ensure user is authenticated, authenticate if not"""
        try:
            # Check if already authenticated
            try:
                logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
                return True  # Already authenticated
            except NoSuchElementException:
                pass  # Not authenticated, need to authenticate
            
            # Authenticate
            customer_input = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Enter your Customer ID']"))
            )
            customer_input.clear()
            customer_input.send_keys("CUST-001")
            
            auth_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Authenticate')]")
            auth_button.click()
            time.sleep(3)
            
            # Check for success
            success_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Welcome, John Smith')]"))
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to ensure authentication: {e}")
            return False
    
    def run_comprehensive_test_suite(self):
        """Run all UI tests and generate comprehensive report"""
        logger.info("🚀 Starting comprehensive UI test suite")
        
        if not self.setup_driver():
            return {"status": "FAIL", "message": "Could not initialize WebDriver"}
        
        test_results = {}
        
        try:
            # Test 1: Page Load
            logger.info("📋 Testing page load...")
            test_results["page_load"] = self.test_page_load()
            
            # Test 2: Valid Authentication
            logger.info("🔐 Testing authentication flow...")
            test_results["authentication"] = self.test_authentication_flow()
            
            # Test 3: Invalid Authentication
            logger.info("❌ Testing invalid authentication...")
            test_results["invalid_auth"] = self.test_invalid_authentication()
            
            # Test 4: Chat Interface
            logger.info("💬 Testing chat interface...")
            test_results["chat_interface"] = self.test_chat_interface()
            
            # Test 5: Agent Orchestration
            logger.info("🧠 Testing agent orchestration display...")
            test_results["agent_orchestration"] = self.test_agent_orchestration_display()
            
            # Test 6: Thinking Steps
            logger.info("🧠 Testing thinking steps display...")
            test_results["thinking_steps"] = self.test_thinking_steps_display()
            
            # Test 7: System Health
            logger.info("⚕️ Testing system health monitor...")
            test_results["system_health"] = self.test_system_health_monitor()
            
            # Test 8: API Monitor
            logger.info("📊 Testing API monitor...")
            test_results["api_monitor"] = self.test_api_monitor_display()
            
            # Test 9: Tab Navigation
            logger.info("🔄 Testing tab navigation...")
            test_results["tab_navigation"] = self.test_tab_navigation()
            
            # Test 10: Logout
            logger.info("🚪 Testing logout functionality...")
            test_results["logout"] = self.test_logout_functionality()
            
            # Generate summary
            passed = len([t for t in test_results.values() if t["status"] == "PASS"])
            partial = len([t for t in test_results.values() if t["status"] == "PARTIAL"])
            failed = len([t for t in test_results.values() if t["status"] == "FAIL"])
            total = len(test_results)
            
            summary = {
                "total_tests": total,
                "passed": passed,
                "partial": partial,
                "failed": failed,
                "success_rate": round((passed / total) * 100, 1),
                "timestamp": datetime.now().isoformat(),
                "test_results": test_results
            }
            
            logger.info(f"🎯 Test Suite Complete: {passed}/{total} passed ({summary['success_rate']}%)")
            
            return summary
            
        finally:
            self.teardown_driver()


def main():
    """Run the comprehensive UI test suite"""
    tester = StreamlitUITester()
    results = tester.run_comprehensive_test_suite()
    
    # Print detailed results
    print("\n" + "="*60)
    print("🧪 COMPREHENSIVE UI TEST RESULTS")
    print("="*60)
    
    print(f"📊 Overall Results:")
    print(f"   Total Tests: {results['total_tests']}")
    print(f"   ✅ Passed: {results['passed']}")
    print(f"   ⚠️ Partial: {results['partial']}")
    print(f"   ❌ Failed: {results['failed']}")
    print(f"   📈 Success Rate: {results['success_rate']}%")
    print(f"   🕐 Completed: {results['timestamp']}")
    
    print(f"\n📋 Detailed Test Results:")
    for test_name, result in results['test_results'].items():
        status_icon = {"PASS": "✅", "PARTIAL": "⚠️", "FAIL": "❌"}[result['status']]
        print(f"   {status_icon} {test_name.replace('_', ' ').title()}: {result['message']}")
    
    # Save results to file
    with open('ui_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: ui_test_results.json")
    print("="*60)
    
    return results


if __name__ == "__main__":
    main() 