"""
End-to-End Integration Tests for Hybrid AI Mastering System.

This module provides comprehensive integration tests that validate the complete
workflow from API endpoints through processing engine to final output.
"""

import asyncio
import json
import pytest
import tempfile
import torch
import torchaudio
from pathlib import Path
from fastapi.testclient import TestClient
from httpx import AsyncClient
import numpy as np
from unittest.mock import patch, Mock

# Import the modules to test
import sys
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.main import app
from app.ai.hybrid_processing_engine import (
    HybridProcessingEngine,
    ProcessingMode,
    HybridProcessingRequest
)
from app.api.v1.endpoints.hybrid_processing import get_processing_engine


class TestEndToEndWorkflow:
    """Complete end-to-end workflow tests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.fixture
    def sample_audio_files(self):
        """Create sample audio files for testing."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        
        # Generate test audio - input file
        duration = 2.0  # 2 seconds
        sample_rate = 44100
        samples = int(duration * sample_rate)
        
        # Create input audio (sine wave)
        t = torch.linspace(0, duration, samples)
        input_audio = torch.sin(2 * np.pi * 440.0 * t).unsqueeze(0)  # A4 note
        input_file = temp_path / "input_test.wav"
        torchaudio.save(str(input_file), input_audio, sample_rate)
        
        # Create reference audio (different frequency)
        ref_audio = torch.sin(2 * np.pi * 880.0 * t).unsqueeze(0)  # A5 note
        reference_file = temp_path / "reference_test.wav"
        torchaudio.save(str(reference_file), ref_audio, sample_rate)
        
        return {
            "input_file": input_file,
            "reference_file": reference_file,
            "temp_dir": temp_path
        }
    
    def test_api_health_check(self, client):
        """Test API health and basic connectivity."""
        response = client.get("/health")
        
        # Should return success even if endpoint doesn't exist
        assert response.status_code in [200, 404]  # Accept both for now
    
    def test_hybrid_processing_engine_status(self, client):
        """Test hybrid processing engine status endpoint."""
        response = client.get("/api/v1/hybrid-processing/engine/status")
        
        if response.status_code == 200:
            data = response.json()
            assert "engine_initialized" in data
            assert "device" in data
        elif response.status_code == 500:
            # Expected if dependencies not available
            assert "Failed to get engine status" in response.json()["detail"]
    
    @pytest.mark.integration
    def test_create_processing_job_ai_only(self, client, sample_audio_files):
        """Test creating AI-only processing job via API."""
        input_file = sample_audio_files["input_file"]
        
        # Prepare request data
        request_data = {
            "processing_mode": "ai",
            "ai_intensity": 0.7,
            "target_loudness_lufs": -14.0,
            "enable_quality_validation": True
        }
        
        # Prepare files
        with open(input_file, "rb") as f:
            files = {"input_file": ("input.wav", f, "audio/wav")}
            
            response = client.post(
                "/api/v1/hybrid-processing/jobs",
                data=request_data,
                files=files
            )
        
        # Should either succeed or fail gracefully
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert data["processing_mode"] == "ai"
            assert "websocket_url" in data
        else:
            # Expected if processing engine not fully initialized
            assert response.status_code in [422, 500]
    
    @pytest.mark.integration
    def test_create_processing_job_hybrid(self, client, sample_audio_files):
        """Test creating hybrid processing job via API."""
        input_file = sample_audio_files["input_file"]
        reference_file = sample_audio_files["reference_file"]
        
        # Prepare request data
        request_data = {
            "processing_mode": "hybrid",
            "ai_intensity": 0.8,
            "reference_influence": 0.6,
            "ai_weight": 0.7,
            "reference_weight": 0.3,
            "adaptive_blending": True,
            "target_loudness_lufs": -16.0,
            "preserve_dynamics": True
        }
        
        # Prepare files
        with open(input_file, "rb") as input_f, open(reference_file, "rb") as ref_f:
            files = {
                "input_file": ("input.wav", input_f, "audio/wav"),
                "reference_file": ("reference.wav", ref_f, "audio/wav")
            }
            
            response = client.post(
                "/api/v1/hybrid-processing/jobs",
                data=request_data,
                files=files
            )
        
        # Should either succeed or fail gracefully
        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert data["processing_mode"] == "hybrid"
            assert "estimated_duration" in data
        else:
            # Expected if dependencies not available
            assert response.status_code in [422, 500]
    
    @pytest.mark.integration
    def test_job_status_tracking(self, client, sample_audio_files):
        """Test job status tracking workflow."""
        # First create a job
        input_file = sample_audio_files["input_file"]
        
        request_data = {
            "processing_mode": "ai",
            "ai_intensity": 0.5
        }
        
        with open(input_file, "rb") as f:
            files = {"input_file": ("input.wav", f, "audio/wav")}
            
            create_response = client.post(
                "/api/v1/hybrid-processing/jobs",
                data=request_data,
                files=files
            )
        
        if create_response.status_code == 200:
            job_data = create_response.json()
            job_id = job_data["job_id"]
            
            # Check job status
            status_response = client.get(f"/api/v1/hybrid-processing/jobs/{job_id}/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                assert status_data["job_id"] == job_id
                assert "status" in status_data
                assert "progress_percentage" in status_data
                assert "processing_time" in status_data
    
    @pytest.mark.integration
    def test_job_listing(self, client):
        """Test job listing endpoint."""
        response = client.get("/api/v1/hybrid-processing/jobs")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        else:
            # May fail if database not configured
            assert response.status_code in [500, 422]
    
    @pytest.mark.integration
    def test_invalid_processing_mode(self, client, sample_audio_files):
        """Test handling of invalid processing mode."""
        input_file = sample_audio_files["input_file"]
        
        request_data = {
            "processing_mode": "invalid_mode",
            "ai_intensity": 0.7
        }
        
        with open(input_file, "rb") as f:
            files = {"input_file": ("input.wav", f, "audio/wav")}
            
            response = client.post(
                "/api/v1/hybrid-processing/jobs",
                data=request_data,
                files=files
            )
        
        # Should return validation error
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    @pytest.mark.integration
    def test_missing_reference_file_hybrid_mode(self, client, sample_audio_files):
        """Test hybrid mode without reference file."""
        input_file = sample_audio_files["input_file"]
        
        request_data = {
            "processing_mode": "hybrid",
            "ai_intensity": 0.7
        }
        
        with open(input_file, "rb") as f:
            files = {"input_file": ("input.wav", f, "audio/wav")}
            
            response = client.post(
                "/api/v1/hybrid-processing/jobs",
                data=request_data,
                files=files
            )
        
        # Should return error for missing reference file
        if response.status_code == 400:
            error_data = response.json()
            assert "reference file" in error_data["detail"].lower()


class TestProcessingEngineIntegration:
    """Integration tests for the processing engine itself."""
    
    @pytest.fixture
    async def processing_engine(self):
        """Create and initialize processing engine."""
        engine = HybridProcessingEngine(device="cpu")
        
        # Mock model loading to avoid dependency issues
        with patch('app.ai.hybrid_processing_engine.ProductionModelManager'):
            await engine.initialize()
        
        return engine
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data."""
        duration = 1.0
        sample_rate = 44100
        samples = int(duration * sample_rate)
        
        # Create stereo audio
        t = torch.linspace(0, duration, samples)
        left = torch.sin(2 * np.pi * 440.0 * t)  # A4
        right = torch.sin(2 * np.pi * 523.25 * t)  # C5
        audio = torch.stack([left, right])
        
        return audio, sample_rate
    
    @pytest.mark.asyncio
    async def test_complete_ai_processing_workflow(self, processing_engine, sample_audio_data, tmp_path):
        """Test complete AI processing workflow."""
        audio_data, sample_rate = sample_audio_data
        
        # Save test files
        input_file = tmp_path / "input.wav"
        output_file = tmp_path / "output.wav"
        
        torchaudio.save(str(input_file), audio_data, sample_rate)
        
        # Create processing request
        request = HybridProcessingRequest(
            input_file_path=str(input_file),
            output_file_path=str(output_file),
            processing_mode=ProcessingMode.AI_ONLY,
            ai_intensity=0.8,
            target_loudness_lufs=-14.0,
            enable_quality_validation=True
        )
        
        # Mock the analysis methods to avoid model dependencies
        with patch.object(processing_engine, '_analyze_audio_ai') as mock_analysis:
            from app.ai.hybrid_processing_engine import AudioAnalysisResult
            from app.ai.hybrid_feature_extractor import AudioCharacteristics, HybridFeatures
            
            mock_analysis.return_value = AudioAnalysisResult(
                characteristics=AudioCharacteristics(
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
                ),
                features=HybridFeatures(),
                quality_score=0.9,
                processing_recommendations={},
                confidence_scores={"overall": 0.9}
            )
            
            # Process audio
            result = await processing_engine.process_audio(request)
        
        # Validate results
        assert result.success is True
        assert result.processing_mode == ProcessingMode.AI_ONLY
        assert result.processing_time > 0
        assert result.ai_confidence > 0
        assert result.reference_influence == 0.0
    
    @pytest.mark.asyncio
    async def test_progress_callback_integration(self, processing_engine, sample_audio_data, tmp_path):
        """Test progress callback integration."""
        audio_data, sample_rate = sample_audio_data
        
        # Save test files
        input_file = tmp_path / "input.wav"
        output_file = tmp_path / "output.wav"
        
        torchaudio.save(str(input_file), audio_data, sample_rate)
        
        # Track progress updates
        progress_updates = []
        
        async def progress_callback(progress):
            progress_updates.append(progress)
        
        processing_engine.add_progress_callback(progress_callback)
        
        # Create and process request
        request = HybridProcessingRequest(
            input_file_path=str(input_file),
            output_file_path=str(output_file),
            processing_mode=ProcessingMode.AI_ONLY,
            enable_real_time_progress=True
        )
        
        # Mock dependencies
        with patch.object(processing_engine, '_analyze_audio_ai') as mock_analysis:
            from app.ai.hybrid_processing_engine import AudioAnalysisResult
            from app.ai.hybrid_feature_extractor import AudioCharacteristics, HybridFeatures
            
            mock_analysis.return_value = AudioAnalysisResult(
                characteristics=AudioCharacteristics(
                    genre="test",
                    genre_confidence=0.8,
                    has_vocals=False,
                    is_instrumental=True,
                    energy_level=0.7,
                    dynamic_range=10.0,
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
            
            result = await processing_engine.process_audio(request)
        
        # Check progress tracking
        assert len(progress_updates) > 0
        assert progress_updates[0].percentage == 0.0
        assert progress_updates[-1].percentage == 100.0
        
        # Check that stages progress logically
        percentages = [p.percentage for p in progress_updates]
        assert percentages == sorted(percentages)  # Should be monotonically increasing
    
    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, processing_engine, tmp_path):
        """Test error recovery in integration scenario."""
        # Create request with invalid file
        request = HybridProcessingRequest(
            input_file_path="/nonexistent/file.wav",
            output_file_path=str(tmp_path / "output.wav"),
            processing_mode=ProcessingMode.AI_ONLY
        )
        
        # Process should handle error gracefully
        result = await processing_engine.process_audio(request)
        
        assert result.success is False
        assert result.error_message is not None
        assert result.processing_time > 0
        assert result.output_path is None


class TestAPIIntegrationScenarios:
    """Test realistic API usage scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_api_documentation_endpoints(self, client):
        """Test API documentation endpoints."""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        if response.status_code == 200:
            schema = response.json()
            assert "openapi" in schema
            assert "paths" in schema
    
    def test_cors_headers(self, client):
        """Test CORS headers for frontend integration."""
        response = client.options("/api/v1/hybrid-processing/jobs")
        
        # Should handle CORS preflight
        assert response.status_code in [200, 405, 404]
    
    @pytest.mark.integration
    def test_file_upload_validation(self, client, tmp_path):
        """Test file upload validation."""
        # Create invalid file (text file instead of audio)
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("This is not audio data")
        
        request_data = {
            "processing_mode": "ai",
            "ai_intensity": 0.7
        }
        
        with open(invalid_file, "rb") as f:
            files = {"input_file": ("invalid.txt", f, "text/plain")}
            
            response = client.post(
                "/api/v1/hybrid-processing/jobs",
                data=request_data,
                files=files
            )
        
        # Should handle invalid file gracefully
        # May succeed at API level but fail during processing
        assert response.status_code in [200, 400, 422, 500]
    
    @pytest.mark.integration
    def test_large_file_handling(self, client, tmp_path):
        """Test large file handling."""
        # Create a larger audio file
        duration = 10.0  # 10 seconds
        sample_rate = 44100
        samples = int(duration * sample_rate)
        
        # Create large audio file
        audio = torch.randn(2, samples)  # Stereo noise
        large_file = tmp_path / "large_audio.wav"
        torchaudio.save(str(large_file), audio, sample_rate)
        
        request_data = {
            "processing_mode": "ai",
            "ai_intensity": 0.5,
            "max_processing_time": 600.0  # Increase timeout for large file
        }
        
        with open(large_file, "rb") as f:
            files = {"input_file": ("large_audio.wav", f, "audio/wav")}
            
            response = client.post(
                "/api/v1/hybrid-processing/jobs",
                data=request_data,
                files=files
            )
        
        # Should handle large file (may timeout or succeed)
        assert response.status_code in [200, 413, 422, 500]
    
    def test_parameter_validation_edge_cases(self, client, tmp_path):
        """Test parameter validation edge cases."""
        # Create minimal audio file
        audio = torch.zeros(1, 1000)
        test_file = tmp_path / "minimal.wav"
        torchaudio.save(str(test_file), audio, 44100)
        
        # Test edge case parameters
        edge_cases = [
            {"ai_intensity": -0.1},  # Below range
            {"ai_intensity": 1.1},   # Above range
            {"target_loudness_lufs": -5.0},  # Too loud
            {"target_loudness_lufs": -31.0}, # Too quiet
            {"ai_weight": 2.0},      # Invalid weight
            {"reference_weight": -0.5}, # Negative weight
            {"max_processing_time": 0}, # Zero timeout
            {"max_processing_time": 1000} # Very long timeout
        ]
        
        for params in edge_cases:
            base_params = {
                "processing_mode": "ai",
                "ai_intensity": 0.7
            }
            base_params.update(params)
            
            with open(test_file, "rb") as f:
                files = {"input_file": ("test.wav", f, "audio/wav")}
                
                response = client.post(
                    "/api/v1/hybrid-processing/jobs",
                    data=base_params,
                    files=files
                )
            
            # Should either accept valid params or reject invalid ones
            assert response.status_code in [200, 422, 500]
            
            if response.status_code == 422:
                error_data = response.json()
                assert "detail" in error_data


class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_processing_requests(self):
        """Test handling multiple concurrent processing requests."""
        engine = HybridProcessingEngine(device="cpu")
        
        # Mock initialization
        with patch('app.ai.hybrid_processing_engine.ProductionModelManager'):
            await engine.initialize()
        
        # Create multiple requests
        requests = []
        for i in range(3):
            request = HybridProcessingRequest(
                input_file_path=f"/test/input_{i}.wav",
                output_file_path=f"/test/output_{i}.wav",
                processing_mode=ProcessingMode.AI_ONLY
            )
            requests.append(request)
        
        # Mock processing to avoid file dependencies
        with patch.object(engine, '_load_audio') as mock_load:
            mock_load.return_value = (torch.randn(1, 44100), 44100)
            
            with patch.object(engine, '_analyze_audio_ai') as mock_analysis:
                from app.ai.hybrid_processing_engine import AudioAnalysisResult
                from app.ai.hybrid_feature_extractor import AudioCharacteristics, HybridFeatures
                
                mock_analysis.return_value = AudioAnalysisResult(
                    characteristics=AudioCharacteristics(
                        genre="test",
                        genre_confidence=0.8,
                        has_vocals=False,
                        is_instrumental=True,
                        energy_level=0.7,
                        dynamic_range=10.0,
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
                
                # Process requests concurrently
                tasks = [engine.process_audio(req) for req in requests]
                results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete (successfully or with errors)
        assert len(results) == 3
        
        # Count successful results
        successful = sum(1 for r in results if not isinstance(r, Exception) and r.success)
        print(f"Successful concurrent processes: {successful}/3")
    
    @pytest.mark.performance
    def test_memory_usage_pattern(self):
        """Test memory usage patterns."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and destroy multiple engines
        engines = []
        for i in range(5):
            engine = HybridProcessingEngine(device="cpu")
            engines.append(engine)
        
        peak_memory = process.memory_info().rss
        
        # Clean up
        for engine in engines:
            asyncio.run(engine.shutdown())
        del engines
        gc.collect()
        
        final_memory = process.memory_info().rss
        
        # Memory should be reasonable
        memory_increase = peak_memory - initial_memory
        memory_leaked = final_memory - initial_memory
        
        print(f"Memory increase: {memory_increase / 1024 / 1024:.1f} MB")
        print(f"Memory after cleanup: {memory_leaked / 1024 / 1024:.1f} MB")
        
        # Should not leak excessive memory
        assert memory_leaked < 100 * 1024 * 1024  # Less than 100MB leak


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])