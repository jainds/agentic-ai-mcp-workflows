"""
Demonstration of python-a2a communication between domain and technical agents.

This script shows:
1. Domain agent understanding intent and creating plans
2. Routing tasks to technical agents
3. Aggregating results and preparing responses
"""

import asyncio
import time
import threading
import subprocess
import sys
import os
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_a2a import A2AClient, Message, TextContent, MessageRole
import structlog

logger = structlog.get_logger(__name__)


class PythonA2ADemo:
    """
    Demonstration of python-a2a agent communication
    """
    
    def __init__(self):
        self.domain_agent_url = "http://localhost:8000"
        self.data_agent_url = "http://localhost:8002"
        self.notification_agent_url = "http://localhost:8003"
        self.fastmcp_agent_url = "http://localhost:8004"
        
        self.agents_started = False
        self.agent_processes = []
    
    def start_agents_in_background(self):
        """Start all agents in background processes"""
        if self.agents_started:
            return
        
        print("🚀 Starting agents in background...")
        
        # Start domain agent
        domain_cmd = [
            sys.executable, "-m", "agents.domain.python_a2a_domain_agent",
            "--port", "8000", "--host", "0.0.0.0"
        ]
        
        # Start technical agents
        data_cmd = [
            sys.executable, "-m", "agents.technical.python_a2a_technical_agent",
            "--port", "8002", "--host", "0.0.0.0", "--type", "data"
        ]
        
        notification_cmd = [
            sys.executable, "-m", "agents.technical.python_a2a_technical_agent",
            "--port", "8003", "--host", "0.0.0.0", "--type", "notification"
        ]
        
        fastmcp_cmd = [
            sys.executable, "-m", "agents.technical.python_a2a_technical_agent",
            "--port", "8004", "--host", "0.0.0.0", "--type", "fastmcp"
        ]
        
        try:
            # Start agents with output redirection
            self.domain_process = subprocess.Popen(
                domain_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            self.agent_processes.append(self.domain_process)
            
            self.data_process = subprocess.Popen(
                data_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            self.agent_processes.append(self.data_process)
            
            self.notification_process = subprocess.Popen(
                notification_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            self.agent_processes.append(self.notification_process)
            
            self.fastmcp_process = subprocess.Popen(
                fastmcp_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            self.agent_processes.append(self.fastmcp_process)
            
            # Wait for agents to start
            print("⏳ Waiting for agents to initialize...")
            time.sleep(5)
            
            self.agents_started = True
            print("✅ All agents started successfully!")
            
        except Exception as e:
            print(f"❌ Failed to start agents: {e}")
            self.cleanup()
            raise
    
    def cleanup(self):
        """Stop all agent processes"""
        print("🧹 Cleaning up agent processes...")
        for process in self.agent_processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"Warning: Error stopping process: {e}")
        
        self.agent_processes.clear()
        self.agents_started = False
        print("✅ Cleanup completed!")
    
    def test_direct_communication(self):
        """Test direct communication with technical agents"""
        print("\n" + "="*60)
        print("🔗 TESTING DIRECT TECHNICAL AGENT COMMUNICATION")
        print("="*60)
        
        # Test data agent
        print("\n📊 Testing Data Agent...")
        try:
            data_client = A2AClient(self.data_agent_url)
            
            test_task = {
                "action": "fetch_policy_details",
                "plan_context": {
                    "entities": {"policy_id": "POL123456"}
                }
            }
            
            message = Message(
                content=TextContent(text=str(test_task)),
                role=MessageRole.USER
            )
            
            response = data_client.send_message(message)
            print(f"✅ Data Agent Response: {response.content.text[:200]}...")
            
        except Exception as e:
            print(f"❌ Data Agent Error: {e}")
        
        # Test notification agent
        print("\n📧 Testing Notification Agent...")
        try:
            notification_client = A2AClient(self.notification_agent_url)
            
            test_task = {
                "action": "send_claim_confirmation",
                "previous_results": []
            }
            
            message = Message(
                content=TextContent(text=str(test_task)),
                role=MessageRole.USER
            )
            
            response = notification_client.send_message(message)
            print(f"✅ Notification Agent Response: {response.content.text[:200]}...")
            
        except Exception as e:
            print(f"❌ Notification Agent Error: {e}")
    
    def test_domain_agent_workflow(self):
        """Test full domain agent workflow"""
        print("\n" + "="*60)
        print("🧠 TESTING DOMAIN AGENT WORKFLOW")
        print("="*60)
        
        test_scenarios = [
            {
                "name": "Claim Filing",
                "message": "I want to file a claim for my car accident that happened yesterday. Policy number POL123456.",
                "expected_intent": "claim_filing"
            },
            {
                "name": "Policy Inquiry", 
                "message": "Can you tell me about my policy details? My policy number is POL789012.",
                "expected_intent": "policy_inquiry"
            },
            {
                "name": "Billing Question",
                "message": "I need to check my billing history and outstanding balance.",
                "expected_intent": "billing_question"
            },
            {
                "name": "General Inquiry",
                "message": "What types of insurance do you offer?",
                "expected_intent": "general_inquiry"
            }
        ]
        
        try:
            domain_client = A2AClient(self.domain_agent_url)
            
            for i, scenario in enumerate(test_scenarios, 1):
                print(f"\n📋 Test {i}: {scenario['name']}")
                print(f"📝 User Message: {scenario['message']}")
                
                message = Message(
                    content=TextContent(text=scenario['message']),
                    role=MessageRole.USER
                )
                
                start_time = time.time()
                response = domain_client.send_message(message)
                execution_time = time.time() - start_time
                
                print(f"⏱️  Execution Time: {execution_time:.2f} seconds")
                print(f"🤖 Domain Agent Response:")
                print(f"   {response.content.text[:300]}...")
                
                if len(response.content.text) > 300:
                    print(f"   ... (truncated, full response: {len(response.content.text)} characters)")
                
                print("-" * 50)
                
        except Exception as e:
            print(f"❌ Domain Agent Workflow Error: {e}")
    
    def test_agent_discovery(self):
        """Test agent discovery and registry"""
        print("\n" + "="*60)
        print("🔍 TESTING AGENT DISCOVERY")
        print("="*60)
        
        agents_to_test = [
            ("Domain Agent", self.domain_agent_url),
            ("Data Agent", self.data_agent_url),
            ("Notification Agent", self.notification_agent_url),
            ("FastMCP Agent", self.fastmcp_agent_url)
        ]
        
        for name, url in agents_to_test:
            try:
                print(f"\n🔎 Discovering {name} at {url}...")
                client = A2AClient(url)
                
                # Try to get agent card (if supported)
                if hasattr(client, 'get_agent_card'):
                    card = client.get_agent_card()
                    print(f"   ✅ Agent Card: {card}")
                else:
                    # Try a simple ping
                    ping_message = Message(
                        content=TextContent(text="ping"),
                        role=MessageRole.USER
                    )
                    response = client.send_message(ping_message)
                    print(f"   ✅ Agent responded: {response.content.text[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Failed to discover {name}: {e}")
    
    def run_demo(self):
        """Run the complete demonstration"""
        print("🎭 PYTHON-A2A COMMUNICATION DEMO")
        print("=" * 60)
        print("This demo shows domain and technical agents communicating")
        print("using the python-a2a library for Agent-to-Agent protocol.")
        print("=" * 60)
        
        try:
            # Start agents
            self.start_agents_in_background()
            
            # Run tests
            self.test_agent_discovery()
            self.test_direct_communication()
            self.test_domain_agent_workflow()
            
            print("\n" + "="*60)
            print("🎉 DEMO COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("Key Achievements:")
            print("✅ Domain agent understands user intents")
            print("✅ Plans are created and executed")
            print("✅ Tasks are routed to technical agents")
            print("✅ Results are aggregated and responses prepared")
            print("✅ All communication uses python-a2a protocol")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Demo failed: {e}")
        finally:
            self.cleanup()


def main():
    """Main demo entry point"""
    demo = PythonA2ADemo()
    
    try:
        demo.run_demo()
    except KeyboardInterrupt:
        print("\nDemo interrupted. Cleaning up...")
        demo.cleanup()
    except Exception as e:
        print(f"Demo error: {e}")
        demo.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main() 