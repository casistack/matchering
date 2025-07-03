"""
User preferences and model selection settings models.

Database models for storing user AI model preferences and performance history.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, CheckConstraint
from sqlalchemy.types import JSON, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type for enterprise cross-database compatibility.
    
    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36) for storage
    as string representation for maximum compatibility.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value) if isinstance(value, uuid.UUID) else value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value)) if value else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value
            else:
                return uuid.UUID(value)


class UserPreferences(Base):
    """User preferences for AI model selection and processing settings."""
    
    __tablename__ = "user_preferences"
    
    # Primary identifiers
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    anonymous_id = Column(String(64), nullable=True, index=True)  # For anonymous users (browser fingerprint)
    user_id = Column(String(64), nullable=True, index=True)       # For authenticated users (future)
    
    # Model selection preferences
    preferred_strategy = Column(String(20), nullable=False, default="auto")  # auto, performance, quality, custom
    ensemble_weights = Column(JSON, nullable=False, default={
        "huggingface": 0.70,
        "ast": 0.25,
        "fallback": 0.05
    })
    quality_preference = Column(String(20), nullable=False, default="balanced")  # fast, balanced, quality
    enable_experimental = Column(Boolean, nullable=False, default=False)
    
    # Processing settings
    confidence_threshold = Column(Float, nullable=False, default=0.6)
    max_processing_time = Column(Integer, nullable=False, default=5000)  # milliseconds
    enable_performance_logging = Column(Boolean, nullable=False, default=True)
    fallback_strategy = Column(String(20), nullable=False, default="graceful")  # strict, graceful, aggressive
    
    # Profile settings
    profile_name = Column(String(100), nullable=False, default="Default")
    profile_description = Column(Text, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_custom = Column(Boolean, nullable=False, default=False)
    
    # Advanced settings (stored as JSON for flexibility)
    advanced_settings = Column(JSON, nullable=True, default={})
    feature_flags = Column(JSON, nullable=True, default={})
    
    # Usage analytics
    usage_count = Column(Integer, nullable=False, default=0)
    total_processing_time = Column(Float, nullable=False, default=0.0)  # Total seconds
    last_model_used = Column(String(50), nullable=True)
    average_satisfaction = Column(Float, nullable=True)  # 1.0-5.0
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    performance_history = relationship("ModelPerformanceHistory", back_populates="user_preferences", cascade="all, delete-orphan")
    
    # Validation constraints
    __table_args__ = (
        CheckConstraint('confidence_threshold >= 0.5 AND confidence_threshold <= 0.95', name='check_confidence_threshold'),
        CheckConstraint('max_processing_time >= 1000 AND max_processing_time <= 10000', name='check_max_processing_time'),
        CheckConstraint('preferred_strategy IN (\'auto\', \'performance\', \'quality\', \'custom\')', name='check_preferred_strategy'),
        CheckConstraint('quality_preference IN (\'fast\', \'balanced\', \'quality\')', name='check_quality_preference'),
        CheckConstraint('fallback_strategy IN (\'strict\', \'graceful\', \'aggressive\')', name='check_fallback_strategy'),
        CheckConstraint('average_satisfaction IS NULL OR (average_satisfaction >= 1.0 AND average_satisfaction <= 5.0)', name='check_average_satisfaction'),
    )
    
    def __repr__(self) -> str:
        return f"<UserPreferences(id={self.id}, profile_name={self.profile_name}, strategy={self.preferred_strategy})>"


class ModelPerformanceHistory(Base):
    """Track model performance per user for optimization and analytics."""
    
    __tablename__ = "model_performance_history"
    
    # Primary key and foreign key
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    user_preferences_id = Column(GUID, ForeignKey("user_preferences.id"), nullable=False, index=True)
    processing_job_id = Column(GUID, nullable=True, index=True)  # Link to ProcessingJob if available
    
    # Model information
    model_used = Column(String(50), nullable=False)  # huggingface_ensemble, ast, fallback
    processing_mode = Column(String(20), nullable=False)  # auto, reference, hybrid, advanced
    ensemble_config = Column(JSON, nullable=True)  # The ensemble weights used
    
    # Performance metrics
    processing_time = Column(Float, nullable=False)  # Total processing time in seconds
    model_inference_time = Column(Float, nullable=True)  # AI model inference time only
    confidence_score = Column(Float, nullable=True)  # Model confidence 0.0-1.0
    user_satisfaction = Column(Integer, nullable=True)  # 1-5 rating (future feature)
    
    # Audio metadata
    predicted_genre = Column(String(50), nullable=True)
    actual_genre = Column(String(50), nullable=True)  # User-corrected genre (future)
    audio_duration = Column(Float, nullable=True)  # Audio file duration in seconds
    file_size = Column(Integer, nullable=True)  # File size in bytes
    sample_rate = Column(Integer, nullable=True)
    
    # System information
    gpu_used = Column(Boolean, nullable=False, default=False)
    memory_usage = Column(Float, nullable=True)  # Peak memory usage in MB
    cpu_usage = Column(Float, nullable=True)  # Average CPU usage percentage
    
    # Error tracking
    errors_encountered = Column(JSON, nullable=True)  # Error details if any
    fallback_used = Column(Boolean, nullable=False, default=False)
    fallback_reason = Column(String(100), nullable=True)
    
    # Quality metrics (future expansion)
    quality_metrics = Column(JSON, nullable=True)  # LUFS, dynamic range improvements, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_preferences = relationship("UserPreferences", back_populates="performance_history")
    
    # Validation constraints
    __table_args__ = (
        CheckConstraint('processing_time > 0', name='check_processing_time_positive'),
        CheckConstraint('model_inference_time IS NULL OR model_inference_time >= 0', name='check_inference_time_positive'),
        CheckConstraint('confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)', name='check_confidence_score'),
        CheckConstraint('user_satisfaction IS NULL OR (user_satisfaction >= 1 AND user_satisfaction <= 5)', name='check_user_satisfaction'),
        CheckConstraint('audio_duration IS NULL OR audio_duration > 0', name='check_audio_duration_positive'),
        CheckConstraint('file_size IS NULL OR file_size > 0', name='check_file_size_positive'),
    )
    
    def __repr__(self) -> str:
        return f"<ModelPerformanceHistory(id={self.id}, model={self.model_used}, time={self.processing_time:.2f}s)>"


class UserSettingsProfile(Base):
    """Named profiles for different user preference configurations."""
    
    __tablename__ = "user_settings_profiles"
    
    # Primary identifiers
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    user_preferences_id = Column(GUID, ForeignKey("user_preferences.id"), nullable=False, index=True)
    
    # Profile information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system_profile = Column(Boolean, nullable=False, default=False)  # Built-in profiles like "Fast", "Quality"
    is_active = Column(Boolean, nullable=False, default=False)
    
    # Profile configuration (snapshot of preferences)
    configuration = Column(JSON, nullable=False)  # Full preference configuration
    
    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Validation constraints - SQLite uses LENGTH() function instead of CHAR_LENGTH()
    __table_args__ = (
        CheckConstraint('LENGTH(name) >= 1', name='check_profile_name_not_empty'),
    )
    
    def __repr__(self) -> str:
        return f"<UserSettingsProfile(id={self.id}, name={self.name}, active={self.is_active})>"