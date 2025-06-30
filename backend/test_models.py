#!/usr/bin/env python3
"""
Test script to verify AI model downloading and initialization.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_model_loading():
    """Test loading AI models."""
    try:
        logger.info("Testing AI model loading...")
        
        # Import after path setup
        from app.ai.production_model_manager import ProductionModelManager
        
        # Create model manager
        model_manager = ProductionModelManager()
        logger.info(f"Model manager initialized with device: {model_manager.device}")
        
        # Test loading a single model first
        logger.info("\n1. Testing single model load (AST)...")
        results = await model_manager.preload_models(["ast"])
        logger.info(f"AST model load result: {results}")
        
        # Get memory stats
        stats = model_manager.get_memory_stats()
        if model_manager.device == "cuda":
            logger.info(f"Memory usage after AST: {stats['gpu_memory_used_mb']:.1f}MB / {stats['gpu_memory_total_mb']:.1f}MB")
        else:
            logger.info(f"Running on CPU - Models loaded: {stats['models_loaded']}")
        
        # Test extracting features with AST
        if results.get("ast", False):
            logger.info("\n2. Testing feature extraction with AST...")
            import torch
            import torchaudio
            
            # Create a test audio tensor (1 second of silence)
            sample_rate = 16000
            duration = 1.0
            audio = torch.zeros(1, int(sample_rate * duration))
            
            try:
                features = await model_manager.extract_features("ast", audio, sample_rate)
                logger.info(f"✅ AST feature extraction successful! Shape: {features.shape}")
            except Exception as e:
                logger.error(f"❌ AST feature extraction failed: {e}")
        
        # Try loading other models
        logger.info("\n3. Testing other models...")
        other_models = ["wav2vec2", "clap"]
        other_results = await model_manager.preload_models(other_models)
        
        for model, success in other_results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {model}: {'Loaded' if success else 'Failed'}")
        
        # Final memory stats
        final_stats = model_manager.get_memory_stats()
        if model_manager.device == "cuda":
            logger.info(f"\nFinal memory usage: {final_stats['gpu_memory_used_mb']:.1f}MB / {final_stats['gpu_memory_total_mb']:.1f}MB")
        else:
            logger.info(f"\nFinal status - Models loaded: {final_stats['models_loaded']}")
        
        # Summary
        all_results = {**results, **other_results}
        success_count = sum(1 for s in all_results.values() if s)
        total_count = len(all_results)
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Model Loading Summary: {success_count}/{total_count} models loaded successfully")
        logger.info(f"{'='*50}")
        
        if success_count == 0:
            logger.error("\n⚠️  No models could be loaded!")
            logger.error("Please check:")
            logger.error("1. Internet connection (models need to be downloaded from HuggingFace)")
            logger.error("2. Disk space (models require several GB)")
            logger.error("3. GPU memory if using CUDA")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_model_loading())
    sys.exit(0 if success else 1)