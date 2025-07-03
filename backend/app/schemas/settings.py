"""
Pydantic schemas for user settings and model preferences.

Provides enterprise-grade validation and serialization for settings API.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum


class ModelSelectionStrategy(str, Enum):
    """Model selection strategy options."""
    AUTO = "auto"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    CUSTOM = "custom"


class QualityPreference(str, Enum):
    """Quality vs speed preference options."""
    FAST = "fast"
    BALANCED = "balanced"
    QUALITY = "quality"


class FallbackStrategy(str, Enum):
    """Fallback strategy when primary models fail."""
    STRICT = "strict"
    GRACEFUL = "graceful"
    AGGRESSIVE = "aggressive"


class ModelType(str, Enum):
    """Types of AI models available."""
    HUGGINGFACE = "huggingface"
    AST = "ast"
    CUSTOM = "custom"


# Base Schemas
class ModelPerformanceInfoSchema(BaseModel):
    """Performance information for an AI model."""
    average_processing_time: float = Field(..., ge=0, description="Average processing time in milliseconds")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Model accuracy (0.0-1.0)")
    memory_usage: float = Field(..., ge=0, description="Memory usage in MB")
    gpu_required: bool = Field(default=False, description="Whether GPU is required")
    supported_genres: List[str] = Field(default=[], description="List of supported music genres")


class ModelPreferencesSchema(BaseModel):
    """User's model selection preferences."""
    preferred_strategy: ModelSelectionStrategy = Field(default=ModelSelectionStrategy.AUTO)
    ensemble_weights: Dict[str, float] = Field(
        default={"huggingface": 0.70, "ast": 0.25, "fallback": 0.05},
        description="Weights for ensemble models"
    )
    quality_preference: QualityPreference = Field(default=QualityPreference.BALANCED)
    enable_experimental: bool = Field(default=False, description="Enable experimental features")
    confidence_threshold: float = Field(default=0.6, ge=0.5, le=0.95, description="Minimum confidence threshold")
    max_processing_time: int = Field(default=5000, ge=1000, le=10000, description="Max processing time in milliseconds")
    fallback_strategy: FallbackStrategy = Field(default=FallbackStrategy.GRACEFUL)
    custom_settings: Dict[str, Any] = Field(default={}, description="Custom user settings")

    @field_validator('ensemble_weights')
    @classmethod
    def validate_ensemble_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate ensemble weights sum to approximately 1.0."""
        total = sum(v.values())
        if not (0.9 <= total <= 1.1):
            raise ValueError(f"Ensemble weights must sum to approximately 1.0, got {total}")
        return v


class UserSettingsProfileSchema(BaseModel):
    """Complete user settings profile."""
    id: str
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    preferred_strategy: ModelSelectionStrategy
    ensemble_weights: Dict[str, float]
    quality_preference: QualityPreference
    enable_experimental: bool
    confidence_threshold: float
    max_processing_time: int
    fallback_strategy: FallbackStrategy
    advanced_settings: Dict[str, Any] = Field(default={})
    feature_flags: Dict[str, Any] = Field(default={})
    
    # Profile metadata
    is_default: bool = Field(default=False)
    is_custom: bool = Field(default=False)
    is_system_profile: bool = Field(default=False)
    usage_count: int = Field(default=0, ge=0)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime] = None

    class Config:
        from_attributes = True


class AvailableModelInfoSchema(BaseModel):
    """Information about an available AI model."""
    id: str
    name: str
    description: str
    type: ModelType
    performance: ModelPerformanceInfoSchema
    is_available: bool = Field(default=True)
    requirements: List[str] = Field(default=[], description="System requirements")
    version: str = Field(default="1.0.0")
    provider: str = Field(default="Matchering")


class SettingsConfigResponse(BaseModel):
    """Complete settings configuration response."""
    current_profile: UserSettingsProfileSchema
    available_profiles: List[UserSettingsProfileSchema]
    available_models: List[AvailableModelInfoSchema]
    system_defaults: ModelPreferencesSchema
    feature_flags: Dict[str, bool] = Field(default={})


class UserSettingsAnalyticsSchema(BaseModel):
    """User settings usage analytics."""
    total_processing_jobs: int = Field(default=0, ge=0)
    average_processing_time: float = Field(default=0.0, ge=0.0)
    most_used_model: Optional[str] = None
    model_usage_distribution: Dict[str, int] = Field(default={})
    quality_ratings: Dict[str, float] = Field(default={})
    performance_trends: Dict[str, List[float]] = Field(default={})
    period_days: int = Field(default=30, ge=1, le=365)


# Request Schemas for Updates
class ModelPreferencesUpdateSchema(BaseModel):
    """Schema for updating model preferences."""
    preferred_strategy: Optional[ModelSelectionStrategy] = None
    ensemble_weights: Optional[Dict[str, float]] = None
    quality_preference: Optional[QualityPreference] = None
    enable_experimental: Optional[bool] = None
    confidence_threshold: Optional[float] = Field(None, ge=0.5, le=0.95)
    max_processing_time: Optional[int] = Field(None, ge=1000, le=10000)
    fallback_strategy: Optional[FallbackStrategy] = None
    custom_settings: Optional[Dict[str, Any]] = None

    @field_validator('ensemble_weights')
    @classmethod
    def validate_ensemble_weights(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        """Validate ensemble weights sum to approximately 1.0."""
        if v is None:
            return v
        total = sum(v.values())
        if not (0.9 <= total <= 1.1):
            raise ValueError(f"Ensemble weights must sum to approximately 1.0, got {total}")
        return v


class UserSettingsProfileCreateSchema(BaseModel):
    """Schema for creating a new settings profile."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    preferences: ModelPreferencesSchema
    copy_from_profile_id: Optional[str] = Field(None, description="Copy settings from existing profile")


class UserSettingsProfileUpdateSchema(BaseModel):
    """Schema for updating an existing settings profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    preferences: Optional[ModelPreferencesUpdateSchema] = None


# Response Schemas
class SettingsUpdateResponse(BaseModel):
    """Response after updating settings."""
    success: bool = True
    profile: UserSettingsProfileSchema
    cache_invalidated: bool = Field(default=False)
    message: str = Field(default="Settings updated successfully")


class ProfileSelectionResponse(BaseModel):
    """Response after selecting a profile."""
    success: bool = True
    active_profile: UserSettingsProfileSchema
    previous_profile_id: Optional[str] = None
    message: str = Field(default="Profile selected successfully")


class SystemStatusResponse(BaseModel):
    """System status for settings service."""
    available_models_count: int
    active_users_count: int
    cache_hit_rate: float = Field(ge=0.0, le=1.0)
    average_response_time: float = Field(ge=0.0)
    feature_flags: Dict[str, bool]
    last_updated: datetime