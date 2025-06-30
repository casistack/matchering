#!/usr/bin/env python3
"""
Initialize and download AI models for the Matchering backend.
Run this script to download and cache all required models before starting the server.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.ai.production_model_manager import ProductionModelManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def initialize_models():
    """Download and cache all required AI models."""
    logger.info("Initializing AI models for Matchering backend...")
    
    try:
        # Create model manager
        model_manager = ProductionModelManager()
        logger.info(f"Model manager created with device: {model_manager.device}")
        
        # List of models to preload
        models_to_load = [
            "ast",
            "wav2vec2",
            "clap",
            # "musicgen"  # Skip MusicGen for now as it's very large
        ]
        
        logger.info(f"Preloading models: {models_to_load}")
        
        # Preload models
        results = await model_manager.preload_models(models_to_load)
        
        # Report results
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"\nModel initialization complete: {success_count}/{total_count} models loaded successfully")
        
        for model_type, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {model_type}: {'Loaded' if success else 'Failed'}")
        
        # Get memory stats
        stats = model_manager.get_memory_stats()
        logger.info(f"\nMemory usage: {stats['gpu_memory_used_mb']:.1f}MB / {stats['gpu_memory_total_mb']:.1f}MB")
        
        if success_count < total_count:
            logger.warning("\n⚠️  Some models failed to load. The system may not function properly.")
            logger.warning("Please check your internet connection and try again.")
            return False
        
        logger.info("\n✅ All models initialized successfully! You can now start the backend server.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(initialize_models())
    sys.exit(0 if success else 1)