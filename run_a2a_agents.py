#!/usr/bin/env python3
"""
A2A Insurance Agents Demo

This script demonstrates Agent-to-Agent (A2A) communication between insurance agents
following the architecture pattern from:
https://medium.com/google-cloud/architecting-a-multi-agent-system-with-google-a2a-and-adk-4ced4502c86a
"""

import asyncio
import logging
import json
from typing import Dict, Any
import time
from python_a2a import A2AServer, AgentCard
import sys
import os

# Add insurance-adk to path
sys.path.append('insurance-adk')

from agents.base_adk import InsuranceADKAgent, ADKModelConfig, A2ARiskCheckTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DomainAgentServer:
    """Domain Agent A2A Server for customer interactions"""
    
    def __init__(self, port: int = 8003):
        self.port = port
        
        # Create agent following the article pattern
        model_config = ADKModelConfig(
            primary_model="anthropic/claude-3.5-sonnet",
            api_key="mock-api-key",
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Create A2A Risk Check Tool for inter-agent communication
        risk_tool = A2ARiskCheckTool("http://localhost:8002")
        
        self.agent = InsuranceADKAgent(
            name="Insurance Domain Agent",
            description="Customer-facing agent for insurance inquiries with A2A communication",
            model_config=model_config,
            tools=[risk_tool],
            agent_url=f"http://localhost:{port}/a2a"
        )
        
        # Create A2A server with proper agent card
        self.a2a_server = A2AServer(
            agent_card=self.agent.get_agent_card(),
            port=port
        )
    
    async def start(self):
        """Start the A2A server"""
        logger.info(f"🤖 Starting Domain Agent A2A Server on port {self.port}")
        # Register A2A endpoints
        self.a2a_server.register_skill("process_customer_request", self.agent.process_customer_request)
        self.a2a_server.register_skill("handle_a2a_communication", self.agent.handle_a2a_communication)
        
        await self.a2a_server.start()

class TechnicalAgentServer:
    """Technical Agent A2A Server for policy operations"""
    
    def __init__(self, port: int = 8002):
        self.port = port
        
        # Create agent following the article pattern
        model_config = ADKModelConfig(
            primary_model="meta-llama/llama-3.1-70b-instruct",
            api_key="mock-api-key",
            base_url="https://openrouter.ai/api/v1"
        )
        
        self.agent = InsuranceADKAgent(
            name="Insurance Technical Agent",
            description="Technical agent for policy data and A2A operations",
            model_config=model_config,
            agent_url=f"http://localhost:{port}/a2a"
        )
        
        # Create A2A server with proper agent card
        self.a2a_server = A2AServer(
            agent_card=self.agent.get_agent_card(),
            port=port
        )
    
    async def start(self):
        """Start the A2A server"""
        logger.info(f"⚙️ Starting Technical Agent A2A Server on port {self.port}")
        # Register A2A endpoints
        self.a2a_server.register_skill("handle_a2a_communication", self.agent.handle_a2a_communication)
        self.a2a_server.register_skill("get_agent_status", self.agent.get_agent_status)
        
        await self.a2a_server.start()

class A2ACommunicationDemo:
    """Demonstrates A2A communication between agents"""
    
    def __init__(self):
        self.domain_agent = None
        self.technical_agent = None
    
    async def start_agents(self):
        """Start both A2A agent servers"""
        logger.info("🚀 Starting A2A Insurance Agents Demo")
        logger.info("Following architecture from: https://medium.com/google-cloud/architecting-a-multi-agent-system-with-google-a2a-and-adk-4ced4502c86a")
        
        # Start technical agent first
        self.technical_agent = TechnicalAgentServer(8002)
        technical_task = asyncio.create_task(self.technical_agent.start())
        
        # Wait a moment then start domain agent
        await asyncio.sleep(2)
        self.domain_agent = DomainAgentServer(8003)
        domain_task = asyncio.create_task(self.domain_agent.start())
        
        logger.info("✅ Both A2A agents started successfully!")
        logger.info("🌐 Agent URLs:")
        logger.info("   📋 Technical Agent: http://localhost:8002/a2a")
        logger.info("   🤖 Domain Agent: http://localhost:8003/a2a")
        
        # Keep servers running
        await asyncio.gather(technical_task, domain_task)
    
    async def demonstrate_a2a_communication(self):
        """Demonstrate A2A communication flow"""
        logger.info("\n🔗 Demonstrating A2A Communication Flow")
        
        # Simulate customer inquiry that requires technical data
        customer_request = {
            "customer_id": "CUST-A2A-001",
            "message": "What are my current insurance policies?",
            "session_id": "demo-session-001",
            "timestamp": time.time()
        }
        
        logger.info(f"📞 Customer Request: {customer_request['message']}")
        
        # Process through domain agent
        if self.domain_agent:
            domain_result = await self.domain_agent.agent.process_customer_request(customer_request)
            logger.info(f"🤖 Domain Agent Response: {domain_result.get('response', 'No response')}")
            
            # Demonstrate A2A call to technical agent
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
            
            logger.info("🔄 Making A2A call to Technical Agent...")
            if self.technical_agent:
                tech_result = await self.technical_agent.agent.handle_a2a_communication(a2a_request)
                logger.info(f"⚙️ Technical Agent A2A Response: {json.dumps(tech_result, indent=2)}")
                
                # Show the A2A Artifact structure
                if "a2a_response" in tech_result and "artifact" in tech_result["a2a_response"]:
                    artifact = tech_result["a2a_response"]["artifact"]
                    logger.info(f"📦 A2A Artifact: {json.dumps(artifact, indent=2)}")

def main():
    """Main execution"""
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run communication demo
        async def run_demo():
            demo = A2ACommunicationDemo()
            await demo.demonstrate_a2a_communication()
        
        asyncio.run(run_demo())
    else:
        # Start A2A servers
        demo = A2ACommunicationDemo()
        try:
            asyncio.run(demo.start_agents())
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down A2A agents...")
            sys.exit(0)

if __name__ == "__main__":
    main() 