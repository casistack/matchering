"""
Audio Feature Extraction Service for AI Mastering.

This module implements comprehensive audio feature extraction for AI-powered
mastering parameter prediction using TorchAudio for Python 3.12 compatibility
and GPU acceleration.
"""

import asyncio
import hashlib
import logging
import os
import time
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torchaudio
import scipy.signal
from pydantic import BaseModel, Field

# Set CUDA environment if available
if 'CUDA_HOME' not in os.environ and os.path.exists('/usr/local/cuda-12.4'):
    os.environ['CUDA_HOME'] = '/usr/local/cuda-12.4'
    cuda_lib_path = '/usr/local/cuda-12.4/lib64'
    if 'LD_LIBRARY_PATH' in os.environ:
        os.environ['LD_LIBRARY_PATH'] = f"{cuda_lib_path}:{os.environ['LD_LIBRARY_PATH']}"
    else:
        os.environ['LD_LIBRARY_PATH'] = cuda_lib_path

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
    """Enterprise-grade audio feature extraction for mastering AI using TorchAudio."""
    
    def __init__(self, 
                 sample_rate: int = 44100,
                 hop_length: int = 512,
                 n_mfcc: int = 13,
                 n_chroma: int = 12,
                 cache_features: bool = True,
                 device: Optional[str] = None):
        """
        Initialize audio feature extractor.
        
        Args:
            sample_rate: Target sample rate for analysis
            hop_length: Hop length for STFT analysis
            n_mfcc: Number of MFCC coefficients
            n_chroma: Number of chroma bins
            cache_features: Whether to cache extracted features
            device: PyTorch device ('cuda' or 'cpu')
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self.n_mfcc = n_mfcc
        self.n_chroma = n_chroma
        self.cache_features = cache_features
        
        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # Initialize transforms
        self._init_transforms()
        
        # Performance tracking
        self._extraction_times = []
        
        logger.info(f"AudioFeatureExtractor initialized: sr={sample_rate}, hop={hop_length}, device={self.device}")
    
    def _init_transforms(self):
        """Initialize TorchAudio transforms."""
        self.mfcc_transform = torchaudio.transforms.MFCC(
            sample_rate=self.sample_rate,
            n_mfcc=self.n_mfcc,
            melkwargs={'hop_length': self.hop_length}
        ).to(self.device)
        
        self.mel_transform = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.sample_rate,
            hop_length=self.hop_length,
            n_mels=128
        ).to(self.device)
        
        self.spectrogram_transform = torchaudio.transforms.Spectrogram(
            hop_length=self.hop_length
        ).to(self.device)
    
    async def extract_features(self, 
                              audio_data: Union[np.ndarray, str, torch.Tensor],
                              audio_path: Optional[str] = None) -> AudioFeatures:
        """
        Extract comprehensive audio features for AI analysis.
        
        Args:
            audio_data: Audio array, tensor, or file path
            audio_path: Optional path for metadata
            
        Returns:
            AudioFeatures object with all extracted features
        """
        start_time = time.time()
        
        try:
            # Load audio if path provided
            if isinstance(audio_data, str):
                audio_path = audio_data
                waveform, original_sr = torchaudio.load(audio_data)
                
                # Resample if needed
                if original_sr != self.sample_rate:
                    resampler = torchaudio.transforms.Resample(
                        orig_freq=original_sr,
                        new_freq=self.sample_rate
                    ).to(self.device)
                    waveform = resampler(waveform.to(self.device))
                else:
                    waveform = waveform.to(self.device)
            
            elif isinstance(audio_data, np.ndarray):
                # Convert numpy to tensor
                waveform = torch.from_numpy(audio_data).float()
                if len(waveform.shape) == 1:
                    waveform = waveform.unsqueeze(0)  # Add channel dimension
                waveform = waveform.to(self.device)
            
            else:
                waveform = audio_data.to(self.device)
            
            # Handle stereo to mono conversion
            if waveform.shape[0] > 1:
                # Calculate stereo width before converting to mono
                stereo_width = self._calculate_stereo_width(waveform)
                audio_mono = torch.mean(waveform, dim=0, keepdim=True)
                channels = waveform.shape[0]
            else:
                stereo_width = 0.0
                audio_mono = waveform
                channels = 1
            
            duration = float(audio_mono.shape[1] / self.sample_rate)
            
            # Extract features
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
                                   audio: torch.Tensor, 
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
    
    async def _extract_spectral_features(self, audio: torch.Tensor) -> Dict:
        """Extract spectral domain features using TorchAudio."""
        
        loop = asyncio.get_event_loop()
        
        # MFCC
        mfcc = await loop.run_in_executor(
            None,
            lambda: self.mfcc_transform(audio).cpu().numpy().tolist()
        )
        
        # Compute spectrogram for other features
        spec = self.spectrogram_transform(audio)
        magnitude = torch.abs(spec)
        
        # Spectral centroid
        freqs = torch.linspace(0, self.sample_rate/2, magnitude.shape[1]).to(self.device)
        spectral_centroid = torch.sum(freqs.unsqueeze(0).unsqueeze(-1) * magnitude, dim=1) / (torch.sum(magnitude, dim=1) + 1e-10)
        spectral_centroid = spectral_centroid.cpu().numpy()[0].tolist()
        
        # Spectral rolloff
        cumsum = torch.cumsum(magnitude, dim=1)
        total = cumsum[:, -1, :].unsqueeze(1)
        rolloff_idx = torch.argmax((cumsum >= 0.85 * total).float(), dim=1)
        spectral_rolloff = freqs[rolloff_idx].cpu().numpy()[0].tolist()
        
        # Spectral bandwidth
        mean_freq = torch.sum(freqs.unsqueeze(0).unsqueeze(-1) * magnitude, dim=1) / (torch.sum(magnitude, dim=1) + 1e-10)
        variance = torch.sum(((freqs.unsqueeze(0).unsqueeze(-1) - mean_freq.unsqueeze(1))**2) * magnitude, dim=1) / (torch.sum(magnitude, dim=1) + 1e-10)
        spectral_bandwidth = torch.sqrt(variance).cpu().numpy()[0].tolist()
        
        # Spectral flatness
        geometric_mean = torch.exp(torch.mean(torch.log(magnitude + 1e-10), dim=1))
        arithmetic_mean = torch.mean(magnitude, dim=1)
        spectral_flatness = (geometric_mean / (arithmetic_mean + 1e-10)).cpu().numpy()[0].tolist()
        
        # Spectral contrast (simplified version)
        spectral_contrast = []
        n_bands = 7
        for i in range(n_bands):
            start_idx = i * magnitude.shape[1] // n_bands
            end_idx = (i + 1) * magnitude.shape[1] // n_bands
            band = magnitude[:, start_idx:end_idx, :]
            peak = torch.quantile(band, 0.95, dim=1)
            valley = torch.quantile(band, 0.05, dim=1)
            contrast = 20 * torch.log10((peak + 1e-10) / (valley + 1e-10))
            spectral_contrast.append(contrast.cpu().numpy()[0].tolist())
        
        return {
            'mfcc': mfcc,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'spectral_contrast': spectral_contrast,
            'spectral_bandwidth': spectral_bandwidth,
            'spectral_flatness': spectral_flatness
        }
    
    async def _extract_harmonic_features(self, audio: torch.Tensor) -> Dict:
        """Extract harmonic and tonal features."""
        
        loop = asyncio.get_event_loop()
        
        # Compute chroma features using mel spectrogram
        mel_spec = self.mel_transform(audio)
        
        # Simple chroma calculation
        n_chroma = self.n_chroma
        chroma_filter = torch.zeros((n_chroma, mel_spec.shape[1])).to(self.device)
        
        for i in range(n_chroma):
            chroma_filter[i, :] = torch.exp(-0.5 * ((torch.arange(mel_spec.shape[1]).float().to(self.device) - i * mel_spec.shape[1] / n_chroma) / (mel_spec.shape[1] / n_chroma / 2))**2)
        
        chroma = torch.matmul(chroma_filter, mel_spec.squeeze(0))
        chroma = chroma.cpu().numpy().tolist()
        
        # Tonnetz (simplified - using chroma as base)
        # In production, this would be more sophisticated
        tonnetz = [[0.0] * 6 for _ in range(len(chroma[0]))]
        
        return {
            'chroma': chroma,
            'tonnetz': tonnetz
        }
    
    async def _extract_temporal_features(self, audio: torch.Tensor) -> Dict:
        """Extract temporal domain features."""
        
        loop = asyncio.get_event_loop()
        
        audio_np = audio.cpu().numpy()[0]
        
        # Zero crossing rate
        zcr = await loop.run_in_executor(
            None,
            lambda: self._compute_zcr(audio_np).tolist()
        )
        
        # RMS energy
        rms = await loop.run_in_executor(
            None,
            lambda: self._compute_rms(audio_np).tolist()
        )
        
        # Tempo estimation (simplified)
        tempo, beat_frames = await loop.run_in_executor(
            None,
            lambda: self._estimate_tempo(audio_np)
        )
        
        return {
            'zero_crossing_rate': zcr,
            'rms_energy': rms,
            'tempo': float(tempo),
            'beat_frames': beat_frames
        }
    
    def _compute_zcr(self, audio: np.ndarray) -> np.ndarray:
        """Compute zero crossing rate."""
        frame_length = 2048
        hop_length = self.hop_length
        
        frames = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            zcr = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * frame_length)
            frames.append(zcr)
        
        return np.array(frames)
    
    def _compute_rms(self, audio: np.ndarray) -> np.ndarray:
        """Compute RMS energy."""
        frame_length = 2048
        hop_length = self.hop_length
        
        frames = []
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            rms = np.sqrt(np.mean(frame**2))
            frames.append(rms)
        
        return np.array(frames)
    
    def _estimate_tempo(self, audio: np.ndarray) -> Tuple[float, List[int]]:
        """Estimate tempo using onset detection."""
        # Simplified tempo estimation
        # In production, use more sophisticated beat tracking
        
        # Compute onset strength
        onset_env = self._compute_onset_strength(audio)
        
        # Estimate tempo from onset autocorrelation
        tempo = self._tempo_from_onset(onset_env)
        
        # Simple beat tracking
        beat_period = int(self.sample_rate * 60.0 / tempo)
        beat_frames = list(range(0, len(audio), beat_period))[:100]  # Limit to 100 beats
        
        return tempo, beat_frames
    
    def _compute_onset_strength(self, audio: np.ndarray) -> np.ndarray:
        """Compute onset strength envelope."""
        # Simple onset detection using spectral flux
        frame_length = 2048
        hop_length = self.hop_length
        
        onset_env = []
        prev_magnitude = None
        
        for i in range(0, len(audio) - frame_length, hop_length):
            frame = audio[i:i+frame_length]
            magnitude = np.abs(np.fft.rfft(frame * np.hanning(frame_length)))
            
            if prev_magnitude is not None:
                flux = np.sum(np.maximum(0, magnitude - prev_magnitude))
                onset_env.append(flux)
            
            prev_magnitude = magnitude
        
        return np.array(onset_env)
    
    def _tempo_from_onset(self, onset_env: np.ndarray) -> float:
        """Estimate tempo from onset strength."""
        # Autocorrelation
        corr = np.correlate(onset_env, onset_env, mode='full')
        corr = corr[len(corr)//2:]
        
        # Find peaks in autocorrelation
        min_period = int(self.sample_rate * 60 / 240 / self.hop_length)  # 240 BPM max
        max_period = int(self.sample_rate * 60 / 40 / self.hop_length)   # 40 BPM min
        
        if max_period < len(corr):
            corr_slice = corr[min_period:max_period]
            if len(corr_slice) > 0:
                peak_idx = np.argmax(corr_slice) + min_period
                tempo = 60.0 * self.sample_rate / (peak_idx * self.hop_length)
                return np.clip(tempo, 40, 240)
        
        return 120.0  # Default tempo
    
    async def _extract_mastering_features(self, audio: torch.Tensor, stereo_width: float) -> Dict:
        """Extract mastering-specific features."""
        
        loop = asyncio.get_event_loop()
        
        audio_np = audio.cpu().numpy()[0]
        
        # Dynamic range calculation
        dynamic_range = await loop.run_in_executor(None, self._calculate_dynamic_range, audio_np)
        
        # Loudness (simplified LUFS estimation)
        loudness_lufs = await loop.run_in_executor(None, self._calculate_lufs, audio_np)
        
        # Peak level
        peak_level = float(20 * np.log10(np.max(np.abs(audio_np)) + 1e-10))
        
        # Crest factor
        rms_level = np.sqrt(np.mean(audio_np**2))
        peak_level_linear = np.max(np.abs(audio_np))
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
    
    def _calculate_stereo_width(self, stereo_audio: torch.Tensor) -> float:
        """Calculate stereo width measurement."""
        if stereo_audio.shape[0] < 2:
            return 0.0
        
        left = stereo_audio[0].cpu().numpy()
        right = stereo_audio[1].cpu().numpy()
        
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
    
    def _analyze_frequency_balance(self, audio: torch.Tensor) -> Dict[str, float]:
        """Analyze energy distribution across frequency bands."""
        
        # Compute STFT using TorchAudio
        spec = self.spectrogram_transform(audio)
        magnitude = torch.abs(spec).squeeze(0)
        
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
        n_fft = (magnitude.shape[0] - 1) * 2
        freqs = torch.linspace(0, self.sample_rate/2, magnitude.shape[0])
        
        energy_distribution = {}
        total_energy = torch.sum(magnitude**2)
        
        for band_name, (low_freq, high_freq) in bands.items():
            # Find frequency bin indices
            low_bin = torch.argmax((freqs >= low_freq).float()).item()
            high_bin = torch.argmax((freqs >= high_freq).float()).item()
            if high_bin == 0:  # Handle case where high_freq > max frequency
                high_bin = magnitude.shape[0]
            
            # Calculate energy in this band
            band_energy = torch.sum(magnitude[low_bin:high_bin]**2)
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
    
    # Add device configuration
    if torch.cuda.is_available():
        default_config['device'] = 'cuda'
    
    return AudioFeatureExtractor(**default_config)