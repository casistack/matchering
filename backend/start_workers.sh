#!/bin/bash

# Celery Workers Startup Script for Matchering API
# Starts Celery workers for audio processing tasks

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

echo -e "${BLUE}🚀 Starting Matchering Celery Workers...${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run setup first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source .venv/bin/activate

# Check if Redis is running
echo -e "${YELLOW}🔍 Checking Redis connection...${NC}"
if ! python -c "import redis; redis.Redis().ping()" 2>/dev/null; then
    echo -e "${RED}❌ Redis is not running or not accessible.${NC}"
    echo -e "${YELLOW}💡 Please start Redis first:${NC}"
    echo -e "   ${BLUE}sudo systemctl start redis${NC}"
    echo -e "   ${BLUE}# or ${NC}"
    echo -e "   ${BLUE}docker run -d -p 6379:6379 redis:alpine${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Redis connection successful${NC}"

# Stop any existing workers
echo -e "${YELLOW}🛑 Stopping any existing workers...${NC}"
pkill -f "celery.*worker" 2>/dev/null || true
sleep 2

# Start Celery workers with proper configuration
echo -e "${YELLOW}🔄 Starting Celery workers...${NC}"

# Start workers for different queues
echo -e "${BLUE}📋 Starting audio processing workers...${NC}"
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=audio_processing \
    --hostname=audio_worker@%h \
    --pidfile=/tmp/celery_audio_%i.pid \
    --logfile=logs/celery_audio.log \
    --detach

echo -e "${BLUE}🔬 Starting audio analysis workers...${NC}"
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=audio_analysis \
    --hostname=analysis_worker@%h \
    --pidfile=/tmp/celery_analysis_%i.pid \
    --logfile=logs/celery_analysis.log \
    --detach

echo -e "${BLUE}📁 Starting file operations workers...${NC}"
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=file_operations \
    --hostname=file_worker@%h \
    --pidfile=/tmp/celery_file_%i.pid \
    --logfile=logs/celery_file.log \
    --detach

echo -e "${BLUE}⚙️ Starting default queue workers...${NC}"
celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=matchering_default \
    --hostname=default_worker@%h \
    --pidfile=/tmp/celery_default_%i.pid \
    --logfile=logs/celery_default.log \
    --detach

# Wait a moment for workers to start
sleep 3

# Check worker status
echo -e "${YELLOW}📊 Checking worker status...${NC}"
if celery -A app.core.celery_app inspect active >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Celery workers started successfully!${NC}"
    
    # Show worker statistics
    echo -e "${BLUE}📈 Worker Statistics:${NC}"
    celery -A app.core.celery_app inspect stats 2>/dev/null | head -20 || echo "Stats temporarily unavailable"
else
    echo -e "${YELLOW}⚠️ Workers started but may need a moment to fully initialize${NC}"
fi

echo -e "${GREEN}🎉 Celery workers startup complete!${NC}"
echo -e "${BLUE}💡 To monitor workers: ${NC}${YELLOW}celery -A app.core.celery_app inspect active${NC}"
echo -e "${BLUE}💡 To stop workers: ${NC}${YELLOW}./stop_workers.sh${NC}"
echo -e "${BLUE}💡 View logs in: ${NC}${YELLOW}logs/celery_*.log${NC}"