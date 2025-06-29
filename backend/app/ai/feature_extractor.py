"""
Audio Feature Extraction Service for AI Mastering.

This module implements comprehensive audio feature extraction for AI-powered
mastering parameter prediction, following enterprise architecture patterns.
"""

import asyncio
import hashlib
import logging
import time
from typing import Dict, List, Optional, Tuple, Union

import librosa
import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AudioFeatures(BaseModel):
    """Comprehensive audio features for AI mastering analysis."""
    
    # Spectral Features
    mfcc: List[List[float]] = Field(description="Mel-frequency cepstral coefficients (13 coefficients)")
    spectral_centroid: List[float] = Field(description="Spectral centroid over time")
    spectral_rolloff: List[float] = Field(description="Spectral rolloff frequency")
    spectral_contrast: List[List[float]] = Field(description="Spectral contrast across frequency bands")
    spectral_bandwidth: List[float] = Field(description="Spectral bandwidth")
    spectral_flatness: List[float] = Field(description="Spectral flatness (tonality)")
    
    # Harmonic Features
    chroma: List[List[float]] = Field(description="Chroma features (12 pitch classes)")
    tonnetz: List[List[float]] = Field(description="Tonal centroid features")
    
    # Temporal Features
    zero_crossing_rate: List[float] = Field(description="Zero crossing rate")
    rms_energy: List[float] = Field(description="RMS energy")
    tempo: float = Field(description="Estimated tempo in BPM")
    beat_frames: List[int] = Field(description="Beat frame locations")
    
    # Mastering-Specific Features
    dynamic_range: float = Field(description="Dynamic range in dB")
    loudness_lufs: float = Field(description="Integrated loudness (LUFS)")
    peak_level: float = Field(description="Peak level in dBFS")
    crest_factor: float = Field(description="Crest factor (peak-to-RMS ratio)")
    frequency_balance: Dict[str, float] = Field(description="Energy distribution across frequency bands")
    stereo_width: float = Field(description="Stereo width measurement")
    
    # Metadata
    sample_rate: int = Field(description="Audio sample rate")
    duration: float = Field(description="Audio duration in seconds")
    channels: int = Field(description="Number of audio channels")
    extraction_time: float = Field(description="Feature extraction time in seconds")
    feature_hash: str = Field(description="Hash of extracted features for caching")
    
    def to_tensor(self) -> np.ndarray:
        """Convert features to numpy array for ML model input."""
        # Aggregate time-varying features with statistics
        feature_vector = []
        
        # MFCC statistics
        mfcc_array = np.array(self.mfcc)
        feature_vector.extend([
            np.mean(mfcc_array, axis=1),  # Mean across time
            np.std(mfcc_array, axis=1),   # Std across time
            np.max(mfcc_array, axis=1),   # Max across time
            np.min(mfcc_array, axis=1)    # Min across time
        ])
        
        # Spectral feature statistics
        spectral_features = [
            self.spectral_centroid,
            self.spectral_rolloff,
            self.spectral_bandwidth,
            self.spectral_flatness
        ]
        
        for feature in spectral_features:
            feature_array = np.array(feature)
            feature_vector.extend([
                np.mean(feature_array),
                np.std(feature_array),
                np.max(feature_array),
                np.min(feature_array)
            ])
        
        # Chroma statistics
        chroma_array = np.array(self.chroma)
        feature_vector.extend([
            np.mean(chroma_array, axis=1),
            np.std(chroma_array, axis=1)
        ])
        
        # Temporal features
        feature_vector.extend([
            np.mean(self.zero_crossing_rate),
            np.std(self.zero_crossing_rate),
            np.mean(self.rms_energy),
            np.std(self.rms_energy),
            self.tempo
        ])
        
        # Mastering-specific features
        feature_vector.extend([
            self.dynamic_range,
            self.loudness_lufs,
            self.peak_level,
            self.crest_factor,
            self.stereo_width
        ])
        
        # Frequency balance
        freq_bands = ['sub_bass', 'bass', 'low_mid', 'mid', 'high_mid', 'presence', 'brilliance']
        for band in freq_bands:
            feature_vector.append(self.frequency_balance.get(band, 0.0))
        
        # Flatten and convert to numpy array
        flattened = []
        for item in feature_vector:
            if isinstance(item, (list, np.ndarray)):
                flattened.extend(item.flatten())
            else:
                flattened.append(float(item))
                
        return np.array(flattened, dtype=np.float32)


class AudioFeatureExtractor:
    """Enterprise-grade audio feature extraction for mastering AI."""
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 hop_length: int = 512,
                 n_mfcc: int = 13,
                 n_chroma: int = 12,
                 cache_features: bool = True):
        """
        Initialize audio feature extractor.
        
        Args:
            sample_rate: Target sample rate for analysis
            hop_length: Hop length for STFT analysis
            n_mfcc: Number of MFCC coefficients
            n_chroma: Number of chroma bins
            cache_features: Whether to cache extracted features
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.n_mfcc = n_mfcc
        self.n_chroma = n_chroma
        self.cache_features = cache_features
        
        # Performance tracking
        self._extraction_times = []
        
        logger.info(f"AudioFeatureExtractor initialized: sr={sample_rate}, hop={hop_length}")
    
    async def extract_features(self, 
                              audio_data: Union[np.ndarray, str],
                              audio_path: Optional[str] = None) -> AudioFeatures:
        """
        Extract comprehensive audio features for AI analysis.
        
        Args:
            audio_data: Audio array or file path
            audio_path: Optional path for metadata
            
        Returns:
            AudioFeatures object with all extracted features
        """
        start_time = time.time()
        
        try:
            # Load audio if path provided
            if isinstance(audio_data, str):
                audio_path = audio_data
                audio_data, original_sr = librosa.load(audio_data, sr=None)
                
                # Resample if needed
                if original_sr != self.sample_rate:
                    audio_data = librosa.resample(
                        audio_data, 
                        orig_sr=original_sr, 
                        target_sr=self.sample_rate
                    )
            
            # Handle stereo to mono conversion
            if len(audio_data.shape) > 1:
                # Calculate stereo width before converting to mono
                stereo_width = self._calculate_stereo_width(audio_data)
                audio_mono = librosa.to_mono(audio_data)
                channels = audio_data.shape[0] if len(audio_data.shape) > 1 else 1
            else:
                stereo_width = 0.0
                audio_mono = audio_data
                channels = 1
            
            duration = len(audio_mono) / self.sample_rate
            
            # Extract features in parallel where possible
            features = await self._extract_all_features(audio_mono, stereo_width, channels, duration)
            
            extraction_time = time.time() - start_time
            self._extraction_times.append(extraction_time)
            
            # Generate feature hash for caching
            feature_hash = self._generate_feature_hash(features, audio_path)
            
            # Create AudioFeatures object
            audio_features = AudioFeatures(
                **features,
                sample_rate=self.sample_rate,
                duration=duration,
                channels=channels,
                extraction_time=extraction_time,
                feature_hash=feature_hash
            )
            
            logger.info(f"Feature extraction completed in {extraction_time:.3f}s for {duration:.1f}s audio")
            return audio_features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {str(e)}")
            raise
    
    async def _extract_all_features(self, 
                                   audio: np.ndarray, 
                                   stereo_width: float,
                                   channels: int,
                                   duration: float) -> Dict:
        """Extract all audio features efficiently."""
        
        # Run feature extraction in parallel using asyncio
        tasks = [
            self._extract_spectral_features(audio),
            self._extract_harmonic_features(audio),
            self._extract_temporal_features(audio),
            self._extract_mastering_features(audio, stereo_width)
        ]
        
        spectral, harmonic, temporal, mastering = await asyncio.gather(*tasks)
        
        # Combine all features
        features = {**spectral, **harmonic, **temporal, **mastering}
        return features
    
    async def _extract_spectral_features(self, audio: np.ndarray) -> Dict:
        """Extract spectral domain features."""
        
        # Run CPU-intensive operations in thread pool
        loop = asyncio.get_event_loop()
        
        # MFCC
        mfcc = await loop.run_in_executor(
            None, 
            lambda: librosa.feature.mfcc(
                y=audio, 
                sr=self.sample_rate, 
                n_mfcc=self.n_mfcc,
                hop_length=self.hop_length
            ).tolist()
        )
        
        # Spectral features
        spectral_centroid = await loop.run_in_executor(
            None,
            lambda: librosa.feature.spectral_centroid(
                y=audio, 
                sr=self.sample_rate,
                hop_length=self.hop_length
            )[0].tolist()
        )
        
        spectral_rolloff = await loop.run_in_executor(
            None,
            lambda: librosa.feature.spectral_rolloff(
                y=audio,
                sr=self.sample_rate,
                hop_length=self.hop_length
            )[0].tolist()
        )
        
        spectral_contrast = await loop.run_in_executor(
            None,
            lambda: librosa.feature.spectral_contrast(
                y=audio,
                sr=self.sample_rate,
                hop_length=self.hop_length
            ).tolist()
        )
        
        spectral_bandwidth = await loop.run_in_executor(
            None,
            lambda: librosa.feature.spectral_bandwidth(
                y=audio,
                sr=self.sample_rate,
                hop_length=self.hop_length
            )[0].tolist()
        )
        
        spectral_flatness = await loop.run_in_executor(
            None,
            lambda: librosa.feature.spectral_flatness(
                y=audio,
                hop_length=self.hop_length
            )[0].tolist()
        )
        
        return {
            'mfcc': mfcc,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'spectral_contrast': spectral_contrast,
            'spectral_bandwidth': spectral_bandwidth,
            'spectral_flatness': spectral_flatness
        }
    
    async def _extract_harmonic_features(self, audio: np.ndarray) -> Dict:
        """Extract harmonic and tonal features."""
        
        loop = asyncio.get_event_loop()
        
        # Chroma features
        chroma = await loop.run_in_executor(
            None,
            lambda: librosa.feature.chroma_stft(
                y=audio,
                sr=self.sample_rate,
                hop_length=self.hop_length,
                n_chroma=self.n_chroma
            ).tolist()
        )
        
        # Tonnetz (tonal centroid features)
        tonnetz = await loop.run_in_executor(
            None,
            lambda: librosa.feature.tonnetz(
                y=audio,
                sr=self.sample_rate
            ).tolist()
        )
        
        return {
            'chroma': chroma,
            'tonnetz': tonnetz
        }
    
    async def _extract_temporal_features(self, audio: np.ndarray) -> Dict:
        """Extract temporal domain features."""
        
        loop = asyncio.get_event_loop()
        
        # Zero crossing rate
        zcr = await loop.run_in_executor(
            None,
            lambda: librosa.feature.zero_crossing_rate(
                audio,
                hop_length=self.hop_length
            )[0].tolist()
        )
        
        # RMS energy
        rms = await loop.run_in_executor(
            None,
            lambda: librosa.feature.rms(
                y=audio,
                hop_length=self.hop_length
            )[0].tolist()
        )
        
        # Tempo and beat tracking
        tempo, beat_frames = await loop.run_in_executor(
            None,
            lambda: librosa.beat.beat_track(
                y=audio,
                sr=self.sample_rate,
                hop_length=self.hop_length
            )
        )
        
        return {
            'zero_crossing_rate': zcr,
            'rms_energy': rms,
            'tempo': float(tempo),
            'beat_frames': beat_frames.tolist()
        }
    
    async def _extract_mastering_features(self, audio: np.ndarray, stereo_width: float) -> Dict:
        """Extract mastering-specific features."""
        
        loop = asyncio.get_event_loop()
        
        # Dynamic range calculation
        dynamic_range = await loop.run_in_executor(None, self._calculate_dynamic_range, audio)
        
        # Loudness (simplified LUFS estimation)
        loudness_lufs = await loop.run_in_executor(None, self._calculate_lufs, audio)
        
        # Peak level
        peak_level = float(20 * np.log10(np.max(np.abs(audio)) + 1e-10))
        
        # Crest factor
        rms_level = np.sqrt(np.mean(audio**2))
        peak_level_linear = np.max(np.abs(audio))
        crest_factor = float(20 * np.log10(peak_level_linear / (rms_level + 1e-10)))
        
        # Frequency balance analysis
        frequency_balance = await loop.run_in_executor(
            None, 
            self._analyze_frequency_balance, 
            audio
        )
        
        return {
            'dynamic_range': dynamic_range,
            'loudness_lufs': loudness_lufs,
            'peak_level': peak_level,
            'crest_factor': crest_factor,
            'frequency_balance': frequency_balance,
            'stereo_width': stereo_width
        }
    
    def _calculate_stereo_width(self, stereo_audio: np.ndarray) -> float:
        """Calculate stereo width measurement."""
        if len(stereo_audio.shape) < 2 or stereo_audio.shape[0] < 2:
            return 0.0
        
        left = stereo_audio[0]
        right = stereo_audio[1]
        
        # Calculate correlation between channels
        correlation = np.corrcoef(left, right)[0, 1]
        
        # Convert correlation to width (0 = mono, 1 = fully wide)
        width = (1 - correlation) / 2
        return float(np.clip(width, 0, 1))
    
    def _calculate_dynamic_range(self, audio: np.ndarray) -> float:
        """Calculate dynamic range using percentile method."""
        
        # Convert to dB
        audio_db = 20 * np.log10(np.abs(audio) + 1e-10)
        
        # Calculate dynamic range as difference between 95th and 10th percentiles
        p95 = np.percentile(audio_db, 95)
        p10 = np.percentile(audio_db, 10)
        
        dynamic_range = p95 - p10
        return float(dynamic_range)
    
    def _calculate_lufs(self, audio: np.ndarray) -> float:
        """Simplified LUFS calculation (integrated loudness)."""
        
        # Apply A-weighting filter (simplified)
        # This is a basic implementation - production should use proper LUFS measurement
        
        # RMS calculation with gating
        rms = np.sqrt(np.mean(audio**2))
        
        # Convert to LUFS (simplified)
        lufs = -0.691 + 10 * np.log10(rms**2 + 1e-10)
        
        return float(lufs)
    
    def _analyze_frequency_balance(self, audio: np.ndarray) -> Dict[str, float]:
        """Analyze energy distribution across frequency bands."""
        
        # Compute STFT
        stft = librosa.stft(audio, hop_length=self.hop_length)
        magnitude = np.abs(stft)
        
        # Define frequency bands (Hz)
        bands = {
            'sub_bass': (20, 60),
            'bass': (60, 250),
            'low_mid': (250, 500),
            'mid': (500, 2000),
            'high_mid': (2000, 4000),
            'presence': (4000, 6000),
            'brilliance': (6000, 20000)
        }
        
        # Convert frequency bands to bin indices
        freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=2048)
        
        energy_distribution = {}
        total_energy = np.sum(magnitude**2)
        
        for band_name, (low_freq, high_freq) in bands.items():
            # Find frequency bin indices
            low_bin = np.argmax(freqs >= low_freq)
            high_bin = np.argmax(freqs >= high_freq)
            if high_bin == 0:  # Handle case where high_freq > max frequency
                high_bin = len(freqs)
            
            # Calculate energy in this band
            band_energy = np.sum(magnitude[low_bin:high_bin]**2)
            energy_ratio = float(band_energy / (total_energy + 1e-10))
            energy_distribution[band_name] = energy_ratio
        
        return energy_distribution
    
    def _generate_feature_hash(self, features: Dict, audio_path: Optional[str] = None) -> str:
        """Generate hash for feature caching."""
        
        # Create a string representation of key features
        hash_data = f"{self.sample_rate}_{self.hop_length}_{self.n_mfcc}"
        
        if audio_path:
            hash_data += f"_{audio_path}"
        
        # Add some feature values for uniqueness
        if 'tempo' in features:
            hash_data += f"_{features['tempo']:.2f}"
        
        return hashlib.md5(hash_data.encode()).hexdigest()
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics for monitoring."""
        
        if not self._extraction_times:
            return {'avg_extraction_time': 0.0, 'max_extraction_time': 0.0}
        
        return {
            'avg_extraction_time': np.mean(self._extraction_times),
            'max_extraction_time': np.max(self._extraction_times),
            'min_extraction_time': np.min(self._extraction_times),
            'total_extractions': len(self._extraction_times)
        }


# Factory function for creating feature extractor instances
def create_feature_extractor(config: Optional[Dict] = None) -> AudioFeatureExtractor:
    """Create configured AudioFeatureExtractor instance."""
    
    default_config = {
        'sample_rate': 44100,
        'hop_length': 512,
        'n_mfcc': 13,
        'n_chroma': 12,
        'cache_features': True
    }
    
    if config:
        default_config.update(config)
    
    return AudioFeatureExtractor(**default_config)