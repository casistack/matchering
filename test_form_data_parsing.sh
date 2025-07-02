#!/bin/bash

# Test script to verify form data parsing for hybrid AI endpoint
# This script tests different user settings to ensure they're properly parsed

echo "========================================="
echo "Testing Hybrid AI Form Data Parsing"
echo "========================================="

# Test 1: High intensity, bright EQ, preserve dynamics false
echo -e "\n[TEST 1] High intensity, bright EQ, no dynamics preservation"
echo "Expected: intensity_level=high, eq_style=bright, preserve_dynamics=false"
echo "Sending request..."

curl -X POST "http://localhost:8000/api/v1/hybrid-ai/process-hybrid" \
  -F "file=@Respek Ma Craft.wav" \
  -F "intensity_level=high" \
  -F "eq_style=bright" \
  -F "preserve_dynamics=false" \
  -F "target_loudness_lufs=-12.0" \
  -F "processing_mode=hybrid" \
  -F "model_preference=auto" \
  -s | jq '.'

echo -e "\n[CHECK] Check logs for received parameters..."
tail -n 20 backend/logs/application.log | grep "Received form parameters"

# Test 2: Low intensity, warm EQ, preserve dynamics true
echo -e "\n\n[TEST 2] Low intensity, warm EQ, preserve dynamics"
echo "Expected: intensity_level=low, eq_style=warm, preserve_dynamics=true"
echo "Sending request..."

curl -X POST "http://localhost:8000/api/v1/hybrid-ai/process-hybrid" \
  -F "file=@Respek Ma Craft.wav" \
  -F "intensity_level=low" \
  -F "eq_style=warm" \
  -F "preserve_dynamics=true" \
  -F "target_loudness_lufs=-18.0" \
  -F "processing_mode=hybrid" \
  -F "model_preference=auto" \
  -s | jq '.'

echo -e "\n[CHECK] Check logs for received parameters..."
tail -n 20 backend/logs/application.log | grep "Received form parameters"

# Test 3: Custom settings - medium intensity, auto EQ
echo -e "\n\n[TEST 3] Medium intensity, auto EQ"
echo "Expected: intensity_level=medium, eq_style=auto, preserve_dynamics=true"
echo "Sending request..."

curl -X POST "http://localhost:8000/api/v1/hybrid-ai/process-hybrid" \
  -F "file=@Respek Ma Craft.wav" \
  -F "intensity_level=medium" \
  -F "eq_style=auto" \
  -F "preserve_dynamics=true" \
  -F "target_loudness_lufs=-14.0" \
  -F "processing_mode=hybrid" \
  -F "model_preference=auto" \
  -s | jq '.'

echo -e "\n[CHECK] Check logs for received parameters..."
tail -n 20 backend/logs/application.log | grep "Received form parameters"

echo -e "\n\n========================================="
echo "Test Complete - Check Enterprise Logs"
echo "========================================="
echo "Run: ./check_test_results.sh [job_id] to see full processing details"
echo ""
echo "Compare the 'Expected' values above with the logged 'user_settings' in:"
echo "  - backend/logs/application.log"
echo "  - backend/logs/processing.log"