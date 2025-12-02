#!/bin/bash
# Test script for the user-services API endpoint

# Configuration
BASE_URL="${1:-http://localhost:8000}"
API_KEY="${2:-your-api-key-here}"

echo "Testing endpoint: ${BASE_URL}/subscriptions/api/user-services/"
echo "=========================================="

# Test 1: Without authentication (should fail)
echo ""
echo "Test 1: Request without authentication"
curl -v "${BASE_URL}/subscriptions/api/user-services/" 2>&1 | grep -E "HTTP|error|401|403|404"

# Test 2: With API key authentication
echo ""
echo "Test 2: Request with API key"
curl -v \
  -H "Authorization: Api-Key ${API_KEY}" \
  "${BASE_URL}/subscriptions/api/user-services/" 2>&1 | grep -E "HTTP|error|401|403|404"

# Test 3: With X-Api-Key header
echo ""
echo "Test 3: Request with X-Api-Key header"
curl -v \
  -H "X-Api-Key: ${API_KEY}" \
  "${BASE_URL}/subscriptions/api/user-services/" 2>&1 | grep -E "HTTP|error|401|403|404"

echo ""
echo "=========================================="
echo "If you see 404 errors:"
echo "1. Check that the server is running"
echo "2. Verify the URL path is correct"
echo "3. Check Django URL configuration"
echo ""
echo "If you see 401/403 errors:"
echo "1. Verify your API key is correct"
echo "2. Make sure the API key hasn't been revoked"
echo "3. Check that the API key belongs to the user"

