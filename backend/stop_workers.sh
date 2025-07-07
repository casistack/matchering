#!/bin/bash

# Celery Workers Stop Script for Matchering API
# Gracefully stops all Celery workers

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

echo -e "${BLUE}🛑 Stopping Matchering Celery Workers...${NC}"

# Check if virtual environment is already activated
if [ -z "$VIRTUAL_ENV" ]; then
    # Not activated, check if virtual environment exists
    if [ -d "../.venv" ]; then
        # Virtual environment is in parent directory (project root)
        source ../.venv/bin/activate
    elif [ -d ".venv" ]; then
        # Virtual environment is in current directory
        source .venv/bin/activate
    fi
    # Note: We don't exit if no venv found - we can still kill processes
fi

# Try graceful shutdown first
echo -e "${YELLOW}📋 Attempting graceful worker shutdown...${NC}"
if command -v celery >/dev/null 2>&1; then
    celery -A app.core.celery_app control shutdown 2>/dev/null || echo "Celery control command not available"
fi

# Wait a moment for graceful shutdown
sleep 3

# Force kill any remaining workers
echo -e "${YELLOW}🔄 Force stopping any remaining workers...${NC}"
pkill -f "celery.*worker" 2>/dev/null || true

# Clean up PID files
echo -e "${YELLOW}🧹 Cleaning up PID files...${NC}"
rm -f /tmp/celery_*.pid

# Wait a moment
sleep 2

# Check if any workers are still running
if pgrep -f "celery.*worker" >/dev/null; then
    echo -e "${RED}⚠️ Some workers may still be running. Force killing...${NC}"
    pkill -9 -f "celery.*worker" 2>/dev/null || true
    sleep 1
fi

# Final check
if ! pgrep -f "celery.*worker" >/dev/null; then
    echo -e "${GREEN}✅ All Celery workers stopped successfully!${NC}"
else
    echo -e "${RED}❌ Some workers may still be running. Please check manually:${NC}"
    echo -e "${YELLOW}ps aux | grep celery${NC}"
fi

echo -e "${BLUE}🎉 Worker shutdown complete!${NC}"