#!/usr/bin/env python3
"""
A2A Communication Test for Official Google ADK v1.2.1 + A2A Implementation

This script tests Agent-to-Agent (A2A) communication between the insurance AI components
using the official Google ADK v1.2.1 library with MCP integration.

Components tested:
1. Policy Server (MCP) - Port 8001
2. Official Google ADK Agents with A2A communication
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

from agents.base_adk import (
    InsuranceADKConfig,
    create_insurance_technical_agent,
    create_insurance_domain_agent,
    create_a2a_agent_card,
    technical_agent,
    domain_agent
)
from agents.orchestrator import create_adk_orchestrator

logging.basicConfig(level=logging.INFO)

class A2ACommunicationTester:
    def __init__(self):
        self.test_results = []
        self.config = InsuranceADKConfig()
        self.orchestrator = create_adk_orchestrator(self.config)
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    async def test_adk_agent_creation(self) -> bool:
        """Test creating Official Google ADK agents with A2A capabilities"""
        self.log("🤖 Testing Official Google ADK v1.2.1 + A2A agent creation...")
        
        try:
            # Use the existing agents created with official ADK
            self.domain_agent = domain_agent
            self.technical_agent = technical_agent
            
            # Verify agent types
            from google.adk.agents import LlmAgent, BaseAgent
            
            assert isinstance(self.technical_agent, BaseAgent), "Technical agent should be BaseAgent"
            assert isinstance(self.domain_agent, LlmAgent), "Domain agent should be LlmAgent"
            
            # Create A2A agent cards
            domain_card = create_a2a_agent_card(
                agent_name=self.domain_agent.name,
                agent_url="http://localhost:8003/a2a",
                description=self.domain_agent.description
            )
            
            technical_card = create_a2a_agent_card(
                agent_name=self.technical_agent.name,
                agent_url="http://localhost:8002/a2a", 
                description=self.technical_agent.description
            )
            
            self.log(f"✅ Domain Agent: {domain_card.name} ({type(self.domain_agent).__name__})")
            self.log(f"✅ Technical Agent: {technical_card.name} ({type(self.technical_agent).__name__})")
            self.log(f"✅ Framework: Official Google ADK v1.2.1")
            
            # Store agent cards
            self.domain_card = domain_card
            self.technical_card = technical_card
            
            return True
            
        except Exception as e:
            self.log(f"❌ Official ADK agent creation failed: {e}", "ERROR")
            return False
    
    async def test_customer_request_processing(self) -> bool:
        """Test customer request processing with Google ADK"""
        self.log("📞 Testing customer request processing with Google ADK...")
        
        try:
            # Test customer inquiry
            customer_request = {
                "customer_id": "CUST-ADK-001",
                "message": "What are my current insurance policies and coverage details?",
                "session_id": "adk-test-session-001",
                "timestamp": time.time()
            }
            
            result = await self.orchestrator.process_customer_request(
                request=customer_request,
                agent_type="domain"
            )
            
            if result.get("success"):
                self.log(f"✅ Customer request processed by Google ADK")
                self.log(f"Framework: {result.get('framework', 'Unknown')}")
                self.log(f"Agent: {result.get('agent', 'Unknown')}")
                return True
            else:
                self.log(f"⚠️  Customer request processing failed: {result.get('error', 'Unknown error')}", "WARN")
                return False
                
        except Exception as e:
            self.log(f"❌ Customer request processing failed: {e}", "ERROR")
            return False
    
    async def test_a2a_communication_flow(self) -> bool:
        """Test A2A communication between Google ADK agents"""
        self.log("🔗 Testing A2A communication flow with Google ADK...")
        
        try:
            # Create A2A request for technical agent
            a2a_request = {
                "customer_id": "CUST-ADK-001",
                "operation": "get_customer_policies",
                "message": "Retrieve detailed policy information for customer analysis",
                "parameters": {
                    "request_type": "policy_inquiry", 
                    "analysis_level": "detailed"
                },
                "source_agent": "domain",
                "timestamp": time.time()
            }
            
            result = await self.orchestrator.handle_a2a_communication(
                source_agent="domain",
                target_agent="technical", 
                a2a_request=a2a_request
            )
            
            if result.get("success"):
                self.log("✅ A2A communication successful with Google ADK")
                self.log(f"Framework: {result.get('framework', 'Unknown')}")
                self.log(f"A2A Protocol: {result.get('a2a_protocol', 'Unknown')}")
                self.log(f"Source: {result.get('source_agent', 'Unknown')}")
                self.log(f"Target: {result.get('target_agent', 'Unknown')}")
                return True
            else:
                self.log(f"❌ A2A communication failed: {result.get('error', 'Unknown error')}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ A2A communication test failed: {e}", "ERROR")
            return False
    
    async def test_inter_agent_workflow(self) -> bool:
        """Test complete inter-agent workflow with Google ADK"""
        self.log("🔄 Testing complete inter-agent workflow with Google ADK...")
        
        try:
            # Simulate full workflow: Customer → Domain Agent → A2A → Technical Agent
            
            # Step 1: Customer inquiry
            customer_request = {
                "customer_id": "CUST-ADK-WORKFLOW-001",
                "message": "I need comprehensive details about my policy coverage and recent claims",
                "session_id": "adk-workflow-session-001",
                "timestamp": time.time()
            }
            
            self.log(f"📞 Customer Request: {customer_request['message']}")
            
            # Step 2: Domain agent processing
            domain_result = await self.orchestrator.process_customer_request(
                request=customer_request,
                agent_type="domain"
            )
            
            self.log(f"🤖 Domain Agent (Google ADK): {domain_result.get('framework', 'Unknown')}")
            
            # Step 3: A2A call to technical agent
            a2a_request = {
                "customer_id": customer_request["customer_id"],
                "operation": "comprehensive_policy_analysis",
                "message": "Perform comprehensive policy and claims analysis",
                "parameters": {
                    "request_type": "full_analysis",
                    "original_message": customer_request["message"],
                    "include_claims": True
                },
                "source_agent": "domain",
                "timestamp": time.time()
            }
            
            self.log("🔄 Initiating A2A call to Technical Agent...")
            
            tech_result = await self.orchestrator.handle_a2a_communication(
                source_agent="domain",
                target_agent="technical",
                a2a_request=a2a_request
            )
            
            self.log(f"⚙️ Technical Agent A2A Response: {tech_result.get('framework', 'Unknown')}")
            
            # Check workflow success
            if domain_result.get("success") and tech_result.get("success"):
                self.log("✅ Complete inter-agent workflow successful!")
                self.log(f"🏗️ Architecture: Google ADK v1.2.1 + A2A Protocol")
                return True
            else:
                self.log("❌ Inter-agent workflow failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Inter-agent workflow test failed: {e}", "ERROR")
            return False
    
    async def test_agent_status_and_capabilities(self) -> bool:
        """Test agent status and capabilities reporting"""
        self.log("📊 Testing agent status and capabilities with Google ADK...")
        
        try:
            # Get agent status
            domain_status = self.orchestrator.get_agent_status("domain")
            technical_status = self.orchestrator.get_agent_status("technical")
            
            self.log(f"🤖 Domain Agent Status:")
            self.log(f"   Framework: {domain_status.get('framework', 'Unknown')}")
            self.log(f"   Status: {domain_status.get('status', 'Unknown')}")
            self.log(f"   Model: {domain_status.get('model', 'Unknown')}")
            
            self.log(f"⚙️ Technical Agent Status:")
            self.log(f"   Framework: {technical_status.get('framework', 'Unknown')}")
            self.log(f"   Status: {technical_status.get('status', 'Unknown')}")
            self.log(f"   Model: {technical_status.get('model', 'Unknown')}")
            
            # Check A2A capabilities
            if hasattr(self, 'domain_card') and hasattr(self, 'technical_card'):
                self.log(f"🔗 A2A Capabilities:")
                self.log(f"   Domain Agent A2A: {self.domain_card.capabilities.get('a2a_communication', False)}")
                self.log(f"   Technical Agent A2A: {self.technical_card.capabilities.get('a2a_communication', False)}")
            
            # Verify both agents are active
            if (domain_status.get('status') == 'active' and 
                technical_status.get('status') == 'active'):
                self.log("✅ All agents active and reporting capabilities")
                return True
            else:
                self.log("❌ Some agents not active", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Agent status test failed: {e}", "ERROR")
            return False
    
    async def test_mcp_integration(self) -> bool:
        """Test MCP toolset integration"""
        self.log("🔧 Testing MCP toolset integration...")
        
        try:
            # Check if technical agent has MCP tools
            if hasattr(self.technical_agent, 'tools'):
                tools_count = len(self.technical_agent.tools)
                self.log(f"✅ Technical agent has {tools_count} tool(s)")
                
                # Check for MCP toolset
                from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
                has_mcp = any(isinstance(tool, MCPToolset) for tool in self.technical_agent.tools)
                
                if has_mcp:
                    self.log("✅ MCP toolset integration confirmed")
                    return True
                else:
                    self.log("⚠️  No MCP toolset found", "WARN")
                    return False
            else:
                self.log("❌ Technical agent has no tools", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ MCP integration test failed: {e}", "ERROR")
            return False

    async def run_comprehensive_a2a_test(self) -> Dict[str, bool]:
        """Run comprehensive A2A test suite for Google ADK"""
        self.log("🚀 Starting Comprehensive Google ADK + A2A Communication Test Suite")
        self.log("=" * 80)
        
        tests = [
            ("ADK Agent Creation", self.test_adk_agent_creation),
            ("Customer Request Processing", self.test_customer_request_processing), 
            ("A2A Communication Flow", self.test_a2a_communication_flow),
            ("Inter-Agent Workflow", self.test_inter_agent_workflow),
            ("Agent Status & Capabilities", self.test_agent_status_and_capabilities),
            ("MCP Integration", self.test_mcp_integration)
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running Test: {test_name}")
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
                self.log(f"❌ {test_name}: ERROR - {e}")
                results[test_name] = False
        
        self.log("\n" + "=" * 80)
        self.log("📊 FINAL TEST RESULTS - Official Google ADK v1.2.1 + A2A")
        self.log("=" * 80)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name}: {status}")
        
        success_rate = (passed / total) * 100
        self.log(f"\n🎯 Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! Google ADK + A2A implementation is working perfectly!")
            self.log("✅ Official Google ADK v1.2.1 framework confirmed")
            self.log("✅ A2A communication protocol working")
            self.log("✅ MCP toolset integration functional")
            self.log("✅ Inter-agent coordination successful")
        else:
            self.log(f"⚠️  {total - passed} test(s) failed. Review implementation.")
            
        return results

async def main():
    """Main test execution"""
    tester = A2ACommunicationTester()
    results = await tester.run_comprehensive_a2a_test()
    
    # Exit with appropriate code
    all_passed = all(results.values())
    exit(0 if all_passed else 1)

if __name__ == "__main__":
    asyncio.run(main()) 