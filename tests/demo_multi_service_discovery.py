#!/usr/bin/env python3
"""
Multi-Service Discovery Demo
Demonstrates dynamic discovery of multiple MCP services and intelligent tool orchestration
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add technical_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'technical_agent'))

from service_discovery import ServiceDiscovery, ServiceEndpoint

async def demo_multi_service_discovery():
    """Demonstrate multi-service discovery and orchestration"""
    print("🌟 Multi-Service Discovery Demo")
    print("=" * 50)
    print("This demo shows how the Technical Agent can dynamically discover")
    print("and orchestrate multiple MCP services without hardcoded configurations.")
    print()
    
    # Configure multiple services
    services_config = [
        ServiceEndpoint(
            name="policy_service",
            url="http://localhost:8001/mcp",
            description="Insurance policy management service",
            enabled=True
        ),
        ServiceEndpoint(
            name="claims_service", 
            url="http://localhost:8002/mcp",
            description="Insurance claims processing service", 
            enabled=False  # Will be enabled if service is running
        )
    ]
    
    # Initialize service discovery
    discovery = ServiceDiscovery(services_config)
    
    print("🔍 Step 1: Discovering Available Services...")
    discovered_services = await discovery.discover_all_services()
    
    print(f"✅ Discovery Results:")
    print(f"   Services found: {len(discovered_services)}")
    
    for service_name, capabilities in discovered_services.items():
        print(f"   📡 {service_name}:")
        print(f"      - Tools: {len(capabilities.tools)}")
        print(f"      - Resources: {len(capabilities.resources)}")
        print(f"      - URL: {capabilities.metadata.get('url')}")
    
    if not discovered_services:
        print("❌ No services discovered. Make sure the policy server is running.")
        print("   Run: python policy_server/main.py")
        return
    
    print(f"\n🛠️  Step 2: Available Tools Inventory...")
    available_tools = discovery.get_available_tools()
    print(f"   Total tools available: {len(available_tools)}")
    
    # Group tools by service
    tools_by_service = {}
    for service_name, capabilities in discovered_services.items():
        tools_by_service[service_name] = [tool.name for tool in capabilities.tools]
    
    for service_name, tool_names in tools_by_service.items():
        print(f"   📋 {service_name}: {tool_names}")
    
    print(f"\n🤖 Step 3: LLM-Ready Tools Description...")
    tools_description = discovery.build_tools_description()
    print(f"   Generated description: {len(tools_description)} characters")
    print("   This description would be sent to LLM for intelligent planning:")
    print(f"   {tools_description[:200]}...")
    
    print(f"\n🧠 Step 4: Simulating Intelligent Multi-Tool Planning...")
    
    # Simulate different customer scenarios
    scenarios = [
        {
            "name": "Simple Policy Lookup",
            "description": "Customer wants to see their policies",
            "tools_needed": ["get_policies"],
            "reasoning": "Single tool call for basic policy information"
        },
        {
            "name": "Complete Customer Overview", 
            "description": "Customer wants complete account overview",
            "tools_needed": ["get_policies", "get_agent", "get_recommendations"],
            "reasoning": "Multi-tool orchestration for comprehensive view"
        }
    ]
    
    # Add claims scenarios if claims service is available
    if "claims_service" in discovered_services:
        scenarios.extend([
            {
                "name": "Claims Status Check",
                "description": "Customer wants to check claim status", 
                "tools_needed": ["list_claims", "get_claim_status"],
                "reasoning": "Cross-service orchestration between policies and claims"
            },
            {
                "name": "Full Account + Claims Review",
                "description": "Customer wants everything - policies, agent, claims",
                "tools_needed": ["get_policies", "get_agent", "list_claims", "get_recommendations"],
                "reasoning": "Complex multi-service orchestration"
            }
        ])
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n   Scenario {i}: {scenario['name']}")
        print(f"      Request: \"{scenario['description']}\"")
        print(f"      Tools planned: {scenario['tools_needed']}")
        print(f"      Reasoning: {scenario['reasoning']}")
        
        # Check if all tools are available
        available_tool_names = set(available_tools.keys())
        tools_available = all(tool in available_tool_names for tool in scenario['tools_needed'])
        print(f"      ✅ All tools available: {tools_available}")
        
        if not tools_available:
            missing = [tool for tool in scenario['tools_needed'] if tool not in available_tool_names]
            print(f"      ❌ Missing tools: {missing}")
    
    print(f"\n📊 Step 5: Service Health & Extensibility...")
    summary = discovery.get_service_summary()
    
    print(f"   Current System Capacity:")
    print(f"      Services: {summary['total_services']}")
    print(f"      Tools: {summary['total_tools']}")
    print(f"      Resources: {summary['total_resources']}")
    
    print(f"\n   🔮 Extensibility Demonstration:")
    print(f"      ✅ Policy Service: Active ({tools_by_service.get('policy_service', 0)} tools)")
    
    if "claims_service" in discovered_services:
        print(f"      ✅ Claims Service: Active ({len(tools_by_service.get('claims_service', []))} tools)")
        print(f"         → Cross-service workflows enabled!")
    else:
        print(f"      💤 Claims Service: Not running")
        print(f"         → To enable: python services/claims_service/main.py")
        print(f"         → System would auto-discover and integrate seamlessly")
    
    print(f"\n      🚀 Future Services (would auto-integrate):")
    print(f"         • Billing Service (payment processing, invoices)")
    print(f"         • Document Service (policy documents, forms)")
    print(f"         • Analytics Service (usage analytics, insights)")
    print(f"         • Notification Service (alerts, reminders)")
    
    print(f"\n🎯 Step 6: Benefits of Dynamic Discovery...")
    benefits = [
        "Zero hardcoded tool lists - everything discovered dynamically",
        "New services integrate automatically without code changes",
        "LLM gets real-time view of available capabilities",
        "Service failures don't break the entire system",
        "Easy A/B testing of different service versions",
        "Microservices architecture with intelligent orchestration"
    ]
    
    for benefit in benefits:
        print(f"   ✅ {benefit}")
    
    print(f"\n🌟 Demo Complete!")
    print(f"The Technical Agent can now intelligently orchestrate any combination")
    print(f"of discovered services to fulfill complex customer requests!")

async def simulate_customer_interaction():
    """Simulate a customer interaction using discovered services"""
    print(f"\n" + "=" * 50)
    print("🎬 Customer Interaction Simulation")
    print("=" * 50)
    
    print("Customer: \"I want to see all my information - policies, agent, and any claims\"")
    print()
    print("🤖 Technical Agent Processing:")
    print("   1. 🔍 Service Discovery: Found policy_service (10 tools)")
    print("   2. 🧠 LLM Planning: Analyzing request...")
    print("   3. 📋 Execution Plan:")
    print("      - get_policies(customer_id='CUST-001')")
    print("      - get_agent(customer_id='CUST-001')")
    print("      - list_claims(user_id='CUST-001')  # If claims service available")
    print("      - get_recommendations(customer_id='CUST-001')")
    print("   4. ⚡ Parallel Execution: All tools run simultaneously")
    print("   5. 📊 Response Synthesis: Combine results into comprehensive overview")
    print()
    print("🎯 Result: Customer gets complete, up-to-date information from")
    print("   whatever services are currently available - no manual configuration!")

if __name__ == "__main__":
    async def main():
        await demo_multi_service_discovery()
        await simulate_customer_interaction()
    
    asyncio.run(main()) 