#!/usr/bin/env python3
"""
Python wrapper that automatically sets CUDA environment before importing PyTorch.
Use this instead of 'python' when running Enhanced Matchering scripts.
"""

import os
import sys

# Set CUDA environment variables before any PyTorch imports
os.environ['CUDA_HOME'] = '/usr/local/cuda-12.4'
cuda_lib_path = '/usr/local/cuda-12.4/lib64'
if 'LD_LIBRARY_PATH' in os.environ:
    os.environ['LD_LIBRARY_PATH'] = f"{cuda_lib_path}:{os.environ['LD_LIBRARY_PATH']}"
else:
    os.environ['LD_LIBRARY_PATH'] = cuda_lib_path

# Now safe to import and run PyTorch code
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_with_cuda.py <script.py> [args...]")
        sys.exit(1)
    
    script_path = sys.argv[1]
    script_args = sys.argv[2:]
    
    # Execute the target script with CUDA environment set
    import subprocess
    cmd = [sys.executable, script_path] + script_args
    subprocess.run(cmd)
