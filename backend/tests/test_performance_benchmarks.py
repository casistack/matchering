"""
Performance Benchmarking Suite for Hybrid AI Mastering System.

This module provides comprehensive performance benchmarks and metrics
for the hybrid processing engine, measuring inference speed, memory usage,
and throughput characteristics.
"""

import asyncio
import gc
import time
import pytest
import torch
import torchaudio
import psutil
import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Import the modules to benchmark
import sys
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.ai.hybrid_processing_engine import (
    HybridProcessingEngine,
    HybridProcessingRequest,
    ProcessingMode
)
from app.ai.production_model_manager import ProductionModelManager
from app.ai.deployment_config import get_deployment_config


@dataclass
class PerformanceMetrics:
    """Performance metrics container."""
    
    operation_name: str
    execution_time: float
    memory_usage_mb: float
    peak_memory_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: str = None
    metadata: Dict = None


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmarking suite."""
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.process = psutil.Process(os.getpid())
        self.benchmark_results: List[PerformanceMetrics] = []
    
    def measure_performance(self, operation_name: str):
        """Decorator to measure performance of operations."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Start measurements
                start_time = time.time()
                start_memory = self.process.memory_info().rss / 1024 / 1024
                start_cpu = self.process.cpu_percent()
                
                try:
                    # Execute operation
                    result = await func(*args, **kwargs)
                    success = True
                    error_message = None
                except Exception as e:
                    result = None
                    success = False
                    error_message = str(e)
                
                # End measurements
                end_time = time.time()
                end_memory = self.process.memory_info().rss / 1024 / 1024
                end_cpu = self.process.cpu_percent()
                
                # Calculate metrics
                execution_time = end_time - start_time
                memory_usage = end_memory - start_memory
                peak_memory = max(start_memory, end_memory)
                avg_cpu = (start_cpu + end_cpu) / 2
                
                # Store metrics
                metrics = PerformanceMetrics(
                    operation_name=operation_name,
                    execution_time=execution_time,
                    memory_usage_mb=memory_usage,
                    peak_memory_mb=peak_memory,
                    cpu_usage_percent=avg_cpu,
                    success=success,
                    error_message=error_message,
                    metadata=kwargs.get('metadata', {})
                )
                
                self.benchmark_results.append(metrics)
                
                return result
            return wrapper
        return decorator
    
    def generate_test_audio(self, duration: float, sample_rate: int = 44100, complexity: str = "simple") -> Tuple[torch.Tensor, int]:
        """Generate test audio with varying complexity."""
        samples = int(duration * sample_rate)
        t = torch.linspace(0, duration, samples)
        
        if complexity == "simple":
            # Simple sine wave
            audio = torch.sin(2 * np.pi * 440.0 * t).unsqueeze(0)
        elif complexity == "complex":
            # Multi-frequency complex signal
            freqs = [440.0, 880.0, 1320.0, 220.0]
            audio = torch.zeros(1, samples)
            for freq in freqs:
                audio += torch.sin(2 * np.pi * freq * t).unsqueeze(0) / len(freqs)
        elif complexity == "music":
            # Simulate more musical content
            fundamental = 440.0
            harmonics = [1, 0.5, 0.25, 0.125, 0.0625]
            audio = torch.zeros(1, samples)
            for i, amp in enumerate(harmonics):
                freq = fundamental * (i + 1)
                audio += amp * torch.sin(2 * np.pi * freq * t).unsqueeze(0)
        else:
            # White noise
            audio = torch.randn(1, samples) * 0.1
        
        return audio, sample_rate
    
    def print_benchmark_summary(self):
        """Print comprehensive benchmark summary."""
        if not self.benchmark_results:
            print("No benchmark results available.")
            return
        
        print("\n" + "=" * 80)
        print("HYBRID AI MASTERING SYSTEM - PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)
        
        # Group by operation
        operations = {}
        for metric in self.benchmark_results:
            if metric.operation_name not in operations:
                operations[metric.operation_name] = []
            operations[metric.operation_name].append(metric)
        
        for op_name, metrics in operations.items():
            successful = [m for m in metrics if m.success]
            failed = [m for m in metrics if not m.success]
            
            print(f"\n{op_name.upper()}")
            print("-" * 60)
            print(f"Runs: {len(metrics)} | Success: {len(successful)} | Failed: {len(failed)}")
            
            if successful:
                times = [m.execution_time for m in successful]
                memories = [m.memory_usage_mb for m in successful]
                
                print(f"Execution Time: {np.mean(times):.3f}s ± {np.std(times):.3f}s")
                print(f"  Min: {np.min(times):.3f}s | Max: {np.max(times):.3f}s")
                print(f"Memory Usage: {np.mean(memories):.1f}MB ± {np.std(memories):.1f}MB")
                print(f"  Peak: {np.max([m.peak_memory_mb for m in successful]):.1f}MB")
            
            if failed:
                print(f"Failures: {len(failed)}")
                for f in failed[:3]:  # Show first 3 failures
                    print(f"  - {f.error_message}")
        
        # Overall statistics
        all_successful = [m for m in self.benchmark_results if m.success]
        if all_successful:
            total_time = sum(m.execution_time for m in all_successful)
            total_memory = sum(m.memory_usage_mb for m in all_successful)
            
            print(f"\nOVERALL PERFORMANCE")
            print("-" * 60)
            print(f"Total benchmark time: {total_time:.2f}s")
            print(f"Average operation time: {np.mean([m.execution_time for m in all_successful]):.3f}s")
            print(f"Total memory usage: {total_memory:.1f}MB")
            print(f"Success rate: {len(all_successful)/len(self.benchmark_results)*100:.1f}%")


class TestPerformanceBenchmarks:
    """Performance benchmark test suite."""
    
    @pytest.fixture
    def benchmark_suite(self):
        """Create benchmark suite."""
        return PerformanceBenchmarkSuite(device="cpu")
    
    @pytest.fixture
    async def processing_engine(self):
        """Create processing engine for benchmarks."""
        # Mock dependencies to focus on core performance
        from unittest.mock import patch, Mock
        
        with patch('app.ai.hybrid_processing_engine.ProductionModelManager'):
            engine = HybridProcessingEngine(device="cpu")
            await engine.initialize()
            return engine
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_engine_initialization_performance(self, benchmark_suite):
        """Benchmark engine initialization performance."""
        
        @benchmark_suite.measure_performance("engine_initialization")
        async def initialize_engine():
            from unittest.mock import patch
            with patch('app.ai.hybrid_processing_engine.ProductionModelManager'):
                engine = HybridProcessingEngine(device="cpu")
                await engine.initialize()
                return engine
        
        # Run multiple initialization benchmarks
        for i in range(3):
            engine = await initialize_engine()
            if engine:
                await engine.shutdown()
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_audio_loading_performance(self, benchmark_suite, processing_engine, tmp_path):
        """Benchmark audio loading performance for different file sizes."""
        
        @benchmark_suite.measure_performance("audio_loading")
        async def load_audio_file(file_path: str, metadata: Dict):
            return await processing_engine._load_audio(file_path)
        
        # Test different audio durations
        durations = [1.0, 5.0, 10.0, 30.0]  # seconds
        
        for duration in durations:
            audio, sr = benchmark_suite.generate_test_audio(duration, complexity="simple")
            
            # Save to file
            test_file = tmp_path / f"test_{duration}s.wav"
            torchaudio.save(str(test_file), audio, sr)
            
            # Benchmark loading
            metadata = {"duration": duration, "file_size_mb": test_file.stat().st_size / 1024 / 1024}
            result = await load_audio_file(str(test_file), metadata=metadata)
            
            if result:
                loaded_audio, loaded_sr = result
                assert loaded_sr == sr
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_ai_analysis_performance(self, benchmark_suite, processing_engine):
        """Benchmark AI analysis performance for different audio characteristics."""
        
        @benchmark_suite.measure_performance("ai_analysis")
        async def analyze_audio(audio_data: torch.Tensor, sample_rate: int, metadata: Dict):
            from unittest.mock import patch
            
            # Mock feature extraction to focus on analysis logic
            with patch.object(processing_engine, 'feature_extractor') as mock_extractor:
                from app.ai.hybrid_feature_extractor import AudioCharacteristics, HybridFeatures
                
                mock_extractor.analyze_characteristics.return_value = AudioCharacteristics(
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
                mock_extractor.extract_features_async.return_value = HybridFeatures()
                
                return await processing_engine._analyze_audio_ai(audio_data, sample_rate)
        
        # Test different audio complexities and durations
        test_cases = [
            (1.0, "simple"),
            (5.0, "simple"),
            (1.0, "complex"),
            (5.0, "complex"),
            (1.0, "music"),
            (5.0, "music")
        ]
        
        for duration, complexity in test_cases:
            audio, sr = benchmark_suite.generate_test_audio(duration, complexity=complexity)
            
            metadata = {
                "duration": duration,
                "complexity": complexity,
                "sample_count": audio.shape[1]
            }
            
            result = await analyze_audio(audio, sr, metadata=metadata)
            assert result is not None
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_parameter_synthesis_performance(self, benchmark_suite, processing_engine):
        """Benchmark parameter synthesis performance."""
        
        @benchmark_suite.measure_performance("parameter_synthesis")
        async def synthesize_parameters(ai_analysis, ref_analysis, request, metadata: Dict):
            from unittest.mock import patch
            
            with patch.object(processing_engine, '_predict_ai_parameters') as mock_predict:
                from app.ai.mastering_model import MasteringParameters
                mock_predict.return_value = MasteringParameters()
                
                return await processing_engine._synthesize_hybrid_parameters(
                    ai_analysis, ref_analysis, request
                )
        
        # Create test analysis data
        from app.ai.hybrid_processing_engine import AudioAnalysisResult, ReferenceAnalysisResult
        from app.ai.hybrid_feature_extractor import AudioCharacteristics, HybridFeatures
        from app.ai.mastering_model import MasteringParameters
        
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
        
        ref_analysis = ReferenceAnalysisResult(
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
        
        # Test different blending scenarios
        blending_scenarios = [
            {"ai_weight": 0.5, "reference_weight": 0.5, "adaptive_blending": False},
            {"ai_weight": 0.8, "reference_weight": 0.2, "adaptive_blending": False},
            {"ai_weight": 0.3, "reference_weight": 0.7, "adaptive_blending": False},
            {"ai_weight": 0.6, "reference_weight": 0.4, "adaptive_blending": True},
        ]
        
        for scenario in blending_scenarios:
            request = HybridProcessingRequest(
                input_file_path="/test/input.wav",
                output_file_path="/test/output.wav",
                processing_mode=ProcessingMode.HYBRID,
                **scenario
            )
            
            metadata = {"scenario": scenario}
            result = await synthesize_parameters(ai_analysis, ref_analysis, request, metadata=metadata)
            assert result is not None
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self, benchmark_suite, processing_engine):
        """Benchmark concurrent processing performance."""
        
        @benchmark_suite.measure_performance("concurrent_processing")
        async def process_concurrent_requests(num_requests: int, metadata: Dict):
            from unittest.mock import patch
            
            # Create multiple requests
            requests = []
            for i in range(num_requests):
                request = HybridProcessingRequest(
                    input_file_path=f"/test/input_{i}.wav",
                    output_file_path=f"/test/output_{i}.wav",
                    processing_mode=ProcessingMode.AI_ONLY
                )
                requests.append(request)
            
            # Mock dependencies
            with patch.object(processing_engine, '_load_audio') as mock_load:
                mock_load.return_value = (torch.randn(1, 44100), 44100)
                
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
                    
                    # Process concurrently
                    tasks = [processing_engine.process_audio(req) for req in requests]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    successful_results = [r for r in results if not isinstance(r, Exception) and r.success]
                    return len(successful_results)
        
        # Test different concurrency levels
        concurrency_levels = [1, 2, 4, 8]
        
        for num_requests in concurrency_levels:
            metadata = {"concurrent_requests": num_requests}
            successful_count = await process_concurrent_requests(num_requests, metadata=metadata)
            
            print(f"Concurrent requests: {num_requests}, Successful: {successful_count}")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_patterns(self, benchmark_suite):
        """Benchmark memory usage patterns."""
        
        @benchmark_suite.measure_performance("memory_pattern")
        async def test_memory_pattern(pattern_name: str, metadata: Dict):
            engines = []
            
            if pattern_name == "create_destroy":
                # Create and destroy multiple engines
                for i in range(5):
                    from unittest.mock import patch
                    with patch('app.ai.hybrid_processing_engine.ProductionModelManager'):
                        engine = HybridProcessingEngine(device="cpu")
                        await engine.initialize()
                        engines.append(engine)
                
                # Clean up
                for engine in engines:
                    await engine.shutdown()
                
            elif pattern_name == "long_running":
                # Single long-running engine with multiple operations
                from unittest.mock import patch
                with patch('app.ai.hybrid_processing_engine.ProductionModelManager'):
                    engine = HybridProcessingEngine(device="cpu")
                    await engine.initialize()
                    
                    # Simulate multiple operations
                    for i in range(10):
                        await engine._update_progress(
                            engine.ProcessingStage.AUDIO_LOADING if hasattr(engine, 'ProcessingStage') else "audio_loading",
                            i * 10.0,
                            f"Operation {i}"
                        )
                    
                    await engine.shutdown()
            
            return len(engines) if engines else 1
        
        # Test different memory patterns
        patterns = ["create_destroy", "long_running"]
        
        for pattern in patterns:
            metadata = {"pattern": pattern}
            result = await test_memory_pattern(pattern, metadata=metadata)
            
            # Force garbage collection
            gc.collect()
    
    @pytest.mark.performance
    def test_throughput_estimation(self, benchmark_suite):
        """Estimate system throughput for different scenarios."""
        
        # Simulate processing times based on benchmarks
        processing_times = {
            ProcessingMode.AI_ONLY: 25.0,      # seconds
            ProcessingMode.REFERENCE_ONLY: 15.0,
            ProcessingMode.HYBRID: 35.0
        }
        
        audio_durations = [30, 60, 180, 300]  # seconds
        
        print("\nTHROUGHPUT ESTIMATION")
        print("-" * 60)
        
        for mode in ProcessingMode:
            base_time = processing_times[mode]
            
            print(f"\n{mode.value.upper()} MODE:")
            print(f"Base processing time: {base_time}s")
            
            for duration in audio_durations:
                # Scale processing time with audio duration
                estimated_time = base_time * (1 + duration / 300)  # Rough scaling
                throughput = 3600 / estimated_time  # Files per hour
                
                print(f"  {duration}s audio: {estimated_time:.1f}s processing, {throughput:.1f} files/hour")
        
        # Concurrent processing estimation
        print(f"\nCONCURRENT PROCESSING (4 workers):")
        for mode in ProcessingMode:
            base_time = processing_times[mode]
            concurrent_throughput = (3600 / base_time) * 4 * 0.8  # 80% efficiency
            print(f"  {mode.value}: ~{concurrent_throughput:.0f} files/hour")
    
    @pytest.mark.performance
    def test_generate_performance_report(self, benchmark_suite):
        """Generate comprehensive performance report."""
        # This would run after all benchmarks to generate a final report
        benchmark_suite.print_benchmark_summary()
        
        # Performance targets and validation
        targets = {
            "engine_initialization": 5.0,     # seconds
            "audio_loading": 2.0,             # seconds for typical file
            "ai_analysis": 10.0,              # seconds
            "parameter_synthesis": 0.5,       # seconds
            "concurrent_processing": 30.0,    # seconds for 4 requests
        }
        
        print(f"\nPERFORMANCE TARGET VALIDATION")
        print("-" * 60)
        
        operations = {}
        for metric in benchmark_suite.benchmark_results:
            if metric.success and metric.operation_name not in operations:
                operations[metric.operation_name] = []
            if metric.success:
                operations[metric.operation_name].append(metric.execution_time)
        
        for op_name, target_time in targets.items():
            if op_name in operations:
                avg_time = np.mean(operations[op_name])
                status = "✅ PASS" if avg_time <= target_time else "❌ FAIL"
                print(f"{op_name}: {avg_time:.2f}s (target: {target_time}s) {status}")
            else:
                print(f"{op_name}: No data available")


if __name__ == "__main__":
    # Run performance benchmarks
    pytest.main([__file__, "-v", "--tb=short", "-m", "performance"])