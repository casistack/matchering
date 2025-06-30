#!/usr/bin/env python3
"""
Platform-aware setup script for Matchering AI dependencies.

This script detects your platform and installs the appropriate AI dependencies
for optimal performance on macOS Intel, Linux with GPU, or Windows with GPU.
"""

import platform
import subprocess
import sys
from pathlib import Path


def detect_cuda_version():
    """Detect CUDA version and compatibility."""
    cuda_version = None
    cuda_runtime_version = None
    
    try:
        # Get CUDA runtime version from nvidia-smi
        result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader,nounits'], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            driver_version = result.stdout.strip()
            print(f"🔧 NVIDIA Driver: {driver_version}")
        
        # Get CUDA version from nvidia-smi
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            output = result.stdout
            # Extract CUDA version from nvidia-smi output
            for line in output.split('\n'):
                if 'CUDA Version:' in line:
                    cuda_version = line.split('CUDA Version:')[1].strip().split()[0]
                    break
        
        # Get CUDA toolkit version if nvcc is available
        try:
            result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout
                for line in output.split('\n'):
                    if 'release' in line and 'V' in line:
                        # Extract version like "V12.1.66"
                        version_part = line.split('V')[1].split(',')[0]
                        cuda_runtime_version = version_part.split('.')[0] + '.' + version_part.split('.')[1]  # e.g., "12.1"
                        break
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
            
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return cuda_version, cuda_runtime_version


def detect_platform():
    """Detect platform and hardware capabilities."""
    system = platform.system()
    machine = platform.machine()
    python_version = platform.python_version()
    
    print(f"🔍 Detected platform: {system} {machine}")
    print(f"🐍 Python version: {python_version}")
    
    # Detect CUDA availability and version
    has_cuda = False
    cuda_version = None
    cuda_runtime_version = None
    gpu_name = None
    
    # First check if nvidia-smi exists (hardware detection)
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                               capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            gpu_name = result.stdout.strip()
            print(f"🚀 NVIDIA GPU detected: {gpu_name}")
            has_cuda = True
            
            # Get detailed CUDA version info
            cuda_version, cuda_runtime_version = detect_cuda_version()
            if cuda_version:
                print(f"🔧 CUDA Driver Version: {cuda_version}")
            if cuda_runtime_version:
                print(f"🛠️  CUDA Runtime Version: {cuda_runtime_version}")
        else:
            print("💻 No NVIDIA GPU detected")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("💻 No NVIDIA GPU detected")
    
    # Then check PyTorch CUDA support if available
    pytorch_cuda_available = False
    try:
        import torch
        pytorch_cuda_available = torch.cuda.is_available()
        if pytorch_cuda_available:
            gpu_count = torch.cuda.device_count()
            pytorch_gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            pytorch_cuda_version = torch.version.cuda
            print(f"✅ PyTorch CUDA ready: {gpu_count} GPU(s) - {pytorch_gpu_name}")
            print(f"🔗 PyTorch CUDA version: {pytorch_cuda_version}")
            has_cuda = True
        elif has_cuda:
            print("⚠️  NVIDIA GPU detected but PyTorch CUDA not available - will install GPU PyTorch")
        else:
            print("💻 PyTorch CUDA not available")
    except ImportError:
        if has_cuda:
            print("⚠️  NVIDIA GPU detected, PyTorch not installed yet - will install GPU PyTorch")
        else:
            print("⚠️  PyTorch not installed yet")
    
    return {
        "system": system,
        "machine": machine,
        "python_version": python_version,
        "has_cuda": has_cuda,
        "cuda_version": cuda_version,
        "cuda_runtime_version": cuda_runtime_version,
        "gpu_name": gpu_name,
        "pytorch_cuda_available": pytorch_cuda_available
    }


def get_install_command(platform_info):
    """Get the appropriate uv install command for the platform."""
    system = platform_info["system"]
    machine = platform_info["machine"]
    has_cuda = platform_info["has_cuda"]
    
    if system == "Darwin":  # macOS
        if machine == "arm64":
            print("📱 macOS Apple Silicon detected")
            return "uv sync --extra ai-dev"
        else:
            print("💻 macOS Intel detected - using CPU-only PyTorch")
            return "uv sync --extra ai-dev"
    
    elif system == "Linux":
        if has_cuda:
            print("🚀 Linux with CUDA detected - installing GPU-optimized dependencies")
            return "uv sync --extra ai-gpu"
        else:
            print("💻 Linux without CUDA - using CPU-only dependencies")
            return "uv sync --extra ai-dev"
    
    elif system == "Windows":
        if has_cuda:
            print("🚀 Windows with CUDA detected - installing GPU-optimized dependencies")
            return "uv sync --extra ai-gpu"
        else:
            print("💻 Windows without CUDA - using CPU-only dependencies")  
            return "uv sync --extra ai-dev"
    
    else:
        print(f"⚠️  Unknown platform: {system}")
        return "uv sync --extra ai-dev"


def determine_pytorch_index_url(platform_info):
    """Determine the correct PyTorch index URL based on CUDA version."""
    if not platform_info["has_cuda"]:
        return "https://download.pytorch.org/whl/cpu"
    
    cuda_version = platform_info.get("cuda_version")
    cuda_runtime = platform_info.get("cuda_runtime_version")
    
    # For Enhanced Matchering, we standardize on CUDA 12.4 for RTX 4090
    # This ensures compatibility with our specific CUDA setup
    if platform_info.get("gpu_name") and "RTX 4090" in platform_info["gpu_name"]:
        print("🚀 RTX 4090 detected - using CUDA 12.4 optimized PyTorch")
        return "https://download.pytorch.org/whl/cu124"
    
    # Map CUDA versions to PyTorch wheel versions
    if cuda_runtime:
        if cuda_runtime.startswith("12.1"):
            return "https://download.pytorch.org/whl/cu121"
        elif cuda_runtime.startswith("12.4"):
            return "https://download.pytorch.org/whl/cu124"  
        elif cuda_runtime.startswith("11.8"):
            return "https://download.pytorch.org/whl/cu118"
    
    # Fallback based on driver version
    if cuda_version:
        if cuda_version.startswith("12."):
            # For CUDA 12.x, try cu124 for modern setups
            return "https://download.pytorch.org/whl/cu124"
        elif cuda_version.startswith("11."):
            return "https://download.pytorch.org/whl/cu118"
    
    # Default to cu124 for modern GPUs
    return "https://download.pytorch.org/whl/cu124"


def install_pytorch_with_cuda(platform_info):
    """Install PyTorch with appropriate CUDA support."""
    if not platform_info["has_cuda"]:
        print("💻 Installing CPU-only PyTorch...")
        cmd = ["uv", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"]
    else:
        index_url = determine_pytorch_index_url(platform_info)
        print(f"🚀 Installing GPU PyTorch with CUDA support...")
        print(f"🔗 Using index: {index_url}")
        
        # For CUDA 12.4 setups, install specific versions to ensure compatibility
        if "cu124" in index_url:
            cmd = ["uv", "pip", "install", "torch==2.5.1+cu124", "torchaudio==2.5.1+cu124", "--index-url", index_url]
        else:
            cmd = ["uv", "pip", "install", "torch", "torchaudio", "--index-url", index_url]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        print("✅ PyTorch installed successfully!")
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"❌ PyTorch installation failed: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def install_dependencies(platform_info):
    """Install appropriate dependencies for the detected platform."""
    
    print(f"\n📦 Installing dependencies for {platform_info['system']} with {'GPU' if platform_info['has_cuda'] else 'CPU'} support")
    print("=" * 50)
    
    # Step 1: Use platform-specific pyproject.toml
    pyproject_file = "pyproject.toml"  # Default
    if platform_info["system"] == "Darwin":
        # Use Mac-specific pyproject.toml for CPU-only dependencies
        pyproject_file = "pyproject-mac.toml"
        print(f"🍎 Using Mac-specific dependencies: {pyproject_file}")
        
        # Temporarily backup original and use Mac version
        if Path("pyproject-mac.toml").exists():
            subprocess.run(["cp", "pyproject.toml", "pyproject-linux.toml.bak"], check=False)
            subprocess.run(["cp", "pyproject-mac.toml", "pyproject.toml"], check=True)
    
    # Step 2: Install core dependencies
    print("🔧 Installing core dependencies...")
    try:
        result = subprocess.run(
            ["uv", "sync"],
            check=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        print("✅ Core dependencies installed!")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"❌ Core dependencies failed: {e}")
        
        # Restore original pyproject.toml if we backed it up
        if platform_info["system"] == "Darwin" and Path("pyproject-linux.toml.bak").exists():
            subprocess.run(["cp", "pyproject-linux.toml.bak", "pyproject.toml"], check=False)
        return False
    
    # Step 2: Install PyTorch with correct CUDA version
    print("\n🤖 Installing PyTorch...")
    if not install_pytorch_with_cuda(platform_info):
        print("⚠️  PyTorch installation failed, trying fallback...")
        # Try CPU version as fallback
        try:
            subprocess.run(
                ["uv", "pip", "install", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"],
                check=True, timeout=300
            )
            print("✅ Fallback CPU PyTorch installed!")
        except:
            print("❌ All PyTorch installation attempts failed")
            return False
    
    # Step 3: Install additional ML libraries
    print("\n🧠 Installing ML libraries...")
    try:
        ml_packages = ["transformers", "accelerate", "scikit-learn"]
        for package in ml_packages:
            print(f"📦 Installing {package}...")
            subprocess.run(["uv", "add", package], check=True, timeout=180)
        print("✅ ML libraries installed!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Some ML libraries failed to install: {e}")
    
    # Step 4: Restore original pyproject.toml if needed
    if platform_info["system"] == "Darwin" and Path("pyproject-linux.toml.bak").exists():
        print("🔄 Restoring original pyproject.toml...")
        subprocess.run(["cp", "pyproject-linux.toml.bak", "pyproject.toml"], check=False)
        subprocess.run(["rm", "pyproject-linux.toml.bak"], check=False)
    
    # Step 5: Test imports
    print("\n🧪 Testing imports...")
    return test_imports()


def test_imports():
    """Test that critical AI dependencies can be imported."""
    
    # Core dependencies (must work)
    core_imports = [
        ("numpy", "NumPy"),
        ("scipy", "SciPy"), 
        ("sklearn", "Scikit-learn"),
        ("redis", "Redis"),
        ("soundfile", "SoundFile"),
    ]
    
    # AI/ML imports (important but optional for basic functionality)
    ai_imports = [
        ("torch", "PyTorch"),
        ("torchaudio", "TorchAudio"),
        ("transformers", "Transformers"),
        ("audioflux", "AudioFlux"),
    ]
    
    print("🧪 Testing core dependencies...")
    success_count = 0
    
    for module, name in core_imports:
        try:
            __import__(module)
            print(f"✅ {name} - OK")
            success_count += 1
        except ImportError:
            print(f"❌ {name} - Failed")
    
    print(f"\n🤖 Testing AI/ML dependencies...")
    ai_success_count = 0
    
    for module, name in ai_imports:
        try:
            imported_module = __import__(module)
            print(f"✅ {name} - OK")
            
            # Special test for PyTorch CUDA
            if module == "torch":
                if hasattr(imported_module, 'cuda') and imported_module.cuda.is_available():
                    gpu_count = imported_module.cuda.device_count()
                    gpu_name = imported_module.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
                    print(f"  🚀 CUDA available: {gpu_count} GPU(s) - {gpu_name}")
                else:
                    print(f"  💻 CUDA not available (CPU only)")
            
            ai_success_count += 1
        except ImportError as e:
            print(f"⚠️  {name} - Not available")
        except Exception as e:
            print(f"⚠️  {name} - Import error: {e}")
    
    # Summary
    core_success = success_count == len(core_imports)
    ai_available = ai_success_count > 0
    
    print(f"\n📊 Import Summary:")
    print(f"   Core dependencies: {success_count}/{len(core_imports)} ({'✅ PASS' if core_success else '❌ FAIL'})")
    print(f"   AI/ML dependencies: {ai_success_count}/{len(ai_imports)} ({'✅ GOOD' if ai_available else '⚠️  LIMITED'})")
    
    if core_success and ai_available:
        print(f"\n🎉 Environment ready for AI development!")
        return True
    elif core_success:
        print(f"\n⚠️  Basic environment ready, but AI capabilities limited")
        return True
    else:
        print(f"\n❌ Environment setup incomplete - core dependencies missing")
        return False


def create_platform_config():
    """Create a platform-specific configuration file."""
    
    platform_info = detect_platform()
    
    config = {
        "platform": platform_info,
        "feature_extractor": {
            "device": "cuda" if platform_info["has_cuda"] else "cpu",
            "batch_size": 32 if platform_info["has_cuda"] else 8,
            "num_workers": 4 if platform_info["has_cuda"] else 2,
        },
        "ai_model": {
            "precision": "float16" if platform_info["has_cuda"] else "float32",
            "enable_gpu": platform_info["has_cuda"],
        }
    }
    
    # Write config file
    config_path = Path("backend/app/config/platform_config.py")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, "w") as f:
        f.write(f"""# Auto-generated platform configuration
# Generated for: {platform_info['system']} {platform_info['machine']}

PLATFORM_CONFIG = {config}

# Device selection for PyTorch
DEVICE = "{config['feature_extractor']['device']}"
ENABLE_GPU = {config['ai_model']['enable_gpu']}
BATCH_SIZE = {config['feature_extractor']['batch_size']}
PRECISION = "{config['ai_model']['precision']}"
""")
    
    print(f"📝 Platform configuration saved to: {config_path}")


def create_cuda_env_script():
    """Create a script to set CUDA environment variables."""
    
    # Create environment setup script
    env_script_path = Path("setup_cuda_env.sh")
    
    with open(env_script_path, "w") as f:
        f.write("""#!/bin/bash
# CUDA Environment Setup for Enhanced Matchering
# Source this file before running Python: source setup_cuda_env.sh

# Set CUDA paths for PyTorch compatibility
export CUDA_HOME=/usr/local/cuda-12.4
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda-12.4/bin:$PATH

echo "✅ CUDA environment variables set for PyTorch 2.5.1+cu124"
echo "🚀 Ready for GPU-accelerated audio processing"
""")
    
    # Make it executable
    subprocess.run(["chmod", "+x", str(env_script_path)], check=True)
    print(f"📝 CUDA environment script created: {env_script_path}")
    
    # Create Python wrapper script
    python_wrapper_path = Path("run_with_cuda.py")
    
    with open(python_wrapper_path, "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Python wrapper that automatically sets CUDA environment before importing PyTorch.
Use this instead of 'python' when running Enhanced Matchering scripts.
\"\"\"

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
""")
    
    subprocess.run(["chmod", "+x", str(python_wrapper_path)], check=True)
    print(f"📝 Python CUDA wrapper created: {python_wrapper_path}")


def main():
    """Main setup routine."""
    
    print("🚀 Matchering AI Platform Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Detect platform
    platform_info = detect_platform()
    
    # Install dependencies
    install_dependencies(platform_info)
    
    # Create platform config
    create_platform_config()
    
    # Create CUDA environment helpers for Linux GPU systems
    if platform_info["system"] == "Linux" and platform_info["has_cuda"]:
        create_cuda_env_script()
    
    print("\n" + "=" * 50)
    print("🎉 Setup complete!")
    
    if platform_info["system"] == "Darwin":
        print("\n💡 Development Tips for macOS:")
        print("   • Use this machine for development and testing")
        print("   • Deploy to Linux/Windows with GPU for production")
        print("   • AI models will run on CPU (slower but functional)")
    else:
        print(f"\n💡 Tips for {platform_info['system']}:")
        if platform_info["has_cuda"]:
            print("   • GPU acceleration enabled for fast AI inference")
            print("   • Perfect for production deployment")
            print("   • CUDA environment helpers created for consistent PyTorch usage")
        else:
            print("   • Consider installing CUDA for better performance")
    
    print("\n📚 Next steps:")
    if platform_info["system"] == "Linux" and platform_info["has_cuda"]:
        print("   • Source CUDA environment: source setup_cuda_env.sh")
        print("   • Or use Python wrapper: python run_with_cuda.py <script>")
        print("   • Test setup: uv run python run_with_cuda.py -c \"import torch; print('CUDA:', torch.cuda.is_available())\"")
    else:
        print("   • Run: uv run python backend/test_ai_imports.py")
    print("   • Start development: uv run python backend/run.py")


if __name__ == "__main__":
    main()