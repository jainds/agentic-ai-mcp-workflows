#!/usr/bin/env python3
"""
Simple Selenium UI Test for Insurance AI Streamlit Interface
"""

import time
import requests
import os
from pathlib import Path

def test_streamlit_via_requests():
    """Test Streamlit UI using simple HTTP requests"""
    base_url = "http://localhost:8501"
    
    # Check health endpoint
    try:
        response = requests.get(f"{base_url}/_stcore/health", timeout=10)
        print(f"✅ Health check: {response.status_code}")
        assert response.status_code == 200, "Health check failed"
    except requests.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Check main page
    try:
        response = requests.get(base_url, timeout=10)
        print(f"✅ Main page: {response.status_code}")
        assert response.status_code == 200, "Main page not accessible"
        
        # Check if it's a Streamlit app
        content = response.text.lower()
        streamlit_indicators = ["streamlit", "stapp", "data-testid"]
        found_indicators = sum(1 for indicator in streamlit_indicators if indicator in content)
        
        print(f"✅ Streamlit indicators found: {found_indicators}/3")
        assert found_indicators >= 1, "No Streamlit indicators found"
        
        # Check for our app content
        app_indicators = ["insurance", "ai", "assistant", "customer", "authentication"]
        found_app = sum(1 for indicator in app_indicators if indicator in content)
        
        print(f"✅ App content indicators: {found_app}/5")
        assert found_app >= 2, "Insurance AI app content not found"
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ Main page test failed: {e}")
        return False

def test_modular_components():
    """Test that our modular components can be imported"""
    try:
        import sys
        sys.path.append('.')
        
        from ui.components.config import UIConfig
        print("✅ Config component imported")
        
        # Test configuration
        features = UIConfig.get_enabled_features()
        print(f"✅ Features loaded: {len(features)} features")
        
        # Test mode detection
        mode = "Advanced" if UIConfig.is_advanced_mode() else "Simple"
        print(f"✅ UI Mode: {mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Component import failed: {e}")
        return False

def run_basic_ui_tests():
    """Run basic UI tests without Selenium"""
    print("🧪 Running Basic Insurance AI UI Tests")
    print("="*50)
    
    tests = [
        ("HTTP Requests Test", test_streamlit_via_requests),
        ("Modular Components Test", test_modular_components)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results[test_name] = "PASSED" if result else "FAILED"
            print(f"Result: {'✅ PASSED' if result else '❌ FAILED'}")
        except Exception as e:
            results[test_name] = "ERROR"
            print(f"Result: ❌ ERROR - {e}")
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for result in results.values() if result == "PASSED")
    total = len(results)
    
    for test_name, result in results.items():
        status_icon = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}[result]
        print(f"{status_icon} {test_name}: {result}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! UI is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    success = run_basic_ui_tests()
    exit(0 if success else 1) 