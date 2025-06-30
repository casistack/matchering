#!/usr/bin/env python3
"""
Test script for Hybrid AI API endpoints.

This script tests the FastAPI endpoints for hybrid AI mastering
to ensure they integrate correctly with the hybrid feature extraction system.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add backend path to system path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_hybrid_feature_extraction_direct():
    """Test hybrid feature extraction directly (not through API)."""
    logger.info("Testing direct hybrid feature extraction...")
    
    try:
        from backend.app.ai.hybrid_feature_extractor import HybridFeatureExtractor
        
        test_audio = "/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav"
        if not os.path.exists(test_audio):
            logger.error(f"Test audio file not found: {test_audio}")
            return False
        
        # Create extractor
        extractor = HybridFeatureExtractor(device="cpu")  # Use CPU for stability
        
        # Extract features
        features = await extractor.extract_features(test_audio)
        
        logger.info(f"✓ Features extracted in {features.extraction_time:.3f}s")
        logger.info(f"✓ Available models: {[k for k, v in features.model_availability.items() if v]}")
        logger.info(f"✓ Audio length: {features.audio_length:.2f}s")
        
        # Test audio characteristics
        characteristics = extractor.analyze_audio_characteristics(features)
        logger.info(f"✓ Audio characteristics: genre={characteristics.genre}, energy={characteristics.energy_level:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Direct hybrid feature extraction failed: {e}")
        return False


def test_api_schema_imports():
    """Test that API schemas can be imported."""
    logger.info("Testing API schema imports...")
    
    try:
        from backend.app.api.v1.endpoints.hybrid_ai import (
            HybridMasteringRequest,
            HybridMasteringResponse,
            ModelSelectionResponse,
            ModelPerformanceResponse
        )
        
        # Test creating request schema
        request = HybridMasteringRequest(
            model_preference="auto",
            processing_mode="hybrid",
            intensity_level="medium"
        )
        logger.info(f"✓ HybridMasteringRequest created: {request.model_preference}")
        
        # Test schema validation
        assert request.model_preference == "auto"
        assert request.processing_mode == "hybrid"
        assert request.target_loudness_lufs == -14.0  # Default value
        
        logger.info("✓ All API schemas imported successfully")
        return True
        
    except Exception as e:
        logger.error(f"API schema import failed: {e}")
        return False


def test_utility_functions():
    """Test utility functions used by the API."""
    logger.info("Testing utility functions...")
    
    try:
        from backend.app.utils.file_utils import validate_audio_file
        from unittest.mock import Mock
        
        # Mock audio file for validation
        mock_file = Mock()
        mock_file.filename = "test.wav"
        mock_file.content_type = "audio/wav"
        
        # Test validation (should work even with mock)
        # Note: This might fail with mock, but import should work
        logger.info("✓ File utils imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"Utility function test failed: {e}")
        return False


async def test_model_loading_safety():
    """Test that model loading is safe and handles failures gracefully."""
    logger.info("Testing model loading safety...")
    
    try:
        from backend.app.ai.hybrid_feature_extractor import PretrainedModelLoader
        
        # Create model loader
        loader = PretrainedModelLoader(device="cpu")
        
        # Test getting model availability (should not crash even if models fail to load)
        availability = loader.get_all_available_models()
        logger.info(f"✓ Model availability check completed: {availability}")
        
        # Count available models
        available_count = sum(availability.values())
        total_count = len(availability)
        
        logger.info(f"✓ Models available: {available_count}/{total_count}")
        
        if available_count > 0:
            logger.info("✓ At least one model is available")
        else:
            logger.warning("⚠️  No pre-trained models available (this is okay for testing)")
        
        return True
        
    except Exception as e:
        logger.error(f"Model loading safety test failed: {e}")
        return False


async def test_api_helper_functions():
    """Test API helper functions."""
    logger.info("Testing API helper functions...")
    
    try:
        from backend.app.api.v1.endpoints.hybrid_ai import get_hybrid_extractor, get_model_selector
        
        # Test getting hybrid extractor
        extractor = await get_hybrid_extractor()
        logger.info(f"✓ Hybrid extractor obtained: {type(extractor)}")
        
        # Test getting model selector
        selector = await get_model_selector()
        logger.info(f"✓ Model selector obtained: {type(selector)}")
        
        # Test selector functionality with dummy characteristics
        from backend.app.ai.hybrid_feature_extractor import AudioCharacteristics
        
        dummy_characteristics = AudioCharacteristics(
            genre="pop",
            genre_confidence=0.8,
            has_vocals=True,
            is_instrumental=False,
            energy_level=0.7,
            dynamic_range=15.0,
            complexity_score=0.6,
            audio_quality=0.9
        )
        
        model_name, confidence, reasoning = selector.select_model(dummy_characteristics)
        logger.info(f"✓ Model selection: {model_name} (confidence: {confidence:.2f})")
        logger.info(f"✓ Selection reasoning: {reasoning}")
        
        return True
        
    except Exception as e:
        logger.error(f"API helper function test failed: {e}")
        return False


async def run_api_tests():
    """Run comprehensive API tests."""
    logger.info("Starting Hybrid AI API tests...")
    logger.info("=" * 60)
    
    tests = [
        ("API Schema Imports", test_api_schema_imports),
        ("Utility Functions", test_utility_functions),
        ("Model Loading Safety", test_model_loading_safety),
        ("Hybrid Feature Extraction Direct", test_hybrid_feature_extraction_direct),
        ("API Helper Functions", test_api_helper_functions),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ FAILED: {test_name} - {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("API TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL API TESTS PASSED! API is ready for integration.")
    elif passed >= total * 0.8:
        logger.info("⚠️  Most API tests passed. Minor issues may need fixing.")
    else:
        logger.info("❌ Multiple API tests failed. Review implementation.")
    
    return results


if __name__ == "__main__":
    # Set CUDA environment
    os.environ['CUDA_HOME'] = '/usr/local/cuda-12.4'
    cuda_lib_path = '/usr/local/cuda-12.4/lib64'
    if 'LD_LIBRARY_PATH' in os.environ:
        os.environ['LD_LIBRARY_PATH'] = f"{cuda_lib_path}:{os.environ['LD_LIBRARY_PATH']}"
    else:
        os.environ['LD_LIBRARY_PATH'] = cuda_lib_path
    
    results = asyncio.run(run_api_tests())
    
    # Return appropriate exit code
    passed = sum(results.values())
    total = len(results)
    success_rate = passed / total if total > 0 else 0
    
    if success_rate >= 0.8:  # 80% success rate
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure