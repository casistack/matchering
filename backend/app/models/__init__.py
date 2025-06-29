"""
Database models for Enhanced Matchering API.

Imports all model classes for SQLAlchemy metadata registration.
"""

from app.core.database import Base
from app.models.audio import AudioFile, AudioMetadata
from app.models.processing import ProcessingJob, JobProgress

# Export all models for easy importing
__all__ = [
    "Base",
    "AudioFile", 
    "AudioMetadata",
    "ProcessingJob",
    "JobProgress",
]