"""
Processing job and progress models.

Database models for tracking audio processing jobs and their progress.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, Enum
from sqlalchemy.types import JSON, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func
import uuid
import enum
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


class JobStatus(enum.Enum):
    """Enumeration of possible job statuses."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingMode(enum.Enum):
    """Enumeration of processing modes."""
    AUTO = "auto"
    REFERENCE = "reference"
    HYBRID = "hybrid"


class ProcessingStage(enum.Enum):
    """Enumeration of processing stages."""
    VALIDATION = "validation"
    FEATURE_EXTRACTION = "feature_extraction"
    AI_ANALYSIS = "ai_analysis"
    PARAMETER_PREDICTION = "parameter_prediction"
    AUDIO_PROCESSING = "audio_processing"
    QUALITY_CHECK = "quality_check"
    FINALIZATION = "finalization"


class ProcessingJob(Base):
    """Model for audio processing jobs."""
    
    __tablename__ = "processing_jobs"
    
    # Primary identifiers
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    
    # File references
    input_file_id = Column(GUID, nullable=False, index=True)
    reference_file_id = Column(GUID, nullable=True, index=True)
    output_file_path = Column(String(500), nullable=True)
    
    # Job configuration
    processing_mode = Column(Enum(ProcessingMode), nullable=False)
    settings = Column(JSON, nullable=False)  # Processing settings as JSON
    
    # Job status and timing
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    queue_position = Column(Integer, nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Progress tracking
    current_stage = Column(Enum(ProcessingStage), nullable=True)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    
    # Results and error handling
    result_metadata = Column(JSON, nullable=True)  # Processing results
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Performance metrics
    processing_duration = Column(Float, nullable=True)  # Total processing time in seconds
    cpu_time = Column(Float, nullable=True)  # CPU time used
    memory_peak = Column(Integer, nullable=True)  # Peak memory usage in MB
    
    def __repr__(self) -> str:
        return f"<ProcessingJob(id={self.id}, status={self.status.value})>"


class JobProgress(Base):
    """Model for detailed job progress tracking."""
    
    __tablename__ = "job_progress"
    
    # Primary key and foreign key
    id = Column(GUID, primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(GUID, nullable=False, index=True)
    
    # Progress details
    stage = Column(Enum(ProcessingStage), nullable=False)
    progress_percentage = Column(Float, nullable=False)
    message = Column(Text, nullable=True)
    
    # Timing information
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    stage_started_at = Column(DateTime(timezone=True), nullable=True)
    stage_duration = Column(Float, nullable=True)  # Duration for completed stages
    
    # Technical details
    details = Column(JSON, nullable=True)  # Stage-specific details
    warnings = Column(JSON, nullable=True)  # Any warnings during processing
    
    def __repr__(self) -> str:
        return f"<JobProgress(job_id={self.job_id}, stage={self.stage.value}, progress={self.progress_percentage}%)>"