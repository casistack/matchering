"""
Database models for Enhanced Matchering API.

Imports all model classes for SQLAlchemy metadata registration.
"""

from app.core.database import Base
from app.models.audio import AudioFile, AudioMetadata
from app.models.processing import ProcessingJob, JobProgress
from app.models.user_preferences import UserPreferences, ModelPerformanceHistory, UserSettingsProfile

# Export all models for easy importing
__all__ = [
    "Base",
    "AudioFile", 
    "AudioMetadata",
    "ProcessingJob",
    "JobProgress",
    "UserPreferences",
    "ModelPerformanceHistory", 
    "UserSettingsProfile",
]