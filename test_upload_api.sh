#!/bin/bash

# Job Listings Upload API Test Script
# Make sure Rails server is running on localhost:3000

echo "🚀 Testing Job Listings Upload API"
echo "=================================="

BASE_URL="http://localhost:4200"

echo ""
echo "1. Testing Single Job Upload via API..."
echo "----------------------------------------"
curl -X POST $BASE_URL/api/upload_job_listings/upload \
  -H 'Content-Type: application/json' \
  -d @single_job_test.json

echo ""
echo ""
echo "2. Testing Batch Job Upload via API..."
echo "---------------------------------------"
curl -X POST $BASE_URL/api/upload_job_listings/batch_upload \
  -H 'Content-Type: application/json' \
  -d @batch_jobs_test.json

echo ""
echo ""
echo "3. Testing Existing API Job Listings Create..."
echo "----------------------------------------------"
curl -X POST $BASE_URL/api/job_listings \
  -H 'Content-Type: application/json' \
  -d @single_job_test.json

echo ""
echo ""
echo "4. Fetching All Job Listings..."
echo "-------------------------------"
curl -X GET $BASE_URL/api/job_listings

echo ""
echo ""
echo "✅ API Testing Complete!"
echo ""
echo "Available endpoints:"
echo "- POST /api/upload_job_listings/upload (single job)"
echo "- POST /api/upload_job_listings/batch_upload (multiple jobs)"
echo "- POST /api/job_listings (existing create endpoint)"
echo "- GET /api/job_listings (list all jobs)"
echo ""
echo "To test manually:"
echo "curl -X POST $BASE_URL/api/upload_job_listings/upload -H 'Content-Type: application/json' -d @single_job_test.json"