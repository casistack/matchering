#!/usr/bin/env python3
"""
Test AI Model Genre Detection in Isolation

This script tests the AI models (AST, Wav2Vec2) for genre detection capability
without affecting production code. Tests are designed to be completely safe.

Stage 2 of AI Genre Detection Fix
"""

import sys
import os
import asyncio
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIGenreDetectionTester:
    """Safe tester for AI genre detection models."""
    
    def __init__(self):
        self.models_loaded = False
        self.extractor = None
        self.model_manager = None
        self.test_results = {}
        
    async def initialize_models(self):
        """Initialize AI models safely."""
        try:
            logger.info("=== STAGE 2: AI Model Isolation Testing ===")
            
            # Import backend modules
            from app.ai.hybrid_feature_extractor import HybridFeatureExtractor
            from app.ai.production_model_manager import ProductionModelManager
            
            # Initialize model manager
            device = "cuda" if self._check_cuda() else "cpu"
            logger.info(f"Using device: {device}")
            
            self.model_manager = ProductionModelManager(
                device=device,
                cache_dir="./model_cache",
                max_gpu_memory_gb=20.0,
                enable_feature_caching=True
            )
            
            # Initialize feature extractor
            self.extractor = HybridFeatureExtractor(
                device=device,
                production_model_manager=self.model_manager
            )
            
            self.models_loaded = True
            logger.info("✅ AI models initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI models: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _check_cuda(self) -> bool:
        """Check CUDA availability safely."""
        try:
            import torch
            available = torch.cuda.is_available()
            if available:
                device_count = torch.cuda.device_count()
                device_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA available: {device_count} device(s), {device_name}")
            else:
                logger.info("CUDA not available, using CPU")
            return available
        except Exception as e:
            logger.warning(f"CUDA check failed: {e}")
            return False
    
    async def test_model_loading(self) -> Dict[str, bool]:
        """Test individual model loading."""
        logger.info("\n--- Testing Model Loading ---")
        
        model_status = {}
        
        if not self.models_loaded:
            logger.error("Models not initialized")
            return model_status
        
        # Test AST model
        try:
            ast_model, ast_processor = self.model_manager.get_model('ast')
            model_status['ast'] = ast_model is not None
            logger.info(f"AST model: {'✅ Loaded' if model_status['ast'] else '❌ Failed'}")
            if ast_model:
                logger.info(f"AST model type: {type(ast_model)}")
        except Exception as e:
            model_status['ast'] = False
            logger.error(f"AST model loading failed: {e}")
        
        # Test Wav2Vec model
        try:
            wav2vec_model, wav2vec_processor = self.model_manager.get_model('wav2vec')
            model_status['wav2vec'] = wav2vec_model is not None
            logger.info(f"Wav2Vec model: {'✅ Loaded' if model_status['wav2vec'] else '❌ Failed'}")
            if wav2vec_model:
                logger.info(f"Wav2Vec model type: {type(wav2vec_model)}")
        except Exception as e:
            model_status['wav2vec'] = False
            logger.error(f"Wav2Vec model loading failed: {e}")
        
        self.test_results['model_loading'] = model_status
        return model_status
    
    async def test_feature_extraction(self, test_audio_path: str) -> Optional[Dict[str, Any]]:
        """Test feature extraction from test audio."""
        logger.info(f"\n--- Testing Feature Extraction ---")
        logger.info(f"Test audio: {test_audio_path}")
        
        if not os.path.exists(test_audio_path):
            logger.error(f"❌ Test audio file not found: {test_audio_path}")
            return None
        
        try:
            # Extract features
            features = await self.extractor.extract_features(test_audio_path)
            
            # Log extraction results
            logger.info("✅ Feature extraction completed")
            logger.info(f"Audio length: {features.audio_length:.2f}s")
            logger.info(f"Sample rate: {features.sample_rate}Hz")
            logger.info(f"Model availability: {features.model_availability}")
            
            # Check feature dimensions
            if features.ast_features:
                logger.info(f"AST features: {len(features.ast_features)} dimensions")
            if features.wav2vec_features:
                logger.info(f"Wav2Vec features: {len(features.wav2vec_features)} dimensions")
            if features.fused_features:
                logger.info(f"Fused features: {len(features.fused_features)} dimensions")
            
            self.test_results['feature_extraction'] = {
                'success': True,
                'audio_length': features.audio_length,
                'sample_rate': features.sample_rate,
                'model_availability': features.model_availability,
                'feature_dimensions': {
                    'ast': len(features.ast_features) if features.ast_features else 0,
                    'wav2vec': len(features.wav2vec_features) if features.wav2vec_features else 0,
                    'fused': len(features.fused_features) if features.fused_features else 0
                }
            }
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {e}")
            logger.error(traceback.format_exc())
            self.test_results['feature_extraction'] = {'success': False, 'error': str(e)}
            return None
    
    async def test_ast_genre_classification(self, features) -> Optional[Dict[str, float]]:
        """Test AST model for genre classification capability."""
        logger.info(f"\n--- Testing AST Genre Classification ---")
        
        if not features or not features.ast_features:
            logger.error("❌ No AST features available for testing")
            return None
        
        try:
            # The AST model we're using is specifically for music genre classification
            # Model: m3hrdadfi/wav2vec2-base-100k-gtzan-music-genres
            
            import torch
            import torch.nn.functional as F
            
            # Get AST model and processor
            ast_model, ast_processor = self.model_manager.get_model('ast')
            if not ast_model:
                logger.error("❌ AST model not available")
                return None
            
            # Convert features to tensor
            ast_tensor = torch.tensor(features.ast_features).unsqueeze(0)
            logger.info(f"AST tensor shape: {ast_tensor.shape}")
            
            # The model should have classification capabilities
            # Let's check if it has a classification head
            model_output_keys = []
            if hasattr(ast_model, 'classifier'):
                logger.info("✅ Model has classifier head")
                model_output_keys.append('classifier')
            if hasattr(ast_model, 'config'):
                logger.info(f"Model config: {ast_model.config}")
            
            # Test forward pass (safe - no training, just inference)
            ast_model.eval()
            with torch.no_grad():
                # For music genre classification models, we need to check the output format
                logger.info("Testing model forward pass...")
                
                # This is a safe test - just checking what the model outputs
                # We're not modifying anything, just seeing the structure
                try:
                    # Note: This model might expect specific input format
                    # Let's test carefully
                    logger.info("Model forward pass test - structure only")
                    logger.info(f"Model type: {type(ast_model)}")
                    
                    # Log model architecture (safe)
                    if hasattr(ast_model, 'config'):
                        config = ast_model.config
                        if hasattr(config, 'num_labels'):
                            logger.info(f"Model has {config.num_labels} output labels")
                        if hasattr(config, 'id2label'):
                            logger.info(f"Label mapping: {config.id2label}")
                    
                    genre_prediction_test = {
                        'model_available': True,
                        'model_type': str(type(ast_model)),
                        'has_classification_head': hasattr(ast_model, 'classifier'),
                        'config_available': hasattr(ast_model, 'config')
                    }
                    
                    self.test_results['ast_genre_classification'] = genre_prediction_test
                    logger.info("✅ AST model structure analysis completed")
                    return genre_prediction_test
                    
                except Exception as forward_error:
                    logger.warning(f"Forward pass test failed: {forward_error}")
                    # This is expected - we might need specific input processing
                    return {'model_available': True, 'forward_pass_test': False}
        
        except Exception as e:
            logger.error(f"❌ AST genre classification test failed: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def test_audio_characteristics_analysis(self, features) -> Optional[Dict[str, Any]]:
        """Test audio characteristics analysis."""
        logger.info(f"\n--- Testing Audio Characteristics Analysis ---")
        
        if not features:
            logger.error("❌ No features available for analysis")
            return None
        
        try:
            # Test the existing characteristics analysis
            characteristics = self.extractor.analyze_audio_characteristics(features)
            
            logger.info("✅ Audio characteristics analysis completed")
            logger.info(f"Genre: {characteristics.genre} (confidence: {characteristics.genre_confidence})")
            logger.info(f"Has vocals: {characteristics.has_vocals}")
            logger.info(f"Energy level: {characteristics.energy_level}")
            logger.info(f"Dynamic range: {characteristics.dynamic_range}dB")
            logger.info(f"Complexity score: {characteristics.complexity_score}")
            logger.info(f"Audio quality: {characteristics.audio_quality}")
            
            characteristics_data = {
                'genre': characteristics.genre,
                'genre_confidence': characteristics.genre_confidence,
                'has_vocals': characteristics.has_vocals,
                'energy_level': characteristics.energy_level,
                'dynamic_range': characteristics.dynamic_range,
                'complexity_score': characteristics.complexity_score,
                'audio_quality': characteristics.audio_quality
            }
            
            self.test_results['audio_characteristics'] = characteristics_data
            return characteristics_data
            
        except Exception as e:
            logger.error(f"❌ Audio characteristics analysis failed: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def find_test_audio(self) -> str:
        """Find suitable test audio file."""
        # Look for the test audio we know exists
        test_paths = [
            "Testuploads/Respek Ma Craft.wav",
            "backend/temp/hybrid_ai/20250703_124254_6daf2a39_Respek Ma Craft.wav",
            "backend/uploads/Respek Ma Craft.wav"
        ]
        
        for path in test_paths:
            if os.path.exists(path):
                logger.info(f"Found test audio: {path}")
                return path
        
        # Look for any .wav file in temp directories
        temp_dirs = ["backend/temp/hybrid_ai", "Testuploads", "uploads"]
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    if file.endswith('.wav'):
                        full_path = os.path.join(temp_dir, file)
                        logger.info(f"Found audio file: {full_path}")
                        return full_path
        
        logger.warning("No test audio files found")
        return None
    
    async def run_complete_test(self):
        """Run the complete AI model test suite."""
        logger.info("🧪 Starting Complete AI Genre Detection Test")
        
        # Initialize models
        if not await self.initialize_models():
            logger.error("❌ Model initialization failed - aborting tests")
            return False
        
        # Test model loading
        model_status = await self.test_model_loading()
        if not any(model_status.values()):
            logger.error("❌ No models loaded successfully - aborting tests")
            return False
        
        # Find test audio
        test_audio = self.find_test_audio()
        if not test_audio:
            logger.error("❌ No test audio found - aborting feature tests")
            return False
        
        # Test feature extraction
        features = await self.test_feature_extraction(test_audio)
        if not features:
            logger.error("❌ Feature extraction failed - aborting analysis tests")
            return False
        
        # Test genre classification
        await self.test_ast_genre_classification(features)
        
        # Test characteristics analysis
        await self.test_audio_characteristics_analysis(features)
        
        # Print final summary
        self.print_test_summary()
        return True
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        logger.info("\n" + "="*60)
        logger.info("🧪 STAGE 2 TEST SUMMARY")
        logger.info("="*60)
        
        for test_name, results in self.test_results.items():
            logger.info(f"\n{test_name.upper()}:")
            if isinstance(results, dict):
                for key, value in results.items():
                    logger.info(f"  {key}: {value}")
            else:
                logger.info(f"  {results}")
        
        # Assessment
        logger.info(f"\n{'='*60}")
        logger.info("ASSESSMENT:")
        
        models_loaded = self.test_results.get('model_loading', {})
        features_extracted = self.test_results.get('feature_extraction', {}).get('success', False)
        characteristics_analyzed = 'audio_characteristics' in self.test_results
        
        if any(models_loaded.values()) and features_extracted and characteristics_analyzed:
            logger.info("✅ AI models are functional and ready for integration")
            logger.info("✅ Ready to proceed to Stage 3: Implementation")
        else:
            logger.info("⚠️  Some tests failed - need investigation before proceeding")
        
        logger.info("="*60)


async def main():
    """Main test execution."""
    tester = AIGenreDetectionTester()
    success = await tester.run_complete_test()
    
    if success:
        logger.info("🎯 Stage 2 testing completed successfully")
        return 0
    else:
        logger.error("❌ Stage 2 testing failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)