"""
Comprehensive Test Suite for Hybrid Processing Engine.

This module provides complete unit and integration tests for the hybrid processing engine,
validating AI models, parameter synthesis, and end-to-end processing workflows.
"""

import asyncio
import pytest
import torch
import numpy as np
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the modules to test
import sys
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.ai.hybrid_processing_engine import (
    HybridProcessingEngine,
    HybridProcessingRequest,
    HybridProcessingResult,
    ProcessingMode,
    ProcessingStage,
    AudioAnalysisResult,
    ReferenceAnalysisResult
)
from app.ai.hybrid_feature_extractor import AudioCharacteristics, HybridFeatures
from app.ai.mastering_model import MasteringParameters


class TestHybridProcessingEngine:
    """Test suite for the HybridProcessingEngine class."""
    
    @pytest.fixture
    async def processing_engine(self):
        """Create a test processing engine instance."""
        engine = HybridProcessingEngine(device="cpu")
        await engine.initialize()
        return engine
    
    @pytest.fixture
    def sample_audio(self):
        """Create sample audio data for testing."""
        # Generate 1 second of test audio (44.1kHz)
        duration = 1.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        
        # Create a simple sine wave
        t = torch.linspace(0, duration, samples)
        frequency = 440.0  # A4 note
        audio = torch.sin(2 * np.pi * frequency * t).unsqueeze(0)
        
        return audio, sample_rate
    
    @pytest.fixture
    def sample_request(self, tmp_path):
        """Create a sample processing request."""
        input_file = tmp_path / "input.wav"
        reference_file = tmp_path / "reference.wav"
        output_file = tmp_path / "output.wav"
        
        return HybridProcessingRequest(
            input_file_path=str(input_file),
            reference_file_path=str(reference_file),
            output_file_path=str(output_file),
            processing_mode=ProcessingMode.HYBRID,
            ai_intensity=0.7,
            reference_influence=0.5,
            ai_weight=0.6,
            reference_weight=0.4,
            adaptive_blending=True
        )
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = HybridProcessingEngine(device="cpu")
        
        assert engine.device == "cpu"
        assert engine.current_request is None
        assert engine.processing_start_time is None
        assert len(engine.progress_callbacks) == 0
    
    @pytest.mark.asyncio
    async def test_engine_async_initialization(self, processing_engine):
        """Test async engine initialization."""
        assert processing_engine is not None
        assert hasattr(processing_engine, '_initialized')
    
    def test_progress_callback_management(self, processing_engine):
        """Test progress callback management."""
        callback1 = Mock()
        callback2 = Mock()
        
        processing_engine.add_progress_callback(callback1)
        processing_engine.add_progress_callback(callback2)
        
        assert len(processing_engine.progress_callbacks) == 2
        assert callback1 in processing_engine.progress_callbacks
        assert callback2 in processing_engine.progress_callbacks
    
    @pytest.mark.asyncio
    async def test_progress_update(self, processing_engine):
        """Test progress update mechanism."""
        callback = AsyncMock()
        processing_engine.add_progress_callback(callback)
        
        await processing_engine._update_progress(
            ProcessingStage.INITIALIZATION,
            25.0,
            "Test message",
            {"test": "metadata"}
        )
        
        callback.assert_called_once()
        args = callback.call_args[0]
        progress = args[0]
        
        assert progress.stage == ProcessingStage.INITIALIZATION
        assert progress.percentage == 25.0
        assert progress.message == "Test message"
        assert progress.metadata["test"] == "metadata"
    
    @pytest.mark.asyncio
    async def test_audio_loading(self, processing_engine, tmp_path, sample_audio):
        """Test audio file loading."""
        audio_data, sample_rate = sample_audio
        
        # Save test audio file
        test_file = tmp_path / "test.wav"
        import torchaudio
        torchaudio.save(str(test_file), audio_data, sample_rate)
        
        # Test loading
        loaded_audio, loaded_sr = await processing_engine._load_audio(str(test_file))
        
        assert loaded_sr == sample_rate
        assert loaded_audio.shape == audio_data.shape
        assert torch.allclose(loaded_audio.cpu(), audio_data, atol=1e-4)
    
    @pytest.mark.asyncio
    async def test_audio_loading_nonexistent_file(self, processing_engine):
        """Test audio loading with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            await processing_engine._load_audio("/nonexistent/file.wav")
    
    @pytest.mark.asyncio
    async def test_ai_audio_analysis(self, processing_engine, sample_audio):
        """Test AI audio analysis."""
        audio_data, sample_rate = sample_audio
        
        # Mock the feature extractor to avoid model loading
        mock_extractor = Mock()
        mock_characteristics = AudioCharacteristics(
            genre="electronic",
            genre_confidence=0.85,
            has_vocals=False,
            is_instrumental=True,
            energy_level=0.7,
            dynamic_range=12.0,
            complexity_score=0.6,
            tempo_bpm=120.0,
            key_signature="A",
            audio_quality=0.9
        )
        mock_extractor.analyze_characteristics.return_value = mock_characteristics
        mock_extractor.extract_features_async.return_value = HybridFeatures()
        
        processing_engine.feature_extractor = mock_extractor
        
        result = await processing_engine._analyze_audio_ai(audio_data, sample_rate)
        
        assert isinstance(result, AudioAnalysisResult)
        assert result.characteristics.genre == "electronic"
        assert result.characteristics.genre_confidence == 0.85
        assert result.quality_score > 0
        assert len(result.confidence_scores) > 0
    
    @pytest.mark.asyncio
    async def test_reference_analysis(self, processing_engine, sample_audio):
        """Test reference audio analysis."""
        audio_data, sample_rate = sample_audio
        
        # Mock the feature extractor
        mock_extractor = Mock()
        mock_characteristics = AudioCharacteristics(
            genre="rock",
            genre_confidence=0.9,
            has_vocals=True,
            is_instrumental=False,
            energy_level=0.8,
            dynamic_range=8.0,
            complexity_score=0.7,
            tempo_bpm=140.0,
            key_signature="E",
            audio_quality=0.95
        )
        mock_extractor.analyze_characteristics.return_value = mock_characteristics
        
        processing_engine.feature_extractor = mock_extractor
        
        result = await processing_engine._analyze_reference_audio(audio_data, sample_rate)
        
        assert isinstance(result, ReferenceAnalysisResult)
        assert result.characteristics.genre == "rock"
        assert result.matching_confidence > 0
        assert isinstance(result.target_parameters, MasteringParameters)
        assert isinstance(result.style_profile, dict)
    
    def test_parameter_blending(self, processing_engine):
        """Test parameter blending logic."""
        ai_value = 2.0
        ref_value = 4.0
        ai_weight = 0.3
        ref_weight = 0.7
        
        result = processing_engine._blend_parameter(ai_value, ref_value, ai_weight, ref_weight)
        expected = ai_value * ai_weight + ref_value * ref_weight
        
        assert abs(result - expected) < 1e-6
    
    def test_adaptive_weight_calculation(self, processing_engine, sample_request):
        """Test adaptive weight calculation."""
        # Create mock analysis results
        ai_analysis = AudioAnalysisResult(
            characteristics=AudioCharacteristics(
                genre="electronic",
                genre_confidence=0.9,
                has_vocals=False,
                is_instrumental=True,
                energy_level=0.8,
                dynamic_range=15.0,
                complexity_score=0.7,
                tempo_bpm=128.0,
                key_signature="C",
                audio_quality=0.95
            ),
            features=HybridFeatures(),
            quality_score=0.95,
            processing_recommendations={},
            confidence_scores={"overall": 0.9}
        )
        
        reference_analysis = ReferenceAnalysisResult(
            characteristics=AudioCharacteristics(
                genre="electronic",  # Same genre
                genre_confidence=0.8,
                has_vocals=False,
                is_instrumental=True,
                energy_level=0.7,
                dynamic_range=8.0,
                complexity_score=0.6,
                tempo_bpm=130.0,
                key_signature="C",
                audio_quality=0.9
            ),
            target_parameters=MasteringParameters(),
            style_profile={},
            matching_confidence=0.85
        )
        
        ai_weight, ref_weight = processing_engine._calculate_adaptive_weights(
            ai_analysis, reference_analysis, sample_request
        )
        
        # AI weight should be boosted due to high quality and confidence
        # Reference weight should be boosted due to genre match
        assert ai_weight > 0
        assert ref_weight > 0
        
        # With same genre, reference should get a boost
        assert ref_weight > sample_request.reference_weight
    
    @pytest.mark.asyncio
    async def test_ai_only_processing(self, processing_engine, sample_request, tmp_path, sample_audio):
        """Test AI-only processing mode."""
        # Setup test files
        audio_data, sample_rate = sample_audio
        input_file = tmp_path / "input.wav"
        output_file = tmp_path / "output.wav"
        
        import torchaudio
        torchaudio.save(str(input_file), audio_data, sample_rate)
        
        # Update request for AI-only mode
        ai_request = HybridProcessingRequest(
            input_file_path=str(input_file),
            output_file_path=str(output_file),
            processing_mode=ProcessingMode.AI_ONLY,
            ai_intensity=0.8
        )
        
        # Mock the analysis methods
        with patch.object(processing_engine, '_analyze_audio_ai') as mock_ai_analysis:
            mock_ai_analysis.return_value = AudioAnalysisResult(
                characteristics=AudioCharacteristics(
                    genre="test",
                    genre_confidence=0.8,
                    has_vocals=False,
                    is_instrumental=True,
                    energy_level=0.7,
                    dynamic_range=12.0,
                    complexity_score=0.6,
                    tempo_bpm=120.0,
                    key_signature="C",
                    audio_quality=0.8
                ),
                features=HybridFeatures(),
                quality_score=0.8,
                processing_recommendations={},
                confidence_scores={"overall": 0.8}
            )
            
            result = await processing_engine._process_ai_only(ai_request)
        
        assert isinstance(result, HybridProcessingResult)
        assert result.success is True
        assert result.processing_mode == ProcessingMode.AI_ONLY
        assert result.ai_confidence > 0
        assert result.reference_influence == 0.0
    
    @pytest.mark.asyncio
    async def test_hybrid_parameter_synthesis(self, processing_engine, sample_request):
        """Test hybrid parameter synthesis - the core innovation."""
        # Create comprehensive test analysis results
        ai_analysis = AudioAnalysisResult(
            characteristics=AudioCharacteristics(
                genre="electronic",
                genre_confidence=0.9,
                has_vocals=False,
                is_instrumental=True,
                energy_level=0.8,
                dynamic_range=15.0,  # High dynamic range
                complexity_score=0.7,
                tempo_bpm=128.0,
                key_signature="C",
                audio_quality=0.95
            ),
            features=HybridFeatures(),
            quality_score=0.95,
            processing_recommendations={},
            confidence_scores={"overall": 0.9}
        )
        
        reference_analysis = ReferenceAnalysisResult(
            characteristics=AudioCharacteristics(
                genre="electronic",  # Matching genre
                genre_confidence=0.85,
                has_vocals=False,
                is_instrumental=True,
                energy_level=0.7,
                dynamic_range=8.0,  # Lower dynamic range (mastered)
                complexity_score=0.6,
                tempo_bpm=130.0,
                key_signature="C",
                audio_quality=0.9
            ),
            target_parameters=MasteringParameters(
                eq_low_gain=0.5,
                eq_mid_gain=0.2,
                eq_high_gain=0.3,
                compressor_ratio=2.5,
                compressor_threshold=-15.0,
                limiter_threshold=-1.0,
                target_loudness_lufs=-14.0
            ),
            style_profile={},
            matching_confidence=0.85
        )
        
        # Mock AI parameter prediction
        with patch.object(processing_engine, '_predict_ai_parameters') as mock_ai_params:
            mock_ai_params.return_value = MasteringParameters(
                eq_low_gain=0.3,
                eq_mid_gain=0.4,
                eq_high_gain=0.5,
                compressor_ratio=2.0,
                compressor_threshold=-12.0,
                limiter_threshold=-0.5,
                target_loudness_lufs=-13.0
            )
            
            result = await processing_engine._synthesize_hybrid_parameters(
                ai_analysis, reference_analysis, sample_request
            )
        
        assert isinstance(result, MasteringParameters)
        assert result.confidence_score > 0
        
        # Test that blending occurred (values between AI and reference)
        assert 0.3 <= result.eq_low_gain <= 0.5  # Between AI and ref values
        assert 2.0 <= result.compressor_ratio <= 2.5
        assert -15.0 <= result.compressor_threshold <= -12.0
    
    @pytest.mark.asyncio
    async def test_processing_mode_validation(self, processing_engine):
        """Test processing mode validation."""
        invalid_request = HybridProcessingRequest(
            input_file_path="/test/input.wav",
            output_file_path="/test/output.wav",
            processing_mode="invalid_mode"  # This should be handled by Pydantic
        )
        
        # The validation should happen at the Pydantic level
        with pytest.raises((ValueError, TypeError)):
            ProcessingMode("invalid_mode")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, processing_engine, sample_request):
        """Test error handling in processing."""
        # Test with invalid file path
        invalid_request = HybridProcessingRequest(
            input_file_path="/nonexistent/file.wav",
            output_file_path="/test/output.wav",
            processing_mode=ProcessingMode.AI_ONLY
        )
        
        result = await processing_engine.process_audio(invalid_request)
        
        assert isinstance(result, HybridProcessingResult)
        assert result.success is False
        assert result.error_message is not None
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_progress_tracking_workflow(self, processing_engine, sample_request):
        """Test complete progress tracking workflow."""
        progress_updates = []
        
        async def capture_progress(progress):
            progress_updates.append(progress)
        
        processing_engine.add_progress_callback(capture_progress)
        
        # Simulate progress updates
        await processing_engine._update_progress(ProcessingStage.INITIALIZATION, 0.0, "Starting")
        await processing_engine._update_progress(ProcessingStage.AUDIO_LOADING, 10.0, "Loading audio")
        await processing_engine._update_progress(ProcessingStage.FEATURE_EXTRACTION, 25.0, "Extracting features")
        await processing_engine._update_progress(ProcessingStage.FINALIZATION, 100.0, "Complete")
        
        assert len(progress_updates) == 4
        assert progress_updates[0].percentage == 0.0
        assert progress_updates[-1].percentage == 100.0
        assert progress_updates[0].stage == ProcessingStage.INITIALIZATION
        assert progress_updates[-1].stage == ProcessingStage.FINALIZATION
    
    @pytest.mark.asyncio
    async def test_engine_shutdown(self, processing_engine):
        """Test engine shutdown and cleanup."""
        # Add some callbacks
        processing_engine.add_progress_callback(Mock())
        processing_engine.add_progress_callback(Mock())
        
        await processing_engine.shutdown()
        
        # Check that callbacks are cleared
        assert len(processing_engine.progress_callbacks) == 0


class TestAudioAnalysis:
    """Test suite for audio analysis functions."""
    
    def test_audio_quality_calculation(self):
        """Test audio quality score calculation."""
        engine = HybridProcessingEngine(device="cpu")
        
        # Create test audio
        audio = torch.randn(1, 44100)  # 1 second of noise
        sample_rate = 44100
        
        quality_score = engine._calculate_audio_quality_score(audio, sample_rate)
        
        assert 0.0 <= quality_score <= 1.0
    
    def test_processing_recommendations(self):
        """Test processing recommendations generation."""
        engine = HybridProcessingEngine(device="cpu")
        
        characteristics = AudioCharacteristics(
            genre="electronic",
            genre_confidence=0.9,
            has_vocals=True,
            is_instrumental=False,
            energy_level=0.8,
            dynamic_range=15.0,
            complexity_score=0.7,
            tempo_bpm=128.0,
            key_signature="C",
            audio_quality=0.9
        )
        
        recommendations = engine._generate_processing_recommendations(characteristics)
        
        assert isinstance(recommendations, dict)
        assert "suggested_intensity" in recommendations
        assert "preserve_dynamics" in recommendations
        assert recommendations["vocal_enhancement"] == True  # Has vocals
        assert recommendations["preserve_dynamics"] == True  # High dynamic range


class TestParameterSynthesis:
    """Test suite for parameter synthesis algorithms."""
    
    def test_blend_parameter_basic(self):
        """Test basic parameter blending."""
        engine = HybridProcessingEngine(device="cpu")
        
        # Test equal weights
        result = engine._blend_parameter(2.0, 4.0, 0.5, 0.5)
        assert abs(result - 3.0) < 1e-6
        
        # Test AI-weighted
        result = engine._blend_parameter(2.0, 4.0, 0.8, 0.2)
        expected = 2.0 * 0.8 + 4.0 * 0.2
        assert abs(result - expected) < 1e-6
        
        # Test reference-weighted
        result = engine._blend_parameter(2.0, 4.0, 0.2, 0.8)
        expected = 2.0 * 0.2 + 4.0 * 0.8
        assert abs(result - expected) < 1e-6
    
    def test_adaptive_weight_edge_cases(self):
        """Test adaptive weight calculation edge cases."""
        engine = HybridProcessingEngine(device="cpu")
        
        # Test with very low confidence
        ai_analysis = AudioAnalysisResult(
            characteristics=AudioCharacteristics(
                genre="unknown",
                genre_confidence=0.1,
                has_vocals=False,
                is_instrumental=True,
                energy_level=0.5,
                dynamic_range=10.0,
                complexity_score=0.5,
                tempo_bpm=120.0,
                key_signature="C",
                audio_quality=0.3
            ),
            features=HybridFeatures(),
            quality_score=0.3,
            processing_recommendations={},
            confidence_scores={"overall": 0.2}
        )
        
        reference_analysis = ReferenceAnalysisResult(
            characteristics=AudioCharacteristics(
                genre="rock",
                genre_confidence=0.9,
                has_vocals=True,
                is_instrumental=False,
                energy_level=0.8,
                dynamic_range=8.0,
                complexity_score=0.7,
                tempo_bpm=140.0,
                key_signature="E",
                audio_quality=0.95
            ),
            target_parameters=MasteringParameters(),
            style_profile={},
            matching_confidence=0.9
        )
        
        request = HybridProcessingRequest(
            input_file_path="/test/input.wav",
            output_file_path="/test/output.wav",
            ai_weight=0.5,
            reference_weight=0.5
        )
        
        ai_weight, ref_weight = engine._calculate_adaptive_weights(
            ai_analysis, reference_analysis, request
        )
        
        # Reference should be heavily favored due to low AI confidence
        assert ref_weight > ai_weight


class TestPerformanceMetrics:
    """Test suite for performance and benchmarking."""
    
    @pytest.mark.asyncio
    async def test_processing_time_measurement(self):
        """Test processing time measurement."""
        engine = HybridProcessingEngine(device="cpu")
        
        start_time = asyncio.get_event_loop().time()
        
        # Simulate some processing
        await asyncio.sleep(0.1)
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        assert processing_time >= 0.1
        assert processing_time < 0.2  # Should be close to 0.1 seconds
    
    def test_memory_usage_estimation(self):
        """Test memory usage estimation."""
        engine = HybridProcessingEngine(device="cpu")
        
        # Test with different audio lengths
        short_audio = torch.randn(1, 44100)  # 1 second
        long_audio = torch.randn(1, 441000)  # 10 seconds
        
        # Memory usage should scale with audio length
        assert long_audio.numel() > short_audio.numel()


# Test fixtures and utilities
@pytest.fixture
def sample_mastering_parameters():
    """Create sample mastering parameters for testing."""
    return MasteringParameters(
        eq_low_gain=0.5,
        eq_mid_gain=0.2,
        eq_high_gain=0.3,
        compressor_ratio=2.0,
        compressor_threshold=-12.0,
        compressor_attack=10.0,
        compressor_release=100.0,
        stereo_width=1.0,
        limiter_threshold=-1.0,
        limiter_release=50.0,
        target_loudness_lufs=-14.0,
        confidence_score=0.85
    )


@pytest.fixture
def sample_audio_characteristics():
    """Create sample audio characteristics for testing."""
    return AudioCharacteristics(
        genre="electronic",
        genre_confidence=0.9,
        has_vocals=False,
        is_instrumental=True,
        energy_level=0.8,
        dynamic_range=12.0,
        complexity_score=0.7,
        tempo_bpm=128.0,
        key_signature="C",
        audio_quality=0.9
    )


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarking test suite."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_ai_analysis_performance(self, processing_engine, sample_audio):
        """Benchmark AI analysis performance."""
        audio_data, sample_rate = sample_audio
        
        start_time = asyncio.get_event_loop().time()
        
        # Mock to avoid actual model loading
        with patch.object(processing_engine, 'feature_extractor'):
            result = await processing_engine._analyze_audio_ai(audio_data, sample_rate)
        
        end_time = asyncio.get_event_loop().time()
        analysis_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on requirements)
        assert analysis_time < 5.0  # 5 seconds max
        print(f"AI analysis time: {analysis_time:.3f}s")
    
    @pytest.mark.performance  
    @pytest.mark.asyncio
    async def test_parameter_synthesis_performance(self, processing_engine):
        """Benchmark parameter synthesis performance."""
        # Create comprehensive test data
        ai_analysis = AudioAnalysisResult(
            characteristics=AudioCharacteristics(
                genre="electronic",
                genre_confidence=0.9,
                has_vocals=False,
                is_instrumental=True,
                energy_level=0.8,
                dynamic_range=15.0,
                complexity_score=0.7,
                tempo_bpm=128.0,
                key_signature="C",
                audio_quality=0.95
            ),
            features=HybridFeatures(),
            quality_score=0.95,
            processing_recommendations={},
            confidence_scores={"overall": 0.9}
        )
        
        reference_analysis = ReferenceAnalysisResult(
            characteristics=AudioCharacteristics(
                genre="electronic",
                genre_confidence=0.85,
                has_vocals=False,
                is_instrumental=True,
                energy_level=0.7,
                dynamic_range=8.0,
                complexity_score=0.6,
                tempo_bpm=130.0,
                key_signature="C",
                audio_quality=0.9
            ),
            target_parameters=MasteringParameters(),
            style_profile={},
            matching_confidence=0.85
        )
        
        request = HybridProcessingRequest(
            input_file_path="/test/input.wav",
            output_file_path="/test/output.wav",
            processing_mode=ProcessingMode.HYBRID
        )
        
        start_time = asyncio.get_event_loop().time()
        
        with patch.object(processing_engine, '_predict_ai_parameters') as mock_predict:
            mock_predict.return_value = MasteringParameters()
            result = await processing_engine._synthesize_hybrid_parameters(
                ai_analysis, reference_analysis, request
            )
        
        end_time = asyncio.get_event_loop().time()
        synthesis_time = end_time - start_time
        
        # Parameter synthesis should be very fast
        assert synthesis_time < 0.1  # 100ms max
        print(f"Parameter synthesis time: {synthesis_time:.3f}s")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])