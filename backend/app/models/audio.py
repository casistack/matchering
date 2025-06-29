"""
Audio file and metadata models.

Database models for storing audio file information and metadata.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.core.database import Base


class AudioFile(Base):
    """Model for uploaded audio files."""
    
    __tablename__ = "audio_files"
    
    # Primary identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    
    # File properties
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(50), nullable=False)
    checksum = Column(String(64), nullable=False, unique=True)  # SHA-256
    
    # Audio format information
    format = Column(String(10), nullable=False)  # wav, mp3, flac, aiff
    sample_rate = Column(Integer, nullable=False)
    bit_depth = Column(Integer, nullable=True)  # May be null for compressed formats
    channels = Column(Integer, nullable=False)
    duration = Column(Float, nullable=False)  # Duration in seconds
    
    # Metadata
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processing_eligible = Column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<AudioFile(id={self.id}, filename={self.filename})>"


class AudioMetadata(Base):
    """Model for detailed audio analysis metadata."""
    
    __tablename__ = "audio_metadata"
    
    # Primary key and foreign key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    audio_file_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    # Basic audio metrics
    rms_level = Column(Float, nullable=True)
    peak_level = Column(Float, nullable=True)
    dynamic_range = Column(Float, nullable=True)
    
    # Spectral analysis
    spectral_centroid = Column(Float, nullable=True)
    spectral_rolloff = Column(Float, nullable=True)
    zero_crossing_rate = Column(Float, nullable=True)
    
    # Loudness measurements
    lufs_integrated = Column(Float, nullable=True)
    lufs_short_term = Column(Float, nullable=True)
    lufs_momentary = Column(Float, nullable=True)
    true_peak = Column(Float, nullable=True)
    
    # Advanced features (stored as JSON)
    mfcc_features = Column(JSONB, nullable=True)  # MFCC coefficients
    spectral_features = Column(JSONB, nullable=True)  # Additional spectral data
    tempo_features = Column(JSONB, nullable=True)  # Tempo and rhythm analysis
    
    # Analysis metadata
    analysis_version = Column(String(20), nullable=False, default="1.0")
    analysis_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    analysis_duration = Column(Float, nullable=True)  # Time taken for analysis
    
    def __repr__(self) -> str:
        return f"<AudioMetadata(id={self.id}, audio_file_id={self.audio_file_id})>"