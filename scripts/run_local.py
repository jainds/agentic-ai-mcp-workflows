#!/usr/bin/env python3
"""
Local development script to run insurance AI PoC services
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class LocalRunner:
    """Manages local development environment"""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.services = {
            'customer-service': {
                'module': 'services.customer.app',
                'port': 8000,
                'env': {'CUSTOMER_SERVICE_PORT': '8000'}
            },
            'policy-service': {
                'module': 'services.policy.app', 
                'port': 8001,
                'env': {'POLICY_SERVICE_PORT': '8001'}
            },
            'claims-service': {
                'module': 'services.claims.app',
                'port': 8002,
                'env': {'CLAIMS_SERVICE_PORT': '8002'}
            },
            'customer-agent': {
                'module': 'agents.technical.customer_agent',
                'port': 8010,
                'env': {
                    'CUSTOMER_AGENT_PORT': '8010',
                    'CUSTOMER_SERVICE_URL': 'http://localhost:8000'
                }
            },
            'policy-agent': {
                'module': 'agents.technical.policy_agent',
                'port': 8011,
                'env': {
                    'POLICY_AGENT_PORT': '8011',
                    'POLICY_SERVICE_URL': 'http://localhost:8001'
                }
            },
            'claims-agent': {
                'module': 'agents.technical.claims_agent',
                'port': 8012,
                'env': {
                    'CLAIMS_DATA_AGENT_PORT': '8012',
                    'CLAIMS_SERVICE_URL': 'http://localhost:8002'
                }
            },
            'support-agent': {
                'module': 'agents.domain.support_agent',
                'port': 8005,
                'env': {
                    'SUPPORT_AGENT_PORT': '8005',
                    'CUSTOMER_AGENT_URL': 'http://localhost:8010',
                    'POLICY_AGENT_URL': 'http://localhost:8011',
                    'CLAIMS_DATA_AGENT_URL': 'http://localhost:8012'
                }
            }
        }
    
    def setup_environment(self):
        """Setup environment variables"""
        # Load .env file if it exists
        env_file = project_root / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Set default environment variables
        default_env = {
            'PYTHONPATH': str(project_root),
            'LOG_LEVEL': 'INFO',
            'DEBUG': 'true'
        }
        
        for key, value in default_env.items():
            if key not in os.environ:
                os.environ[key] = value
    
    def start_service(self, name: str, config: Dict[str, Any]):
        """Start a single service"""
        print(f"Starting {name} on port {config['port']}...")
        
        # Set up environment for this service
        env = os.environ.copy()
        env.update(config.get('env', {}))
        
        # Start the service
        cmd = [sys.executable, '-m', config['module']]
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.processes.append(process)
            print(f"✓ {name} started (PID: {process.pid})")
            return process
            
        except Exception as e:
            print(f"✗ Failed to start {name}: {e}")
            return None
    
    def wait_for_service(self, port: int, timeout: int = 30) -> bool:
        """Wait for service to be ready"""
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        
        return False
    
    def start_all_services(self):
        """Start all services in dependency order"""
        print("Starting Insurance AI PoC services...")
        print("=" * 50)
        
        self.setup_environment()
        
        # Start backend services first
        backend_services = ['customer-service', 'policy-service', 'claims-service']
        for service_name in backend_services:
            if service_name in self.services:
                self.start_service(service_name, self.services[service_name])
                # Wait a bit for service to start
                time.sleep(2)
        
        print("\nWaiting for backend services to be ready...")
        for service_name in backend_services:
            port = self.services[service_name]['port']
            if self.wait_for_service(port):
                print(f"✓ {service_name} is ready")
            else:
                print(f"✗ {service_name} failed to start properly")
        
        # Start technical agents
        technical_agents = ['customer-agent', 'policy-agent', 'claims-agent']
        print("\nStarting technical agents...")
        for agent_name in technical_agents:
            if agent_name in self.services:
                self.start_service(agent_name, self.services[agent_name])
                time.sleep(1)
        
        # Wait for technical agents
        print("\nWaiting for technical agents to be ready...")
        for agent_name in technical_agents:
            port = self.services[agent_name]['port']
            if self.wait_for_service(port):
                print(f"✓ {agent_name} is ready")
            else:
                print(f"✗ {agent_name} failed to start properly")
        
        # Start domain agents
        domain_agents = ['support-agent']
        print("\nStarting domain agents...")
        for agent_name in domain_agents:
            if agent_name in self.services:
                self.start_service(agent_name, self.services[agent_name])
                time.sleep(1)
        
        # Wait for domain agents
        print("\nWaiting for domain agents to be ready...")
        for agent_name in domain_agents:
            port = self.services[agent_name]['port']
            if self.wait_for_service(port):
                print(f"✓ {agent_name} is ready")
            else:
                print(f"✗ {agent_name} failed to start properly")
        
        print("\n" + "=" * 50)
        print("All services started!")
        print("\nService URLs:")
        for name, config in self.services.items():
            print(f"  {name}: http://localhost:{config['port']}")
        
        print("\nExample API calls:")
        print("  curl http://localhost:8000/customer/101")
        print("  curl http://localhost:8001/policy/202/status")
        print("  curl http://localhost:8002/claim/1001/status")
        print("  curl -X POST http://localhost:8005/chat -H 'Content-Type: application/json' -d '{\"message\": \"What is my policy status?\", \"customer_id\": 101}'")
        print("\nPress Ctrl+C to stop all services")
    
    def stop_all_services(self):
        """Stop all running services"""
        print("\nStopping all services...")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✓ Stopped process {process.pid}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"✓ Killed process {process.pid}")
            except Exception as e:
                print(f"✗ Error stopping process {process.pid}: {e}")
        
        self.processes.clear()
        print("All services stopped")
    
    def run(self):
        """Run the local development environment"""
        def signal_handler(signum, frame):
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            self.start_all_services()
            
            # Keep the main process alive
            while True:
                time.sleep(1)
                
                # Check if any process has died
                for process in self.processes[:]:
                    if process.poll() is not None:
                        print(f"Process {process.pid} has stopped")
                        self.processes.remove(process)
                
                if not self.processes:
                    print("All processes have stopped")
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all_services()


def run_tests():
    """Run the test suite"""
    print("Running test suite...")
    
    # Run unit tests
    test_cmd = [sys.executable, '-m', 'pytest', 'tests/', '-v']
    result = subprocess.run(test_cmd, cwd=project_root)
    
    return result.returncode == 0


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Insurance AI PoC Local Runner')
    parser.add_argument('command', choices=['start', 'test'], 
                       help='Command to execute')
    parser.add_argument('--service', help='Start only specific service')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        success = run_tests()
        sys.exit(0 if success else 1)
    
    elif args.command == 'start':
        runner = LocalRunner()
        
        if args.service:
            if args.service in runner.services:
                runner.setup_environment()
                runner.start_service(args.service, runner.services[args.service])
                print(f"Started {args.service}. Press Ctrl+C to stop.")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    runner.stop_all_services()
            else:
                print(f"Unknown service: {args.service}")
                print(f"Available services: {', '.join(runner.services.keys())}")
                sys.exit(1)
        else:
            runner.run()


if __name__ == '__main__':
    main()