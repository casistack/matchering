#!/bin/bash
echo "🧪 Testing Hybrid AI Frontend Integration..."

# Test 1: Backend health
echo "1. Testing backend health..."
curl -s http://localhost:8000/health | jq .

# Test 2: Hybrid AI health
echo -e "\n2. Testing hybrid AI health..."
curl -s http://localhost:8000/api/v1/hybrid-ai/health | jq .

# Test 3: Available models
echo -e "\n3. Testing available models..."
curl -s http://localhost:8000/api/v1/hybrid-ai/available-models | jq .

echo -e "\n✅ Frontend integration tests complete!"
echo "Now test in browser:"
echo "1. Go to http://localhost:5173/"
echo "2. Upload an audio file"
echo "3. Switch to 'Hybrid' mode in Processing Settings"
echo "4. Click 'Start Processing'"