"""
Audio file and metadata models.

Database models for storing audio file information and metadata.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean
from sqlalchemy.types import JSON, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.core.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type for enterprise cross-database compatibility."""
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


class AudioFile(Base):
    """Model for uploaded audio files."""
    
    __tablename__ = "audio_files"
    
    # Primary identifiers
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
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
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    audio_file_id = Column(GUID, nullable=False, unique=True, index=True)
    
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
    mfcc_features = Column(JSON, nullable=True)  # MFCC coefficients
    spectral_features = Column(JSON, nullable=True)  # Additional spectral data
    tempo_features = Column(JSON, nullable=True)  # Tempo and rhythm analysis
    
    # Analysis metadata
    analysis_version = Column(String(20), nullable=False, default="1.0")
    analysis_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    analysis_duration = Column(Float, nullable=True)  # Time taken for analysis
    
    def __repr__(self) -> str:
        return f"<AudioMetadata(id={self.id}, audio_file_id={self.audio_file_id})>"