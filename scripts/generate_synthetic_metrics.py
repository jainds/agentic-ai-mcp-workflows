#!/usr/bin/env python3
"""
Generate synthetic metrics for the insurance agents to populate Grafana dashboards
"""

import random
import time
import requests
import json
from datetime import datetime

# Prometheus Pushgateway URL (if available) or direct metrics
PROMETHEUS_URL = "http://localhost:30090"

def generate_sample_metrics():
    """Generate sample metrics data"""
    agents = ["support-agent", "claims-agent", "customer-agent", "policy-agent", "claims-data-agent"]
    
    metrics = []
    
    for agent in agents:
        # Agent request rate
        request_rate = random.uniform(0.1, 2.0)
        metrics.append(f'agent_requests_total{{agent_name="{agent}"}} {request_rate}')
        
        # Agent response time
        response_time = random.uniform(0.5, 3.0)
        metrics.append(f'agent_response_duration_seconds{{agent_name="{agent}"}} {response_time}')
        
        # Agent success rate
        success_rate = random.uniform(0.85, 0.99)
        metrics.append(f'agent_success_rate{{agent_name="{agent}"}} {success_rate}')
        
        # LLM token usage
        token_usage = random.randint(100, 1000)
        metrics.append(f'llm_tokens_total{{agent_name="{agent}",token_type="completion"}} {token_usage}')
        
        # Agent health
        metrics.append(f'agent_health{{agent_name="{agent}"}} 1.0')
        
        # Workflow metrics
        workflows = ["general_support", "policy_inquiry", "claim_status", "billing_inquiry"]
        for workflow in workflows:
            count = random.randint(1, 10)
            duration = random.uniform(2.0, 8.0)
            metrics.append(f'workflow_executions_total{{agent_name="{agent}",workflow="{workflow}",status="success"}} {count}')
            metrics.append(f'workflow_duration_seconds{{agent_name="{agent}",workflow="{workflow}"}} {duration}')
    
    return "\n".join(metrics)

def create_metrics_configmap():
    """Create a ConfigMap with metrics data that can be scraped by Prometheus"""
    metrics_data = generate_sample_metrics()
    
    # Create a simple HTTP server that serves metrics
    server_code = f'''
import http.server
import socketserver
from http import HTTPStatus

class MetricsHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            
            metrics = """{metrics_data}"""
            self.wfile.write(metrics.encode())
        else:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()

if __name__ == "__main__":
    PORT = 8080
    with socketserver.TCPServer(("", PORT), MetricsHandler) as httpd:
        print(f"Serving metrics at http://localhost:{{PORT}}/metrics")
        httpd.serve_forever()
'''
    
    return server_code

def test_prometheus_connection():
    """Test if we can connect to Prometheus"""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/status/config", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🎯 Generating synthetic metrics for Insurance AI dashboard...")
    
    # Test Prometheus connection
    if not test_prometheus_connection():
        print(f"❌ Cannot connect to Prometheus at {PROMETHEUS_URL}")
        return
    
    print("✅ Connected to Prometheus")
    
    # Generate metrics
    metrics = generate_sample_metrics()
    print(f"📊 Generated {len(metrics.split())} metrics")
    
    # Since we can't directly push to Prometheus without pushgateway,
    # let's create a simple metrics server and update Prometheus config
    print("\n📋 Sample metrics generated:")
    print("=" * 50)
    print(metrics[:500] + "..." if len(metrics) > 500 else metrics)
    print("=" * 50)
    
    print("\n💡 To populate your Grafana dashboard:")
    print("1. The agents need /metrics endpoints working")
    print("2. Alternative: Use the generated metrics above for testing")
    print("3. Or wait for the agent deployments to fully restart")
    
    # Save metrics to file for testing
    with open("/tmp/sample_metrics.txt", "w") as f:
        f.write(metrics)
    print(f"\n💾 Metrics saved to /tmp/sample_metrics.txt")

if __name__ == "__main__":
    main() 