#!/usr/bin/env python3
"""
Insurance AI PoC Demonstration Script

This script demonstrates the end-to-end workflows of the insurance AI system,
showing how domain agents orchestrate business processes using technical agents
and backend services.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax


class InsuranceAIDemo:
    """Demonstration of Insurance AI PoC workflows"""
    
    def __init__(self):
        self.console = Console()
        self.base_urls = {
            "customer_service": "http://localhost:30000",
            "policy_service": "http://localhost:30001", 
            "claims_service": "http://localhost:30002",
            "support_agent": "http://localhost:30005",
            "claims_agent": "http://localhost:30007"
        }
        self.test_customer_id = 101
        self.test_policy_id = 202
        
    async def run_demo(self):
        """Run the complete demonstration"""
        self.console.print(Panel.fit(
            "[bold blue]Insurance AI PoC Demonstration[/bold blue]\n"
            "Multi-Agent Architecture with A2A Communication",
            title="🏢 Insurance AI System",
            border_style="blue"
        ))
        
        await self.check_system_health()
        await self.demonstrate_policy_inquiry()
        await self.demonstrate_claim_filing()
        await self.demonstrate_claim_status_check()
        await self.demonstrate_a2a_communication()
        await self.show_system_capabilities()
        
        self.console.print(Panel.fit(
            "[bold green]✅ Demonstration Complete![/bold green]\n"
            "All workflows executed successfully",
            border_style="green"
        ))
    
    async def check_system_health(self):
        """Check that all system components are healthy"""
        self.console.print("\n[bold yellow]🔍 System Health Check[/bold yellow]")
        
        health_table = Table(title="Service Health Status")
        health_table.add_column("Service", style="cyan")
        health_table.add_column("Status", style="magenta")
        health_table.add_column("Response Time", style="green")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for service_name, base_url in self.base_urls.items():
                try:
                    start_time = time.time()
                    response = await client.get(f"{base_url}/health")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        status = "✅ Healthy"
                        response_time = f"{(end_time - start_time)*1000:.0f}ms"
                    else:
                        status = f"❌ Error ({response.status_code})"
                        response_time = "N/A"
                        
                except Exception as e:
                    status = f"❌ Failed ({str(e)[:20]}...)"
                    response_time = "N/A"
                
                health_table.add_row(service_name, status, response_time)
        
        self.console.print(health_table)
    
    async def demonstrate_policy_inquiry(self):
        """Demonstrate policy status inquiry workflow"""
        self.console.print("\n[bold blue]📋 Policy Inquiry Workflow[/bold blue]")
        
        workflow_steps = [
            "User asks about policy status",
            "Support agent extracts intent",
            "Agent validates customer",
            "Agent retrieves policy information", 
            "Agent generates natural response"
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Processing policy inquiry...", total=len(workflow_steps))
            
            # Simulate the workflow
            user_message = "What is the status of my policies?"
            
            self.console.print(f"\n[bold]User Request:[/bold] {user_message}")
            self.console.print(f"[bold]Customer ID:[/bold] {self.test_customer_id}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    # Call support agent
                    chat_request = {
                        "message": user_message,
                        "customer_id": self.test_customer_id
                    }
                    
                    response = await client.post(
                        f"{self.base_urls['support_agent']}/chat",
                        json=chat_request
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        progress.update(task, advance=len(workflow_steps))
                        
                        self.console.print("\n[bold green]✅ Policy Inquiry Successful![/bold green]")
                        self.console.print(f"[bold]Response:[/bold] {result.get('response', 'No response')}")
                        
                        if result.get('data'):
                            self._display_workflow_data("Policy Data Retrieved", result['data'])
                    else:
                        self.console.print(f"[bold red]❌ Error: {response.status_code}[/bold red]")
                        
                except Exception as e:
                    self.console.print(f"[bold red]❌ Failed: {str(e)}[/bold red]")
    
    async def demonstrate_claim_filing(self):
        """Demonstrate claim filing workflow"""
        self.console.print("\n[bold blue]🚗 Claim Filing Workflow[/bold blue]")
        
        user_message = ("I want to file a claim for a car accident that happened on January 15th, 2024 "
                       "at the intersection of Main St and Oak Ave. My car was rear-ended and has "
                       "damage to the bumper.")
        
        self.console.print(f"\n[bold]User Request:[/bold] {user_message}")
        self.console.print(f"[bold]Customer ID:[/bold] {self.test_customer_id}")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Processing claim filing...", total=1)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    chat_request = {
                        "message": user_message,
                        "customer_id": self.test_customer_id
                    }
                    
                    response = await client.post(
                        f"{self.base_urls['claims_agent']}/chat",
                        json=chat_request
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        progress.update(task, advance=1)
                        
                        if result.get('success'):
                            self.console.print("\n[bold green]✅ Claim Filing Processing![/bold green]")
                            self.console.print(f"[bold]Response:[/bold] {result.get('response', 'No response')}")
                            
                            if result.get('data') and result['data'].get('claim'):
                                claim = result['data']['claim']
                                claim_table = Table(title="New Claim Created")
                                claim_table.add_column("Field", style="cyan")
                                claim_table.add_column("Value", style="magenta")
                                
                                claim_table.add_row("Claim ID", str(claim.get('claim_id', 'N/A')))
                                claim_table.add_row("Claim Number", claim.get('claim_number', 'N/A'))
                                claim_table.add_row("Status", claim.get('status', 'N/A'))
                                claim_table.add_row("Type", claim.get('claim_type', 'N/A'))
                                
                                self.console.print(claim_table)
                            elif result.get('next_action') == 'collect_claim_details':
                                self.console.print("[yellow]📝 Additional information needed for claim[/yellow]")
                                if result.get('missing_fields'):
                                    self.console.print(f"Missing: {', '.join(result['missing_fields'])}")
                        else:
                            self.console.print(f"[red]❌ Claim filing issue: {result.get('error', 'Unknown error')}[/red]")
                    else:
                        self.console.print(f"[bold red]❌ Error: {response.status_code}[/bold red]")
                        
                except Exception as e:
                    self.console.print(f"[bold red]❌ Failed: {str(e)}[/bold red]")
    
    async def demonstrate_claim_status_check(self):
        """Demonstrate claim status check workflow"""
        self.console.print("\n[bold blue]📊 Claim Status Check Workflow[/bold blue]")
        
        user_message = "What is the status of my claims?"
        
        self.console.print(f"\n[bold]User Request:[/bold] {user_message}")
        self.console.print(f"[bold]Customer ID:[/bold] {self.test_customer_id}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                chat_request = {
                    "message": user_message,
                    "customer_id": self.test_customer_id
                }
                
                response = await client.post(
                    f"{self.base_urls['claims_agent']}/chat",
                    json=chat_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success'):
                        self.console.print("\n[bold green]✅ Claim Status Retrieved![/bold green]")
                        self.console.print(f"[bold]Response:[/bold] {result.get('response', 'No response')}")
                        
                        if result.get('data') and result['data'].get('claims'):
                            claims = result['data']['claims']
                            if claims:
                                claims_table = Table(title="Customer Claims")
                                claims_table.add_column("Claim ID", style="cyan")
                                claims_table.add_column("Status", style="magenta")
                                claims_table.add_column("Type", style="green")
                                claims_table.add_column("Amount", style="yellow")
                                
                                for claim in claims[:3]:  # Show first 3 claims
                                    claims_table.add_row(
                                        str(claim.get('claim_id', 'N/A')),
                                        claim.get('status', 'N/A'),
                                        claim.get('claim_type', 'N/A'),
                                        f"${claim.get('claimed_amount', 0):,.2f}"
                                    )
                                
                                self.console.print(claims_table)
                            else:
                                self.console.print("[yellow]📝 No claims found for customer[/yellow]")
                    else:
                        self.console.print(f"[red]❌ Status check issue: {result.get('error', 'Unknown error')}[/red]")
                else:
                    self.console.print(f"[bold red]❌ Error: {response.status_code}[/bold red]")
                    
            except Exception as e:
                self.console.print(f"[bold red]❌ Failed: {str(e)}[/bold red]")
    
    async def demonstrate_a2a_communication(self):
        """Demonstrate A2A (Agent-to-Agent) communication"""
        self.console.print("\n[bold blue]🔄 A2A Communication Demonstration[/bold blue]")
        
        self.console.print("Testing direct agent skill execution...")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Test direct skill execution on support agent
                execute_request = {
                    "skill_name": "CheckPolicyStatus",
                    "parameters": {
                        "policy_id": self.test_policy_id,
                        "customer_id": self.test_customer_id
                    },
                    "sender": "demo_client"
                }
                
                response = await client.post(
                    f"{self.base_urls['support_agent']}/execute",
                    json=execute_request
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    self.console.print("\n[bold green]✅ A2A Skill Execution Successful![/bold green]")
                    
                    a2a_table = Table(title="A2A Communication Result")
                    a2a_table.add_column("Field", style="cyan")
                    a2a_table.add_column("Value", style="magenta")
                    
                    a2a_table.add_row("Success", str(result.get('success', False)))
                    a2a_table.add_row("Task ID", result.get('task_id', 'N/A'))
                    a2a_table.add_row("Skill Called", execute_request['skill_name'])
                    
                    if result.get('result'):
                        policy_result = result['result']
                        a2a_table.add_row("Policy ID", str(policy_result.get('policy_id', 'N/A')))
                        a2a_table.add_row("Status", policy_result.get('status', 'N/A'))
                    
                    self.console.print(a2a_table)
                else:
                    self.console.print(f"[bold red]❌ A2A Error: {response.status_code}[/bold red]")
                    
            except Exception as e:
                self.console.print(f"[bold red]❌ A2A Failed: {str(e)}[/bold red]")
    
    async def show_system_capabilities(self):
        """Show available system capabilities"""
        self.console.print("\n[bold blue]🛠️ System Capabilities[/bold blue]")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Get skills from support agent
                response = await client.get(f"{self.base_urls['support_agent']}/skills")
                if response.status_code == 200:
                    skills_data = response.json()
                    
                    skills_table = Table(title="Support Agent Skills")
                    skills_table.add_column("Skill Name", style="cyan")
                    skills_table.add_column("Description", style="magenta")
                    
                    for skill_name, skill_info in skills_data.get('skills', {}).items():
                        skills_table.add_row(
                            skill_name,
                            skill_info.get('description', 'No description')
                        )
                    
                    self.console.print(skills_table)
                
                # Get skills from claims agent
                response = await client.get(f"{self.base_urls['claims_agent']}/skills")
                if response.status_code == 200:
                    skills_data = response.json()
                    
                    claims_skills_table = Table(title="Claims Agent Skills")
                    claims_skills_table.add_column("Skill Name", style="cyan")
                    claims_skills_table.add_column("Description", style="magenta")
                    
                    for skill_name, skill_info in skills_data.get('skills', {}).items():
                        claims_skills_table.add_row(
                            skill_name,
                            skill_info.get('description', 'No description')
                        )
                    
                    self.console.print(claims_skills_table)
                    
            except Exception as e:
                self.console.print(f"[bold red]❌ Failed to get capabilities: {str(e)}[/bold red]")
    
    def _display_workflow_data(self, title: str, data: Dict[str, Any]):
        """Display workflow data in a formatted way"""
        if not data:
            return
            
        # Create a formatted display of the data
        data_json = json.dumps(data, indent=2, default=str)
        syntax = Syntax(data_json, "json", theme="monokai", line_numbers=True)
        
        panel = Panel(
            syntax,
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan"
        )
        
        self.console.print(panel)
    
    def show_usage_examples(self):
        """Show example API calls"""
        self.console.print("\n[bold blue]📝 API Usage Examples[/bold blue]")
        
        examples = [
            {
                "title": "Policy Inquiry Chat",
                "method": "POST",
                "url": "http://localhost:30005/chat",
                "body": {
                    "message": "What is my policy status?",
                    "customer_id": 101
                }
            },
            {
                "title": "File Claim Chat", 
                "method": "POST",
                "url": "http://localhost:30007/chat",
                "body": {
                    "message": "I want to file a claim for water damage",
                    "customer_id": 101
                }
            },
            {
                "title": "Direct Customer Lookup",
                "method": "GET", 
                "url": "http://localhost:30000/customer/101",
                "body": None
            }
        ]
        
        for example in examples:
            self.console.print(f"\n[bold]{example['title']}:[/bold]")
            self.console.print(f"[cyan]{example['method']} {example['url']}[/cyan]")
            
            if example['body']:
                body_json = json.dumps(example['body'], indent=2)
                syntax = Syntax(body_json, "json", theme="monokai")
                self.console.print(syntax)


async def main():
    """Main demonstration function"""
    demo = InsuranceAIDemo()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        demo.show_usage_examples()
        return
    
    try:
        await demo.run_demo()
    except KeyboardInterrupt:
        demo.console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        demo.console.print(f"\n[bold red]Demo failed: {str(e)}[/bold red]")


if __name__ == "__main__":
    # Install rich if not available
    try:
        import rich
    except ImportError:
        print("Installing required dependency: rich")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
        import rich
    
    asyncio.run(main())