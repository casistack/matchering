#!/bin/bash
# Start Enhanced Matchering Backend with CUDA support

# Set CUDA environment
export CUDA_HOME=/usr/local/cuda-12.4
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda-12.4/bin:$PATH

echo "🚀 Starting Enhanced Matchering Backend with GPU support..."
echo "✅ CUDA environment configured for PyTorch 2.5.1+cu124"

# Change to backend directory
cd backend

# Start uvicorn with CUDA support
uv run uvicorn app.main:app --reload --port 8000