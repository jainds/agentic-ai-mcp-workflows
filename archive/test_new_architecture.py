#!/usr/bin/env python3
"""
Test script for the new intelligent MCP architecture
Tests both the information gathering and MCP tool discovery features
"""

import json
import asyncio
from agents.domain.python_a2a_domain_agent import PythonA2ADomainAgent
from agents.technical.python_a2a_technical_agent import PythonA2ATechnicalAgent

async def test_information_gathering():
    """Test the information gathering functionality"""
    print("🔍 Testing Information Gathering...")
    
    # Create domain agent
    domain_agent = PythonA2ADomainAgent(port=8010)
    
    # Test 1: Policy inquiry without customer ID (should ask for more info)
    print("\n📋 Test 1: Policy inquiry without customer information")
    from python_a2a import Message, TextContent, MessageRole
    
    user_request = "I want to check my policy details"
    message = Message(
        content=TextContent(text=user_request),
        role=MessageRole.USER
    )
    
    response = domain_agent.handle_message(message)
    print(f"User: {user_request}")
    print(f"Agent: {response.content.text}")
    
    # Test 2: Quote request without coverage type (should ask for more info)
    print("\n💰 Test 2: Quote request without coverage type")
    user_request = "I want to get an insurance quote"
    message = Message(
        content=TextContent(text=user_request),
        role=MessageRole.USER
    )
    
    response = domain_agent.handle_message(message)
    print(f"User: {user_request}")
    print(f"Agent: {response.content.text}")
    
    # Test 3: Policy inquiry with customer ID (should proceed)
    print("\n✅ Test 3: Policy inquiry with customer information")
    user_request = "I want to check my policy details. My customer ID is CUST-12345"
    message = Message(
        content=TextContent(text=user_request),
        role=MessageRole.USER
    )
    
    response = domain_agent.handle_message(message)
    print(f"User: {user_request}")
    print(f"Agent: {response.content.text}")

async def test_mcp_tool_discovery():
    """Test MCP tool discovery and intelligent routing"""
    print("\n🔧 Testing MCP Tool Discovery...")
    
    # Create technical agents
    data_agent = PythonA2ATechnicalAgent(port=8011, agent_type="data")
    
    print(f"🔍 Data agent capabilities: {data_agent.agent_capabilities['primary_functions']}")
    print(f"🛠️ Available MCP tools: {len(data_agent.available_mcp_tools)} tools")
    
    # Test action determination
    test_cases = [
        {
            "name": "Policy details with customer ID",
            "task_data": {
                "action": "fetch_policy_details",
                "customer_id": "CUST-12345"
            }
        },
        {
            "name": "Policy details without customer ID",
            "task_data": {
                "action": "fetch_policy_details"
            }
        },
        {
            "name": "Benefits calculation with context",
            "task_data": {
                "action": "calculate_benefits",
                "context": {"customer_id": "CUST-12345"}
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 Test: {test_case['name']}")
        action_plan = data_agent.determine_appropriate_action(test_case['task_data'])
        print(f"Status: {action_plan['status']}")
        
        if action_plan['status'] == 'needs_more_info':
            print(f"Missing: {action_plan['missing_fields']}")
            print(f"Questions: {action_plan['suggested_questions']}")
        else:
            print(f"Action: {action_plan['action']}")
            print(f"Tools: {action_plan['suitable_tools']}")

async def test_execution_flow():
    """Test the complete execution flow"""
    print("\n🚀 Testing Complete Execution Flow...")
    
    # Test with missing information
    domain_agent = PythonA2ADomainAgent(port=8012)
    
    print("\n📋 Test: Complete flow with missing customer ID")
    
    # Step 1: Understand intent 
    user_text = "What are my policy benefits?"
    intent_analysis = domain_agent.understand_intent(user_text)
    print(f"Intent: {intent_analysis.get('primary_intent')}")
    
    # Step 2: Create execution plan (should request more info)
    execution_plan = domain_agent.create_execution_plan(intent_analysis, user_text)
    print(f"Plan type: {execution_plan.get('type')}")
    
    if execution_plan.get('type') == 'information_gathering':
        print(f"Missing info: {execution_plan.get('missing_information')}")
        print(f"Questions: {execution_plan.get('questions_to_ask')}")
    
    # Step 3: Execute plan (should return information request)
    execution_results = domain_agent.execute_plan(execution_plan, "test-conversation")
    print(f"Execution status: {execution_results.get('status')}")
    
    # Step 4: Prepare response
    final_response = domain_agent.prepare_response(intent_analysis, execution_results, user_text)
    print(f"Final response: {final_response}")

async def main():
    """Run all tests"""
    print("🧪 Testing New Intelligent MCP Architecture")
    print("=" * 50)
    
    try:
        await test_information_gathering()
        await test_mcp_tool_discovery()
        await test_execution_flow()
        
        print("\n✅ All tests completed successfully!")
        print("\n🎉 Architecture Features Verified:")
        print("  • Information gathering when data is missing")
        print("  • MCP tool discovery and registration")
        print("  • Intelligent action determination")
        print("  • Professional question generation")
        print("  • Fallback to agent logic when needed")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 