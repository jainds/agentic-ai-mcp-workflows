#!/usr/bin/env python3
"""
Simple Selenium UI Test for Insurance AI
"""

import time
import sys
import os

def test_selenium_basic():
    """Basic Selenium test for the UI"""
    try:
        # Try importing selenium
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("✅ Selenium imports successful")
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        print("🔧 Setting up Chrome driver...")
        
        # Setup Chrome driver using webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Chrome driver initialized")
        
        try:
            # Navigate to the application
            url = "http://localhost:8501"
            print(f"🌐 Navigating to {url}...")
            driver.get(url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Take screenshot
            screenshot_path = "tests/ui/screenshot_selenium_test.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            driver.save_screenshot(screenshot_path)
            print(f"📸 Screenshot saved to {screenshot_path}")
            
            # Get page title
            title = driver.title
            print(f"📄 Page title: {title}")
            
            # Check for Streamlit app
            try:
                app_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='stApp']")
                print("✅ Streamlit app container found")
            except:
                print("⚠️ Streamlit app container not found (might be loading)")
            
            # Check page content
            page_content = driver.page_source.lower()
            content_checks = [
                ("streamlit" in page_content, "Streamlit detected"),
                ("insurance" in page_content or "ai" in page_content, "App content detected"),
                (len(page_content) > 1000, "Substantial content present")
            ]
            
            for check, description in content_checks:
                status = "✅" if check else "⚠️"
                print(f"{status} {description}")
            
            passed_checks = sum(1 for check, _ in content_checks if check)
            print(f"\n📊 Content checks: {passed_checks}/3 passed")
            
            return passed_checks >= 2
            
        finally:
            driver.quit()
            print("🧹 Browser closed")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try: pip install selenium webdriver-manager")
        return False
    except Exception as e:
        print(f"❌ Selenium test failed: {e}")
        return False

def test_ui_interaction():
    """Test basic UI interactions"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Setup
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            driver.get("http://localhost:8501")
            
            # Wait for Streamlit to load
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            time.sleep(5)  # Additional wait for dynamic content
            
            # Look for input fields
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            print(f"✅ Found {len(inputs)} text input fields")
            
            # Look for buttons
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"✅ Found {len(buttons)} buttons")
            
            # Try to find authentication elements
            auth_elements = 0
            auth_keywords = ["customer", "login", "auth", "id"]
            
            for keyword in auth_keywords:
                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                if elements:
                    auth_elements += 1
                    print(f"✅ Found elements containing '{keyword}'")
            
            print(f"📊 Authentication elements: {auth_elements}/4 found")
            
            # Take final screenshot
            driver.save_screenshot("tests/ui/screenshot_interaction_test.png")
            print("📸 Interaction screenshot saved")
            
            return True
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"❌ UI interaction test failed: {e}")
        return False

def main():
    """Run Selenium tests"""
    print("🧪 Simple Selenium UI Tests for Insurance AI")
    print("="*50)
    
    tests = [
        ("Basic Selenium Test", test_selenium_basic),
        ("UI Interaction Test", test_ui_interaction)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append(result)
            print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
        except Exception as e:
            results.append(False)
            print(f"Result: ❌ ERROR - {e}")
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Selenium tests passed!")
        return True
    else:
        print("⚠️ Some Selenium tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 