#!/usr/bin/env python3
"""
Simple script to create and test Grafana dashboard queries
"""
import json
import subprocess
import time

def test_prometheus_query(query, description):
    """Test a Prometheus query"""
    print(f"\n🔍 Testing: {description}")
    print(f"Query: {query}")
    
    # Use curl to query Prometheus
    cmd = f'curl -s "http://localhost:30090/api/v1/query?query={query}"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('status') == 'success':
                results = data.get('data', {}).get('result', [])
                print(f"✅ Found {len(results)} results")
                for i, res in enumerate(results[:3]):
                    metric_labels = ', '.join([f"{k}={v}" for k, v in res.get('metric', {}).items()])
                    value = res.get('value', [None, 'N/A'])[1]
                    print(f"   └─ [{metric_labels}] = {value}")
            else:
                print(f"❌ Query failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP error: {result.stderr}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def create_sample_dashboard():
    """Create sample dashboard JSON for insurance agents"""
    
    dashboard = {
        "dashboard": {
            "id": None,
            "title": "Insurance Agents - Live Monitoring",
            "tags": ["insurance", "agents", "AI"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Service Health Status",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "up",
                            "legendFormat": "{{job}} - {{instance}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "fieldConfig": {
                        "defaults": {
                            "color": {"mode": "thresholds"},
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "green", "value": 1}
                                ]
                            }
                        }
                    }
                },
                {
                    "id": 2,
                    "title": "Available Metrics",
                    "type": "table",
                    "targets": [
                        {
                            "expr": "group by (__name__) ({__name__=~\".+\"})",
                            "legendFormat": "{{__name__}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                }
            ],
            "time": {"from": "now-1h", "to": "now"},
            "refresh": "10s"
        }
    }
    
    return dashboard

def main():
    """Main function to test metrics and create dashboard"""
    
    print("🚀 Insurance AI Observability Dashboard Creator")
    print("=" * 60)
    
    # Test basic connectivity
    print("\n📊 Testing Prometheus connectivity...")
    test_prometheus_query("up", "Service status")
    
    # Test existing custom metrics
    print("\n🤖 Testing Agent metrics...")
    test_prometheus_query("agent_health_status", "Agent health")
    test_prometheus_query("workflow_executions_total", "Workflow executions")
    test_prometheus_query("agent_requests_total", "Agent requests")
    test_prometheus_query("llm_request_duration_seconds", "LLM request duration")
    
    # Test HTTP metrics
    print("\n🌐 Testing HTTP metrics...")
    test_prometheus_query("http_requests_total", "HTTP requests")
    test_prometheus_query("http_request_duration_seconds", "HTTP duration")
    
    # Create dashboard
    print("\n📋 Creating sample dashboard...")
    dashboard = create_sample_dashboard()
    
    # Save dashboard JSON
    with open('/tmp/insurance_dashboard.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print("✅ Dashboard saved to /tmp/insurance_dashboard.json")
    print("\n📈 You can import this dashboard into Grafana:")
    print("   1. Open Grafana at http://localhost:30030")
    print("   2. Go to Dashboards > Import")
    print("   3. Upload the JSON file")
    
    print("\n🎯 Manual Prometheus queries to try:")
    queries = [
        "up",
        "rate(http_requests_total[5m])",
        "agent_health_status",
        "workflow_executions_total",
        "process_resident_memory_bytes"
    ]
    
    for query in queries:
        print(f"   - {query}")
    
    print("\n🏁 Dashboard creation complete!")

if __name__ == "__main__":
    main() 