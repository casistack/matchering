"""
Audio-related Pydantic schemas for Enhanced Matchering API.

Contains models for audio file uploads, metadata, and responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID

from .common import APIResponse, PaginationInfo


class AudioFileBase(BaseModel):
    """Base audio file model."""
    
    filename: str = Field(..., min_length=1, max_length=255, description="Audio filename")
    original_filename: str = Field(..., min_length=1, max_length=255, description="Original upload filename")
    format: str = Field(..., description="Audio format (wav, mp3, flac, aiff)")
    sample_rate: int = Field(..., gt=0, description="Audio sample rate in Hz")
    bit_depth: Optional[int] = Field(None, gt=0, description="Audio bit depth")
    channels: int = Field(..., gt=0, description="Number of audio channels")
    duration: float = Field(..., gt=0, description="Audio duration in seconds")
    file_size: int = Field(..., gt=0, description="File size in bytes")


class AudioFileCreate(AudioFileBase):
    """Audio file creation model."""
    
    file_path: str = Field(..., description="Server file path")
    mime_type: str = Field(..., description="MIME type")
    checksum: str = Field(..., min_length=64, max_length=64, description="SHA-256 checksum")
    processing_eligible: bool = Field(False, description="Whether file is eligible for processing")


class AudioFileResponse(AudioFileBase):
    """Audio file response model."""
    
    id: UUID = Field(..., description="Unique file identifier")
    file_path: str = Field(..., description="Server file path")
    mime_type: str = Field(..., description="MIME type")
    checksum: str = Field(..., description="SHA-256 checksum")
    upload_timestamp: datetime = Field(..., description="Upload timestamp")
    processing_eligible: bool = Field(..., description="Whether file is eligible for processing")
    
    class Config:
        from_attributes = True


class AudioMetadataResponse(BaseModel):
    """Audio metadata response model."""
    
    id: UUID = Field(..., description="Metadata identifier")
    audio_file_id: UUID = Field(..., description="Associated audio file ID")
    
    # Basic audio measurements
    rms_level: Optional[float] = Field(None, description="RMS level in dB")
    peak_level: Optional[float] = Field(None, description="Peak level in dB")
    dynamic_range: Optional[float] = Field(None, description="Dynamic range in dB")
    
    # Spectral features
    spectral_centroid: Optional[float] = Field(None, description="Spectral centroid in Hz")
    spectral_rolloff: Optional[float] = Field(None, description="Spectral rolloff in Hz")
    zero_crossing_rate: Optional[float] = Field(None, description="Zero crossing rate")
    
    # Loudness measurements (EBU R128)
    lufs_integrated: Optional[float] = Field(None, description="Integrated LUFS")
    lufs_short_term: Optional[float] = Field(None, description="Short-term LUFS")
    lufs_momentary: Optional[float] = Field(None, description="Momentary LUFS")
    true_peak: Optional[float] = Field(None, description="True peak in dBTP")
    
    # Complex features (JSON)
    mfcc_features: Optional[Dict[str, Any]] = Field(None, description="MFCC features")
    spectral_features: Optional[Dict[str, Any]] = Field(None, description="Spectral features")
    tempo_features: Optional[Dict[str, Any]] = Field(None, description="Tempo and rhythm features")
    
    # Analysis metadata
    analysis_version: str = Field(..., description="Analysis version")
    analysis_timestamp: datetime = Field(..., description="Analysis completion time")
    analysis_duration: Optional[float] = Field(None, description="Analysis time in seconds")
    
    class Config:
        from_attributes = True


class AudioUploadRequest(BaseModel):
    """Audio upload request parameters."""
    
    processing_mode: str = Field("auto", description="Processing mode (auto, reference, hybrid)")
    auto_analyze: bool = Field(True, description="Automatically analyze uploaded file")
    
    @validator('processing_mode')
    def validate_processing_mode(cls, v):
        allowed_modes = ['auto', 'reference', 'hybrid']
        if v not in allowed_modes:
            raise ValueError(f'Processing mode must be one of: {allowed_modes}')
        return v


class AudioUploadResponse(BaseModel):
    """Audio upload response model."""
    
    file_id: UUID = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Stored filename")
    original_filename: str = Field(..., description="Original upload filename")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Audio format")
    upload_status: str = Field(..., description="Upload status")
    validation_task_id: Optional[str] = Field(None, description="File validation task ID")
    analysis_task_id: Optional[str] = Field(None, description="Analysis task ID")
    processing_eligible: bool = Field(..., description="Whether file can be processed")
    
    # Quick audio properties (if available)
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    sample_rate: Optional[int] = Field(None, description="Sample rate in Hz")
    channels: Optional[int] = Field(None, description="Number of channels")
    
    # Upload metadata
    upload_timestamp: datetime = Field(..., description="Upload completion time")
    checksum: str = Field(..., description="File checksum")


class AudioFileListResponse(BaseModel):
    """Audio file list response model."""
    
    files: List[AudioFileResponse] = Field(..., description="List of audio files")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class AudioFileDetailResponse(BaseModel):
    """Detailed audio file response with metadata."""
    
    file: AudioFileResponse = Field(..., description="Audio file information")
    metadata: Optional[AudioMetadataResponse] = Field(None, description="Audio analysis metadata")
    processing_jobs: List[Dict[str, Any]] = Field([], description="Associated processing jobs")


class DuplicateFileResponse(BaseModel):
    """Response for duplicate file detection."""
    
    is_duplicate: bool = Field(..., description="Whether file is a duplicate")
    existing_file_id: Optional[UUID] = Field(None, description="Existing file ID if duplicate")
    existing_filename: Optional[str] = Field(None, description="Existing filename if duplicate")
    checksum: str = Field(..., description="File checksum")
    message: str = Field(..., description="Human-readable message")


# Type aliases for API responses
AudioFileAPIResponse = APIResponse[AudioFileResponse]
AudioFileListAPIResponse = APIResponse[AudioFileListResponse]
AudioUploadAPIResponse = APIResponse[AudioUploadResponse]
AudioMetadataAPIResponse = APIResponse[AudioMetadataResponse]
AudioFileDetailAPIResponse = APIResponse[AudioFileDetailResponse]
DuplicateFileAPIResponse = APIResponse[DuplicateFileResponse]