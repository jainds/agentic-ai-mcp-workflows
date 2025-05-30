#!/usr/bin/env python3
"""
Pytest configuration for Streamlit UI Selenium tests
"""

import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

# Test configuration
BASE_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
IMPLICIT_WAIT = 10
EXPLICIT_WAIT = 30

@pytest.fixture(scope="session")
def driver_setup():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    
    if HEADLESS:
        chrome_options.add_argument("--headless")
    
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    
    # Setup Chrome driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(IMPLICIT_WAIT)
    
    yield driver
    
    driver.quit()

@pytest.fixture
def driver(driver_setup):
    """Fresh driver instance for each test"""
    driver_setup.delete_all_cookies()
    driver_setup.refresh()
    time.sleep(2)  # Allow page to load
    return driver_setup

@pytest.fixture(scope="session")
def wait_for_streamlit():
    """Wait for Streamlit to be available before running tests"""
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = requests.get(f"{BASE_URL}/_stcore/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Streamlit is ready at {BASE_URL}")
                return True
        except requests.RequestException:
            pass
        
        retry_count += 1
        print(f"⏳ Waiting for Streamlit to be ready... ({retry_count}/{max_retries})")
        time.sleep(2)
    
    pytest.fail(f"❌ Streamlit not available at {BASE_URL} after {max_retries * 2} seconds")

@pytest.fixture
def streamlit_page(driver, wait_for_streamlit):
    """Load Streamlit page and wait for it to be ready"""
    driver.get(BASE_URL)
    
    # Wait for Streamlit to load
    WebDriverWait(driver, EXPLICIT_WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stApp']"))
    )
    
    # Wait a bit more for dynamic content
    time.sleep(3)
    return driver

class StreamlitHelpers:
    """Helper methods for interacting with Streamlit elements"""
    
    @staticmethod
    def wait_for_element(driver, selector, timeout=EXPLICIT_WAIT):
        """Wait for element to be present"""
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    
    @staticmethod
    def wait_for_clickable(driver, selector, timeout=EXPLICIT_WAIT):
        """Wait for element to be clickable"""
        return WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
    
    @staticmethod
    def find_streamlit_input(driver, label_text):
        """Find Streamlit input by label text"""
        try:
            # Try different label selectors
            selectors = [
                f"//label[contains(text(), '{label_text}')]//following::input[1]",
                f"//div[contains(text(), '{label_text}')]//following::input[1]",
                f"//p[contains(text(), '{label_text}')]//following::input[1]"
            ]
            
            for selector in selectors:
                try:
                    return driver.find_element(By.XPATH, selector)
                except:
                    continue
            
            # Fallback: find by placeholder
            return driver.find_element(By.CSS_SELECTOR, f"input[placeholder*='{label_text}']")
        except:
            return None
    
    @staticmethod
    def find_streamlit_button(driver, button_text):
        """Find Streamlit button by text"""
        try:
            # Try different button selectors
            selectors = [
                f"//button[contains(text(), '{button_text}')]",
                f"//div[@data-testid='stButton']//button[contains(text(), '{button_text}')]",
                f"//p[contains(text(), '{button_text}')]//parent::button"
            ]
            
            for selector in selectors:
                try:
                    return driver.find_element(By.XPATH, selector)
                except:
                    continue
            return None
        except:
            return None
    
    @staticmethod
    def wait_for_spinner_to_disappear(driver, timeout=30):
        """Wait for Streamlit spinner to disappear"""
        try:
            WebDriverWait(driver, timeout).until_not(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stSpinner']"))
            )
        except:
            pass  # Spinner might not be present
    
    @staticmethod
    def take_screenshot(driver, filename):
        """Take screenshot for debugging"""
        screenshot_dir = "tests/ui/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        driver.save_screenshot(f"{screenshot_dir}/{filename}")

@pytest.fixture
def helpers():
    """Provide helper methods to tests"""
    return StreamlitHelpers

def pytest_configure(config):
    """Configure pytest"""
    # Create screenshots directory
    os.makedirs("tests/ui/screenshots", exist_ok=True)
    
def pytest_html_report_title(report):
    """Customize HTML report title"""
    report.title = "Insurance AI UI - Selenium Test Report" 