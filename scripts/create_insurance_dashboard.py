#!/usr/bin/env python3
"""
Create comprehensive insurance-specific Grafana dashboards
"""
import json
import subprocess
import time

def create_insurance_business_dashboard():
    """Create business metrics dashboard for insurance operations"""
    
    dashboard = {
        "id": None,
        "title": "Insurance Business Operations",
        "tags": ["insurance", "business", "kpis"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "Claims Processing Volume",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(workflow_executions_total{workflow_type=~\".*claim.*\"}[5m])",
                        "legendFormat": "Claims per minute - {{workflow_type}}"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                "yAxes": [
                    {"label": "Claims/min", "min": 0},
                    {"show": False}
                ]
            },
            {
                "id": 2, 
                "title": "Customer Inquiry Success Rate",
                "type": "singlestat",
                "targets": [
                    {
                        "expr": "rate(workflow_executions_total{status=\"success\"}[5m]) / rate(workflow_executions_total[5m]) * 100"
                    }
                ],
                "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
                "valueName": "current",
                "format": "percent",
                "thresholds": "80,95"
            },
            {
                "id": 3,
                "title": "Average Response Time",
                "type": "singlestat", 
                "targets": [
                    {
                        "expr": "avg(workflow_execution_duration_seconds)"
                    }
                ],
                "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0},
                "valueName": "current",
                "format": "s",
                "thresholds": "5,10"
            },
            {
                "id": 4,
                "title": "Agent Communication Flow",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(agent_requests_total[5m])",
                        "legendFormat": "{{source_agent}} → {{target_agent}}"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
            },
            {
                "id": 5,
                "title": "LLM Token Usage",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(llm_token_usage_total[5m])",
                        "legendFormat": "{{task_type}} - {{token_type}}"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
            },
            {
                "id": 6,
                "title": "Top Claims by Type", 
                "type": "table",
                "targets": [
                    {
                        "expr": "topk(5, sum by (claim_type) (workflow_executions_total{workflow_type=~\".*claim.*\"}))",
                        "format": "table"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
            }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "30s"
    }
    
    return dashboard

def create_insurance_technical_dashboard():
    """Create technical performance dashboard"""
    
    dashboard = {
        "id": None,
        "title": "Insurance System Performance",
        "tags": ["insurance", "technical", "performance"],
        "timezone": "browser", 
        "panels": [
            {
                "id": 1,
                "title": "Service Health Status",
                "type": "stat",
                "targets": [
                    {
                        "expr": "up{job=\"insurance-agents\"}",
                        "legendFormat": "{{instance}}"
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
                "title": "HTTP Request Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(http_requests_total[5m])",
                        "legendFormat": "{{method}} {{handler}} - {{status}}"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            {
                "id": 3,
                "title": "Response Times (95th percentile)",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "{{handler}}"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
            },
            {
                "id": 4,
                "title": "Error Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(http_requests_total{status=~\"4..|5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
                        "legendFormat": "Error rate %"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
            },
            {
                "id": 5,
                "title": "Memory Usage",
                "type": "graph",
                "targets": [
                    {
                        "expr": "process_resident_memory_bytes / 1024 / 1024",
                        "legendFormat": "{{instance}} Memory (MB)"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
            },
            {
                "id": 6,
                "title": "Active Connections",
                "type": "graph",
                "targets": [
                    {
                        "expr": "http_requests_currently_processing",
                        "legendFormat": "{{instance}} Active requests"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
            }
        ],
        "time": {"from": "now-1h", "to": "now"},
        "refresh": "10s"
    }
    
    return dashboard

def create_insurance_alerts_dashboard():
    """Create alerts and monitoring dashboard"""
    
    dashboard = {
        "id": None,
        "title": "Insurance System Alerts",
        "tags": ["insurance", "alerts", "monitoring"],
        "timezone": "browser",
        "panels": [
            {
                "id": 1,
                "title": "High Priority Alerts",
                "type": "alert-list",
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0}
            },
            {
                "id": 2,
                "title": "Failed Claims Processing",
                "type": "graph",
                "targets": [
                    {
                        "expr": "increase(workflow_executions_total{status=\"error\",workflow_type=~\".*claim.*\"}[5m])",
                        "legendFormat": "Failed claims - {{workflow_type}}"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "alert": {
                    "conditions": [
                        {
                            "query": {"queryType": "A", "refId": "A"},
                            "reducer": {"type": "last", "params": []},
                            "evaluator": {"params": [5], "type": "gt"}
                        }
                    ],
                    "executionErrorState": "alerting",
                    "frequency": "1m",
                    "handler": 1,
                    "name": "High failed claims rate",
                    "noDataState": "no_data"
                }
            },
            {
                "id": 3,
                "title": "Agent Response Time SLA",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(workflow_execution_duration_seconds_bucket[5m])) > 10",
                        "legendFormat": "Response time > 10s"
                    }
                ],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
            }
        ],
        "time": {"from": "now-6h", "to": "now"},
        "refresh": "1m"
    }
    
    return dashboard

def save_dashboard(dashboard, filename):
    """Save dashboard to file"""
    with open(f'/tmp/{filename}', 'w') as f:
        json.dump(dashboard, f, indent=2)
    print(f"✅ Dashboard saved to /tmp/{filename}")

def main():
    """Create all insurance dashboards"""
    
    print("🏢 Creating Insurance-Specific Grafana Dashboards")
    print("=" * 60)
    
    # Create business dashboard
    print("\n📊 Creating Business Operations Dashboard...")
    business_dashboard = create_insurance_business_dashboard()
    save_dashboard(business_dashboard, "insurance_business_dashboard.json")
    
    # Create technical dashboard  
    print("\n⚙️ Creating Technical Performance Dashboard...")
    technical_dashboard = create_insurance_technical_dashboard()
    save_dashboard(technical_dashboard, "insurance_technical_dashboard.json")
    
    # Create alerts dashboard
    print("\n🚨 Creating Alerts & Monitoring Dashboard...")
    alerts_dashboard = create_insurance_alerts_dashboard()
    save_dashboard(alerts_dashboard, "insurance_alerts_dashboard.json")
    
    print("\n🎯 Import Instructions:")
    print("1. Open Grafana at http://localhost:30030")
    print("2. Login with admin/admin123")
    print("3. Go to Dashboards > Import")
    print("4. Upload each JSON file:")
    print("   - insurance_business_dashboard.json")
    print("   - insurance_technical_dashboard.json") 
    print("   - insurance_alerts_dashboard.json")
    
    print("\n💡 Key Metrics to Monitor:")
    print("📈 Business Metrics:")
    print("   - Claims processing volume & success rate")
    print("   - Customer inquiry response times")
    print("   - Agent workflow effectiveness")
    
    print("🔧 Technical Metrics:")
    print("   - Service health & uptime")
    print("   - API response times & error rates")
    print("   - Resource utilization")
    
    print("🚨 Alert Scenarios:")
    print("   - High failed claims rate (>5 per 5 min)")
    print("   - Response time SLA breach (>10 seconds)")
    print("   - Service downtime")
    
    print("\n🚀 Next Steps:")
    print("1. Import dashboards into Grafana")
    print("2. Configure alert notifications (email/slack)")
    print("3. Set up monitoring playbooks")
    print("4. Generate more test data for visualization")
    
    print("\n🏁 All dashboards created successfully!")

if __name__ == "__main__":
    main() 