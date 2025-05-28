#!/usr/bin/env python3
"""
Test script to validate Prometheus metrics collection
"""
import requests
import json
import time
from datetime import datetime

def test_prometheus_metrics():
    """Test various Prometheus metrics queries"""
    
    prometheus_url = "http://localhost:30090"
    
    # Test queries for our custom metrics
    queries = [
        # Agent Communication Metrics
        ("agent_requests_total", "Total agent requests"),
        ("rate(agent_requests_total[5m])", "Agent request rate (5m)"),
        
        # LLM Metrics
        ("llm_request_duration_seconds", "LLM request duration"),
        ("llm_token_usage_total", "LLM token usage"),
        
        # Workflow Metrics
        ("workflow_executions_total", "Workflow executions"),
        ("agent_health_status", "Agent health status"),
        
        # HTTP Metrics (from FastAPI)
        ("http_requests_total", "HTTP requests total"),
        ("http_request_duration_seconds", "HTTP request duration"),
        
        # System Metrics
        ("up", "Service up status"),
        ("process_resident_memory_bytes", "Memory usage")
    ]
    
    print(f"🔍 Testing Prometheus at {prometheus_url}")
    print("=" * 60)
    
    for query, description in queries:
        try:
            response = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": query},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get('data', {}).get('result', []))
                
                if result_count > 0:
                    print(f"✅ {description}: {result_count} metrics found")
                    
                    # Show sample values
                    for i, result in enumerate(data['data']['result'][:3]):
                        metric = result.get('metric', {})
                        value = result.get('value', [None, 'N/A'])[1]
                        labels = ', '.join([f"{k}={v}" for k, v in metric.items()])
                        print(f"   └─ [{labels}] = {value}")
                        
                        if i >= 2:  # Show max 3 samples
                            break
                else:
                    print(f"⚠️  {description}: No data found")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: Error - {str(e)}")
        
        print()
    
    # Test if targets are being scraped
    print("🎯 Checking Prometheus targets...")
    try:
        response = requests.get(f"{prometheus_url}/api/v1/targets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            targets = data.get('data', {}).get('activeTargets', [])
            
            print(f"Found {len(targets)} active targets:")
            for target in targets:
                job = target.get('labels', {}).get('job', 'unknown')
                health = target.get('health', 'unknown')
                endpoint = target.get('scrapeUrl', 'unknown')
                print(f"   └─ {job}: {health} ({endpoint})")
        else:
            print(f"❌ Failed to get targets: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to get targets: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting Prometheus metrics test at {datetime.now()}")
    test_prometheus_metrics()
    print("🏁 Test completed!") 