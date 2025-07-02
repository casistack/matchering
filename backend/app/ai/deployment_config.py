"""
Production Deployment Configuration for Hybrid AI System.

This module provides configuration management for production deployment
of the hybrid AI mastering system with environment-specific optimizations.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentEnvironment(str, Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class GPUConfig(BaseModel):
    """GPU configuration for production deployment."""
    
    enabled: bool = Field(default=True, description="Enable GPU acceleration")
    device_id: int = Field(default=0, description="GPU device ID")
    memory_limit_gb: float = Field(default=20.0, description="GPU memory limit in GB")
    mixed_precision: bool = Field(default=True, description="Enable mixed precision training")
    cuda_version: str = Field(default="12.4", description="CUDA version")
    
    @validator('memory_limit_gb')
    def validate_memory_limit(cls, v):
        if v <= 0 or v > 80:
            raise ValueError("GPU memory limit must be between 0 and 80 GB")
        return v


class ModelDeploymentConfig(BaseModel):
    """Configuration for individual model deployment."""
    
    enabled: bool = Field(default=True, description="Enable this model")
    quantization: bool = Field(default=True, description="Enable quantization")
    max_batch_size: int = Field(default=8, description="Maximum batch size")
    max_concurrent_requests: int = Field(default=2, description="Max concurrent requests")
    cache_features: bool = Field(default=True, description="Cache extracted features")
    preload_on_startup: bool = Field(default=False, description="Preload model on startup")
    memory_limit_mb: int = Field(description="Memory limit in MB")
    
    @validator('max_batch_size')
    def validate_batch_size(cls, v):
        if v <= 0 or v > 32:
            raise ValueError("Batch size must be between 1 and 32")
        return v


class CacheConfig(BaseModel):
    """Configuration for production caching."""
    
    enabled: bool = Field(default=True, description="Enable caching")
    cache_dir: str = Field(default="./model_cache", description="Cache directory path")
    max_cache_size_gb: float = Field(default=10.0, description="Maximum cache size in GB")
    feature_cache_ttl: int = Field(default=3600, description="Feature cache TTL in seconds")
    model_cache_ttl: int = Field(default=86400, description="Model cache TTL in seconds")
    cleanup_interval: int = Field(default=1800, description="Cache cleanup interval in seconds")


class MonitoringConfig(BaseModel):
    """Configuration for production monitoring."""
    
    enabled: bool = Field(default=True, description="Enable monitoring")
    metrics_port: int = Field(default=8080, description="Metrics server port")
    log_level: str = Field(default="INFO", description="Logging level")
    performance_tracking: bool = Field(default=True, description="Track performance metrics")
    health_check_interval: int = Field(default=60, description="Health check interval in seconds")
    alert_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "gpu_memory_usage": 0.9,
            "inference_time": 10.0,
            "error_rate": 0.05
        }
    )


class ProductionDeploymentConfig(BaseModel):
    """Complete production deployment configuration."""
    
    environment: DeploymentEnvironment = Field(default=DeploymentEnvironment.PRODUCTION)
    
    # GPU Configuration
    gpu: GPUConfig = Field(default_factory=GPUConfig)
    
    # Model Configurations
    models: Dict[str, ModelDeploymentConfig] = Field(
        default_factory=lambda: {
            "ast": ModelDeploymentConfig(
                enabled=True,
                quantization=True,
                max_batch_size=4,
                max_concurrent_requests=2,
                cache_features=True,
                preload_on_startup=True,
                memory_limit_mb=2800
            ),
            "wav2vec": ModelDeploymentConfig(
                enabled=True,
                quantization=True,
                max_batch_size=4,
                max_concurrent_requests=2,
                cache_features=True,
                preload_on_startup=True,
                memory_limit_mb=3200
            ),
            "musicgen": ModelDeploymentConfig(
                enabled=False,  # Disabled by default due to size
                quantization=True,
                max_batch_size=2,
                max_concurrent_requests=1,
                cache_features=False,
                preload_on_startup=False,
                memory_limit_mb=4500
            ),
            "custom": ModelDeploymentConfig(
                enabled=True,
                quantization=True,
                max_batch_size=16,
                max_concurrent_requests=4,
                cache_features=True,
                preload_on_startup=True,
                memory_limit_mb=500
            )
        }
    )
    
    # Cache Configuration
    cache: CacheConfig = Field(default_factory=CacheConfig)
    
    # Monitoring Configuration
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # API Configuration
    api_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_file_size_mb": 100,
            "supported_formats": ["wav", "mp3", "flac", "aiff"],
            "max_concurrent_uploads": 10,
            "request_timeout": 300,
            "background_task_timeout": 600
        }
    )
    
    # Security Configuration
    security: Dict[str, Any] = Field(
        default_factory=lambda: {
            "input_validation": True,
            "file_sanitization": True,
            "rate_limiting": True,
            "max_requests_per_minute": 100
        }
    )


class DeploymentConfigManager:
    """Manages deployment configuration with environment-specific overrides."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("DEPLOYMENT_CONFIG_PATH", "deployment_config.json")
        self._config: Optional[ProductionDeploymentConfig] = None
        self._environment = os.getenv("DEPLOYMENT_ENV", "production")
    
    def load_config(self) -> ProductionDeploymentConfig:
        """Load configuration from file or environment variables."""
        if self._config is not None:
            return self._config
        
        # Start with default configuration
        config_dict = {}
        
        # Load from file if exists
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                import json
                with open(config_file) as f:
                    config_dict = json.load(f)
                logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {config_file}: {e}")
        
        # Apply environment-specific overrides
        config_dict = self._apply_environment_overrides(config_dict)
        
        # Create configuration object
        self._config = ProductionDeploymentConfig(**config_dict)
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"Deployment configuration loaded for {self._config.environment}")
        return self._config
    
    def _apply_environment_overrides(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        
        # Environment detection
        config_dict["environment"] = self._environment
        
        # GPU configuration from environment
        if "gpu" not in config_dict:
            config_dict["gpu"] = {}
        
        gpu_config = config_dict["gpu"]
        
        # Check for GPU availability
        try:
            import torch
            gpu_available = torch.cuda.is_available()
            if not gpu_available:
                logger.warning("CUDA not available, disabling GPU acceleration")
                gpu_config["enabled"] = False
            else:
                gpu_config["enabled"] = True
                gpu_config["device_id"] = int(os.getenv("CUDA_VISIBLE_DEVICES", "0"))
                
                # Get GPU memory info
                if torch.cuda.is_available():
                    gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                    gpu_config["memory_limit_gb"] = min(gpu_memory_gb * 0.85, 20.0)  # Use 85% of available
                    logger.info(f"GPU detected: {gpu_memory_gb:.1f}GB total, {gpu_config['memory_limit_gb']:.1f}GB limit")
        except ImportError:
            logger.warning("PyTorch not available, disabling GPU")
            gpu_config["enabled"] = False
        
        # Cache configuration from environment
        if "cache" not in config_dict:
            config_dict["cache"] = {}
        
        cache_config = config_dict["cache"]
        cache_config["cache_dir"] = os.getenv("MODEL_CACHE_DIR", "./model_cache")
        
        # Model configuration based on environment
        if self._environment == "development":
            # Development optimizations
            if "models" not in config_dict:
                config_dict["models"] = {}
            
            # Disable heavy models in development
            for model_name in ["musicgen"]:
                if model_name not in config_dict["models"]:
                    config_dict["models"][model_name] = {}
                config_dict["models"][model_name]["enabled"] = False
                config_dict["models"][model_name]["preload_on_startup"] = False
        
        elif self._environment == "production":
            # Production optimizations
            if "monitoring" not in config_dict:
                config_dict["monitoring"] = {}
            
            config_dict["monitoring"]["enabled"] = True
            config_dict["monitoring"]["performance_tracking"] = True
        
        return config_dict
    
    def _validate_config(self):
        """Validate configuration for deployment environment."""
        if not self._config:
            return
        
        # Validate GPU configuration
        if self._config.gpu.enabled:
            try:
                import torch
                if not torch.cuda.is_available():
                    logger.error("GPU enabled in config but CUDA not available")
                    raise ValueError("GPU configuration invalid")
            except ImportError:
                logger.error("GPU enabled but PyTorch not available")
                raise ValueError("PyTorch required for GPU acceleration")
        
        # Validate model memory requirements
        total_memory_mb = sum(
            model_config.memory_limit_mb 
            for model_config in self._config.models.values() 
            if model_config.enabled and model_config.preload_on_startup
        )
        
        available_memory_mb = self._config.gpu.memory_limit_gb * 1024
        if total_memory_mb > available_memory_mb:
            logger.warning(f"Model memory requirements ({total_memory_mb}MB) exceed available GPU memory ({available_memory_mb:.0f}MB)")
        
        # Validate cache directory
        cache_dir = Path(self._config.cache.cache_dir)
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Cannot create cache directory {cache_dir}: {e}")
            raise ValueError(f"Cache directory configuration invalid: {e}")
    
    def get_model_config(self, model_type: str) -> Optional[ModelDeploymentConfig]:
        """Get configuration for a specific model."""
        config = self.load_config()
        return config.models.get(model_type)
    
    def is_model_enabled(self, model_type: str) -> bool:
        """Check if a model is enabled for deployment."""
        model_config = self.get_model_config(model_type)
        return model_config.enabled if model_config else False
    
    def get_enabled_models(self) -> List[str]:
        """Get list of enabled models."""
        config = self.load_config()
        return [
            model_type 
            for model_type, model_config in config.models.items() 
            if model_config.enabled
        ]
    
    def get_preload_models(self) -> List[str]:
        """Get list of models to preload on startup."""
        config = self.load_config()
        return [
            model_type 
            for model_type, model_config in config.models.items() 
            if model_config.enabled and model_config.preload_on_startup
        ]
    
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to file."""
        if not self._config:
            return
        
        save_path = config_path or self.config_path
        
        try:
            import json
            with open(save_path, 'w') as f:
                json.dump(self._config.dict(), f, indent=2)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance-related configuration."""
        config = self.load_config()
        return {
            "gpu_enabled": config.gpu.enabled,
            "gpu_memory_limit": config.gpu.memory_limit_gb,
            "mixed_precision": config.gpu.mixed_precision,
            "cache_enabled": config.cache.enabled,
            "monitoring_enabled": config.monitoring.enabled,
            "enabled_models": self.get_enabled_models(),
            "preload_models": self.get_preload_models()
        }


# Global configuration manager instance
config_manager = DeploymentConfigManager()


def get_deployment_config() -> ProductionDeploymentConfig:
    """Get the current deployment configuration."""
    return config_manager.load_config()


def get_model_config(model_type: str) -> Optional[ModelDeploymentConfig]:
    """Get configuration for a specific model type."""
    return config_manager.get_model_config(model_type)


def is_model_enabled(model_type: str) -> bool:
    """Check if a model is enabled for deployment."""
    return config_manager.is_model_enabled(model_type)