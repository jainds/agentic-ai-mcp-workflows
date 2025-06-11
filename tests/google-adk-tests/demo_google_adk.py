#!/usr/bin/env python3
"""
Google ADK Demo - Official Implementation

This demo showcases insurance AI agents built with official Google ADK v1.2.1
following patterns from google/adk-samples customer service examples.
"""

import sys
import asyncio
import logging

# Add insurance-adk to path
sys.path.append('insurance-adk')

from agents.base_adk import (
    InsuranceADKConfig,
    create_insurance_technical_agent,
    create_insurance_domain_agent,
    create_insurance_coordinator_agent,
    technical_agent,
    domain_agent
)
from agents.orchestrator import create_adk_orchestrator

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

async def demo_google_adk():
    """Demonstrate Google ADK insurance agents"""
    print("🚀 Google ADK v1.2.1 Insurance Agents Demo")
    print("=" * 60)
    
    # Initialize configuration
    config = InsuranceADKConfig()
    print(f"📋 Configuration:")
    print(f"   Model: {config.model}")
    print(f"   Framework: Official Google ADK v1.2.1")
    
    # Create orchestrator
    orchestrator = create_adk_orchestrator(config)
    print(f"\n🎯 Orchestrator: {type(orchestrator).__name__}")
    
    # Show agent status
    print(f"\n🤖 Agent Status:")
    all_status = orchestrator.get_all_agent_status()
    for agent_type, status in all_status.items():
        print(f"   {agent_type.title()}: {status['framework']} ({status['status']})")
    
    # Demonstrate customer request processing
    print(f"\n📞 Customer Request Demo:")
    customer_request = {
        "customer_id": "DEMO-001",
        "message": "I would like to check my insurance policy details and coverage information.",
        "session_id": "demo-session-001"
    }
    
    print(f"   Request: {customer_request['message']}")
    
    # Process with domain agent
    result = await orchestrator.process_customer_request(
        request=customer_request,
        agent_type="domain"
    )
    
    print(f"   ✅ Response: {result['agent']} processed successfully")
    print(f"   Framework: {result['framework']}")
    
    # Demonstrate A2A communication
    print(f"\n🔗 A2A Communication Demo:")
    a2a_request = {
        "customer_id": "DEMO-001",
        "operation": "policy_analysis",
        "message": "Analyze customer policy portfolio for recommendations",
        "parameters": {"analysis_type": "comprehensive"}
    }
    
    a2a_result = await orchestrator.handle_a2a_communication(
        source_agent="domain",
        target_agent="technical",
        a2a_request=a2a_request
    )
    
    print(f"   ✅ A2A: {a2a_result['source_agent']} → {a2a_result['target_agent']}")
    print(f"   Protocol: {a2a_result['a2a_protocol']}")
    print(f"   Framework: {a2a_result['framework']}")
    
    # Show agent cards
    print(f"\n🏷️ A2A Agent Cards:")
    agent_cards = orchestrator.get_agent_cards()
    for agent_type, card in agent_cards.items():
        print(f"   {card.name}:")
        print(f"     URL: {card.url}")
        print(f"     Capabilities: {len(card.capabilities)} features")
    
    print(f"\n🎉 Google ADK Demo Complete!")
    print(f"✅ All agents using official google.adk.agents classes")
    print(f"✅ Framework: Google ADK v1.2.1")
    print(f"✅ A2A Protocol: python-a2a v0.5.6")

def show_agent_structure():
    """Show the agent structure and hierarchy"""
    print("\n🏗️ Agent Architecture:")
    print("   📋 InsuranceADKConfig")
    print("   ├── 🤖 Technical Agent (BaseAgent)")
    print("   │   ├── Complex operations")
    print("   │   └── Policy management")
    print("   ├── 👤 Domain Agent (LlmAgent)")
    print("   │   ├── Customer service")
    print("   │   └── Sub-agent: Technical Agent")
    print("   └── 🎯 Coordinator Agent (LlmAgent)")
    print("       ├── Orchestration")
    print("       └── Sub-agents: Domain + Technical")
    
    # Verify agent types
    from google.adk.agents import LlmAgent, BaseAgent
    print(f"\n🔍 Type Verification:")
    print(f"   Technical: {type(technical_agent).__name__} ← BaseAgent: {isinstance(technical_agent, BaseAgent)}")
    print(f"   Domain: {type(domain_agent).__name__} ← LlmAgent: {isinstance(domain_agent, LlmAgent)}")

if __name__ == "__main__":
    show_agent_structure()
    asyncio.run(demo_google_adk()) 