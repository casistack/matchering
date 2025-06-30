"""
Pydantic schemas for AI processing endpoints.

This module defines the request/response schemas for AI-powered
audio analysis and mastering features.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.ai.feature_extractor import AudioFeatures


class FeatureExtractionRequest(BaseModel):
    """Request schema for feature extraction."""
    
    analysis_depth: str = Field(
        default="standard",
        description="Analysis depth: fast, standard, or full",
        pattern="^(fast|standard|full)$"
    )
    cache_result: bool = Field(
        default=True,
        description="Whether to cache extracted features"
    )


class AudioFeaturesResponse(BaseModel):
    """Response schema for audio features (summary view)."""
    
    feature_hash: str = Field(description="Unique hash for the extracted features")
    extraction_time: float = Field(description="Time taken for feature extraction (seconds)")
    sample_rate: int = Field(description="Audio sample rate")
    duration: float = Field(description="Audio duration in seconds")
    channels: int = Field(description="Number of audio channels")
    
    # Feature array shapes (for efficiency - not full arrays)
    mfcc_shape: tuple[int, int] = Field(description="Shape of MFCC feature array")
    spectral_features_count: int = Field(description="Number of spectral feature frames")
    chroma_shape: tuple[int, int] = Field(description="Shape of chroma feature array")
    
    # Key mastering features
    mastering_features: Dict[str, float] = Field(
        description="Key mastering-specific features"
    )
    
    # Optional: full raw features (included on request)
    raw_features: Optional[AudioFeatures] = Field(
        default=None,
        description="Complete raw audio features (optional)"
    )


class FeatureExtractionResponse(BaseModel):
    """Response schema for feature extraction endpoint."""
    
    success: bool = Field(description="Whether extraction succeeded")
    features: Optional[AudioFeaturesResponse] = Field(
        default=None,
        description="Extracted audio features"
    )
    processing_time: float = Field(description="Total processing time (seconds)")
    file_info: Dict[str, Any] = Field(description="Information about the processed file")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ParameterPredictionRequest(BaseModel):
    """Request schema for AI parameter prediction."""
    
    feature_hash: str = Field(description="Hash of cached features to use")
    processing_mode: str = Field(
        default="auto",
        description="Processing mode: auto, reference, or hybrid",
        pattern="^(auto|reference|hybrid)$"
    )
    target_loudness: Optional[float] = Field(
        default=None,
        description="Target loudness in LUFS"
    )
    genre_hint: Optional[str] = Field(
        default=None,
        description="Genre hint for better parameter prediction"
    )


class MasteringParameters(BaseModel):
    """AI-predicted mastering parameters."""
    
    # EQ Parameters
    eq_curve: List[float] = Field(description="31-band EQ curve adjustments (dB)")
    
    # Compression Parameters
    compression: Dict[str, float] = Field(
        description="Compression settings (ratio, attack, release, threshold)"
    )
    
    # Stereo Enhancement
    stereo: Dict[str, float] = Field(
        description="Stereo enhancement settings (width, pan)"
    )
    
    # Limiting Parameters
    limiting: Dict[str, float] = Field(
        description="Limiting settings (threshold, release, ceiling)"
    )
    
    # Metadata
    predicted_genre: str = Field(description="AI-predicted genre")
    confidence: float = Field(description="Prediction confidence (0-1)")
    processing_notes: List[str] = Field(description="AI processing recommendations")


class ParameterPredictionResponse(BaseModel):
    """Response schema for parameter prediction."""
    
    success: bool = Field(description="Whether prediction succeeded")
    parameters: Optional[MasteringParameters] = Field(
        default=None,
        description="Predicted mastering parameters"
    )
    model_info: Dict[str, Any] = Field(description="Information about the AI model used")
    inference_time: float = Field(description="AI inference time (seconds)")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class HybridProcessingRequest(BaseModel):
    """Request schema for hybrid AI + reference processing."""
    
    audio_file_id: str = Field(description="ID of uploaded audio file")
    processing_mode: str = Field(
        default="hybrid",
        description="Processing mode",
        pattern="^(ai_autonomous|reference_based|hybrid)$"
    )
    reference_file_id: Optional[str] = Field(
        default=None,
        description="ID of reference file (for reference/hybrid modes)"
    )
    ai_blend_ratio: float = Field(
        default=0.7,
        description="AI vs reference blend ratio (0=full reference, 1=full AI)",
        ge=0.0,
        le=1.0
    )
    target_settings: Optional[Dict[str, Any]] = Field(
        default=None,
        description="User-specified target settings"
    )


class ProcessingProgress(BaseModel):
    """Real-time processing progress update."""
    
    job_id: str = Field(description="Processing job ID")
    stage: str = Field(description="Current processing stage")
    progress: float = Field(description="Progress percentage (0-1)")
    message: str = Field(description="Status message")
    estimated_remaining: Optional[float] = Field(
        default=None,
        description="Estimated remaining time (seconds)"
    )


class PerformanceStatsResponse(BaseModel):
    """Performance statistics for AI services."""
    
    extraction_stats: Dict[str, float] = Field(
        description="Feature extraction performance metrics"
    )
    cache_stats: Dict[str, Any] = Field(
        description="Feature cache performance metrics"
    )
    service_uptime: float = Field(description="Service uptime in seconds")
    total_extractions: int = Field(description="Total number of feature extractions performed")


class AIModelInfo(BaseModel):
    """Information about AI models."""
    
    model_name: str = Field(description="Model name")
    version: str = Field(description="Model version")
    architecture: str = Field(description="Model architecture type")
    training_date: str = Field(description="Model training date")
    performance_metrics: Dict[str, float] = Field(
        description="Model performance metrics"
    )
    supported_genres: List[str] = Field(description="Supported music genres")


class AIServiceStatus(BaseModel):
    """Overall AI service status."""
    
    status: str = Field(description="Service status")
    models_loaded: List[str] = Field(description="Currently loaded models")
    gpu_available: bool = Field(description="Whether GPU is available")
    memory_usage: Dict[str, float] = Field(description="Memory usage statistics")
    active_jobs: int = Field(description="Number of active processing jobs")


# Request/Response schemas for batch operations
class BatchFeatureExtractionRequest(BaseModel):
    """Request schema for batch feature extraction."""
    
    file_ids: List[str] = Field(description="List of audio file IDs to process")
    analysis_depth: str = Field(default="standard", description="Analysis depth for all files")
    max_concurrent: int = Field(default=3, description="Maximum concurrent extractions", ge=1, le=10)


class BatchFeatureExtractionResponse(BaseModel):
    """Response schema for batch feature extraction."""
    
    results: List[FeatureExtractionResponse] = Field(description="Individual extraction results")
    total_processing_time: float = Field(description="Total batch processing time")
    successful_extractions: int = Field(description="Number of successful extractions")
    failed_extractions: int = Field(description="Number of failed extractions")


# Cache management schemas
class CacheStatsResponse(BaseModel):
    """Feature cache statistics."""
    
    total_cached_features: int = Field(description="Total number of cached feature sets")
    cache_hit_rate: float = Field(description="Cache hit rate (0-1)")
    cache_size_mb: float = Field(description="Cache size in megabytes")
    average_feature_size_kb: float = Field(description="Average feature set size in kilobytes")
    oldest_cache_entry: Optional[str] = Field(description="Timestamp of oldest cache entry")


class CacheCleanupRequest(BaseModel):
    """Request schema for cache cleanup."""
    
    max_age_hours: int = Field(default=24, description="Maximum age of cache entries in hours")
    max_cache_size_mb: int = Field(default=1000, description="Maximum cache size in MB")
    force_cleanup: bool = Field(default=False, description="Force cleanup regardless of settings")