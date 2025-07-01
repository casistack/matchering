#!/bin/bash
# CUDA Environment Setup for Enhanced Matchering
# Source this file before running Python: source setup_cuda_env.sh

# Set CUDA paths for PyTorch compatibility
export CUDA_HOME=/usr/local/cuda-12.4
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda-12.4/bin:$PATH

echo "✅ CUDA environment variables set for PyTorch 2.6.0+cu124"
echo "🚀 Ready for GPU-accelerated audio processing"
