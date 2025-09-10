#!/bin/bash

# Comprehensive API Test Script
# Tests all API endpoints with raw input/output logging

LOG_FILE="api_test_results.log"
SESSION_ID="d8317886-fe21-4e2e-b3a3-f36c1b6691d9"

echo "=== COMPREHENSIVE API TEST SUITE ===" | tee $LOG_FILE
echo "Test Date: $(date)" | tee -a $LOG_FILE
echo "Session ID: $SESSION_ID" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Function to log and execute curl commands
test_endpoint() {
    local description="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    echo "----------------------------------------" | tee -a $LOG_FILE
    echo "TEST: $description" | tee -a $LOG_FILE
    echo "METHOD: $method" | tee -a $LOG_FILE
    echo "ENDPOINT: $endpoint" | tee -a $LOG_FILE
    
    if [ -n "$data" ]; then
        echo "INPUT DATA: $data" | tee -a $LOG_FILE
        echo "CURL COMMAND: curl -X $method http://localhost:8000$endpoint -H 'Content-Type: application/json' -d '$data'" | tee -a $LOG_FILE
        response=$(curl -s -X $method "http://localhost:8000$endpoint" -H "Content-Type: application/json" -d "$data")
    else
        echo "CURL COMMAND: curl -X $method http://localhost:8000$endpoint" | tee -a $LOG_FILE
        response=$(curl -s -X $method "http://localhost:8000$endpoint")
    fi
    
    echo "RESPONSE:" | tee -a $LOG_FILE
    echo "$response" | jq . 2>/dev/null || echo "$response" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
}

# 1. Health Check
test_endpoint "Health Check" "GET" "/health" ""

# 2. Get Session Details
test_endpoint "Get Session Details" "GET" "/api/sessions/$SESSION_ID" ""

# 3. List All Sessions
test_endpoint "List All Sessions" "GET" "/api/sessions" ""

# 4. Get Codes for Session
test_endpoint "Get Codes for Session" "GET" "/api/sessions/$SESSION_ID/codes" ""

# 5. Count Codes
echo "----------------------------------------" | tee -a $LOG_FILE
echo "CODE COUNT TEST" | tee -a $LOG_FILE
code_count=$(curl -s "http://localhost:8000/api/sessions/$SESSION_ID/codes" | jq '. | length')
echo "Total codes extracted: $code_count" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 6. Get Quotes
test_endpoint "Get Quotes for Session" "GET" "/api/sessions/$SESSION_ID/quotes" ""

# 7. Get Interviews
test_endpoint "Get Interviews for Session" "GET" "/api/sessions/$SESSION_ID/interviews" ""

# 8. Analytics - Network Hubs
test_endpoint "Analytics: Network Hubs" "GET" "/api/analytics/sessions/$SESSION_ID/network-hubs?limit=10" ""

# 9. Analytics - Causal Chains
test_endpoint "Analytics: Causal Chains" "GET" "/api/analytics/sessions/$SESSION_ID/causal-chains" ""

# 10. Analytics - Conflicts
test_endpoint "Analytics: Conflicts" "GET" "/api/analytics/sessions/$SESSION_ID/conflicts" ""

# 11. Analytics - Clusters
test_endpoint "Analytics: Clusters" "GET" "/api/analytics/sessions/$SESSION_ID/clusters" ""

# 12. Analytics - Summary
test_endpoint "Analytics: Summary" "GET" "/api/analytics/sessions/$SESSION_ID/summary" ""

# 13. Export CSV
echo "----------------------------------------" | tee -a $LOG_FILE
echo "TEST: Export Results as CSV" | tee -a $LOG_FILE
echo "ENDPOINT: /api/sessions/$SESSION_ID/export?format=csv" | tee -a $LOG_FILE
csv_response=$(curl -s "http://localhost:8000/api/sessions/$SESSION_ID/export?format=csv")
echo "CSV Preview (first 5 lines):" | tee -a $LOG_FILE
echo "$csv_response" | head -5 | tee -a $LOG_FILE
echo "Total CSV lines: $(echo "$csv_response" | wc -l)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 14. Export JSON
echo "----------------------------------------" | tee -a $LOG_FILE
echo "TEST: Export Results as JSON" | tee -a $LOG_FILE
echo "ENDPOINT: /api/sessions/$SESSION_ID/export?format=json" | tee -a $LOG_FILE
json_export=$(curl -s "http://localhost:8000/api/sessions/$SESSION_ID/export?format=json")
echo "JSON Export Preview:" | tee -a $LOG_FILE
echo "$json_export" | jq '.codes[0:2]' 2>/dev/null | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# 15. Test Creating a New Session
test_endpoint "Create New Test Session" "POST" "/api/sessions" '{"name": "API Test Session"}'

# 16. Get Memos
test_endpoint "Get Memos for Session" "GET" "/api/sessions/$SESSION_ID/memos" ""

# 17. Create a Test Memo
test_endpoint "Create Test Memo" "POST" "/api/sessions/$SESSION_ID/memos" '{"title": "Test Memo", "content": "This is a test memo created via API"}'

# Summary
echo "========================================" | tee -a $LOG_FILE
echo "TEST SUITE COMPLETE" | tee -a $LOG_FILE
echo "Results saved to: $LOG_FILE" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Check for errors
echo "ERROR CHECK:" | tee -a $LOG_FILE
grep -i "error\|failed\|500\|404" $LOG_FILE | tee -a $LOG_FILE || echo "No errors detected" | tee -a $LOG_FILE