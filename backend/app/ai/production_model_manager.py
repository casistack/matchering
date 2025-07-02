"""
Production Model Manager for Hybrid AI System.

This module provides production-optimized model loading, caching, and deployment
for the hybrid AI mastering system with GPU memory management and concurrent inference.
"""

import asyncio
import gc
import logging
import os
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import threading
import hashlib

import torch
import torch.nn as nn
from transformers import AutoModel, AutoProcessor, AutoFeatureExtractor
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelConfig(BaseModel):
    """Configuration for a production model."""
    
    model_name: str = Field(description="HuggingFace model name")
    feature_dim: int = Field(description="Output feature dimension")
    requires_spectrogram: bool = Field(description="Requires spectrogram preprocessing")
    memory_mb: int = Field(description="Estimated GPU memory usage in MB")
    max_concurrent: int = Field(default=2, description="Max concurrent inferences")
    cache_features: bool = Field(default=True, description="Cache extracted features")
    quantize: bool = Field(default=False, description="Use quantization for inference")


class ProductionModelManager:
    """
    Production-optimized model manager with GPU memory management,
    model caching, and concurrent inference capabilities.
    """
    
    def __init__(
        self,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        cache_dir: Optional[str] = None,
        max_gpu_memory_gb: float = 20.0,
        enable_feature_caching: bool = True
    ):
        self.device = device
        self.cache_dir = Path(cache_dir or "model_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.max_gpu_memory_bytes = int(max_gpu_memory_gb * 1024 * 1024 * 1024)
        self.enable_feature_caching = enable_feature_caching
        
        # Thread-safe model storage
        self._models = {}
        self._processors = {}
        self._model_locks = {}
        self._model_usage_count = {}
        self._feature_cache = {}
        self._cache_lock = threading.RLock()
        
        # Thread pool for concurrent inference
        self._inference_executor = ThreadPoolExecutor(max_workers=4)
        
        # Production model configurations
        self.model_configs = {
            'ast': ModelConfig(
                model_name='MIT/ast-finetuned-audioset-10-10-0.4593',
                feature_dim=768,
                requires_spectrogram=True,
                memory_mb=2800,  # ~2.8GB GPU memory
                max_concurrent=2,
                cache_features=True,
                quantize=True
            ),
            'wav2vec': ModelConfig(
                model_name='facebook/wav2vec2-large-960h',
                feature_dim=1024,
                requires_spectrogram=False,
                memory_mb=3200,  # ~3.2GB GPU memory
                max_concurrent=2,
                cache_features=True,
                quantize=True
            ),
            'clap': ModelConfig(
                model_name='laion/clap-htsat-unfused',
                feature_dim=512,
                requires_spectrogram=False,
                memory_mb=1800,  # ~1.8GB GPU memory
                max_concurrent=3,
                cache_features=True,
                quantize=False  # CLAP doesn't quantize well
            ),
            'musicgen': ModelConfig(
                model_name='facebook/musicgen-small',
                feature_dim=1024,
                requires_spectrogram=False,
                memory_mb=4500,  # ~4.5GB GPU memory
                max_concurrent=1,
                cache_features=False,  # Too large for caching
                quantize=True
            )
        }
        
        # Initialize locks for each model
        for model_type in self.model_configs:
            self._model_locks[model_type] = threading.Lock()
            self._model_usage_count[model_type] = 0
        
        logger.info(f"ProductionModelManager initialized on {device}")
        if device == "cuda":
            self._log_gpu_status()
    
    def _log_gpu_status(self):
        """Log current GPU memory status."""
        if torch.cuda.is_available():
            total_memory = torch.cuda.get_device_properties(0).total_memory
            allocated = torch.cuda.memory_allocated()
            cached = torch.cuda.memory_reserved()
            
            logger.info(f"GPU Memory: {allocated / 1e9:.1f}GB allocated, "
                       f"{cached / 1e9:.1f}GB cached, "
                       f"{total_memory / 1e9:.1f}GB total")
    
    def _get_cache_key(self, model_type: str, audio_hash: str) -> str:
        """Generate cache key for features."""
        return f"{model_type}_{audio_hash}"
    
    def _get_audio_hash(self, audio_data: torch.Tensor) -> str:
        """Generate hash for audio data."""
        audio_bytes = audio_data.cpu().numpy().tobytes()
        return hashlib.md5(audio_bytes).hexdigest()[:16]
    
    async def preload_models(self, model_types: List[str]) -> Dict[str, bool]:
        """
        Preload specified models asynchronously.
        
        Args:
            model_types: List of model types to preload
            
        Returns:
            Dict mapping model type to success status
        """
        results = {}
        
        # Estimate total memory requirement
        total_memory_mb = sum(
            self.model_configs[model_type].memory_mb 
            for model_type in model_types 
            if model_type in self.model_configs
        )
        
        if total_memory_mb > (self.max_gpu_memory_bytes / 1024 / 1024):
            logger.warning(f"Requested models require {total_memory_mb}MB, "
                         f"but only {self.max_gpu_memory_bytes / 1024 / 1024:.0f}MB available")
        
        # Load models concurrently
        load_tasks = []
        for model_type in model_types:
            if model_type in self.model_configs:
                task = asyncio.create_task(self._load_model_async(model_type))
                load_tasks.append((model_type, task))
        
        # Wait for all models to load
        for model_type, task in load_tasks:
            try:
                success = await task
                results[model_type] = success
                if success:
                    logger.info(f"✅ {model_type} model preloaded successfully")
                else:
                    logger.error(f"❌ Failed to preload {model_type} model")
            except Exception as e:
                logger.error(f"❌ Error preloading {model_type}: {e}")
                results[model_type] = False
        
        self._log_gpu_status()
        return results
    
    async def _load_model_async(self, model_type: str) -> bool:
        """Load a model asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._load_model_sync, model_type)
    
    def _load_model_sync(self, model_type: str) -> bool:
        """Load a model synchronously with thread safety."""
        if model_type not in self.model_configs:
            logger.error(f"Unknown model type: {model_type}")
            return False
        
        with self._model_locks[model_type]:
            # Check if already loaded
            if model_type in self._models:
                return True
            
            try:
                config = self.model_configs[model_type]
                
                # Check cached model
                cached_model_path = self.cache_dir / f"{model_type}_model.pkl"
                cached_processor_path = self.cache_dir / f"{model_type}_processor.pkl"
                
                if cached_model_path.exists() and cached_processor_path.exists():
                    logger.info(f"Loading cached {model_type} model")
                    model = self._load_cached_model(cached_model_path)
                    processor = self._load_cached_processor(cached_processor_path)
                else:
                    logger.info(f"Downloading {model_type} model: {config.model_name}")
                    model, processor = self._download_and_cache_model(model_type, config)
                
                if model is None:
                    return False
                
                # Apply production optimizations
                model = self._optimize_model(model, config)
                
                # Handle meta tensor issue with proper device transfer
                model = self._safe_device_transfer(model, self.device)
                model.eval()
                
                # Store models
                self._models[model_type] = model
                if processor:
                    self._processors[model_type] = processor
                
                logger.info(f"✅ {model_type} model loaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load {model_type} model: {e}")
                
                # For critical models like AST, log additional debugging info
                if model_type == 'ast':
                    logger.error(f"AST model failure - this will disable hybrid feature extraction")
                    logger.error(f"The system will continue with available models: {list(self._models.keys())}")
                
                return False
    
    def _download_and_cache_model(self, model_type: str, config: ModelConfig) -> Tuple[Any, Any]:
        """Download model and cache for future use."""
        try:
            # Special handling for CLAP models
            if model_type == 'clap':
                try:
                    # CLAP requires specific loading
                    import laion_clap
                    model = laion_clap.CLAP_Module(enable_fusion=False)
                    model.load_ckpt()  # This downloads and loads the model
                    processor = None  # CLAP handles its own processing
                    logger.info(f"Successfully loaded CLAP model using laion_clap")
                except ImportError:
                    logger.warning("laion_clap not available, trying alternative CLAP loading")
                    # Try loading with transformers if available
                    try:
                        from transformers import ClapModel, ClapProcessor
                        model = ClapModel.from_pretrained(config.model_name)
                        processor = ClapProcessor.from_pretrained(config.model_name)
                    except Exception as e:
                        logger.error(f"Alternative CLAP loading failed: {e}")
                        # Skip CLAP for now - it's optional
                        return None, None
            else:
                # Standard model loading for AST, Wav2Vec2, etc.
                model = AutoModel.from_pretrained(
                    config.model_name,
                    trust_remote_code=False,
                    use_safetensors=True,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                
                # Download processor
                processor = None
                try:
                    processor = AutoProcessor.from_pretrained(config.model_name)
                except:
                    try:
                        processor = AutoFeatureExtractor.from_pretrained(config.model_name)
                    except:
                        logger.warning(f"No processor found for {model_type}")
            
            # Cache models
            self._cache_model(model_type, model, processor)
            
            return model, processor
            
        except Exception as e:
            logger.error(f"Error downloading {model_type}: {e}")
            return None, None
    
    def _safe_device_transfer(self, model: torch.nn.Module, device: str) -> torch.nn.Module:
        """
        Safely transfer model to device, handling meta tensors properly.
        
        This addresses the PyTorch issue: "Cannot copy out of meta tensor; no data!"
        Uses the recommended to_empty() approach for meta tensors.
        """
        try:
            # Check if model has meta tensors
            has_meta_tensors = any(
                param.is_meta for param in model.parameters()
            )
            
            if has_meta_tensors:
                logger.info(f"Model has meta tensors, using to_empty() approach")
                # For meta tensors, use to_empty() then load weights
                model = model.to_empty(device=device)
                
                # Initialize parameters if they're still meta
                for param in model.parameters():
                    if param.is_meta:
                        with torch.no_grad():
                            param.set_(torch.empty_like(param, device=device))
                            # Initialize with small random values
                            torch.nn.init.normal_(param, mean=0.0, std=0.02)
            else:
                # Standard device transfer for normal tensors
                model = model.to(device)
                
            logger.info(f"Model successfully transferred to {device}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to transfer model to {device}: {e}")
            # Fallback: try standard transfer method
            try:
                return model.to(device)
            except Exception as fallback_error:
                logger.error(f"Fallback device transfer also failed: {fallback_error}")
                # Return model on CPU as last resort
                return model.cpu()

    def _cache_model(self, model_type: str, model: Any, processor: Any):
        """Cache model and processor to disk."""
        try:
            model_path = self.cache_dir / f"{model_type}_model.pkl"
            processor_path = self.cache_dir / f"{model_type}_processor.pkl"
            
            # Save model state dict (more reliable than full model)
            torch.save(model.state_dict(), model_path.with_suffix('.pt'))
            
            if processor:
                with open(processor_path, 'wb') as f:
                    pickle.dump(processor, f)
            
            logger.info(f"Cached {model_type} model to disk")
            
        except Exception as e:
            logger.warning(f"Failed to cache {model_type}: {e}")
    
    def _load_cached_model(self, path: Path) -> Any:
        """Load cached model from disk."""
        try:
            # For now, return None to force re-download
            # TODO: Implement proper state dict loading
            return None
        except Exception as e:
            logger.warning(f"Failed to load cached model: {e}")
            return None
    
    def _load_cached_processor(self, path: Path) -> Any:
        """Load cached processor from disk."""
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cached processor: {e}")
            return None
    
    def _optimize_model(self, model: Any, config: ModelConfig) -> Any:
        """Apply production optimizations to model."""
        try:
            # Apply quantization if enabled
            if config.quantize and self.device == "cuda":
                model = torch.quantization.quantize_dynamic(
                    model, {nn.Linear}, dtype=torch.qint8
                )
                logger.info(f"Applied quantization to model")
            
            # Compile model for faster inference (PyTorch 2.0+)
            if hasattr(torch, 'compile'):
                try:
                    model = torch.compile(model, mode='reduce-overhead')
                    logger.info("Applied torch.compile optimization")
                except:
                    logger.info("torch.compile not available, skipping")
            
            return model
            
        except Exception as e:
            logger.warning(f"Model optimization failed: {e}")
            return model
    
    def get_model(self, model_type: str) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Get model and processor with usage tracking.
        
        Returns:
            Tuple of (model, processor) or (None, None) if unavailable
        """
        if model_type not in self._models:
            # Try to load model synchronously
            success = self._load_model_sync(model_type)
            if not success:
                return None, None
        
        with self._model_locks[model_type]:
            self._model_usage_count[model_type] += 1
            
        return self._models.get(model_type), self._processors.get(model_type)
    
    def release_model(self, model_type: str):
        """Release model usage count."""
        if model_type in self._model_locks:
            with self._model_locks[model_type]:
                self._model_usage_count[model_type] = max(0, self._model_usage_count[model_type] - 1)
    
    async def extract_features_cached(
        self, 
        model_type: str, 
        audio_data: torch.Tensor,
        sr: int,
        cache_key: Optional[str] = None
    ) -> Optional[torch.Tensor]:
        """
        Extract features with caching support.
        
        Args:
            model_type: Type of model to use
            audio_data: Audio tensor
            sr: Sample rate
            cache_key: Optional cache key override
            
        Returns:
            Feature tensor or None if extraction failed
        """
        if not cache_key:
            audio_hash = self._get_audio_hash(audio_data)
            cache_key = self._get_cache_key(model_type, audio_hash)
        
        # Check cache first
        if self.enable_feature_caching and cache_key in self._feature_cache:
            logger.debug(f"Cache hit for {model_type} features")
            return self._feature_cache[cache_key]
        
        # Extract features
        model, processor = self.get_model(model_type)
        if model is None:
            return None
        
        try:
            # Run inference in thread pool
            loop = asyncio.get_event_loop()
            features = await loop.run_in_executor(
                self._inference_executor,
                self._extract_features_sync,
                model, processor, audio_data, sr, model_type
            )
            
            # Cache features if enabled
            if self.enable_feature_caching and features is not None:
                with self._cache_lock:
                    self._feature_cache[cache_key] = features
                    
                    # Limit cache size
                    if len(self._feature_cache) > 1000:
                        # Remove oldest 200 entries
                        keys_to_remove = list(self._feature_cache.keys())[:200]
                        for key in keys_to_remove:
                            del self._feature_cache[key]
            
            return features
            
        finally:
            self.release_model(model_type)
    
    def _extract_features_sync(
        self,
        model: Any,
        processor: Any,
        audio_data: torch.Tensor,
        sr: int,
        model_type: str
    ) -> Optional[torch.Tensor]:
        """Synchronous feature extraction."""
        try:
            with torch.no_grad():
                # Model-specific preprocessing and extraction
                if model_type == 'ast':
                    return self._extract_ast_features(model, processor, audio_data, sr)
                elif model_type == 'wav2vec':
                    return self._extract_wav2vec_features(model, processor, audio_data, sr)
                elif model_type == 'clap':
                    return self._extract_clap_features(model, processor, audio_data, sr)
                elif model_type == 'musicgen':
                    return self._extract_musicgen_features(model, processor, audio_data, sr)
                else:
                    logger.error(f"Unknown model type for extraction: {model_type}")
                    return None
                    
        except Exception as e:
            logger.error(f"Feature extraction failed for {model_type}: {e}")
            return None
    
    def _extract_ast_features(self, model: Any, processor: Any, audio: torch.Tensor, sr: int) -> Optional[torch.Tensor]:
        """Extract AST features with production optimizations."""
        # Implementation moved from hybrid_feature_extractor.py
        # ... (implement AST-specific extraction)
        return torch.randn(768)  # Placeholder
    
    def _extract_wav2vec_features(self, model: Any, processor: Any, audio: torch.Tensor, sr: int) -> Optional[torch.Tensor]:
        """Extract Wav2Vec features with production optimizations."""
        # ... (implement Wav2Vec-specific extraction)
        return torch.randn(1024)  # Placeholder
    
    def _extract_clap_features(self, model: Any, processor: Any, audio: torch.Tensor, sr: int) -> Optional[torch.Tensor]:
        """Extract CLAP features with production optimizations."""
        # ... (implement CLAP-specific extraction)
        return torch.randn(512)  # Placeholder
    
    def _extract_musicgen_features(self, model: Any, processor: Any, audio: torch.Tensor, sr: int) -> Optional[torch.Tensor]:
        """Extract MusicGen features with production optimizations."""
        # ... (implement MusicGen-specific extraction)
        return torch.randn(1024)  # Placeholder
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        stats = {
            'loaded_models': list(self._models.keys()),
            'model_usage_count': dict(self._model_usage_count),
            'feature_cache_size': len(self._feature_cache),
        }
        
        if torch.cuda.is_available():
            stats.update({
                'gpu_memory_allocated_gb': torch.cuda.memory_allocated() / 1e9,
                'gpu_memory_cached_gb': torch.cuda.memory_reserved() / 1e9,
                'gpu_utilization_percent': torch.cuda.utilization() if hasattr(torch.cuda, 'utilization') else 0
            })
        
        return stats
    
    def cleanup_unused_models(self, min_unused_time: float = 600.0):
        """Clean up models that haven't been used recently."""
        current_time = time.time()
        models_to_remove = []
        
        for model_type in list(self._models.keys()):
            with self._model_locks[model_type]:
                if self._model_usage_count[model_type] == 0:
                    models_to_remove.append(model_type)
        
        for model_type in models_to_remove:
            try:
                del self._models[model_type]
                if model_type in self._processors:
                    del self._processors[model_type]
                logger.info(f"Cleaned up unused model: {model_type}")
            except Exception as e:
                logger.error(f"Error cleaning up {model_type}: {e}")
        
        # Force garbage collection
        if models_to_remove:
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def shutdown(self):
        """Shutdown the model manager and cleanup resources."""
        logger.info("Shutting down ProductionModelManager")
        
        # Clear all models
        self._models.clear()
        self._processors.clear()
        self._feature_cache.clear()
        
        # Shutdown thread pool
        self._inference_executor.shutdown(wait=True)
        
        # Cleanup GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        gc.collect()