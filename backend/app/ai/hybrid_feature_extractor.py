"""
Hybrid Feature Extraction System.

This module implements the hybrid approach combining pre-trained models
(AST, Wav2Vec, CLAP, MusicGen) with our custom TorchAudio-based feature extraction
for comprehensive audio analysis and mastering parameter prediction.
"""

import logging
import os
import time
import warnings
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio
from pydantic import BaseModel, Field

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)

# Set CUDA environment if available
if 'CUDA_HOME' not in os.environ and os.path.exists('/usr/local/cuda-12.4'):
    os.environ['CUDA_HOME'] = '/usr/local/cuda-12.4'
    cuda_lib_path = '/usr/local/cuda-12.4/lib64'
    if 'LD_LIBRARY_PATH' in os.environ:
        os.environ['LD_LIBRARY_PATH'] = f"{cuda_lib_path}:{os.environ['LD_LIBRARY_PATH']}"
    else:
        os.environ['LD_LIBRARY_PATH'] = cuda_lib_path

logger = logging.getLogger(__name__)


class HybridFeatures(BaseModel):
    """Comprehensive audio features from multiple pre-trained models."""
    
    # Pre-trained model features
    ast_features: Optional[List[float]] = Field(default=None, description="Audio Spectrogram Transformer features")
    wav2vec_features: Optional[List[float]] = Field(default=None, description="Wav2Vec 2.0 temporal features")
    clap_features: Optional[List[float]] = Field(default=None, description="CLAP semantic features")
    musicgen_features: Optional[List[float]] = Field(default=None, description="MusicGen music-specific features")
    
    # Custom features (from our original extractor)
    custom_features: Optional[Dict[str, Any]] = Field(default=None, description="Custom mastering-specific features")
    
    # Fused features
    fused_features: Optional[List[float]] = Field(default=None, description="Fused multi-modal features")
    
    # Metadata
    audio_length: float = Field(description="Audio length in seconds")
    sample_rate: int = Field(description="Audio sample rate")
    model_availability: Dict[str, bool] = Field(description="Which models were successfully used")
    extraction_time: float = Field(description="Total feature extraction time")


class AudioCharacteristics(BaseModel):
    """Audio characteristics for model selection."""
    
    genre: Optional[str] = Field(description="Detected genre")
    genre_confidence: float = Field(description="Genre detection confidence")
    has_vocals: bool = Field(description="Contains vocal content")
    is_instrumental: bool = Field(description="Instrumental track")
    energy_level: float = Field(description="Overall energy level (0-1)")
    dynamic_range: float = Field(description="Dynamic range in dB")
    complexity_score: float = Field(description="Musical complexity (0-1)")
    tempo_bpm: Optional[float] = Field(description="Estimated tempo in BPM")
    key_signature: Optional[str] = Field(description="Detected key signature")
    audio_quality: float = Field(description="Overall audio quality (0-1)")


class PretrainedModelLoader:
    """Manages loading and caching of pre-trained models."""
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.models = {}
        self.processors = {}
        self.model_configs = {
            'ast': {
                'model_name': 'MIT/ast-finetuned-audioset-10-10-0.4593',
                'feature_dim': 768,
                'requires_spectrogram': True
            },
            'wav2vec': {
                'model_name': 'facebook/wav2vec2-large-960h', 
                'feature_dim': 1024,
                'requires_spectrogram': False
            },
            'clap': {
                'model_name': 'laion/clap-htsat-unfused',
                'feature_dim': 512,
                'requires_spectrogram': False
            }
        }
        
    def load_model(self, model_type: str) -> Tuple[Optional[Any], Optional[Any]]:
        """Load a specific pre-trained model."""
        if model_type in self.models:
            return self.models[model_type], self.processors.get(model_type)
        
        try:
            from transformers import AutoModel, AutoProcessor, AutoFeatureExtractor
            
            config = self.model_configs[model_type]
            model_name = config['model_name']
            
            logger.info(f"Loading {model_type} model: {model_name}")
            
            # Load model and processor with safe loading
            model = AutoModel.from_pretrained(
                model_name,
                trust_remote_code=False,  # Security: don't trust remote code
                use_safetensors=True  # Use safer tensor format
            )
            
            try:
                processor = AutoProcessor.from_pretrained(model_name)
            except:
                try:
                    processor = AutoFeatureExtractor.from_pretrained(model_name)
                except:
                    processor = None
                    logger.warning(f"No processor found for {model_type}, using manual preprocessing")
            
            # Move to device
            model = model.to(self.device)
            model.eval()
            
            # Cache models
            self.models[model_type] = model
            if processor:
                self.processors[model_type] = processor
            
            logger.info(f"Successfully loaded {model_type} model")
            return model, processor
            
        except Exception as e:
            logger.error(f"Failed to load {model_type} model: {e}")
            return None, None
    
    def get_all_available_models(self) -> Dict[str, bool]:
        """Get availability status of all models."""
        availability = {}
        for model_type in self.model_configs:
            model, processor = self.load_model(model_type)
            availability[model_type] = model is not None
        return availability


class FeatureFusionNetwork(nn.Module):
    """Neural network for fusing features from multiple pre-trained models."""
    
    def __init__(
        self,
        feature_dims: Dict[str, int],
        output_dim: int = 512,
        hidden_dim: int = 256
    ):
        super().__init__()
        
        self.feature_dims = feature_dims
        self.output_dim = output_dim
        
        # Individual feature projections
        self.projections = nn.ModuleDict()
        for model_type, dim in feature_dims.items():
            if dim > 0:  # Only create projection if we have features
                self.projections[model_type] = nn.Sequential(
                    nn.Linear(dim, hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(hidden_dim, hidden_dim // 2)
                )
        
        # Fusion layers
        total_projected_dim = len(feature_dims) * (hidden_dim // 2)
        self.fusion = nn.Sequential(
            nn.Linear(total_projected_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim)
        )
        
        # Attention mechanism for feature weighting
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim // 2,
            num_heads=4,
            dropout=0.1,
            batch_first=True
        )
    
    def forward(self, features: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Fuse features from multiple models."""
        projected_features = []
        attention_features = []
        
        for model_type, feature_tensor in features.items():
            if model_type in self.projections and feature_tensor is not None:
                projected = self.projections[model_type](feature_tensor)
                projected_features.append(projected)
                attention_features.append(projected.unsqueeze(1))  # Add sequence dim for attention
        
        if not projected_features:
            # Return zero tensor if no features available
            return torch.zeros(1, self.output_dim, device=next(self.parameters()).device)
        
        # Apply attention if we have multiple feature types
        if len(attention_features) > 1:
            # Stack features for attention
            stacked_features = torch.cat(attention_features, dim=1)  # (batch, num_features, dim)
            
            # Apply self-attention
            attended_features, _ = self.attention(
                stacked_features, stacked_features, stacked_features
            )
            
            # Pool attended features
            pooled_features = attended_features.mean(dim=1)  # (batch, dim)
            
            # Final fusion
            fused = self.fusion(pooled_features.repeat(1, len(projected_features)))
        else:
            # Simple concatenation if only one feature type
            concatenated = torch.cat(projected_features, dim=-1)
            fused = self.fusion(concatenated)
        
        return fused


class HybridFeatureExtractor:
    """
    Hybrid feature extraction combining pre-trained models with custom features.
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.model_loader = PretrainedModelLoader(device)
        
        # Load our custom feature extractor
        try:
            import sys
            from pathlib import Path
            
            # Add backend path to sys.path if not already there
            backend_path = Path(__file__).parent.parent.parent
            if str(backend_path) not in sys.path:
                sys.path.append(str(backend_path))
            
            from backend.app.ai.feature_extractor import AudioFeatureExtractor
            self.custom_extractor = AudioFeatureExtractor()
            logger.info("Loaded custom feature extractor")
        except Exception as e:
            logger.warning(f"Could not load custom feature extractor: {e}")
            self.custom_extractor = None
        
        # Initialize feature fusion network
        feature_dims = {
            'ast': 768,
            'wav2vec': 1024,
            'clap': 512,
            'custom': 128
        }
        
        self.feature_fusion = FeatureFusionNetwork(feature_dims).to(device)
        self.model_availability = {}
        
    def _extract_ast_features(self, audio: torch.Tensor, sr: int) -> Optional[torch.Tensor]:
        """Extract features using Audio Spectrogram Transformer."""
        try:
            model, processor = self.model_loader.load_model('ast')
            if model is None:
                return None
            
            # AST expects 16kHz audio
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(sr, 16000).to(self.device)
                audio = resampler(audio.to(self.device))
                sr = 16000
            
            # Convert to numpy for processor
            audio_np = audio.squeeze().cpu().numpy()
            
            if processor is not None:
                # Use processor if available
                inputs = processor(audio_np, sampling_rate=sr, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            else:
                # Manual preprocessing for AST
                # Convert to mel spectrogram
                mel_transform = torchaudio.transforms.MelSpectrogram(
                    sample_rate=sr,
                    n_mels=128,
                    n_fft=2048,
                    hop_length=512
                ).to(self.device)
                
                mel_spec = mel_transform(audio.to(self.device))
                mel_spec = torch.log(mel_spec + 1e-8)  # Log mel spectrogram
                
                # Resize to expected input size (typically 1024 time frames)
                target_length = 1024
                if mel_spec.shape[-1] < target_length:
                    # Pad if too short
                    pad_length = target_length - mel_spec.shape[-1]
                    mel_spec = F.pad(mel_spec, (0, pad_length))
                else:
                    # Truncate if too long
                    mel_spec = mel_spec[:, :, :target_length]
                
                inputs = {"input_values": mel_spec.unsqueeze(0)}
            
            with torch.no_grad():
                outputs = model(**inputs)
                # Get last hidden state and pool
                if hasattr(outputs, 'last_hidden_state'):
                    features = outputs.last_hidden_state.mean(dim=1)  # Pool over time
                else:
                    features = outputs.pooler_output if hasattr(outputs, 'pooler_output') else outputs[0].mean(dim=1)
                
            return features.squeeze()
            
        except Exception as e:
            logger.warning(f"AST feature extraction failed: {e}")
            return None
    
    def _extract_wav2vec_features(self, audio: torch.Tensor, sr: int) -> Optional[torch.Tensor]:
        """Extract features using Wav2Vec 2.0."""
        try:
            model, processor = self.model_loader.load_model('wav2vec')
            if model is None:
                return None
            
            # Resample to 16kHz if needed (Wav2Vec expects 16kHz)
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(sr, 16000).to(self.device)
                audio = resampler(audio.to(self.device))
                sr = 16000
            
            # Convert to numpy for processor
            audio_np = audio.squeeze().cpu().numpy()
            
            if processor is not None:
                inputs = processor(audio_np, sampling_rate=sr, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            else:
                # Manual preprocessing
                inputs = {"input_values": audio.unsqueeze(0).to(self.device)}
            
            with torch.no_grad():
                outputs = model(**inputs)
                # Pool over time dimension
                features = outputs.last_hidden_state.mean(dim=1)
                
            return features.squeeze()
            
        except Exception as e:
            logger.warning(f"Wav2Vec feature extraction failed: {e}")
            return None
    
    def _extract_clap_features(self, audio: torch.Tensor, sr: int) -> Optional[torch.Tensor]:
        """Extract features using CLAP."""
        try:
            model, processor = self.model_loader.load_model('clap')
            if model is None:
                return None
            
            # CLAP typically expects 48kHz
            target_sr = 48000
            if sr != target_sr:
                resampler = torchaudio.transforms.Resample(sr, target_sr).to(self.device)
                audio = resampler(audio.to(self.device))
                sr = target_sr
            
            # Convert to numpy
            audio_np = audio.squeeze().cpu().numpy()
            
            if processor is not None:
                inputs = processor(audios=audio_np, sampling_rate=sr, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            else:
                # Manual preprocessing for CLAP
                inputs = {"input_values": audio.unsqueeze(0).to(self.device)}
            
            with torch.no_grad():
                outputs = model.get_audio_features(**inputs)
                features = outputs if isinstance(outputs, torch.Tensor) else outputs.last_hidden_state.mean(dim=1)
                
            return features.squeeze()
            
        except Exception as e:
            logger.warning(f"CLAP feature extraction failed: {e}")
            return None
    
    async def _extract_custom_features(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """Extract features using our custom feature extractor."""
        try:
            if self.custom_extractor is None:
                return None
            
            # Check if the method is async
            features = self.custom_extractor.extract_features(audio_path)
            
            # Handle both async and sync cases
            if hasattr(features, '__await__'):  # It's a coroutine
                features = await features
            
            return features.model_dump() if hasattr(features, 'model_dump') else features
            
        except Exception as e:
            logger.warning(f"Custom feature extraction failed: {e}")
            return None
    
    async def extract_features(self, audio_path: str) -> HybridFeatures:
        """
        Extract comprehensive features using hybrid approach.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            HybridFeatures object with all extracted features
        """
        start_time = time.time()
        
        try:
            # Load audio
            audio, sr = torchaudio.load(audio_path)
            audio_length = audio.shape[-1] / sr
            
            # Ensure mono
            if audio.shape[0] > 1:
                audio = audio.mean(dim=0, keepdim=True)
            
            logger.info(f"Processing audio: {audio_length:.2f}s at {sr}Hz")
            
            # Extract features from each model
            features = {}
            model_availability = {}
            
            # 1. AST features
            ast_features = self._extract_ast_features(audio, sr)
            if ast_features is not None:
                features['ast'] = ast_features
                model_availability['ast'] = True
                logger.debug("AST features extracted successfully")
            else:
                model_availability['ast'] = False
            
            # 2. Wav2Vec features  
            wav2vec_features = self._extract_wav2vec_features(audio, sr)
            if wav2vec_features is not None:
                features['wav2vec'] = wav2vec_features
                model_availability['wav2vec'] = True
                logger.debug("Wav2Vec features extracted successfully")
            else:
                model_availability['wav2vec'] = False
            
            # 3. CLAP features
            clap_features = self._extract_clap_features(audio, sr)
            if clap_features is not None:
                features['clap'] = clap_features
                model_availability['clap'] = True
                logger.debug("CLAP features extracted successfully")
            else:
                model_availability['clap'] = False
            
            # 4. Custom features
            custom_features = await self._extract_custom_features(audio_path)
            if custom_features is not None:
                # Convert custom features to tensor for fusion
                custom_tensor = self._convert_custom_features_to_tensor(custom_features)
                if custom_tensor is not None:
                    features['custom'] = custom_tensor
                model_availability['custom'] = True
                logger.debug("Custom features extracted successfully")
            else:
                model_availability['custom'] = False
            
            # 5. Fuse features
            fused_features = None
            if features:
                try:
                    fused_features = self.feature_fusion(features)
                    logger.debug("Features fused successfully")
                except Exception as e:
                    logger.warning(f"Feature fusion failed: {e}")
            
            # Calculate extraction time
            extraction_time = time.time() - start_time
            
            # Create HybridFeatures object
            hybrid_features = HybridFeatures(
                ast_features=ast_features.tolist() if ast_features is not None else None,
                wav2vec_features=wav2vec_features.tolist() if wav2vec_features is not None else None,
                clap_features=clap_features.tolist() if clap_features is not None else None,
                musicgen_features=None,  # TODO: Implement MusicGen extraction
                custom_features=custom_features,
                fused_features=fused_features.tolist() if fused_features is not None else None,
                audio_length=audio_length,
                sample_rate=sr,
                model_availability=model_availability,
                extraction_time=extraction_time
            )
            
            logger.info(f"Hybrid feature extraction completed in {extraction_time:.3f}s")
            logger.info(f"Available models: {[k for k, v in model_availability.items() if v]}")
            
            return hybrid_features
            
        except Exception as e:
            logger.error(f"Hybrid feature extraction failed: {e}")
            # Return minimal features object
            return HybridFeatures(
                audio_length=0.0,
                sample_rate=44100,
                model_availability={},
                extraction_time=time.time() - start_time
            )
    
    def _convert_custom_features_to_tensor(self, custom_features: Dict[str, Any]) -> Optional[torch.Tensor]:
        """Convert custom features dictionary to tensor for fusion."""
        try:
            # Extract numeric features from custom feature dict
            numeric_features = []
            
            if isinstance(custom_features, dict):
                for key, value in custom_features.items():
                    if isinstance(value, (int, float)):
                        numeric_features.append(float(value))
                    elif isinstance(value, (list, np.ndarray)):
                        if isinstance(value, np.ndarray):
                            value = value.flatten()
                        # Take first few values if list is too long
                        numeric_features.extend([float(x) for x in value[:10]])
            
            if numeric_features:
                # Pad or truncate to expected size (128 features)
                target_size = 128
                if len(numeric_features) < target_size:
                    numeric_features.extend([0.0] * (target_size - len(numeric_features)))
                else:
                    numeric_features = numeric_features[:target_size]
                
                return torch.tensor(numeric_features, dtype=torch.float32, device=self.device)
            
            return None
            
        except Exception as e:
            logger.warning(f"Custom feature conversion failed: {e}")
            return None
    
    def analyze_audio_characteristics(self, features: HybridFeatures) -> AudioCharacteristics:
        """Analyze audio characteristics for model selection."""
        # Basic implementation - can be enhanced with more sophisticated analysis
        try:
            characteristics = AudioCharacteristics(
                genre="unknown",
                genre_confidence=0.5,
                has_vocals=False,  # TODO: Implement vocal detection
                is_instrumental=True,
                energy_level=0.5,
                dynamic_range=20.0,
                complexity_score=0.5,
                tempo_bpm=None,
                key_signature=None,
                audio_quality=0.8
            )
            
            # Use custom features if available
            if features.custom_features:
                try:
                    cf = features.custom_features
                    if 'loudness_lufs' in cf:
                        # Estimate energy from loudness
                        lufs = cf['loudness_lufs']
                        characteristics.energy_level = min(1.0, max(0.0, (lufs + 60) / 60))
                    
                    if 'dynamic_range' in cf:
                        characteristics.dynamic_range = cf['dynamic_range']
                    
                    if 'tempo' in cf:
                        characteristics.tempo_bpm = cf['tempo']
                        
                except Exception as e:
                    logger.warning(f"Error analyzing custom features: {e}")
            
            return characteristics
            
        except Exception as e:
            logger.error(f"Audio characteristics analysis failed: {e}")
            # Return default characteristics
            return AudioCharacteristics(
                genre="unknown",
                genre_confidence=0.0,
                has_vocals=False,
                is_instrumental=True,
                energy_level=0.5,
                dynamic_range=20.0,
                complexity_score=0.5,
                audio_quality=0.5
            )


async def test_hybrid_extraction(audio_path: str) -> HybridFeatures:
    """Test function for hybrid feature extraction."""
    extractor = HybridFeatureExtractor()
    features = await extractor.extract_features(audio_path)
    return features


if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Test with available audio file
        test_audio = "/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Respek Ma Craft.wav"
        if os.path.exists(test_audio):
            print("Testing hybrid feature extraction...")
            features = await test_hybrid_extraction(test_audio)
            print(f"Extraction completed in {features.extraction_time:.3f}s")
            print(f"Available models: {[k for k, v in features.model_availability.items() if v]}")
        else:
            print("Test audio file not found")
    
    asyncio.run(main())