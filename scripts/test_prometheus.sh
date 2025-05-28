#!/bin/bash

# Test script to validate Prometheus metrics collection
PROMETHEUS_URL="http://localhost:30090"

echo "🔍 Testing Prometheus at $PROMETHEUS_URL"
echo "============================================================"

# Function to test a Prometheus query
test_query() {
    local query="$1"
    local description="$2"
    
    echo "Testing: $description"
    echo "Query: $query"
    
    response=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$(echo $query | sed 's/ /%20/g')")
    
    if echo "$response" | grep -q '"status":"success"'; then
        result_count=$(echo "$response" | grep -o '"result":\[.*\]' | grep -o '\[.*\]' | grep -o ',' | wc -l)
        result_count=$((result_count + 1))
        
        if [ "$result_count" -gt 0 ]; then
            echo "✅ Found $result_count metrics"
            # Show first few results
            echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    results = data.get('data', {}).get('result', [])
    for i, result in enumerate(results[:3]):
        metric = result.get('metric', {})
        value = result.get('value', [None, 'N/A'])[1]
        labels = ', '.join([f'{k}={v}' for k, v in metric.items()])
        print(f'   └─ [{labels}] = {value}')
except:
    pass
"
        else
            echo "⚠️  No data found"
        fi
    else
        echo "❌ Query failed"
        echo "$response" | head -1
    fi
    echo
}

# Test basic connectivity
echo "🌐 Testing Prometheus connectivity..."
if curl -s "$PROMETHEUS_URL/-/healthy" > /dev/null; then
    echo "✅ Prometheus is reachable"
else
    echo "❌ Cannot reach Prometheus"
    exit 1
fi
echo

# Test various metrics
test_query "up" "Service up status"
test_query "agent_requests_total" "Agent requests total"
test_query "rate(agent_requests_total[5m])" "Agent request rate"
test_query "llm_request_duration_seconds" "LLM request duration"
test_query "workflow_executions_total" "Workflow executions"
test_query "agent_health_status" "Agent health status"
test_query "http_requests_total" "HTTP requests total"

# Check targets
echo "🎯 Checking Prometheus targets..."
targets_response=$(curl -s "$PROMETHEUS_URL/api/v1/targets")
if echo "$targets_response" | grep -q '"status":"success"'; then
    echo "✅ Targets endpoint reachable"
    echo "$targets_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    targets = data.get('data', {}).get('activeTargets', [])
    print(f'Found {len(targets)} active targets:')
    for target in targets:
        job = target.get('labels', {}).get('job', 'unknown')
        health = target.get('health', 'unknown')
        endpoint = target.get('scrapeUrl', 'unknown')
        print(f'   └─ {job}: {health} ({endpoint})')
except Exception as e:
    print(f'Error parsing targets: {e}')
"
else
    echo "❌ Failed to get targets"
fi

echo
echo "�� Test completed!" 