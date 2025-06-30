#!/bin/bash
# Enhanced Production Startup Script for Hybrid AI System
# Integrates with existing CUDA environment setup while adding production optimizations

set -e  # Exit on any error

echo "🚀 Starting Enhanced Matchering Hybrid AI Production Environment"
echo "=================================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Load existing CUDA environment (preserving user's setup)
print_status "Loading CUDA environment..."
if [ -f "./setup_cuda_env.sh" ]; then
    source ./setup_cuda_env.sh
    print_success "CUDA environment loaded"
else
    print_warning "setup_cuda_env.sh not found, skipping CUDA setup"
fi

# Step 2: Check Python environment
print_status "Validating Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION detected"
else
    print_error "Python3 not found"
    exit 1
fi

# Step 3: Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Not in project root directory (pyproject.toml not found)"
    exit 1
fi

# Step 4: Activate virtual environment (if using uv)
print_status "Checking virtual environment..."
if command -v uv &> /dev/null; then
    print_status "Using uv virtual environment"
    # Note: uv run will automatically use the project's virtual environment
elif [ -d ".venv" ]; then
    print_status "Activating .venv virtual environment"
    source .venv/bin/activate
    print_success "Virtual environment activated"
else
    print_warning "No virtual environment detected, using system Python"
fi

# Step 5: Check GPU availability
print_status "Checking GPU availability..."
if python3 -c "import torch; print('CUDA available:', torch.cuda.is_available())"; then
    GPU_NAME=$(python3 -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')")
    if [ "$GPU_NAME" != "N/A" ]; then
        print_success "GPU detected: $GPU_NAME"
    else
        print_warning "No GPU detected, using CPU mode"
    fi
else
    print_warning "PyTorch not available or GPU check failed"
fi

# Step 6: Set production environment variables
print_status "Setting production environment variables..."
export DEPLOYMENT_ENV="production"
export MODEL_CACHE_DIR="./model_cache"
export CUDA_LAUNCH_BLOCKING=1  # Better error reporting
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Optimize memory allocation
print_success "Environment variables set"

# Step 7: Create necessary directories
print_status "Creating production directories..."
mkdir -p model_cache
mkdir -p logs
mkdir -p temp
print_success "Directories created"

# Step 8: Run production initialization
print_status "Initializing production AI models..."
if command -v uv &> /dev/null; then
    # Use uv to run the startup script
    if uv run python scripts/production_startup.py; then
        print_success "Production models initialized successfully"
    else
        print_error "Production model initialization failed"
        exit 1
    fi
else
    # Use regular python
    if python3 scripts/production_startup.py; then
        print_success "Production models initialized successfully"
    else
        print_error "Production model initialization failed"
        exit 1
    fi
fi

# Step 9: Start backend with production configuration
print_status "Starting production backend server..."

# Check if backend start script exists (preserving user's setup)
if [ -f "./start_backend.sh" ]; then
    print_status "Using existing start_backend.sh script"
    # Add production flags to existing script
    export FASTAPI_ENV="production"
    export UVICORN_WORKERS=1  # Single worker for now due to model loading
    ./start_backend.sh --production
else
    # Fallback to direct uvicorn start
    print_status "Starting backend directly with uvicorn"
    cd backend
    if command -v uv &> /dev/null; then
        uv run uvicorn app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers 1 \
            --log-level info \
            --access-log \
            --reload
    else
        python3 -m uvicorn app.main:app \
            --host 0.0.0.0 \
            --port 8000 \
            --workers 1 \
            --log-level info \
            --access-log \
            --reload
    fi
fi

# If we get here, something went wrong with the backend start
print_error "Backend startup failed or was terminated"
exit 1