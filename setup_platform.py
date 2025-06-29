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


def detect_platform():
    """Detect platform and hardware capabilities."""
    system = platform.system()
    machine = platform.machine()
    python_version = platform.python_version()
    
    print(f"🔍 Detected platform: {system} {machine}")
    print(f"🐍 Python version: {python_version}")
    
    # Detect CUDA availability
    has_cuda = False
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        if has_cuda:
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            print(f"🚀 CUDA available: {gpu_count} GPU(s) - {gpu_name}")
        else:
            print("💻 CUDA not available - using CPU")
    except ImportError:
        print("⚠️  PyTorch not installed yet")
    
    return {
        "system": system,
        "machine": machine,
        "python_version": python_version,
        "has_cuda": has_cuda
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


def install_dependencies(platform_info):
    """Install appropriate dependencies for the detected platform."""
    
    install_cmd = get_install_command(platform_info)
    
    print(f"\n📦 Installing dependencies with: {install_cmd}")
    print("=" * 50)
    
    try:
        # Run the installation command
        result = subprocess.run(
            install_cmd.split(),
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✅ Dependencies installed successfully!")
        
        # Test imports
        print("\n🧪 Testing imports...")
        test_imports()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        
        # Fallback to basic AI dependencies
        print("\n🔄 Trying fallback installation...")
        fallback_cmd = "uv add librosa scikit-learn redis numpy --frozen"
        subprocess.run(fallback_cmd.split(), check=True)
        print("✅ Fallback installation completed")


def test_imports():
    """Test that critical AI dependencies can be imported."""
    
    imports_to_test = [
        ("numpy", "NumPy"),
        ("librosa", "Librosa"),
        ("sklearn", "Scikit-learn"),
        ("redis", "Redis"),
    ]
    
    # Optional imports
    optional_imports = [
        ("torch", "PyTorch"),
        ("torchaudio", "TorchAudio"),
    ]
    
    success_count = 0
    
    for module, name in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {name} - OK")
            success_count += 1
        except ImportError:
            print(f"❌ {name} - Failed")
    
    for module, name in optional_imports:
        try:
            __import__(module)
            print(f"✅ {name} - OK (optional)")
        except ImportError:
            print(f"⚠️  {name} - Not available (optional)")
    
    if success_count == len(imports_to_test):
        print(f"\n🎉 All {success_count} core dependencies imported successfully!")
        return True
    else:
        print(f"\n⚠️  Only {success_count}/{len(imports_to_test)} core dependencies working")
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
        else:
            print("   • Consider installing CUDA for better performance")
    
    print("\n📚 Next steps:")
    print("   • Run: uv run python backend/test_ai_imports.py")
    print("   • Start development: uv run python backend/run.py")


if __name__ == "__main__":
    main()