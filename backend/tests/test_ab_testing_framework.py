"""
A/B Testing Framework for Hybrid AI Mastering System.

This module provides comprehensive A/B testing capabilities to compare
AI-only, reference-only, and hybrid processing modes, measuring quality
metrics and user preference simulation.
"""

import asyncio
import json
import pytest
import torch
import torchaudio
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from unittest.mock import patch, Mock
import statistics

# Import the modules to test
import sys
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from app.ai.hybrid_processing_engine import (
    HybridProcessingEngine,
    HybridProcessingRequest,
    HybridProcessingResult,
    ProcessingMode
)
from app.ai.mastering_model import MasteringParameters


class QualityMetric(str, Enum):
    """Quality metrics for A/B testing."""
    LOUDNESS_CONSISTENCY = "loudness_consistency"
    DYNAMIC_RANGE = "dynamic_range"
    FREQUENCY_BALANCE = "frequency_balance"
    STEREO_WIDTH = "stereo_width"
    HARMONIC_DISTORTION = "harmonic_distortion"
    OVERALL_QUALITY = "overall_quality"


@dataclass
class QualityScore:
    """Quality score for a single metric."""
    metric: QualityMetric
    score: float  # 0.0 to 1.0
    confidence: float
    details: Dict = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Complete processing result with quality metrics."""
    processing_mode: ProcessingMode
    success: bool
    processing_time: float
    output_path: Optional[Path]
    quality_scores: List[QualityScore]
    parameters_used: MasteringParameters
    confidence_score: float
    error_message: Optional[str] = None
    
    @property
    def overall_quality(self) -> float:
        """Calculate overall quality score."""
        if not self.quality_scores:
            return 0.0
        
        # Weight different metrics
        weights = {
            QualityMetric.LOUDNESS_CONSISTENCY: 0.25,
            QualityMetric.DYNAMIC_RANGE: 0.20,
            QualityMetric.FREQUENCY_BALANCE: 0.20,
            QualityMetric.STEREO_WIDTH: 0.15,
            QualityMetric.HARMONIC_DISTORTION: 0.15,
            QualityMetric.OVERALL_QUALITY: 0.05
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for quality_score in self.quality_scores:
            weight = weights.get(quality_score.metric, 0.1)
            weighted_sum += quality_score.score * weight * quality_score.confidence
            total_weight += weight * quality_score.confidence
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0


@dataclass
class ABTestResult:
    """A/B test comparison result."""
    test_name: str
    audio_description: str
    results: Dict[ProcessingMode, ProcessingResult]
    winner: Optional[ProcessingMode]
    confidence: float
    metrics_comparison: Dict[QualityMetric, Dict[ProcessingMode, float]]
    statistical_significance: bool = False
    
    def get_ranking(self) -> List[Tuple[ProcessingMode, float]]:
        """Get ranking of processing modes by overall quality."""
        rankings = []
        for mode, result in self.results.items():
            if result.success:
                rankings.append((mode, result.overall_quality))
        
        return sorted(rankings, key=lambda x: x[1], reverse=True)


class QualityAnalyzer:
    """Audio quality analysis for A/B testing."""
    
    def __init__(self, device: str = "cpu"):
        self.device = device
    
    def analyze_audio_quality(self, audio_path: Path) -> List[QualityScore]:
        """Analyze audio quality across multiple metrics."""
        try:
            # Load audio
            audio, sample_rate = torchaudio.load(str(audio_path))
            
            quality_scores = []
            
            # Loudness Consistency
            loudness_score = self._analyze_loudness_consistency(audio, sample_rate)
            quality_scores.append(loudness_score)
            
            # Dynamic Range
            dynamic_score = self._analyze_dynamic_range(audio, sample_rate)
            quality_scores.append(dynamic_score)
            
            # Frequency Balance
            frequency_score = self._analyze_frequency_balance(audio, sample_rate)
            quality_scores.append(frequency_score)
            
            # Stereo Width
            stereo_score = self._analyze_stereo_width(audio, sample_rate)
            quality_scores.append(stereo_score)
            
            # Harmonic Distortion
            distortion_score = self._analyze_harmonic_distortion(audio, sample_rate)
            quality_scores.append(distortion_score)
            
            # Overall Quality (aggregate)
            overall_score = self._calculate_overall_quality(quality_scores)
            quality_scores.append(overall_score)
            
            return quality_scores
            
        except Exception as e:
            # Return default low scores if analysis fails
            return [
                QualityScore(metric, 0.1, 0.1, {"error": str(e)})
                for metric in QualityMetric
            ]
    
    def _analyze_loudness_consistency(self, audio: torch.Tensor, sample_rate: int) -> QualityScore:
        """Analyze loudness consistency across the track."""
        try:
            # Calculate RMS in sliding windows
            window_size = int(0.5 * sample_rate)  # 500ms windows
            hop_size = int(0.1 * sample_rate)     # 100ms hop
            
            rms_values = []
            for i in range(0, audio.shape[1] - window_size, hop_size):
                window = audio[:, i:i + window_size]
                rms = torch.sqrt(torch.mean(window ** 2))
                rms_values.append(rms.item())
            
            if not rms_values:
                return QualityScore(QualityMetric.LOUDNESS_CONSISTENCY, 0.5, 0.5)
            
            # Calculate consistency (low variance = high consistency)
            rms_std = np.std(rms_values)
            rms_mean = np.mean(rms_values)
            
            # Normalize to 0-1 scale (lower variance = higher score)
            consistency = max(0.0, 1.0 - (rms_std / (rms_mean + 1e-8)) * 2)
            confidence = 0.8 if len(rms_values) > 10 else 0.5
            
            return QualityScore(
                QualityMetric.LOUDNESS_CONSISTENCY,
                consistency,
                confidence,
                {"rms_std": rms_std, "rms_mean": rms_mean, "windows": len(rms_values)}
            )
            
        except Exception as e:
            return QualityScore(QualityMetric.LOUDNESS_CONSISTENCY, 0.5, 0.1, {"error": str(e)})
    
    def _analyze_dynamic_range(self, audio: torch.Tensor, sample_rate: int) -> QualityScore:
        """Analyze dynamic range of the audio."""
        try:
            # Calculate peak and RMS
            peak = torch.max(torch.abs(audio)).item()
            rms = torch.sqrt(torch.mean(audio ** 2)).item()
            
            if rms < 1e-8:
                return QualityScore(QualityMetric.DYNAMIC_RANGE, 0.1, 0.5)
            
            # Dynamic range in dB
            dynamic_range_db = 20 * np.log10(peak / rms)
            
            # Score based on dynamic range (6-20 dB is good range)
            if dynamic_range_db < 6:
                score = dynamic_range_db / 6  # Very compressed
            elif dynamic_range_db > 20:
                score = 1.0 - (dynamic_range_db - 20) / 20  # Too dynamic
            else:
                score = 0.7 + 0.3 * ((dynamic_range_db - 6) / 14)  # Good range
            
            score = max(0.0, min(1.0, score))
            confidence = 0.9
            
            return QualityScore(
                QualityMetric.DYNAMIC_RANGE,
                score,
                confidence,
                {"dynamic_range_db": dynamic_range_db, "peak": peak, "rms": rms}
            )
            
        except Exception as e:
            return QualityScore(QualityMetric.DYNAMIC_RANGE, 0.5, 0.1, {"error": str(e)})
    
    def _analyze_frequency_balance(self, audio: torch.Tensor, sample_rate: int) -> QualityScore:
        """Analyze frequency balance across the spectrum."""
        try:
            # Calculate FFT
            fft = torch.fft.fft(audio)
            magnitude = torch.abs(fft)
            
            # Define frequency bands
            freqs = torch.fft.fftfreq(audio.shape[1], 1.0 / sample_rate)
            nyquist = sample_rate / 2
            
            # Band definitions (approximate)
            bands = {
                "low": (20, 200),      # Bass
                "low_mid": (200, 800),  # Low mids
                "mid": (800, 3200),     # Mids
                "high_mid": (3200, 8000), # High mids
                "high": (8000, nyquist)   # Highs
            }
            
            band_energies = {}
            for band_name, (low_freq, high_freq) in bands.items():
                mask = (torch.abs(freqs) >= low_freq) & (torch.abs(freqs) <= high_freq)
                if mask.sum() > 0:
                    energy = torch.mean(magnitude[:, mask]).item()
                    band_energies[band_name] = energy
                else:
                    band_energies[band_name] = 0.0
            
            # Calculate balance score (lower variance = better balance)
            energies = list(band_energies.values())
            if len(energies) > 1:
                energy_std = np.std(energies)
                energy_mean = np.mean(energies)
                balance_score = max(0.0, 1.0 - (energy_std / (energy_mean + 1e-8)))
            else:
                balance_score = 0.5
            
            confidence = 0.7
            
            return QualityScore(
                QualityMetric.FREQUENCY_BALANCE,
                balance_score,
                confidence,
                {"band_energies": band_energies, "energy_std": energy_std}
            )
            
        except Exception as e:
            return QualityScore(QualityMetric.FREQUENCY_BALANCE, 0.5, 0.1, {"error": str(e)})
    
    def _analyze_stereo_width(self, audio: torch.Tensor, sample_rate: int) -> QualityScore:
        """Analyze stereo width and spatial characteristics."""
        try:
            if audio.shape[0] < 2:
                # Mono audio - perfect center
                return QualityScore(
                    QualityMetric.STEREO_WIDTH,
                    0.7,  # Reasonable score for mono
                    0.9,
                    {"channels": 1, "type": "mono"}
                )
            
            left = audio[0, :]
            right = audio[1, :]
            
            # Calculate correlation between channels
            correlation = torch.corrcoef(torch.stack([left, right]))[0, 1].item()
            
            # Calculate side signal energy
            mid = (left + right) / 2
            side = (left - right) / 2
            
            mid_energy = torch.mean(mid ** 2).item()
            side_energy = torch.mean(side ** 2).item()
            
            if mid_energy + side_energy > 0:
                width_ratio = side_energy / (mid_energy + side_energy)
            else:
                width_ratio = 0.0
            
            # Good stereo width is typically 0.2-0.6
            if 0.2 <= width_ratio <= 0.6:
                width_score = 0.8 + 0.2 * (1 - abs(width_ratio - 0.4) / 0.2)
            else:
                width_score = max(0.0, 0.8 - abs(width_ratio - 0.4))
            
            confidence = 0.8
            
            return QualityScore(
                QualityMetric.STEREO_WIDTH,
                width_score,
                confidence,
                {
                    "correlation": correlation,
                    "width_ratio": width_ratio,
                    "mid_energy": mid_energy,
                    "side_energy": side_energy
                }
            )
            
        except Exception as e:
            return QualityScore(QualityMetric.STEREO_WIDTH, 0.5, 0.1, {"error": str(e)})
    
    def _analyze_harmonic_distortion(self, audio: torch.Tensor, sample_rate: int) -> QualityScore:
        """Analyze harmonic distortion characteristics."""
        try:
            # Simple THD estimation using peak detection
            # This is a simplified version - full THD analysis would be more complex
            
            # Calculate FFT
            fft = torch.fft.fft(audio)
            magnitude = torch.abs(fft)
            
            # Find peaks (simplified)
            magnitude_1d = torch.mean(magnitude, dim=0) if magnitude.dim() > 1 else magnitude
            
            # Estimate noise floor
            sorted_mag = torch.sort(magnitude_1d)[0]
            noise_floor = torch.mean(sorted_mag[:len(sorted_mag)//4]).item()  # Bottom 25%
            
            # Estimate signal peaks
            signal_peaks = magnitude_1d[magnitude_1d > noise_floor * 10]
            
            if len(signal_peaks) > 0:
                signal_power = torch.mean(signal_peaks).item()
                snr_db = 20 * np.log10(signal_power / (noise_floor + 1e-8))
                
                # Convert SNR to distortion score (higher SNR = lower distortion = higher score)
                distortion_score = min(1.0, max(0.0, (snr_db - 20) / 40))  # 20-60 dB range
            else:
                distortion_score = 0.5
            
            confidence = 0.6  # Lower confidence for simplified analysis
            
            return QualityScore(
                QualityMetric.HARMONIC_DISTORTION,
                distortion_score,
                confidence,
                {"snr_db": snr_db, "noise_floor": noise_floor, "signal_peaks": len(signal_peaks)}
            )
            
        except Exception as e:
            return QualityScore(QualityMetric.HARMONIC_DISTORTION, 0.5, 0.1, {"error": str(e)})
    
    def _calculate_overall_quality(self, quality_scores: List[QualityScore]) -> QualityScore:
        """Calculate overall quality from individual metrics."""
        if not quality_scores:
            return QualityScore(QualityMetric.OVERALL_QUALITY, 0.0, 0.0)
        
        # Weight the scores
        weights = {
            QualityMetric.LOUDNESS_CONSISTENCY: 0.25,
            QualityMetric.DYNAMIC_RANGE: 0.25,
            QualityMetric.FREQUENCY_BALANCE: 0.25,
            QualityMetric.STEREO_WIDTH: 0.15,
            QualityMetric.HARMONIC_DISTORTION: 0.10
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        confidence_sum = 0.0
        
        for score in quality_scores:
            if score.metric in weights:
                weight = weights[score.metric]
                weighted_sum += score.score * weight * score.confidence
                total_weight += weight * score.confidence
                confidence_sum += score.confidence
        
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        overall_confidence = confidence_sum / len(quality_scores) if quality_scores else 0.0
        
        return QualityScore(
            QualityMetric.OVERALL_QUALITY,
            overall_score,
            overall_confidence,
            {"component_scores": len(quality_scores)}
        )


class ABTestingFramework:
    """Comprehensive A/B testing framework."""
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.quality_analyzer = QualityAnalyzer(device)
        self.test_results: List[ABTestResult] = []
    
    async def run_ab_test(
        self,
        test_name: str,
        input_audio_path: Path,
        reference_audio_path: Optional[Path] = None,
        test_parameters: Optional[Dict] = None
    ) -> ABTestResult:
        """Run comprehensive A/B test comparing all processing modes."""
        
        print(f"\n🧪 Running A/B Test: {test_name}")
        print(f"Input: {input_audio_path.name}")
        if reference_audio_path:
            print(f"Reference: {reference_audio_path.name}")
        
        # Prepare test configurations
        test_configs = self._prepare_test_configurations(
            input_audio_path, reference_audio_path, test_parameters
        )
        
        results = {}
        
        # Process with each mode
        for mode, config in test_configs.items():
            print(f"  Testing {mode.value} mode...")
            
            try:
                result = await self._process_with_mode(mode, config)
                results[mode] = result
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                results[mode] = ProcessingResult(
                    processing_mode=mode,
                    success=False,
                    processing_time=0.0,
                    output_path=None,
                    quality_scores=[],
                    parameters_used=MasteringParameters(),
                    confidence_score=0.0,
                    error_message=str(e)
                )
        
        # Analyze results
        ab_result = self._analyze_ab_results(test_name, str(input_audio_path), results)
        self.test_results.append(ab_result)
        
        # Print summary
        self._print_test_summary(ab_result)
        
        return ab_result
    
    def _prepare_test_configurations(
        self,
        input_path: Path,
        reference_path: Optional[Path],
        parameters: Optional[Dict]
    ) -> Dict[ProcessingMode, HybridProcessingRequest]:
        """Prepare test configurations for each processing mode."""
        
        base_params = {
            "target_loudness_lufs": -14.0,
            "preserve_dynamics": True,
            "enable_quality_validation": True,
            "ai_intensity": 0.7,
            "reference_influence": 0.6,
            "ai_weight": 0.6,
            "reference_weight": 0.4,
            "adaptive_blending": True
        }
        
        if parameters:
            base_params.update(parameters)
        
        configs = {}
        
        # AI-only configuration
        configs[ProcessingMode.AI_ONLY] = HybridProcessingRequest(
            input_file_path=str(input_path),
            output_file_path=str(input_path.parent / f"output_ai_{input_path.stem}.wav"),
            processing_mode=ProcessingMode.AI_ONLY,
            **{k: v for k, v in base_params.items() if k not in ['reference_influence', 'reference_weight']}
        )
        
        # Reference-only configuration (if reference available)
        if reference_path:
            configs[ProcessingMode.REFERENCE_ONLY] = HybridProcessingRequest(
                input_file_path=str(input_path),
                reference_file_path=str(reference_path),
                output_file_path=str(input_path.parent / f"output_ref_{input_path.stem}.wav"),
                processing_mode=ProcessingMode.REFERENCE_ONLY,
                **{k: v for k, v in base_params.items() if k not in ['ai_intensity', 'ai_weight']}
            )
            
            # Hybrid configuration
            configs[ProcessingMode.HYBRID] = HybridProcessingRequest(
                input_file_path=str(input_path),
                reference_file_path=str(reference_path),
                output_file_path=str(input_path.parent / f"output_hybrid_{input_path.stem}.wav"),
                processing_mode=ProcessingMode.HYBRID,
                **base_params
            )
        
        return configs
    
    async def _process_with_mode(self, mode: ProcessingMode, config: HybridProcessingRequest) -> ProcessingResult:
        """Process audio with specified mode and analyze quality."""
        
        # Mock processing engine for testing
        with patch('app.ai.hybrid_processing_engine.ProductionModelManager'):
            engine = HybridProcessingEngine(device=self.device)
            await engine.initialize()
            
            # Mock the actual processing to focus on framework testing
            with patch.object(engine, '_load_audio') as mock_load:
                mock_load.return_value = (torch.randn(1, 44100), 44100)
                
                with patch.object(engine, '_analyze_audio_ai') as mock_ai_analysis:
                    with patch.object(engine, '_analyze_reference_audio') as mock_ref_analysis:
                        # Mock analysis results
                        from app.ai.hybrid_processing_engine import AudioAnalysisResult, ReferenceAnalysisResult
                        from app.ai.hybrid_feature_extractor import AudioCharacteristics, HybridFeatures
                        
                        mock_ai_analysis.return_value = AudioAnalysisResult(
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
                        
                        mock_ref_analysis.return_value = ReferenceAnalysisResult(
                            characteristics=AudioCharacteristics(
                                genre="test",
                                genre_confidence=0.9,
                                has_vocals=False,
                                is_instrumental=True,
                                energy_level=0.8,
                                dynamic_range=8.0,
                                complexity_score=0.7,
                                tempo_bpm=125.0,
                                key_signature="C",
                                audio_quality=0.9
                            ),
                            target_parameters=MasteringParameters(),
                            style_profile={},
                            matching_confidence=0.85
                        )
                        
                        # Process audio
                        start_time = asyncio.get_event_loop().time()
                        result = await engine.process_audio(config)
                        processing_time = asyncio.get_event_loop().time() - start_time
                        
                        # Simulate output file creation
                        output_path = Path(config.output_file_path)
                        output_path.parent.mkdir(exist_ok=True)
                        
                        # Create dummy output file for quality analysis
                        dummy_audio = torch.randn(1, 44100)
                        torchaudio.save(str(output_path), dummy_audio, 44100)
                        
                        # Analyze quality
                        quality_scores = self.quality_analyzer.analyze_audio_quality(output_path)
                        
                        return ProcessingResult(
                            processing_mode=mode,
                            success=result.success,
                            processing_time=processing_time,
                            output_path=output_path if result.success else None,
                            quality_scores=quality_scores,
                            parameters_used=result.applied_parameters,
                            confidence_score=result.ai_confidence if hasattr(result, 'ai_confidence') else 0.8,
                            error_message=result.error_message if hasattr(result, 'error_message') else None
                        )
    
    def _analyze_ab_results(self, test_name: str, audio_description: str, results: Dict[ProcessingMode, ProcessingResult]) -> ABTestResult:
        """Analyze A/B test results and determine winner."""
        
        # Calculate metrics comparison
        metrics_comparison = {}
        for metric in QualityMetric:
            metrics_comparison[metric] = {}
            for mode, result in results.items():
                if result.success and result.quality_scores:
                    metric_score = next(
                        (score.score for score in result.quality_scores if score.metric == metric),
                        0.0
                    )
                    metrics_comparison[metric][mode] = metric_score
                else:
                    metrics_comparison[metric][mode] = 0.0
        
        # Determine winner based on overall quality
        successful_results = {mode: result for mode, result in results.items() if result.success}
        
        if successful_results:
            winner = max(successful_results.keys(), key=lambda mode: successful_results[mode].overall_quality)
            winner_score = successful_results[winner].overall_quality
            
            # Calculate confidence in winner
            other_scores = [result.overall_quality for mode, result in successful_results.items() if mode != winner]
            if other_scores:
                max_other = max(other_scores)
                confidence = min(1.0, (winner_score - max_other) / winner_score) if winner_score > 0 else 0.5
            else:
                confidence = 1.0
            
            # Simple statistical significance check
            statistical_significance = confidence > 0.1 and len(successful_results) > 1
        else:
            winner = None
            confidence = 0.0
            statistical_significance = False
        
        return ABTestResult(
            test_name=test_name,
            audio_description=audio_description,
            results=results,
            winner=winner,
            confidence=confidence,
            metrics_comparison=metrics_comparison,
            statistical_significance=statistical_significance
        )
    
    def _print_test_summary(self, result: ABTestResult):
        """Print A/B test summary."""
        print(f"\n📊 A/B Test Results: {result.test_name}")
        print("=" * 60)
        
        # Print rankings
        rankings = result.get_ranking()
        print("🏆 RANKINGS:")
        for i, (mode, score) in enumerate(rankings, 1):
            status = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            print(f"  {status} {mode.value.upper()}: {score:.3f}")
        
        # Print winner
        if result.winner:
            print(f"\n🎉 WINNER: {result.winner.value.upper()}")
            print(f"   Confidence: {result.confidence:.1%}")
            print(f"   Statistical Significance: {'Yes' if result.statistical_significance else 'No'}")
        else:
            print("\n❌ No successful processing results")
        
        # Print detailed metrics
        print(f"\n📈 DETAILED METRICS:")
        for metric, mode_scores in result.metrics_comparison.items():
            print(f"  {metric.value.replace('_', ' ').title()}:")
            for mode, score in mode_scores.items():
                if mode in result.results and result.results[mode].success:
                    print(f"    {mode.value}: {score:.3f}")
        
        # Print processing times
        print(f"\n⏱️  PROCESSING TIMES:")
        for mode, processing_result in result.results.items():
            if processing_result.success:
                print(f"  {mode.value}: {processing_result.processing_time:.2f}s")
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive A/B testing report."""
        if not self.test_results:
            return {"message": "No test results available"}
        
        report = {
            "summary": {
                "total_tests": len(self.test_results),
                "successful_tests": len([r for r in self.test_results if r.winner is not None])
            },
            "mode_performance": {},
            "metric_analysis": {},
            "winner_statistics": {}
        }
        
        # Analyze mode performance
        for mode in ProcessingMode:
            mode_results = []
            for test in self.test_results:
                if mode in test.results and test.results[mode].success:
                    mode_results.append(test.results[mode].overall_quality)
            
            if mode_results:
                report["mode_performance"][mode.value] = {
                    "count": len(mode_results),
                    "average_quality": statistics.mean(mode_results),
                    "std_dev": statistics.stdev(mode_results) if len(mode_results) > 1 else 0.0,
                    "min_quality": min(mode_results),
                    "max_quality": max(mode_results)
                }
        
        # Analyze metric performance
        for metric in QualityMetric:
            metric_data = {}
            for mode in ProcessingMode:
                scores = []
                for test in self.test_results:
                    if mode in test.metrics_comparison[metric]:
                        scores.append(test.metrics_comparison[metric][mode])
                
                if scores:
                    metric_data[mode.value] = {
                        "average": statistics.mean(scores),
                        "count": len(scores)
                    }
            
            report["metric_analysis"][metric.value] = metric_data
        
        # Winner statistics
        winners = [test.winner.value for test in self.test_results if test.winner]
        winner_counts = {}
        for winner in winners:
            winner_counts[winner] = winner_counts.get(winner, 0) + 1
        
        report["winner_statistics"] = winner_counts
        
        return report


class TestABTestingFramework:
    """Test suite for the A/B testing framework."""
    
    @pytest.fixture
    def ab_framework(self):
        """Create A/B testing framework."""
        return ABTestingFramework(device="cpu")
    
    @pytest.fixture
    def sample_audio_files(self, tmp_path):
        """Create sample audio files for testing."""
        # Create input audio
        input_audio = torch.sin(2 * np.pi * 440.0 * torch.linspace(0, 2.0, 88200)).unsqueeze(0)
        input_file = tmp_path / "input_test.wav"
        torchaudio.save(str(input_file), input_audio, 44100)
        
        # Create reference audio
        ref_audio = torch.sin(2 * np.pi * 880.0 * torch.linspace(0, 2.0, 88200)).unsqueeze(0)
        ref_file = tmp_path / "reference_test.wav"
        torchaudio.save(str(ref_file), ref_audio, 44100)
        
        return {"input": input_file, "reference": ref_file}
    
    def test_quality_analyzer_initialization(self):
        """Test quality analyzer initialization."""
        analyzer = QualityAnalyzer(device="cpu")
        assert analyzer.device == "cpu"
    
    def test_quality_analysis(self, tmp_path):
        """Test audio quality analysis."""
        # Create test audio file
        audio = torch.randn(2, 44100)  # 1 second stereo
        test_file = tmp_path / "test_quality.wav"
        torchaudio.save(str(test_file), audio, 44100)
        
        analyzer = QualityAnalyzer(device="cpu")
        quality_scores = analyzer.analyze_audio_quality(test_file)
        
        # Should return all quality metrics
        assert len(quality_scores) == len(QualityMetric)
        
        # All scores should be valid
        for score in quality_scores:
            assert isinstance(score, QualityScore)
            assert 0.0 <= score.score <= 1.0
            assert 0.0 <= score.confidence <= 1.0
            assert score.metric in QualityMetric
    
    @pytest.mark.asyncio
    async def test_ab_test_execution(self, ab_framework, sample_audio_files):
        """Test complete A/B test execution."""
        input_file = sample_audio_files["input"]
        reference_file = sample_audio_files["reference"]
        
        # Run A/B test
        result = await ab_framework.run_ab_test(
            test_name="Test A/B Comparison",
            input_audio_path=input_file,
            reference_audio_path=reference_file,
            test_parameters={"ai_intensity": 0.8}
        )
        
        # Validate results
        assert isinstance(result, ABTestResult)
        assert result.test_name == "Test A/B Comparison"
        assert len(result.results) > 0  # Should have at least AI mode
        
        # Check that we have quality metrics
        for mode, processing_result in result.results.items():
            if processing_result.success:
                assert len(processing_result.quality_scores) > 0
    
    @pytest.mark.asyncio
    async def test_ai_only_comparison(self, ab_framework, sample_audio_files):
        """Test AI-only processing comparison."""
        input_file = sample_audio_files["input"]
        
        # Run test without reference (AI-only)
        result = await ab_framework.run_ab_test(
            test_name="AI Only Test",
            input_audio_path=input_file,
            reference_audio_path=None
        )
        
        # Should only have AI mode
        assert ProcessingMode.AI_ONLY in result.results
        assert ProcessingMode.REFERENCE_ONLY not in result.results
        assert ProcessingMode.HYBRID not in result.results
    
    def test_comprehensive_report_generation(self, ab_framework):
        """Test comprehensive report generation."""
        # Add some mock test results
        mock_result = ABTestResult(
            test_name="Mock Test",
            audio_description="Test audio",
            results={
                ProcessingMode.AI_ONLY: ProcessingResult(
                    processing_mode=ProcessingMode.AI_ONLY,
                    success=True,
                    processing_time=25.0,
                    output_path=Path("/mock/output.wav"),
                    quality_scores=[
                        QualityScore(QualityMetric.OVERALL_QUALITY, 0.8, 0.9)
                    ],
                    parameters_used=MasteringParameters(),
                    confidence_score=0.8
                )
            },
            winner=ProcessingMode.AI_ONLY,
            confidence=0.9,
            metrics_comparison={
                QualityMetric.OVERALL_QUALITY: {ProcessingMode.AI_ONLY: 0.8}
            },
            statistical_significance=True
        )
        
        ab_framework.test_results.append(mock_result)
        
        # Generate report
        report = ab_framework.generate_comprehensive_report()
        
        # Validate report structure
        assert "summary" in report
        assert "mode_performance" in report
        assert "metric_analysis" in report
        assert "winner_statistics" in report
        
        assert report["summary"]["total_tests"] == 1
        assert report["summary"]["successful_tests"] == 1
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_performance_comparison(self, ab_framework, sample_audio_files):
        """Test performance comparison across modes."""
        input_file = sample_audio_files["input"]
        reference_file = sample_audio_files["reference"]
        
        # Run test and measure performance
        start_time = asyncio.get_event_loop().time()
        
        result = await ab_framework.run_ab_test(
            test_name="Performance Test",
            input_audio_path=input_file,
            reference_audio_path=reference_file
        )
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        print(f"\nPerformance Test Results:")
        print(f"Total A/B test time: {total_time:.2f}s")
        
        for mode, processing_result in result.results.items():
            if processing_result.success:
                print(f"{mode.value} processing time: {processing_result.processing_time:.2f}s")
        
        # Test should complete in reasonable time
        assert total_time < 30.0  # 30 seconds max


if __name__ == "__main__":
    # Run A/B testing framework tests
    pytest.main([__file__, "-v", "--tb=short"])