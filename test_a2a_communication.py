#!/usr/bin/env python3
"""
A2A Communication Test for Google ADK + A2A Implementation

This script tests Agent-to-Agent (A2A) communication between the insurance AI components
following the architecture from:
https://medium.com/google-cloud/architecting-a-multi-agent-system-with-google-a2a-and-adk-4ced4502c86a

Components tested:
1. Policy Server (MCP) - Port 8001
2. Insurance ADK Agents with A2A communication
3. Inter-agent communication protocols
"""

import sys
import time
import json
import asyncio
import logging
from typing import Dict, Any, Optional

# Add insurance-adk to path
sys.path.append('insurance-adk')

from agents.base_adk import InsuranceADKAgent, ADKModelConfig, A2ARiskCheckTool

logging.basicConfig(level=logging.INFO)

class A2ACommunicationTester:
    def __init__(self):
        self.test_results = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    async def test_adk_agent_creation(self) -> bool:
        """Test creating Google ADK agents with A2A capabilities"""
        self.log("🤖 Testing Google ADK + A2A agent creation...")
        
        try:
            # Create model configurations
            domain_config = ADKModelConfig(
                primary_model="anthropic/claude-3.5-sonnet",
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1"
            )
            
            technical_config = ADKModelConfig(
                primary_model="meta-llama/llama-3.1-70b-instruct", 
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1"
            )
            
            # Create A2A tools
            risk_tool = A2ARiskCheckTool("http://localhost:8002")
            
            # Create agents
            domain_agent = InsuranceADKAgent(
                name="Insurance Domain Agent",
                description="Customer-facing agent with A2A communication",
                model_config=domain_config,
                tools=[risk_tool],
                agent_url="http://localhost:8003/a2a"
            )
            
            technical_agent = InsuranceADKAgent(
                name="Insurance Technical Agent",
                description="Technical agent for policy data with A2A",
                model_config=technical_config,
                agent_url="http://localhost:8002/a2a"
            )
            
            # Test agent cards
            domain_card = domain_agent.get_agent_card()
            technical_card = technical_agent.get_agent_card()
            
            self.log(f"✅ Domain Agent Card: {domain_card.name} at {domain_card.url}")
            self.log(f"✅ Technical Agent Card: {technical_card.name} at {technical_card.url}")
            
            # Store agents for other tests
            self.domain_agent = domain_agent
            self.technical_agent = technical_agent
            
            return True
            
        except Exception as e:
            self.log(f"❌ ADK agent creation failed: {e}", "ERROR")
            return False
    
    async def test_customer_request_processing(self) -> bool:
        """Test customer request processing"""
        self.log("📞 Testing customer request processing...")
        
        try:
            if not hasattr(self, 'domain_agent'):
                self.log("❌ Domain agent not available", "ERROR")
                return False
            
            # Test customer inquiry
            customer_request = {
                "customer_id": "CUST-TEST-001",
                "message": "What are my current insurance policies?",
                "session_id": "test-session-001",
                "timestamp": time.time()
            }
            
            result = await self.domain_agent.process_customer_request(customer_request)
            
            if result.get("processed"):
                self.log(f"✅ Customer request processed successfully")
                self.log(f"Response: {result.get('response', 'No response')}")
                return True
            else:
                self.log("⚠️  Customer request processing failed", "WARN")
                return False
                
        except Exception as e:
            self.log(f"❌ Customer request processing failed: {e}", "ERROR")
            return False
    
    async def test_a2a_communication_flow(self) -> bool:
        """Test A2A communication between agents"""
        self.log("🔗 Testing A2A communication flow...")
        
        try:
            if not hasattr(self, 'technical_agent'):
                self.log("❌ Technical agent not available", "ERROR")
                return False
            
            # Create A2A request following the article pattern
            a2a_request = {
                "customer_id": "CUST-TEST-001",
                "operation": "get_customer_policies",
                "parameters": {
                    "request_type": "policy_inquiry",
                    "original_message": "What are my policies?"
                },
                "source_agent": "domain",
                "timestamp": time.time()
            }
            
            result = await self.technical_agent.handle_a2a_communication(a2a_request)
            
            if result.get("a2a_processed"):
                self.log("✅ A2A communication successful")
                
                # Check for A2A Artifact structure
                if "a2a_response" in result and "artifact" in result["a2a_response"]:
                    artifact = result["a2a_response"]["artifact"]
                    self.log(f"📦 A2A Artifact received: {json.dumps(artifact, indent=2)}")
                    return True
                else:
                    self.log("⚠️  A2A response missing artifact structure", "WARN")
                    return False
            else:
                self.log("❌ A2A communication failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ A2A communication test failed: {e}", "ERROR")
            return False
    
    async def test_inter_agent_workflow(self) -> bool:
        """Test complete inter-agent workflow"""
        self.log("🔄 Testing complete inter-agent workflow...")
        
        try:
            if not hasattr(self, 'domain_agent') or not hasattr(self, 'technical_agent'):
                self.log("❌ Agents not available", "ERROR")
                return False
            
            # Simulate full workflow: Customer → Domain Agent → A2A → Technical Agent
            
            # Step 1: Customer inquiry
            customer_request = {
                "customer_id": "CUST-WORKFLOW-001", 
                "message": "I need details about my policy coverage",
                "session_id": "workflow-session-001",
                "timestamp": time.time()
            }
            
            self.log(f"📞 Customer Request: {customer_request['message']}")
            
            # Step 2: Domain agent processing
            domain_result = await self.domain_agent.process_customer_request(customer_request)
            self.log(f"🤖 Domain Agent Response: {domain_result.get('response', 'No response')}")
            
            # Step 3: A2A call to technical agent
            a2a_request = {
                "customer_id": customer_request["customer_id"],
                "operation": "get_customer_policies", 
                "parameters": {
                    "request_type": "policy_inquiry",
                    "original_message": customer_request["message"]
                },
                "source_agent": "domain",
                "timestamp": time.time()
            }
            
            self.log("🔄 Making A2A call to Technical Agent...")
            technical_result = await self.technical_agent.handle_a2a_communication(a2a_request)
            
            # Step 4: Verify complete workflow
            if (domain_result.get("processed") and 
                technical_result.get("a2a_processed") and
                "artifact" in technical_result.get("a2a_response", {})):
                
                self.log("✅ Complete inter-agent workflow successful!")
                
                # Show the workflow results
                artifact = technical_result["a2a_response"]["artifact"]
                self.log(f"📋 Final A2A Artifact: {json.dumps(artifact, indent=2)}")
                
                return True
            else:
                self.log("❌ Inter-agent workflow incomplete", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Inter-agent workflow test failed: {e}", "ERROR")
            return False
    
    async def test_agent_status_and_capabilities(self) -> bool:
        """Test agent status and A2A capabilities"""
        self.log("📊 Testing agent status and A2A capabilities...")
        
        try:
            if not hasattr(self, 'domain_agent') or not hasattr(self, 'technical_agent'):
                self.log("❌ Agents not available", "ERROR")
                return False
            
            # Test domain agent status
            domain_status = await self.domain_agent.get_agent_status()
            self.log(f"🤖 Domain Agent Status: {domain_status.get('status', 'Unknown')}")
            self.log(f"Framework: {domain_status.get('framework', 'Unknown')}")
            
            # Test technical agent status  
            technical_status = await self.technical_agent.get_agent_status()
            self.log(f"⚙️ Technical Agent Status: {technical_status.get('status', 'Unknown')}")
            self.log(f"A2A Protocol: {technical_status.get('a2a_protocol', 'Unknown')}")
            
            # Verify A2A capabilities
            domain_capabilities = domain_status.get('capabilities', [])
            technical_capabilities = technical_status.get('capabilities', [])
            
            if ("a2a_communication" in domain_capabilities and 
                "a2a_communication" in technical_capabilities):
                self.log("✅ Both agents have A2A communication capabilities")
                return True
            else:
                self.log("❌ Missing A2A capabilities", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Agent status test failed: {e}", "ERROR")
            return False
    
    async def run_comprehensive_a2a_test(self) -> Dict[str, bool]:
        """Run all A2A communication tests"""
        self.log("🚀 Starting Google ADK + A2A Communication Test")
        self.log("Following architecture from: https://medium.com/google-cloud/architecting-a-multi-agent-system-with-google-a2a-and-adk-4ced4502c86a")
        self.log("=" * 80)
        
        tests = [
            ("ADK Agent Creation", self.test_adk_agent_creation),
            ("Customer Request Processing", self.test_customer_request_processing),
            ("A2A Communication Flow", self.test_a2a_communication_flow),
            ("Inter-Agent Workflow", self.test_inter_agent_workflow),
            ("Agent Status & Capabilities", self.test_agent_status_and_capabilities),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n📝 Running: {test_name}")
            self.log("-" * 50)
            
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    passed += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"💥 {test_name}: EXCEPTION - {e}", "ERROR")
                results[test_name] = False
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("📋 GOOGLE ADK + A2A COMMUNICATION TEST SUMMARY")
        self.log("=" * 80)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name:.<40} {status}")
        
        self.log(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            self.log("\n🎉 All Google ADK + A2A communication tests PASSED!")
            self.log("✅ Agents are communicating via A2A protocol successfully!")
        else:
            self.log(f"\n⚠️  {total-passed} A2A communication tests FAILED")
            
        return results


async def main():
    """Main test execution"""
    print("Insurance AI POC - Google ADK + A2A Communication Test")
    print("=" * 60)
    print("Reference: https://medium.com/google-cloud/architecting-a-multi-agent-system-with-google-a2a-and-adk-4ced4502c86a")
    print()
    
    tester = A2ACommunicationTester()
    results = await tester.run_comprehensive_a2a_test()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 