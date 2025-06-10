#!/usr/bin/env python3
"""
Google ADK Agents Test

This script tests the official Google ADK implementation for insurance agents
following the patterns from google/adk-samples.
"""

import sys
import logging

# Add insurance-adk to path
sys.path.append('insurance-adk')

from agents.base_adk import (
    InsuranceADKConfig,
    create_insurance_technical_agent,
    create_insurance_domain_agent,
    create_insurance_coordinator_agent,
    create_a2a_agent_card
)

logging.basicConfig(level=logging.INFO)

def test_google_adk_implementation():
    """Test Google ADK agent creation and validation"""
    print("🚀 Testing Google ADK v1.2.1 Implementation")
    print("=" * 60)
    
    try:
        # Test configuration
        print("📋 Testing ADK Configuration...")
        config = InsuranceADKConfig()
        print(f"✅ Model: {config.model}")
        print(f"✅ Policy Server Path: {config.policy_server_path}")
        
        # Test agent creation
        print("\n🤖 Testing Agent Creation...")
        
        # Technical Agent
        technical_agent = create_insurance_technical_agent(config)
        print(f"✅ Technical Agent: {technical_agent.name}")
        print(f"   Type: {type(technical_agent).__name__}")
        print(f"   Description: {technical_agent.description}")
        
        # Domain Agent  
        domain_agent = create_insurance_domain_agent(config)
        print(f"✅ Domain Agent: {domain_agent.name}")
        print(f"   Type: {type(domain_agent).__name__}")
        print(f"   Model: {getattr(domain_agent, 'model', 'Not set')}")
        print(f"   Sub-agents: {len(getattr(domain_agent, 'sub_agents', []))}")
        
        # Coordinator Agent
        coordinator_agent = create_insurance_coordinator_agent(config)
        print(f"✅ Coordinator Agent: {coordinator_agent.name}")
        print(f"   Type: {type(coordinator_agent).__name__}")
        print(f"   Sub-agents: {len(getattr(coordinator_agent, 'sub_agents', []))}")
        
        # Test A2A cards
        print("\n🔗 Testing A2A Agent Cards...")
        domain_card = create_a2a_agent_card(
            "test_domain_agent",
            "http://localhost:8003/a2a",
            "Test domain agent"
        )
        print(f"✅ A2A Card: {domain_card.name}")
        print(f"   URL: {domain_card.url}")
        print(f"   Capabilities: {domain_card.capabilities}")
        
        # Verify agent types are from official Google ADK
        print("\n🏗️ Framework Verification...")
        from google.adk.agents import LlmAgent, BaseAgent
        
        assert isinstance(technical_agent, BaseAgent), "Technical agent should be BaseAgent"
        assert isinstance(domain_agent, LlmAgent), "Domain agent should be LlmAgent"
        assert isinstance(coordinator_agent, LlmAgent), "Coordinator agent should be LlmAgent"
        
        print("✅ All agents using real google.adk.agents classes")
        print("✅ Framework: Official Google ADK v1.2.1")
        
        print("\n🎉 Google ADK Implementation Test: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Google ADK Implementation Test: FAILED")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_adk_implementation()
    sys.exit(0 if success else 1) 