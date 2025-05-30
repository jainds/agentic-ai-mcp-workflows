#!/usr/bin/env python3
"""
Script to start all FastMCP-enabled insurance services.
Handles port conflicts and service coordination.
"""

import subprocess
import sys
import os
import time
import signal
from typing import List, Dict

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from services.shared.port_utils import get_service_port

class ServiceManager:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.service_ports: Dict[str, int] = {}  # Store actual assigned ports
        self.services = {
            "user": {
                "path": "services/user_service/main.py",
                "default_port": 8000,
                "name": "User Service"
            },
            "claims": {
                "path": "services/claims_service/main.py", 
                "default_port": 8001,
                "name": "Claims Service"
            },
            "policy": {
                "path": "services/policy_service/main.py",
                "default_port": 8002,
                "name": "Policy Service"
            },
            "analytics": {
                "path": "services/analytics_service/main.py",
                "default_port": 8003,
                "name": "Analytics Service"
            }
        }
        
    def start_service(self, service_name: str, service_config: Dict) -> subprocess.Popen:
        """Start a single service"""
        print(f"Starting {service_config['name']}...")
        
        # Find available port
        try:
            port = get_service_port(service_name, service_config['default_port'])
            print(f"  {service_config['name']} will use port {port}")
            self.service_ports[service_name] = port  # Store the actual port
        except Exception as e:
            print(f"  Error finding port for {service_name}: {e}")
            port = service_config['default_port']
            self.service_ports[service_name] = port
        
        # Set environment variables
        env = os.environ.copy()
        env[f"{service_name.upper()}_SERVICE_PORT"] = str(port)
        env[f"{service_name.upper()}_SERVICE_HOST"] = "0.0.0.0"
        
        # Start the service
        try:
            process = subprocess.Popen(
                [sys.executable, service_config['path']],
                cwd=project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            print(f"  {service_config['name']} started with PID {process.pid}")
            return process
            
        except Exception as e:
            print(f"  Failed to start {service_config['name']}: {e}")
            return None
    
    def start_all_services(self):
        """Start all services"""
        print("Starting FastMCP Insurance Services...")
        print("=" * 50)
        
        for service_name, service_config in self.services.items():
            process = self.start_service(service_name, service_config)
            if process:
                self.processes.append(process)
                time.sleep(2)  # Give service time to start
        
        print("\n" + "=" * 50)
        print(f"Started {len(self.processes)} services successfully")
        
        if self.processes:
            print("\nService URLs:")
            for i, (service_name, service_config) in enumerate(self.services.items()):
                if i < len(self.processes):
                    port = self.service_ports[service_name]
                    print(f"  {service_config['name']}: http://localhost:{port}")
            
            print("\nPress Ctrl+C to stop all services")
    
    def monitor_services(self):
        """Monitor running services"""
        try:
            while True:
                time.sleep(1)
                # Check if any process has died
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        service_name = list(self.services.keys())[i]
                        print(f"\nWarning: {self.services[service_name]['name']} has stopped")
        except KeyboardInterrupt:
            print("\nShutting down services...")
            self.stop_all_services()
    
    def stop_all_services(self):
        """Stop all running services"""
        for i, process in enumerate(self.processes):
            if process.poll() is None:  # Process is still running
                service_name = list(self.services.keys())[i]
                print(f"Stopping {self.services[service_name]['name']}...")
                
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"  Force killing {self.services[service_name]['name']}...")
                    process.kill()
                except Exception as e:
                    print(f"  Error stopping {self.services[service_name]['name']}: {e}")
        
        print("All services stopped.")

def main():
    manager = ServiceManager()
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\nReceived shutdown signal...")
        manager.stop_all_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start all services
    manager.start_all_services()
    
    # Monitor services
    manager.monitor_services()

if __name__ == "__main__":
    main() 