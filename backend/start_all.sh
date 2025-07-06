#!/bin/bash

# Complete Matchering API Startup Script
# Starts both the API server and Celery workers

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Complete Matchering API System...${NC}"

# Start Celery workers first
echo -e "${YELLOW}📋 Step 1: Starting Celery workers...${NC}"
if [ -f "./start_workers.sh" ]; then
    chmod +x ./start_workers.sh
    ./start_workers.sh
else
    echo -e "${RED}❌ start_workers.sh not found${NC}"
    exit 1
fi

echo -e "${YELLOW}⏳ Waiting for workers to initialize...${NC}"
sleep 5

# Start the API server
echo -e "${YELLOW}🌐 Step 2: Starting API server...${NC}"
if [ -f "./start_backend.sh" ]; then
    chmod +x ./start_backend.sh
    
    # Check if we should run in background or foreground
    if [ "$1" = "--background" ] || [ "$1" = "-b" ]; then
        echo -e "${BLUE}🔄 Starting API server in background...${NC}"
        nohup ./start_backend.sh > logs/api_server.log 2>&1 &
        API_PID=$!
        echo $API_PID > /tmp/matchering_api.pid
        echo -e "${GREEN}✅ API server started with PID: $API_PID${NC}"
        echo -e "${BLUE}💡 View logs: ${NC}${YELLOW}tail -f logs/api_server.log${NC}"
        echo -e "${BLUE}💡 Stop all: ${NC}${YELLOW}./stop_all.sh${NC}"
    else
        echo -e "${BLUE}🔄 Starting API server in foreground...${NC}"
        echo -e "${YELLOW}💡 Use Ctrl+C to stop, or run with --background flag${NC}"
        ./start_backend.sh
    fi
else
    echo -e "${RED}❌ start_backend.sh not found${NC}"
    exit 1
fi