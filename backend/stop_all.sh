#!/bash

# Complete Matchering API Shutdown Script
# Stops both the API server and Celery workers

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

echo -e "${BLUE}🛑 Stopping Complete Matchering API System...${NC}"

# Stop API server
echo -e "${YELLOW}🌐 Step 1: Stopping API server...${NC}"
if [ -f "/tmp/matchering_api.pid" ]; then
    API_PID=$(cat /tmp/matchering_api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        echo -e "${YELLOW}📋 Stopping API server (PID: $API_PID)...${NC}"
        kill $API_PID
        sleep 3
        # Force kill if still running
        if kill -0 $API_PID 2>/dev/null; then
            kill -9 $API_PID 2>/dev/null || true
        fi
    fi
    rm -f /tmp/matchering_api.pid
fi

# Also stop any uvicorn processes
pkill -f "uvicorn.*main:app" 2>/dev/null || true

# Stop Celery workers
echo -e "${YELLOW}📋 Step 2: Stopping Celery workers...${NC}"
if [ -f "./stop_workers.sh" ]; then
    chmod +x ./stop_workers.sh
    ./stop_workers.sh
else
    echo -e "${YELLOW}⚠️ stop_workers.sh not found, attempting manual cleanup...${NC}"
    pkill -f "celery.*worker" 2>/dev/null || true
fi

echo -e "${GREEN}✅ Complete system shutdown finished!${NC}"
echo -e "${BLUE}💡 To restart: ${NC}${YELLOW}./start_all.sh${NC}"