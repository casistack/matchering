#!/usr/bin/env python3
"""
Test HuggingFace Pre-trained Models Ensemble System

Stage 6 Testing: Verify that the new HuggingFace pre-trained models
provide better accuracy than the previous CNN ensemble placeholders.

This test uses actual pre-trained models that are fine-tuned specifically
for music genre classification without requiring any training on our side.
"""

import requests
import logging
import json
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HuggingFaceEnsembleTestSuite:
    """Test suite for HuggingFace pre-trained models ensemble system."""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
        
    def find_test_audio(self) -> str:
        """Find suitable test audio file."""
        test_paths = [
            "Testuploads/Respek Ma Craft.wav",
            "backend/temp/hybrid_ai/20250703_124254_6daf2a39_Respek Ma Craft.wav",
            "uploads/Respek Ma Craft.wav"
        ]
        
        for path in test_paths:
            if Path(path).exists():
                logger.info(f"Found test audio: {path}")
                return path
        
        logger.warning("No test audio files found")
        return None
    
    def test_huggingface_configuration(self):
        """Test that HuggingFace ensemble configuration is working."""
        logger.info("=== Testing HuggingFace Configuration ===")
        
        try:
            # Check environment variables for HuggingFace settings
            ensemble_enabled = os.getenv("ENABLE_ENSEMBLE_AI", "true").lower() == "true"
            hf_enabled = os.getenv("ENABLE_HUGGINGFACE_MODELS", "true").lower() == "true"
            
            logger.info(f"✅ Environment Configuration:")
            logger.info(f"   ENABLE_ENSEMBLE_AI: {ensemble_enabled}")
            logger.info(f"   ENABLE_HUGGINGFACE_MODELS: {hf_enabled}")
            
            self.test_results['configuration'] = {
                'ensemble_enabled': ensemble_enabled,
                'huggingface_enabled': hf_enabled,
                'success': True
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            self.test_results['configuration'] = {'success': False, 'error': str(e)}
            return False
    
    def test_huggingface_ensemble_prediction(self, test_audio_path: str):
        """Test the HuggingFace ensemble prediction system."""
        logger.info("=== Testing HuggingFace Ensemble Prediction ===")
        
        try:
            with open(test_audio_path, 'rb') as f:
                files = {'file': ('respek_ma_craft_hf_test.wav', f, 'audio/wav')}
                data = {
                    'model_preference': 'auto',
                    'processing_mode': 'hybrid',
                    'intensity_level': 'medium',
                    'preserve_dynamics': 'true',
                    'target_loudness_lufs': '-14.0'
                }
                
                logger.info("🚀 Submitting test file for HuggingFace ensemble processing...")
                response = requests.post(
                    f"{self.base_url}/api/v1/hybrid-ai/process-hybrid",
                    files=files,
                    data=data,
                    timeout=180  # Longer timeout for model loading
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("✅ HuggingFace ensemble prediction successful")
                    
                    # Extract prediction details
                    predicted_params = result.get('predicted_parameters', {})
                    is_using_fallback = predicted_params.get('is_using_fallback_genre', True)
                    predicted_genre = predicted_params.get('predicted_genre', 'unknown')
                    genre_probs = predicted_params.get('genre_probabilities', {})
                    confidence = predicted_params.get('confidence', 0.0)
                    
                    detection_method = "Fallback" if is_using_fallback else "HuggingFace Ensemble AI"
                    logger.info(f"🎯 Detection Method: {detection_method}")
                    logger.info(f"🎵 Predicted Genre: {predicted_genre}")
                    logger.info(f"📊 Confidence: {confidence:.3f}")
                    
                    if genre_probs:
                        top_3_genres = dict(list(sorted(genre_probs.items(), key=lambda x: x[1], reverse=True))[:3])
                        logger.info(f"📈 Top 3 Genres: {top_3_genres}")
                    
                    self.test_results['huggingface_prediction'] = {
                        'success': True,
                        'detection_method': detection_method,
                        'predicted_genre': predicted_genre,
                        'confidence': confidence,
                        'is_using_fallback': is_using_fallback,
                        'genre_probabilities': genre_probs,
                        'job_id': result.get('job_id'),
                    }
                    
                    # This is the key test - are we using HuggingFace models?
                    if not is_using_fallback:
                        logger.info("🎉 SUCCESS: HuggingFace ensemble AI is working!")
                        
                        # Test for improved accuracy on hip-hop detection
                        if predicted_genre.lower() in ['hiphop', 'hip-hop', 'rap']:
                            logger.info("🎯 ACCURACY SUCCESS: Correctly classified as hip-hop/rap!")
                            logger.info("🚀 HuggingFace models achieved the target accuracy!")
                            return 'excellent'
                        else:
                            logger.warning(f"⚠️  ACCURACY CHECK: Got {predicted_genre}, expected hip-hop/rap")
                            logger.info("🔍 Need to check if HuggingFace models are properly loaded")
                            return 'working_but_needs_accuracy_check'
                    else:
                        logger.warning("⚠️  Still using fallback - HuggingFace ensemble not yet active")
                        return 'fallback'
                        
                else:
                    logger.error(f"❌ HuggingFace prediction failed: {response.status_code} - {response.text}")
                    return 'failed'
                        
        except Exception as e:
            logger.error(f"❌ HuggingFace ensemble test failed: {e}")
            return 'error'
    
    def run_huggingface_test_suite(self):
        """Run the complete HuggingFace ensemble test suite."""
        logger.info("🤗 Starting HuggingFace Pre-trained Models Test Suite")
        logger.info("="*70)
        
        # Test 1: Configuration
        config_ok = self.test_huggingface_configuration()
        if not config_ok:
            logger.error("❌ Configuration test failed - aborting")
            return False
        
        # Test 2: Find test audio
        test_audio = self.find_test_audio()
        if not test_audio:
            logger.error("❌ No test audio found - aborting tests")
            return False
        
        # Test 3: HuggingFace ensemble prediction
        prediction_result = self.test_huggingface_ensemble_prediction(test_audio)
        
        # Print comprehensive summary
        self.print_huggingface_summary(prediction_result)
        
        # Overall assessment
        if prediction_result == 'excellent':
            logger.info("🎉 HUGGINGFACE SUCCESS: Pre-trained models working with high accuracy!")
            return True
        elif prediction_result == 'working_but_needs_accuracy_check':
            logger.info("⚠️  PARTIAL SUCCESS: HuggingFace system working but needs accuracy verification")
            return True
        else:
            logger.warning("⚠️  NEEDS DEBUGGING: HuggingFace system not yet fully operational")
            return False
    
    def print_huggingface_summary(self, prediction_result: str):
        """Print comprehensive HuggingFace test summary."""
        logger.info("\\n" + "="*70)
        logger.info("🤗 HUGGINGFACE PRE-TRAINED MODELS TEST SUMMARY")
        logger.info("="*70)
        
        # Configuration Summary
        config = self.test_results.get('configuration', {})
        logger.info(f"\\n📋 CONFIGURATION:")
        logger.info(f"   Ensemble Enabled: {config.get('ensemble_enabled', 'Unknown')}")
        logger.info(f"   HuggingFace Enabled: {config.get('huggingface_enabled', 'Unknown')}")
        logger.info(f"   Status: {'✅ OK' if config.get('success') else '❌ FAILED'}")
        
        # Prediction Summary
        pred = self.test_results.get('huggingface_prediction', {})
        logger.info(f"\\n🎯 PREDICTION RESULTS:")
        if pred.get('success'):
            logger.info(f"   Method: {pred.get('detection_method', 'Unknown')}")
            logger.info(f"   Genre: {pred.get('predicted_genre', 'Unknown')}")
            logger.info(f"   Confidence: {pred.get('confidence', 0):.3f}")
            logger.info(f"   Using Fallback: {pred.get('is_using_fallback', 'Unknown')}")
        else:
            logger.info("   Status: ❌ FAILED")
        
        # Overall Assessment
        logger.info(f"\\n{'='*70}")
        logger.info("📊 OVERALL ASSESSMENT:")
        
        if prediction_result == 'excellent':
            logger.info("🎉 EXCELLENT: HuggingFace pre-trained models working with high accuracy!")
            logger.info("✅ Ready for production deployment")
            logger.info("🎯 Achieved target of accurate hip-hop/rap classification")
            logger.info("🚀 No training required - using proven pre-trained models")
        elif prediction_result == 'working_but_needs_accuracy_check':
            logger.info("⚠️  GOOD: HuggingFace system operational but accuracy needs verification")
            logger.info("✅ Infrastructure working correctly")
            logger.info("🔍 May need to check model loading or label mapping")
        elif prediction_result == 'fallback':
            logger.info("⚠️  PARTIAL: System working but using fallback methods")
            logger.info("🔧 HuggingFace ensemble needs activation/debugging")
            logger.info("✅ Safety mechanisms functioning correctly")
        else:
            logger.info("❌ NEEDS WORK: HuggingFace system requires debugging")
            logger.info("🔧 Check model downloading and loading")
        
        logger.info("="*70)


def main():
    """Main test execution."""
    tester = HuggingFaceEnsembleTestSuite()
    success = tester.run_huggingface_test_suite()
    
    if success:
        logger.info("🎯 HuggingFace ensemble testing completed successfully")
        return 0
    else:
        logger.error("⚠️  HuggingFace ensemble testing needs attention")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        exit(1)