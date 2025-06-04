#!/bin/bash

# Test Session Fix
echo "🧪 Testing Session Data Fix"
echo "============================"

echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "🔍 Testing valid customers with session data:"
echo ""

# Test CUST-001
echo "📋 Test 1: CUST-001"
response1=$(curl -s -X POST http://localhost:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What are my policies?", "session_data": {"customer_id": "CUST-001", "authenticated": true}}')
echo "Response: $response1"
echo ""

# Test user_003
echo "📋 Test 2: user_003"
response2=$(curl -s -X POST http://localhost:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Show me my coverage", "session_data": {"customer_id": "user_003", "authenticated": true}}')
echo "Response: $response2"
echo ""

# Test invalid customer
echo "📋 Test 3: Invalid customer"
response3=$(curl -s -X POST http://localhost:8003/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What are my policies?", "session_data": {"customer_id": "INVALID", "authenticated": true}}')
echo "Response: $response3"
echo ""

echo "✅ Session fix tests completed!"
echo ""
echo "🔍 What to look for:"
echo "   ✓ Valid customers should get policy details"
echo "   ✓ Invalid customers should get appropriate error messages"
echo "   ✓ No more 'I'm having trouble retrieving your policy information'" 