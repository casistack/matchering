"""
Simplified Audio Feature Extraction for macOS Intel Development.

This version uses only basic numpy/scipy operations to avoid dependency conflicts
while providing core functionality for development and testing.
"""

import asyncio
import hashlib
import logging
import time
from typing import Dict, List, Optional, Union

import numpy as np
import scipy.signal
import soundfile as sf
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AudioFeaturesSimple(BaseModel):
    """Simplified audio features for development on macOS Intel."""
    
    # Basic Spectral Features
    spectral_centroid: List[float] = Field(description="Spectral centroid over time")
    spectral_rolloff: List[float] = Field(description="Spectral rolloff frequency")
    spectral_flatness: List[float] = Field(description="Spectral flatness")
    
    # Temporal Features
    zero_crossing_rate: List[float] = Field(description="Zero crossing rate")
    rms_energy: List[float] = Field(description="RMS energy")
    tempo_estimate: float = Field(description="Simple tempo estimate")
    
    # Mastering-Specific Features
    dynamic_range: float = Field(description="Dynamic range in dB")
    peak_level: float = Field(description="Peak level in dBFS")
    crest_factor: float = Field(description="Crest factor")
    frequency_balance: Dict[str, float] = Field(description="Energy per frequency band")
    stereo_width: float = Field(description="Stereo width measurement")
    
    # Metadata
    sample_rate: int = Field(description="Audio sample rate")
    duration: float = Field(description="Audio duration in seconds")
    channels: int = Field(description="Number of audio channels")
    extraction_time: float = Field(description="Feature extraction time")
    feature_hash: str = Field(description="Hash for caching")
    
    def to_tensor(self) -> np.ndarray:
        """Convert to numpy array for ML compatibility."""
        features = []
        
        # Aggregate time-varying features
        features.extend([
            np.mean(self.spectral_centroid),
            np.std(self.spectral_centroid),
            np.mean(self.spectral_rolloff),
            np.std(self.spectral_rolloff),
            np.mean(self.spectral_flatness),
            np.std(self.spectral_flatness),
            np.mean(self.zero_crossing_rate),
            np.std(self.zero_crossing_rate),
            np.mean(self.rms_energy),
            np.std(self.rms_energy),
            self.tempo_estimate,
            self.dynamic_range,
            self.peak_level,
            self.crest_factor,
            self.stereo_width
        ])
        
        # Add frequency balance
        for band in ['low', 'mid', 'high']:
            features.append(self.frequency_balance.get(band, 0.0))
        
        return np.array(features, dtype=np.float32)


class AudioFeatureExtractorSimple:
    """Simplified feature extractor for macOS Intel development."""
    
    def __init__(self, sample_rate: int = 44100, frame_size: int = 2048):
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.hop_length = frame_size // 4
        
        logger.info(f"SimpleFeatureExtractor: sr={sample_rate}, frame={frame_size}")
    
    async def extract_features(self, 
                              audio_data: Union[np.ndarray, str],
                              audio_path: Optional[str] = None) -> AudioFeaturesSimple:
        """Extract simplified audio features."""
        
        start_time = time.time()
        
        # Load audio if path provided
        if isinstance(audio_data, str):
            audio_path = audio_data
            audio_data, sr = sf.read(audio_data)
            if sr != self.sample_rate:
                audio_data = self._resample_basic(audio_data, sr, self.sample_rate)
        
        # Handle stereo
        if len(audio_data.shape) > 1:
            stereo_width = self._calculate_stereo_width(audio_data)
            audio_mono = np.mean(audio_data, axis=1)
            channels = audio_data.shape[1]
        else:
            stereo_width = 0.0
            audio_mono = audio_data
            channels = 1
        
        duration = len(audio_mono) / self.sample_rate
        
        # Extract features using basic operations
        features = await self._extract_basic_features(audio_mono, stereo_width, channels, duration)
        
        extraction_time = time.time() - start_time
        feature_hash = self._generate_hash(features, audio_path)
        
        return AudioFeaturesSimple(
            **features,
            sample_rate=self.sample_rate,
            duration=duration,
            channels=channels,
            extraction_time=extraction_time,
            feature_hash=feature_hash
        )
    
    async def _extract_basic_features(self, audio: np.ndarray, stereo_width: float, 
                                    channels: int, duration: float) -> Dict:
        """Extract basic features using numpy/scipy only."""
        
        # Frame the audio
        frames = self._frame_audio(audio)
        
        # Spectral features using FFT
        fft_frames = np.fft.rfft(frames, axis=1)
        magnitude_frames = np.abs(fft_frames)
        
        # Frequency bins
        freqs = np.fft.rfftfreq(self.frame_size, 1/self.sample_rate)
        
        # Spectral centroid
        spectral_centroid = []
        for mag in magnitude_frames:
            if np.sum(mag) > 0:
                centroid = np.sum(freqs * mag) / np.sum(mag)
                spectral_centroid.append(centroid)
            else:
                spectral_centroid.append(0.0)
        
        # Spectral rolloff (85% of energy)
        spectral_rolloff = []
        for mag in magnitude_frames:
            cumsum = np.cumsum(mag)
            if cumsum[-1] > 0:
                rolloff_point = 0.85 * cumsum[-1]
                rolloff_idx = np.argmax(cumsum >= rolloff_point)
                spectral_rolloff.append(freqs[rolloff_idx])
            else:
                spectral_rolloff.append(0.0)
        
        # Spectral flatness
        spectral_flatness = []
        for mag in magnitude_frames:
            if np.sum(mag) > 0 and np.min(mag) > 0:
                geometric_mean = np.exp(np.mean(np.log(mag + 1e-10)))
                arithmetic_mean = np.mean(mag)
                flatness = geometric_mean / (arithmetic_mean + 1e-10)
                spectral_flatness.append(flatness)
            else:
                spectral_flatness.append(0.0)
        
        # Zero crossing rate
        zero_crossings = []
        for frame in frames:
            zc = np.sum(np.abs(np.diff(np.sign(frame)))) / (2.0 * len(frame))
            zero_crossings.append(zc)
        
        # RMS energy
        rms_energy = [np.sqrt(np.mean(frame**2)) for frame in frames]
        
        # Simple tempo estimation (count of energy peaks)
        energy_smoothed = np.convolve(rms_energy, np.ones(5)/5, mode='valid')
        peaks = self._find_peaks_simple(energy_smoothed)
        tempo_estimate = len(peaks) * 60.0 / duration if duration > 0 else 0.0
        
        # Mastering features
        dynamic_range = self._calculate_dynamic_range(audio)
        peak_level = 20 * np.log10(np.max(np.abs(audio)) + 1e-10)
        rms_level = np.sqrt(np.mean(audio**2))
        crest_factor = 20 * np.log10(np.max(np.abs(audio)) / (rms_level + 1e-10))
        
        # Frequency balance (simple 3-band)
        frequency_balance = self._analyze_frequency_bands(magnitude_frames, freqs)
        
        return {
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'spectral_flatness': spectral_flatness,
            'zero_crossing_rate': zero_crossings,
            'rms_energy': rms_energy,
            'tempo_estimate': tempo_estimate,
            'dynamic_range': dynamic_range,
            'peak_level': peak_level,
            'crest_factor': crest_factor,
            'frequency_balance': frequency_balance,
            'stereo_width': stereo_width
        }
    
    def _frame_audio(self, audio: np.ndarray) -> np.ndarray:
        """Frame audio into overlapping windows."""
        n_frames = 1 + (len(audio) - self.frame_size) // self.hop_length
        frames = np.zeros((n_frames, self.frame_size))
        
        for i in range(n_frames):
            start = i * self.hop_length
            end = start + self.frame_size
            if end <= len(audio):
                frames[i] = audio[start:end] * np.hanning(self.frame_size)
        
        return frames
    
    def _calculate_stereo_width(self, stereo_audio: np.ndarray) -> float:
        """Calculate stereo width."""
        if stereo_audio.shape[1] < 2:
            return 0.0
        
        left = stereo_audio[:, 0]
        right = stereo_audio[:, 1]
        
        correlation = np.corrcoef(left, right)[0, 1]
        width = (1 - correlation) / 2
        return float(np.clip(width, 0, 1))
    
    def _calculate_dynamic_range(self, audio: np.ndarray) -> float:
        """Calculate dynamic range using percentiles."""
        audio_db = 20 * np.log10(np.abs(audio) + 1e-10)
        p95 = np.percentile(audio_db, 95)
        p10 = np.percentile(audio_db, 10)
        return float(p95 - p10)
    
    def _find_peaks_simple(self, signal: np.ndarray) -> np.ndarray:
        """Simple peak detection."""
        if len(signal) < 3:
            return np.array([])
        
        peaks = []
        for i in range(1, len(signal) - 1):
            if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                if signal[i] > np.mean(signal):  # Above average
                    peaks.append(i)
        
        return np.array(peaks)
    
    def _analyze_frequency_bands(self, magnitude_frames: np.ndarray, 
                                freqs: np.ndarray) -> Dict[str, float]:
        """Analyze energy in frequency bands."""
        
        # Define simple frequency bands
        low_mask = freqs < 500
        mid_mask = (freqs >= 500) & (freqs < 4000)
        high_mask = freqs >= 4000
        
        total_energy = np.sum(magnitude_frames)
        
        if total_energy == 0:
            return {'low': 0.0, 'mid': 0.0, 'high': 0.0}
        
        low_energy = np.sum(magnitude_frames[:, low_mask])
        mid_energy = np.sum(magnitude_frames[:, mid_mask])
        high_energy = np.sum(magnitude_frames[:, high_mask])
        
        return {
            'low': float(low_energy / total_energy),
            'mid': float(mid_energy / total_energy),
            'high': float(high_energy / total_energy)
        }
    
    def _resample_basic(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Basic resampling using scipy."""
        if orig_sr == target_sr:
            return audio
        
        # Simple decimation/interpolation
        ratio = target_sr / orig_sr
        return scipy.signal.resample(audio, int(len(audio) * ratio))
    
    def _generate_hash(self, features: Dict, audio_path: Optional[str] = None) -> str:
        """Generate feature hash."""
        hash_data = f"{self.sample_rate}_{self.frame_size}"
        if audio_path:
            hash_data += f"_{audio_path}"
        if 'tempo_estimate' in features:
            hash_data += f"_{features['tempo_estimate']:.2f}"
        
        return hashlib.md5(hash_data.encode()).hexdigest()


def create_simple_feature_extractor(config: Optional[Dict] = None) -> AudioFeatureExtractorSimple:
    """Create simple feature extractor for development."""
    
    default_config = {
        'sample_rate': 44100,
        'frame_size': 2048
    }
    
    if config:
        default_config.update(config)
    
    return AudioFeatureExtractorSimple(**default_config)