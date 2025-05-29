#!/usr/bin/env python3
"""
OpenRouter LLM Integration Test
This test demonstrates how to use the OpenRouter API with the Claims Agent
"""

import os
import asyncio
from agents.domain.claims_agent import ClaimsAgent


async def test_openrouter_llm_call():
    """Test OpenRouter LLM integration"""
    print("\n" + "="*80)
    print("TESTING OPENROUTER LLM INTEGRATION")
    print("="*80)
    
    # Create Claims Agent
    claims_agent = ClaimsAgent(port=8000)
    
    # Check configuration
    print(f"Primary Model: {claims_agent.primary_model}")
    print(f"Fallback Model: {claims_agent.fallback_model}")
    print(f"Base URL: {claims_agent.openai_client.base_url}")
    
    # Check if we have a real OpenRouter API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key or openrouter_key == "your-openrouter-api-key-here":
        print("\n⚠️  OpenRouter API key not configured")
        print("To test with real OpenRouter API:")
        print("1. Get an API key from https://openrouter.ai/")
        print("2. Set OPENROUTER_API_KEY in your .env file")
        print("3. Run this test again")
        print("\nFor now, running with mock demonstration...")
        
        # Demonstrate how the LLM call would work
        test_message = "I was in a car accident and need to file a claim"
        
        try:
            # This will fail in demo mode but shows the structure
            result = await claims_agent._analyze_user_intent(test_message, "test_conv")
            print(f"✓ Intent analysis result: {result}")
        except Exception as e:
            print(f"Expected error in demo mode: {str(e)}")
            
        return
    
    print(f"✓ Using OpenRouter API with key: {openrouter_key[:8]}...")
    
    # Test actual LLM call
    test_message = "I was in a car accident yesterday and need to file an insurance claim"
    
    try:
        print(f"\nTesting intent analysis with message: '{test_message}'")
        result = await claims_agent._analyze_user_intent(test_message, "test_conv")
        
        print("✓ LLM Response received:")
        print(f"  Intent: {result.get('intent', 'unknown')}")
        print(f"  Confidence: {result.get('confidence', 0)}")
        print(f"  Technical Actions: {len(result.get('technical_actions', []))}")
        print(f"  Response Strategy: {result.get('response_strategy', 'unknown')}")
        
    except Exception as e:
        print(f"❌ LLM call failed: {str(e)}")
        print("This might be due to:")
        print("- Invalid API key")
        print("- Network issues")
        print("- Model availability")
        print("- Rate limiting")


async def test_claim_extraction():
    """Test claim information extraction"""
    print("\n" + "="*60)
    print("TESTING CLAIM INFORMATION EXTRACTION")
    print("="*60)
    
    claims_agent = ClaimsAgent(port=8000)
    
    test_message = """
    I was rear-ended at the intersection of Main St and 5th Ave yesterday around 3 PM.
    The other driver ran a red light. My policy number is POL-AUTO-123456.
    There's about $8,000 worth of damage to my car's rear bumper and trunk.
    Police report number is PR-2024-5829.
    """
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key or openrouter_key == "your-openrouter-api-key-here":
        print("⚠️  Skipping real LLM test - no API key configured")
        return
    
    try:
        print("Extracting claim information from detailed message...")
        result = await claims_agent._extract_claim_information(test_message)
        
        print("✓ Claim Information extracted:")
        for key, value in result.items():
            if value:
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"❌ Claim extraction failed: {str(e)}")


def main():
    """Run OpenRouter integration tests"""
    print("\n" + "="*100)
    print("OPENROUTER API INTEGRATION TESTS")
    print("="*100)
    
    # Check environment
    print("\nEnvironment Configuration:")
    print(f"OPENROUTER_API_KEY: {'✓ Set' if os.getenv('OPENROUTER_API_KEY') else '❌ Not set'}")
    print(f"PRIMARY_MODEL: {os.getenv('PRIMARY_MODEL', 'Not set')}")
    print(f"FALLBACK_MODEL: {os.getenv('FALLBACK_MODEL', 'Not set')}")
    print(f"OPENROUTER_BASE_URL: {os.getenv('OPENROUTER_BASE_URL', 'Not set')}")
    
    # Run tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(test_openrouter_llm_call())
        loop.run_until_complete(test_claim_extraction())
        
        print("\n" + "="*100)
        print("OpenRouter integration tests completed!")
        print("="*100)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
    finally:
        loop.close()


if __name__ == "__main__":
    main() 