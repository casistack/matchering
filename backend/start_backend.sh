#!/bin/bash

# Backend API Startup Script for Matchering
# Starts the FastAPI server with proper configuration

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

echo -e "${BLUE}🚀 Starting Matchering Backend API...${NC}"

# Check if virtual environment is already activated
if [ -z "$VIRTUAL_ENV" ]; then
    # Not activated, check if virtual environment exists
    if [ -d "../.venv" ]; then
        # Virtual environment is in parent directory (project root)
        echo -e "${YELLOW}📦 Activating virtual environment from project root...${NC}"
        source ../.venv/bin/activate
    elif [ -d ".venv" ]; then
        # Virtual environment is in current directory
        echo -e "${YELLOW}📦 Activating virtual environment from backend directory...${NC}"
        source .venv/bin/activate
    else
        echo -e "${RED}❌ Virtual environment not found in backend/ or project root.${NC}"
        echo -e "${YELLOW}💡 Please ensure .venv exists in the project root or run setup first.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Virtual environment already activated: $VIRTUAL_ENV${NC}"
fi

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo -e "${YELLOW}📁 Creating logs directory...${NC}"
    mkdir -p logs
fi

# Start the backend server
echo -e "${YELLOW}🌐 Starting FastAPI server...${NC}"
echo -e "${BLUE}📍 Server will be available at: ${NC}${GREEN}http://localhost:8000${NC}"
echo -e "${BLUE}📚 API documentation at: ${NC}${GREEN}http://localhost:8000/docs${NC}"
echo -e "${YELLOW}💡 Press Ctrl+C to stop the server${NC}"
echo ""

# Run the backend server
python run.py