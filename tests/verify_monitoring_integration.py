#!/usr/bin/env python3
"""
Monitoring Integration Verification Script

This script verifies that monitoring is properly integrated with Google ADK agents.
Tests Langfuse, Prometheus, and health check integrations.
"""

import os
import sys
import time
import requests
from typing import Dict, Any, List

# Add project paths
sys.path.append('.')
sys.path.append('insurance-adk')

def check_environment_variables() -> Dict[str, bool]:
    """Check if monitoring environment variables are set."""
    required_vars = {
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
        "LANGFUSE_SECRET_KEY": os.getenv("LANGFUSE_SECRET_KEY"),
        "LANGFUSE_PUBLIC_KEY": os.getenv("LANGFUSE_PUBLIC_KEY"),
    }
    
    optional_vars = {
        "LANGFUSE_HOST": os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        "PROMETHEUS_GATEWAY_URL": os.getenv("PROMETHEUS_GATEWAY_URL"),
        "PROMETHEUS_JOB_NAME": os.getenv("PROMETHEUS_JOB_NAME", "insurance-adk"),
    }
    
    print("🔍 Checking Environment Variables...")
    print("=" * 50)
    
    for var, value in required_vars.items():
        status = "✅ SET" if value else "❌ MISSING"
        masked_value = f"{value[:8]}..." if value and len(value) > 8 else value
        print(f"{var:25}: {status} ({masked_value})")
    
    print("\nOptional Variables:")
    for var, value in optional_vars.items():
        status = "✅ SET" if value else "ℹ️  DEFAULT/EMPTY"
        print(f"{var:25}: {status} ({value})")
    
    return {var: bool(value) for var, value in required_vars.items()}

def test_monitoring_initialization():
    """Test if monitoring can be initialized."""
    print("\n🚀 Testing Monitoring Initialization...")
    print("=" * 50)
    
    try:
        from monitoring.setup.monitoring_setup import MonitoringManager
        
        monitoring = MonitoringManager()
        status = monitoring.get_monitoring_status()
        
        print(f"Monitoring Initialized: {'✅ YES' if status['initialized'] else '❌ NO'}")
        print(f"Active Providers: {len(status['providers'])}")
        
        for provider_name, provider_info in status['providers'].items():
            enabled_status = "✅ ENABLED" if provider_info['enabled'] else "❌ DISABLED"
            print(f"  {provider_name:15}: {enabled_status} ({provider_info['type']})")
        
        return monitoring
        
    except ImportError as e:
        print(f"❌ Monitoring module not available: {e}")
        return None
    except Exception as e:
        print(f"❌ Failed to initialize monitoring: {e}")
        return None

def test_adk_agent_monitoring():
    """Test monitoring integration in ADK agents."""
    print("\n🤖 Testing ADK Agent Monitoring Integration...")
    print("=" * 50)
    
    agents_to_test = [
        ("Customer Service", "insurance_customer_service"),
        ("Technical Agent", "insurance_technical_agent"),
        ("Orchestrator", "insurance_orchestrator")
    ]
    
    results = {}
    
    for agent_name, agent_module in agents_to_test:
        try:
            print(f"\nTesting {agent_name} Agent...")
            
            # Try to import the agent module
            import importlib
            module = importlib.import_module(f"{agent_module}.agent")
            
            # Check if monitoring was initialized
            if hasattr(module, 'monitoring') and module.monitoring:
                print(f"  ✅ Monitoring initialized in {agent_name}")
                results[agent_name] = "enabled"
            elif hasattr(module, 'monitoring_enabled') and module.monitoring_enabled:
                print(f"  ✅ Monitoring enabled in {agent_name}")
                results[agent_name] = "enabled"
            else:
                print(f"  ℹ️  Monitoring not detected in {agent_name}")
                results[agent_name] = "not_detected"
                
        except ImportError as e:
            print(f"  ❌ Could not import {agent_name}: {e}")
            results[agent_name] = "import_error"
        except Exception as e:
            print(f"  ⚠️  Error testing {agent_name}: {e}")
            results[agent_name] = "error"
    
    return results

def test_health_endpoints():
    """Test health check endpoints."""
    print("\n🏥 Testing Health Check Endpoints...")
    print("=" * 50)
    
    endpoints = [
        ("ADK Customer Service", "http://localhost:8000/health"),
        ("ADK Technical Agent", "http://localhost:8001/health"),
        ("ADK Orchestrator", "http://localhost:8002/health"),
        ("Policy Server", "http://localhost:8003/health"),
        ("Google ADK Web UI", "http://localhost:8000/dev-ui/"),
        ("Streamlit UI", "http://localhost:8501"),
    ]
    
    health_results = {}
    
    for service_name, endpoint in endpoints:
        try:
            start_time = time.time()
            response = requests.get(endpoint, timeout=3)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                print(f"  ✅ {service_name:20}: OK ({response_time:.1f}ms)")
                health_results[service_name] = "healthy"
            else:
                print(f"  ⚠️  {service_name:20}: HTTP {response.status_code}")
                health_results[service_name] = "unhealthy"
                
        except requests.RequestException as e:
            print(f"  ❌ {service_name:20}: {str(e)[:50]}...")
            health_results[service_name] = "unreachable"
    
    return health_results

def test_langfuse_connectivity():
    """Test Langfuse connectivity if configured."""
    print("\n🔗 Testing Langfuse Connectivity...")
    print("=" * 50)
    
    if not os.getenv("LANGFUSE_SECRET_KEY") or not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("  ℹ️  Langfuse not configured - skipping connectivity test")
        return False
    
    try:
        from monitoring.providers.langfuse_provider import LangfuseProvider
        
        provider = LangfuseProvider()
        if provider.is_enabled():
            print("  ✅ Langfuse provider initialized successfully")
            
            # Test recording a dummy metric
            provider.record_llm_call(
                model="test-model",
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                duration_seconds=1.0,
                success=True,
                metadata={"test": "monitoring_verification"}
            )
            print("  ✅ Successfully recorded test LLM call to Langfuse")
            return True
        else:
            print("  ❌ Langfuse provider failed to initialize")
            return False
            
    except ImportError:
        print("  ❌ Langfuse provider not available")
        return False
    except Exception as e:
        print(f"  ❌ Langfuse test failed: {e}")
        return False

def generate_summary(env_vars: Dict[str, bool], agent_results: Dict[str, str], 
                    health_results: Dict[str, str], langfuse_test: bool):
    """Generate monitoring integration summary."""
    print("\n📊 Monitoring Integration Summary")
    print("=" * 50)
    
    # Environment configuration
    env_configured = all(env_vars.values())
    print(f"Environment Configuration: {'✅ COMPLETE' if env_configured else '⚠️  INCOMPLETE'}")
    
    # Agent integration
    agents_with_monitoring = sum(1 for status in agent_results.values() if status == "enabled")
    total_agents = len(agent_results)
    print(f"Agent Integration: {agents_with_monitoring}/{total_agents} agents have monitoring")
    
    # Health checks
    healthy_services = sum(1 for status in health_results.values() if status == "healthy")
    total_services = len(health_results)
    print(f"Service Health: {healthy_services}/{total_services} services are healthy")
    
    # Langfuse connectivity
    print(f"Langfuse Integration: {'✅ WORKING' if langfuse_test else '❌ NOT WORKING'}")
    
    # Overall status
    print("\n🎯 Overall Status:")
    if env_configured and agents_with_monitoring > 0 and healthy_services > total_services // 2:
        print("✅ Monitoring integration is FUNCTIONAL")
        print("   • Environment is properly configured")
        print("   • Agents have monitoring integrated")
        print("   • Services are responding to health checks")
    elif agents_with_monitoring > 0:
        print("⚠️  Monitoring integration is PARTIAL")
        print("   • Some components are working")
        print("   • May need additional configuration")
    else:
        print("❌ Monitoring integration has ISSUES")
        print("   • Check environment variables")
        print("   • Verify service availability")
        print("   • Review agent configurations")

def main():
    """Main verification function."""
    print("🔍 Google ADK Monitoring Integration Verification")
    print("=" * 60)
    print("This script verifies monitoring integration across:")
    print("• Environment configuration")
    print("• Google ADK agents")
    print("• Health check endpoints")
    print("• Langfuse connectivity")
    print()
    
    # Run all tests
    env_vars = check_environment_variables()
    monitoring = test_monitoring_initialization()
    agent_results = test_adk_agent_monitoring()
    health_results = test_health_endpoints()
    langfuse_test = test_langfuse_connectivity()
    
    # Generate summary
    generate_summary(env_vars, agent_results, health_results, langfuse_test)
    
    print("\n💡 Next Steps:")
    if not all(env_vars.values()):
        print("• Set missing environment variables in .env file")
    if sum(1 for s in health_results.values() if s == "healthy") < len(health_results) // 2:
        print("• Start services: ./start_port_forwards_adk.sh")
    if not langfuse_test and env_vars.get("LANGFUSE_SECRET_KEY"):
        print("• Check Langfuse credentials and connectivity")
    
    print("\n📚 Documentation: GOOGLE_ADK_LITELLM_INTEGRATION.md")

if __name__ == "__main__":
    main() 