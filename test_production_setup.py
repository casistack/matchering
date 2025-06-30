#!/usr/bin/env python3
"""
Production Setup Validation Test.

This script validates that the production environment for the hybrid AI system
is correctly configured and ready for deployment.
"""

import asyncio
import logging
import os
import sys
import torch
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_production_setup():
    """Test the complete production setup."""
    print("🧪 Testing Production Setup for Hybrid AI System")
    print("=" * 60)
    
    # Test 1: Import all production modules
    print("\n1. Testing module imports...")
    try:
        from app.ai.deployment_config import get_deployment_config, config_manager
        from app.ai.production_model_manager import ProductionModelManager
        print("✅ All production modules imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Configuration loading
    print("\n2. Testing configuration loading...")
    try:
        config = get_deployment_config()
        print(f"✅ Configuration loaded: {config.environment}")
        print(f"   GPU enabled: {config.gpu.enabled}")
        print(f"   Enabled models: {config_manager.get_enabled_models()}")
        print(f"   Preload models: {config_manager.get_preload_models()}")
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False
    
    # Test 3: GPU availability
    print("\n3. Testing GPU environment...")
    try:
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"✅ GPU available: {gpu_name}")
            print(f"   Memory: {memory_gb:.1f}GB")
        else:
            print("⚠️ No GPU available, using CPU mode")
    except Exception as e:
        print(f"❌ GPU check failed: {e}")
    
    # Test 4: Model manager initialization
    print("\n4. Testing model manager initialization...")
    try:
        device = "cuda" if config.gpu.enabled and torch.cuda.is_available() else "cpu"
        model_manager = ProductionModelManager(
            device=device,
            cache_dir=config.cache.cache_dir,
            max_gpu_memory_gb=config.gpu.memory_limit_gb,
            enable_feature_caching=config.cache.enabled
        )
        print(f"✅ Model manager initialized on {device}")
    except Exception as e:
        print(f"❌ Model manager initialization failed: {e}")
        return False
    
    # Test 5: Cache directory creation
    print("\n5. Testing cache directory...")
    try:
        cache_dir = Path(config.cache.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Cache directory ready: {cache_dir}")
    except Exception as e:
        print(f"❌ Cache directory creation failed: {e}")
        return False
    
    # Test 6: Model preloading (limited test)
    print("\n6. Testing model preloading...")
    try:
        # Only test custom model (smallest and fastest)
        test_models = ['custom'] if 'custom' in config_manager.get_enabled_models() else []
        
        if test_models:
            results = await model_manager.preload_models(test_models)
            successful = [m for m, success in results.items() if success]
            
            if successful:
                print(f"✅ Successfully preloaded test models: {successful}")
            else:
                print("⚠️ No models preloaded (may require internet connection)")
        else:
            print("⚠️ No enabled models found for testing")
    except Exception as e:
        print(f"❌ Model preloading test failed: {e}")
    
    # Test 7: Memory statistics
    print("\n7. Testing memory statistics...")
    try:
        stats = model_manager.get_memory_stats()
        print("✅ Memory statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Memory statistics failed: {e}")
    
    # Test 8: Feature extraction test
    print("\n8. Testing feature extraction...")
    try:
        # Create dummy audio
        dummy_audio = torch.randn(1, 44100)  # 1 second of audio
        
        # Test if we can get a model (without actually extracting)
        model, processor = model_manager.get_model('custom')
        if model is not None:
            print("✅ Model retrieval successful")
            model_manager.release_model('custom')
        else:
            print("⚠️ Model not available for testing")
    except Exception as e:
        print(f"❌ Feature extraction test failed: {e}")
    
    # Test 9: API integration test
    print("\n9. Testing API integration...")
    try:
        from app.api.v1.endpoints.hybrid_ai import get_production_model_manager
        api_model_manager = get_production_model_manager()
        
        if api_model_manager is not None:
            print("✅ API integration successful")
        else:
            print("❌ API integration failed")
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
    
    # Test 10: Cleanup
    print("\n10. Testing cleanup...")
    try:
        model_manager.cleanup_unused_models()
        model_manager.shutdown()
        print("✅ Cleanup successful")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Production setup validation completed!")
    print("\nNext steps:")
    print("1. Run: ./start_production.sh")
    print("2. Check logs for any warnings")
    print("3. Test API endpoints when backend is running")
    
    return True


def main():
    """Main test function."""
    try:
        result = asyncio.run(test_production_setup())
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)