#!/usr/bin/env python3
"""
Production Startup Script for Hybrid AI System.

This script initializes the production environment for the hybrid AI mastering system,
including model preloading, GPU optimization, and system validation.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

# Import our production modules
from app.ai.deployment_config import get_deployment_config, config_manager
from app.ai.production_model_manager import ProductionModelManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('production_startup.log')
    ]
)
logger = logging.getLogger(__name__)


class ProductionStartupManager:
    """Manages production startup and initialization."""
    
    def __init__(self):
        self.config = get_deployment_config()
        self.model_manager = None
        self.startup_time = time.time()
        
    async def initialize_production_environment(self) -> bool:
        """Initialize the complete production environment."""
        logger.info("🚀 Starting Hybrid AI Production Environment Initialization")
        logger.info(f"Environment: {self.config.environment}")
        
        try:
            # Step 1: Validate system requirements
            if not await self._validate_system_requirements():
                return False
            
            # Step 2: Initialize GPU environment
            if not await self._initialize_gpu_environment():
                return False
            
            # Step 3: Create production model manager
            if not await self._initialize_model_manager():
                return False
            
            # Step 4: Preload production models
            if not await self._preload_models():
                return False
            
            # Step 5: Validate system health
            if not await self._validate_system_health():
                return False
            
            total_time = time.time() - self.startup_time
            logger.info(f"✅ Production environment initialized successfully in {total_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Production initialization failed: {e}")
            return False
    
    async def _validate_system_requirements(self) -> bool:
        """Validate system requirements for production deployment."""
        logger.info("📋 Validating system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("Python 3.8+ required for production deployment")
            return False
        
        # Check required packages
        required_packages = [
            'torch', 'torchaudio', 'transformers', 'fastapi', 
            'pydantic', 'numpy', 'scipy'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            return False
        
        # Check disk space for cache
        cache_dir = Path(self.config.cache.cache_dir)
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Check available space (simplified check)
            stat = os.statvfs(cache_dir)
            available_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
            required_gb = self.config.cache.max_cache_size_gb + 5  # +5GB buffer
            
            if available_gb < required_gb:
                logger.warning(f"Low disk space: {available_gb:.1f}GB available, {required_gb:.1f}GB recommended")
            else:
                logger.info(f"✅ Sufficient disk space: {available_gb:.1f}GB available")
                
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
        
        logger.info("✅ System requirements validated")
        return True
    
    async def _initialize_gpu_environment(self) -> bool:
        """Initialize GPU environment for production."""
        logger.info("🔧 Initializing GPU environment...")
        
        if not self.config.gpu.enabled:
            logger.info("GPU disabled in configuration, using CPU mode")
            return True
        
        try:
            import torch
            
            if not torch.cuda.is_available():
                logger.error("CUDA not available but GPU enabled in config")
                return False
            
            # Set CUDA device
            device_id = self.config.gpu.device_id
            torch.cuda.set_device(device_id)
            
            # Get GPU info
            gpu_props = torch.cuda.get_device_properties(device_id)
            total_memory_gb = gpu_props.total_memory / 1e9
            
            logger.info(f"✅ GPU initialized: {gpu_props.name}")
            logger.info(f"   Memory: {total_memory_gb:.1f}GB total, {self.config.gpu.memory_limit_gb:.1f}GB limit")
            logger.info(f"   CUDA version: {torch.version.cuda}")
            
            # Set memory fraction if specified
            if hasattr(torch.cuda, 'set_per_process_memory_fraction'):
                memory_fraction = self.config.gpu.memory_limit_gb / total_memory_gb
                torch.cuda.set_per_process_memory_fraction(memory_fraction, device_id)
                logger.info(f"   Memory fraction set to {memory_fraction:.2f}")
            
            # Enable mixed precision if configured
            if self.config.gpu.mixed_precision:
                logger.info("✅ Mixed precision enabled")
            
            # Clear cache to start fresh
            torch.cuda.empty_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPU environment: {e}")
            return False
    
    async def _initialize_model_manager(self) -> bool:
        """Initialize the production model manager."""
        logger.info("🤖 Initializing production model manager...")
        
        try:
            device = "cuda" if self.config.gpu.enabled and torch.cuda.is_available() else "cpu"
            
            self.model_manager = ProductionModelManager(
                device=device,
                cache_dir=self.config.cache.cache_dir,
                max_gpu_memory_gb=self.config.gpu.memory_limit_gb,
                enable_feature_caching=self.config.cache.enabled
            )
            
            logger.info(f"✅ Model manager initialized on {device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize model manager: {e}")
            return False
    
    async def _preload_models(self) -> bool:
        """Preload production models."""
        preload_models = config_manager.get_preload_models()
        
        if not preload_models:
            logger.info("No models configured for preloading")
            return True
        
        logger.info(f"📥 Preloading models: {preload_models}")
        
        try:
            start_time = time.time()
            results = await self.model_manager.preload_models(preload_models)
            load_time = time.time() - start_time
            
            # Check results
            successful_models = [model for model, success in results.items() if success]
            failed_models = [model for model, success in results.items() if not success]
            
            if successful_models:
                logger.info(f"✅ Successfully preloaded models: {successful_models}")
                logger.info(f"   Total load time: {load_time:.2f}s")
            
            if failed_models:
                logger.warning(f"⚠️ Failed to preload models: {failed_models}")
                
                # Check if any critical models failed
                critical_models = ['ast', 'wav2vec', 'custom']
                failed_critical = [m for m in failed_models if m in critical_models]
                
                if failed_critical:
                    logger.error(f"Critical models failed to load: {failed_critical}")
                    return False
            
            # Log memory stats
            if self.model_manager:
                stats = self.model_manager.get_memory_stats()
                logger.info(f"   Memory stats: {stats}")
            
            return len(successful_models) > 0
            
        except Exception as e:
            logger.error(f"Model preloading failed: {e}")
            return False
    
    async def _validate_system_health(self) -> bool:
        """Validate system health after initialization."""
        logger.info("🔍 Validating system health...")
        
        try:
            if not self.model_manager:
                logger.error("Model manager not initialized")
                return False
            
            # Check loaded models
            stats = self.model_manager.get_memory_stats()
            loaded_models = stats.get('loaded_models', [])
            
            if not loaded_models:
                logger.warning("No models loaded - system may not function properly")
                return False
            
            logger.info(f"✅ Models loaded: {loaded_models}")
            
            # Check GPU memory if applicable
            if self.config.gpu.enabled and torch.cuda.is_available():
                gpu_memory_gb = stats.get('gpu_memory_allocated_gb', 0)
                memory_limit_gb = self.config.gpu.memory_limit_gb
                
                if gpu_memory_gb > memory_limit_gb:
                    logger.warning(f"GPU memory usage ({gpu_memory_gb:.1f}GB) exceeds limit ({memory_limit_gb:.1f}GB)")
                else:
                    logger.info(f"✅ GPU memory usage: {gpu_memory_gb:.1f}GB / {memory_limit_gb:.1f}GB")
            
            # Test feature extraction
            logger.info("🧪 Testing feature extraction...")
            try:
                import torch
                # Create dummy audio for testing
                dummy_audio = torch.randn(1, 44100)  # 1 second of audio
                
                # Test at least one model
                if 'custom' in loaded_models:
                    # Test custom model (smallest and fastest)
                    features = await self.model_manager.extract_features_cached(
                        'custom', dummy_audio, 44100
                    )
                    if features is not None:
                        logger.info("✅ Feature extraction test passed")
                    else:
                        logger.warning("Feature extraction test failed")
                
            except Exception as e:
                logger.warning(f"Feature extraction test failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"System health validation failed: {e}")
            return False
    
    def get_startup_summary(self) -> Dict[str, any]:
        """Get startup summary information."""
        total_time = time.time() - self.startup_time
        
        summary = {
            "startup_time": total_time,
            "environment": self.config.environment.value,
            "gpu_enabled": self.config.gpu.enabled,
            "models_enabled": config_manager.get_enabled_models(),
            "models_preloaded": config_manager.get_preload_models(),
            "cache_enabled": self.config.cache.enabled,
            "monitoring_enabled": self.config.monitoring.enabled
        }
        
        if self.model_manager:
            summary.update(self.model_manager.get_memory_stats())
        
        return summary


async def main():
    """Main startup function."""
    startup_manager = ProductionStartupManager()
    
    try:
        success = await startup_manager.initialize_production_environment()
        
        if success:
            summary = startup_manager.get_startup_summary()
            logger.info("📊 Startup Summary:")
            for key, value in summary.items():
                logger.info(f"   {key}: {value}")
            
            print("\n🎉 Production environment ready!")
            print("✅ Hybrid AI system initialized successfully")
            print(f"✅ Environment: {summary['environment']}")
            print(f"✅ GPU enabled: {summary['gpu_enabled']}")
            print(f"✅ Models loaded: {len(summary.get('loaded_models', []))}")
            print(f"✅ Startup time: {summary['startup_time']:.2f}s")
            
            return 0
        else:
            print("\n❌ Production initialization failed!")
            print("Check logs for details: production_startup.log")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Startup interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during startup: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)