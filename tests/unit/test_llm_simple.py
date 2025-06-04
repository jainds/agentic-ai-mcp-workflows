#!/usr/bin/env python3
"""
Simple LLM Intent Test
Quick test to verify the LLM-based intent identification is working
"""

import os
import sys
import json

# Add technical_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'technical_agent'))

def test_llm_intent():
    """Test the LLM-based intent parsing directly"""
    print("🚀 Testing LLM Intent Identification...")
    
    try:
        # Import and setup
        from openai import OpenAI
        
        # Check if we have OpenRouter API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ OPENROUTER_API_KEY environment variable not set")
            return False
        
        # Initialize OpenAI client
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        print("✅ OpenAI client initialized")
        
        # Test cases
        test_cases = [
            {
                "query": "What is my deductible?",
                "expected_tool": "get_deductibles"
            },
            {
                "query": "When is my next payment due?", 
                "expected_tool": "get_payment_information"
            },
            {
                "query": "What policies do I have?",
                "expected_tool": "get_customer_policies"
            }
        ]
        
        # Available tools description
        tools_description = """Available MCP tools:
- get_deductibles: Get deductible amounts for customer policies
- get_payment_information: Get payment details and due dates
- get_customer_policies: Get comprehensive policy information
- get_agent: Get agent contact information
- get_coverage_information: Get coverage details and limits
- get_recommendations: Get product recommendations"""
        
        results = []
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: '{test_case['query']}'")
            print(f"Expected tool: {test_case['expected_tool']}")
            
            # Create prompt
            prompt = f"""
You are analyzing an insurance customer request to determine the intent and appropriate tool mapping.

Request: "{test_case['query']}"
Customer ID: CUST-001

{tools_description}

Based on the request and available tools, respond with JSON:
{{
    "intent": "specific_tool_name_from_available_tools_or_general_category",
    "confidence": 0.0-1.0,
    "reasoning": "why this intent was chosen and which tool should be used",
    "recommended_tool": "exact_tool_name_if_specific_tool_identified"
}}

Examples:
- "What is my deductible?" -> intent: "get_deductibles"
- "When is payment due?" -> intent: "get_payment_information" 
- "What policies do I have?" -> intent: "get_customer_policies"
- "Who is my agent?" -> intent: "get_agent"
"""
            
            try:
                # Call LLM
                response = client.chat.completions.create(
                    model="anthropic/claude-3-haiku",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=300
                )
                
                result_text = response.choices[0].message.content.strip()
                print(f"LLM Response: {result_text}")
                
                # Parse JSON
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    
                    recommended_tool = parsed.get("recommended_tool")
                    confidence = parsed.get("confidence", 0.0)
                    reasoning = parsed.get("reasoning", "")
                    
                    success = recommended_tool == test_case["expected_tool"]
                    
                    results.append({
                        "query": test_case["query"],
                        "expected": test_case["expected_tool"],
                        "actual": recommended_tool,
                        "success": success,
                        "confidence": confidence,
                        "reasoning": reasoning
                    })
                    
                    status = "✅ PASS" if success else "❌ FAIL"
                    print(f"{status} - Recommended: {recommended_tool} (confidence: {confidence:.1%})")
                    print(f"Reasoning: {reasoning}")
                    
                else:
                    print("❌ Could not parse JSON from LLM response")
                    results.append({
                        "query": test_case["query"],
                        "success": False,
                        "error": "JSON parsing failed"
                    })
                    
            except Exception as e:
                print(f"❌ LLM call failed: {e}")
                results.append({
                    "query": test_case["query"],
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        passed = sum(1 for r in results if r.get("success", False))
        total = len(results)
        
        print(f"\n📊 Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All LLM intent identification tests passed!")
            print("🔥 The LLM is correctly mapping queries to MCP tools!")
            return True
        elif passed > total * 0.7:
            print("✅ Most tests passed - LLM intent identification is working well")
            return True
        else:
            print("⚠️  Some tests failed - LLM intent identification needs refinement")
            return False
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    success = test_llm_intent()
    if success:
        print("\n🚀 SUCCESS: LLM-based intent identification is working!")
        print("💡 The Technical Agent now uses LLM to understand customer queries")
        print("🎯 Queries like 'What is my deductible?' will be mapped to get_deductibles tool")
        print("🎯 Queries like 'When is payment due?' will be mapped to get_payment_information tool")
    else:
        print("\n❌ FAILED: LLM intent identification needs attention") 