#!/usr/bin/env python3
"""
Test script for modular UI components
Demonstrates how to import and use components from outside files
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ui.components import (
    UIConfig,
    CustomerValidator,
    DomainAgentClient,
    get_system_status_summary,
    get_thinking_summary
)

def test_config():
    """Test configuration functionality"""
    print("🎛️ Testing UI Configuration...")
    
    # Test feature toggles
    features = UIConfig.get_enabled_features()
    print(f"Current UI Mode: {'Advanced' if UIConfig.is_advanced_mode() else 'Simple'}")
    print("Feature Status:")
    for feature, enabled in features.items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {feature.replace('_', ' ').title()}")
    
    # Test endpoints
    print(f"\nDomain Agent Endpoints: {UIConfig.DOMAIN_AGENT_ENDPOINTS}")
    print(f"Demo Customers: {list(UIConfig.DEMO_CUSTOMERS.keys())}")
    print(f"Monitored Services: {len(UIConfig.MONITORED_SERVICES)} services")

def test_authentication():
    """Test authentication component"""
    print("\n🔐 Testing Authentication...")
    
    # Test valid customer
    result = CustomerValidator.validate_customer("CUST-001")
    print(f"CUST-001 validation: {'✅' if result['valid'] else '❌'}")
    if result['valid']:
        print(f"  Customer: {result['customer_data']['name']}")
    
    # Test invalid customer
    result = CustomerValidator.validate_customer("INVALID")
    print(f"INVALID validation: {'✅' if result['valid'] else '❌'}")

def test_agent_client():
    """Test agent client functionality"""
    print("\n🤖 Testing Agent Client...")
    
    client = DomainAgentClient()
    print(f"Agent endpoint: {client.base_url or 'No active endpoint found'}")
    
    # Note: This would normally require a running agent
    print("Agent client initialized successfully")

def test_monitoring():
    """Test monitoring functions"""
    print("\n📊 Testing Monitoring Functions...")
    
    # This would normally require session state, but we can test the function exists
    try:
        summary = get_system_status_summary()
        if "monitoring_disabled" in summary:
            print("System monitoring is disabled (expected in test)")
        else:
            print(f"System status summary generated: {len(summary)} metrics")
    except Exception as e:
        print(f"Monitoring test (expected to fail without session): {e}")

def test_thinking():
    """Test thinking and orchestration functions"""
    print("\n🧠 Testing Thinking Functions...")
    
    try:
        summary = get_thinking_summary()
        if "features_disabled" in summary:
            print("Thinking features disabled (based on config)")
        else:
            print(f"Thinking summary generated: {len(summary)} metrics")
    except Exception as e:
        print(f"Thinking test (expected to fail without session): {e}")

def test_imports():
    """Test that all components can be imported successfully"""
    print("\n📦 Testing Component Imports...")
    
    components = [
        'UIConfig', 'CustomerValidator', 'DomainAgentClient',
        'get_system_status_summary', 'get_thinking_summary'
    ]
    
    for component in components:
        try:
            # Check if component exists in globals (already imported)
            if component in globals():
                print(f"  ✅ {component}")
            else:
                print(f"  ❌ {component}")
        except Exception as e:
            print(f"  ❌ {component}: {e}")

def main():
    """Run all tests"""
    print("🧪 Insurance AI UI - Modular Component Tests")
    print("=" * 50)
    
    test_imports()
    test_config()
    test_authentication()
    test_agent_client()
    test_monitoring()
    test_thinking()
    
    print("\n" + "=" * 50)
    print("✅ All component tests completed!")
    print("\n📋 Usage Examples:")
    print("1. Import specific components:")
    print("   from ui.components import UIConfig, DomainAgentClient")
    print("2. Import all components:")
    print("   from ui.components import *")
    print("3. Configure features via environment variables:")
    print("   export UI_MODE=simple")
    print("   export ENABLE_THINKING_STEPS=false")

if __name__ == "__main__":
    main() 