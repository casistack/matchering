#!/bin/bash

# Quick Test Results Checker for Matchering AI
# This script provides instant feedback on your test results

echo "🧪 MATCHERING AI - ENTERPRISE TEST ANALYSIS"
echo "=============================================="

# Check if backend is running
if pgrep -f "uvicorn.*app.main" > /dev/null; then
    echo "✅ Backend is running"
else
    echo "❌ Backend is not running - start it first!"
    exit 1
fi

# Check if logs directory exists
if [ ! -d "backend/logs" ]; then
    echo "❌ No logs directory found - run a test first!"
    exit 1
fi

echo ""
echo "📊 LOG FILES STATUS:"
echo "===================="

# Check log files
for log_file in backend/logs/*.log; do
    if [ -f "$log_file" ]; then
        basename_file=$(basename "$log_file")
        size=$(stat -c%s "$log_file" 2>/dev/null || stat -f%z "$log_file" 2>/dev/null)
        lines=$(wc -l < "$log_file")
        modified=$(stat -c %y "$log_file" 2>/dev/null || stat -f %Sm "$log_file" 2>/dev/null)
        
        echo "📁 $basename_file: $lines lines, ${size} bytes"
        echo "   Last modified: $modified"
    fi
done

echo ""
echo "🔍 QUALITY ANALYSIS:"
echo "==================="

# Run quality analysis
python3 view_test_logs.py --quality

echo ""
echo "📋 LATEST TEST SESSION:"
echo "======================"

# Show latest logs with key information
python3 view_test_logs.py --latest --events user_action ai_prediction matchering_config

echo ""
echo "💡 USAGE TIPS:"
echo "=============="
echo "• View all latest logs: ./view_test_logs.py --latest"
echo "• Check quality issues: ./view_test_logs.py --quality"
echo "• View specific events: ./view_test_logs.py --events user_action ai_prediction"
echo "• View raw JSON data: ./view_test_logs.py --latest --raw"

echo ""
echo "🚀 Ready for analysis! Upload a file and check results with this script."