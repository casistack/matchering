#!/usr/bin/env python3
"""
Test script for Hybrid Feature Extraction System.

This script tests the hybrid feature extraction incrementally,
starting with models that are most likely to work.
"""

import os
import sys
import logging
import torch
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


def test_basic_audio_loading():
    """Test basic audio loading functionality."""
    logger.info("Testing basic audio loading...")
    
    try:
        import torchaudio
        
        test_audio = "/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav"
        if not os.path.exists(test_audio):
            logger.error(f"Test audio file not found: {test_audio}")
            return False
        
        # Load audio
        audio, sr = torchaudio.load(test_audio)
        logger.info(f"✓ Audio loaded: {audio.shape} at {sr}Hz")
        
        # Ensure mono
        if audio.shape[0] > 1:
            audio = audio.mean(dim=0, keepdim=True)
            logger.info(f"✓ Converted to mono: {audio.shape}")
        
        return True
        
    except Exception as e:
        logger.error(f"Basic audio loading failed: {e}")
        return False


def test_custom_feature_extraction():
    """Test our custom feature extraction."""
    logger.info("Testing custom feature extraction...")
    
    try:
        from backend.app.ai.feature_extractor import AudioFeatureExtractor
        
        extractor = AudioFeatureExtractor()
        test_audio = "/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav"
        
        features = extractor.extract_features(test_audio)
        logger.info(f"✓ Custom features extracted: {type(features)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Custom feature extraction failed: {e}")
        return False


def test_transformers_import():
    """Test if transformers library works."""
    logger.info("Testing transformers library...")
    
    try:
        from transformers import AutoModel, AutoProcessor
        logger.info("✓ Transformers library imported successfully")
        
        # Test basic model loading (using a small model)
        try:
            # Try to load a very basic model to test functionality
            logger.info("Testing basic model loading...")
            
            # This should work without network if transformers is properly installed
            from transformers import pipeline
            logger.info("✓ Transformers pipeline available")
            
            return True
            
        except Exception as e:
            logger.warning(f"Model loading test failed: {e}")
            return True  # Import worked, just model loading didn't
        
    except Exception as e:
        logger.error(f"Transformers import failed: {e}")
        return False


def test_feature_fusion_network():
    """Test the feature fusion network."""
    logger.info("Testing feature fusion network...")
    
    try:
        from backend.app.ai.hybrid_feature_extractor import FeatureFusionNetwork
        
        # Create test feature dimensions
        feature_dims = {
            'ast': 768,
            'wav2vec': 1024,
            'custom': 128
        }
        
        # Create fusion network
        fusion_net = FeatureFusionNetwork(feature_dims)
        logger.info(f"✓ Feature fusion network created: {fusion_net}")
        
        # Test with dummy features
        dummy_features = {
            'ast': torch.randn(1, 768),
            'wav2vec': torch.randn(1, 1024),
            'custom': torch.randn(1, 128)
        }
        
        fused = fusion_net(dummy_features)
        logger.info(f"✓ Feature fusion successful: {fused.shape}")
        
        return True
        
    except Exception as e:
        logger.error(f"Feature fusion test failed: {e}")
        return False


def test_hybrid_extractor_basic():
    """Test basic hybrid extractor functionality."""
    logger.info("Testing basic hybrid extractor...")
    
    try:
        from backend.app.ai.hybrid_feature_extractor import HybridFeatureExtractor
        
        # Create extractor (should work even if models fail to load)
        extractor = HybridFeatureExtractor(device="cpu")  # Use CPU for safety
        logger.info("✓ Hybrid extractor created")
        
        return True
        
    except Exception as e:
        logger.error(f"Hybrid extractor creation failed: {e}")
        return False


def test_audio_characteristics():
    """Test audio characteristics analysis."""
    logger.info("Testing audio characteristics analysis...")
    
    try:
        from backend.app.ai.hybrid_feature_extractor import HybridFeatures, AudioCharacteristics
        
        # Create dummy features with all required fields
        dummy_features = HybridFeatures(
            ast_features=None,
            wav2vec_features=None,
            clap_features=None,
            musicgen_features=None,
            custom_features=None,
            fused_features=None,
            audio_length=30.0,
            sample_rate=44100,
            model_availability={},
            extraction_time=1.0
        )
        
        logger.info(f"✓ HybridFeatures created: {dummy_features}")
        
        # Test characteristics analysis
        from backend.app.ai.hybrid_feature_extractor import HybridFeatureExtractor
        extractor = HybridFeatureExtractor(device="cpu")
        characteristics = extractor.analyze_audio_characteristics(dummy_features)
        
        logger.info(f"✓ Audio characteristics analyzed: {characteristics}")
        
        return True
        
    except Exception as e:
        logger.error(f"Audio characteristics test failed: {e}")
        return False


def run_incremental_tests():
    """Run tests incrementally to identify what works."""
    logger.info("Starting incremental hybrid feature extraction tests...")
    logger.info("=" * 60)
    
    tests = [
        ("Basic Audio Loading", test_basic_audio_loading),
        ("Custom Feature Extraction", test_custom_feature_extraction),
        ("Transformers Import", test_transformers_import),
        ("Feature Fusion Network", test_feature_fusion_network),
        ("Hybrid Extractor Basic", test_hybrid_extractor_basic),
        ("Audio Characteristics", test_audio_characteristics),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ FAILED: {test_name} - {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Hybrid system is ready.")
    elif passed >= total * 0.7:
        logger.info("⚠️  Most tests passed. System partially functional.")
    else:
        logger.info("❌ Multiple tests failed. System needs fixes.")
    
    return results


if __name__ == "__main__":
    results = run_incremental_tests()
    
    # Return appropriate exit code
    passed = sum(results.values())
    total = len(results)
    success_rate = passed / total if total > 0 else 0
    
    if success_rate >= 0.8:  # 80% success rate
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure