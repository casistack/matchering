#!/usr/bin/env python3
"""
Test Stage 3: AI-First Genre Detection Integration

This script tests that our new AI-first genre detection is working correctly
in the production pipeline by making actual API calls.

Stage 3 Testing
"""

import requests
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIGenreIntegrationTester:
    """Test the AI-first genre detection integration."""
    
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
    
    def test_extract_features_endpoint(self, test_audio_path: str):
        """Test the extract features endpoint to see what features we get."""
        logger.info("=== Testing Feature Extraction Endpoint ===")
        
        try:
            with open(test_audio_path, 'rb') as f:
                files = {'file': ('test_audio.wav', f, 'audio/wav')}
                data = {
                    'include_model_features': 'true',
                    'cache_result': 'true'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/hybrid-ai/extract-hybrid-features",
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("✅ Feature extraction successful")
                    logger.info(f"Models used: {result.get('extraction_metadata', {}).get('models_used', [])}")
                    logger.info(f"Model availability: {result.get('model_availability', {})}")
                    
                    features = result.get('features', {})
                    if features.get('ast_features'):
                        logger.info(f"AST features: {len(features['ast_features'])} dimensions")
                    if features.get('wav2vec_features'):
                        logger.info(f"Wav2Vec features: {len(features['wav2vec_features'])} dimensions")
                    
                    self.test_results['feature_extraction'] = {
                        'success': True,
                        'models_available': result.get('model_availability', {}),
                        'features_extracted': {k: len(v) if v else 0 for k, v in features.items() if v}
                    }
                    return True
                else:
                    logger.error(f"❌ Feature extraction failed: {response.status_code} - {response.text}")
                    return False
                            
        except Exception as e:
            logger.error(f"❌ Feature extraction test failed: {e}")
            return False
    
    def test_hybrid_processing_with_ai_genre(self, test_audio_path: str):
        """Test the full hybrid processing with AI genre detection."""
        logger.info("=== Testing Hybrid Processing with AI Genre Detection ===")
        
        try:
            with open(test_audio_path, 'rb') as f:
                files = {'file': ('test_audio.wav', f, 'audio/wav')}
                data = {
                    'model_preference': 'auto',
                    'processing_mode': 'hybrid',
                    'intensity_level': 'medium',
                    'preserve_dynamics': 'true',
                    'target_loudness_lufs': '-14.0'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/hybrid-ai/process-hybrid",
                    files=files,
                    data=data,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("✅ Hybrid processing successful")
                    
                    # Check if we used AI or fallback genre detection
                    predicted_params = result.get('predicted_parameters', {})
                    is_using_fallback = predicted_params.get('is_using_fallback_genre', True)
                    predicted_genre = predicted_params.get('predicted_genre', 'unknown')
                    genre_probs = predicted_params.get('genre_probabilities', {})
                    
                    detection_method = "Fallback" if is_using_fallback else "AI Models"
                    logger.info(f"🎯 Genre Detection Method: {detection_method}")
                    logger.info(f"🎵 Predicted Genre: {predicted_genre}")
                    logger.info(f"📊 Top 3 Genres: {dict(list(sorted(genre_probs.items(), key=lambda x: x[1], reverse=True))[:3])}")
                    
                    self.test_results['hybrid_processing'] = {
                        'success': True,
                        'genre_detection_method': detection_method,
                        'predicted_genre': predicted_genre,
                        'is_using_fallback': is_using_fallback,
                        'genre_probabilities': genre_probs,
                        'job_id': result.get('job_id'),
                        'model_used': result.get('model_used')
                    }
                    
                    # This is the key test - did we use AI models?
                    if not is_using_fallback:
                        logger.info("🎉 SUCCESS: AI models are being used for genre detection!")
                        return True
                    else:
                        logger.warning("⚠️  Still using fallback detection - need to investigate")
                        return False
                        
                else:
                    logger.error(f"❌ Hybrid processing failed: {response.status_code} - {response.text}")
                    return False
                        
        except Exception as e:
            logger.error(f"❌ Hybrid processing test failed: {e}")
            return False
    
    def run_integration_test(self):
        """Run the complete integration test."""
        logger.info("🧪 Starting Stage 3 AI Genre Detection Integration Test")
        
        # Find test audio
        test_audio = self.find_test_audio()
        if not test_audio:
            logger.error("❌ No test audio found - aborting tests")
            return False
        
        # Test feature extraction first
        features_ok = self.test_extract_features_endpoint(test_audio)
        if not features_ok:
            logger.error("❌ Feature extraction failed - aborting integration test")
            return False
        
        # Test full hybrid processing with AI genre detection
        integration_ok = self.test_hybrid_processing_with_ai_genre(test_audio)
        
        # Print summary
        self.print_test_summary()
        
        return integration_ok
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        logger.info("\n" + "="*60)
        logger.info("🧪 STAGE 3 INTEGRATION TEST SUMMARY")
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
        
        hybrid_results = self.test_results.get('hybrid_processing', {})
        ai_detection_working = not hybrid_results.get('is_using_fallback', True)
        
        if ai_detection_working:
            logger.info("🎉 SUCCESS: AI-first genre detection is working!")
            logger.info("✅ Stage 3 implementation successful")
            logger.info("✅ Ready to proceed to Stage 4: Comprehensive Testing")
        else:
            logger.info("⚠️  AI detection not yet working - need debugging")
            logger.info("📋 Still using fallback detection method")
            if hybrid_results.get('success'):
                logger.info("✅ But system still works with fallback (safe)")
        
        logger.info("="*60)


def main():
    """Main test execution."""
    tester = AIGenreIntegrationTester()
    success = tester.run_integration_test()
    
    if success:
        logger.info("🎯 Stage 3 integration testing completed successfully")
        return 0
    else:
        logger.error("⚠️  Stage 3 integration testing needs debugging")
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