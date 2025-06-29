"""
Processing-related Pydantic schemas for Enhanced Matchering API.

Contains models for processing jobs, progress tracking, and results.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID

from .common import APIResponse, PaginationInfo


class ProcessingJobCreate(BaseModel):
    """Processing job creation request."""
    
    input_file_id: UUID = Field(..., description="Input audio file ID")
    reference_file_id: Optional[UUID] = Field(None, description="Reference file ID (for reference mastering)")
    processing_mode: str = Field(..., description="Processing mode (auto, reference, hybrid)")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Processing settings")
    priority: int = Field(5, ge=1, le=10, description="Job priority (1=highest, 10=lowest)")
    
    @validator('processing_mode')
    def validate_processing_mode(cls, v):
        allowed_modes = ['auto', 'reference', 'hybrid']
        if v not in allowed_modes:
            raise ValueError(f'Processing mode must be one of: {allowed_modes}')
        return v


class ProcessingJobResponse(BaseModel):
    """Processing job response model."""
    
    id: UUID = Field(..., description="Job identifier")
    input_file_id: UUID = Field(..., description="Input file ID")
    reference_file_id: Optional[UUID] = Field(None, description="Reference file ID")
    output_file_path: Optional[str] = Field(None, description="Output file path")
    
    # Job configuration
    processing_mode: str = Field(..., description="Processing mode")
    settings: Dict[str, Any] = Field(..., description="Processing settings")
    status: str = Field(..., description="Job status")
    queue_position: Optional[int] = Field(None, description="Position in queue")
    priority: int = Field(..., description="Job priority")
    
    # Timestamps
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    
    # Progress tracking
    current_stage: Optional[str] = Field(None, description="Current processing stage")
    progress_percentage: float = Field(..., description="Overall progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    # Results and errors
    result_metadata: Optional[Dict[str, Any]] = Field(None, description="Processing results")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    retry_count: int = Field(..., description="Number of retry attempts")
    
    # Performance metrics
    processing_duration: Optional[float] = Field(None, description="Processing time in seconds")
    cpu_time: Optional[float] = Field(None, description="CPU time used")
    memory_peak: Optional[int] = Field(None, description="Peak memory usage in bytes")
    
    class Config:
        from_attributes = True


class JobProgressResponse(BaseModel):
    """Job progress response model."""
    
    id: UUID = Field(..., description="Progress entry ID")
    job_id: UUID = Field(..., description="Associated job ID")
    stage: str = Field(..., description="Processing stage")
    progress_percentage: float = Field(..., description="Stage progress percentage")
    message: Optional[str] = Field(None, description="Progress message")
    timestamp: datetime = Field(..., description="Progress timestamp")
    stage_started_at: Optional[datetime] = Field(None, description="Stage start time")
    stage_duration: Optional[float] = Field(None, description="Stage duration in seconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    warnings: Optional[Dict[str, Any]] = Field(None, description="Stage warnings")
    
    class Config:
        from_attributes = True


class ProcessingJobListResponse(BaseModel):
    """Processing job list response model."""
    
    jobs: List[ProcessingJobResponse] = Field(..., description="List of processing jobs")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class ProcessingJobDetailResponse(BaseModel):
    """Detailed processing job response with progress history."""
    
    job: ProcessingJobResponse = Field(..., description="Job information")
    progress_history: List[JobProgressResponse] = Field(..., description="Progress history")
    input_file: Optional[Dict[str, Any]] = Field(None, description="Input file information")
    reference_file: Optional[Dict[str, Any]] = Field(None, description="Reference file information")
    output_file: Optional[Dict[str, Any]] = Field(None, description="Output file information")


class ProcessingStatsResponse(BaseModel):
    """Processing statistics response."""
    
    total_jobs: int = Field(..., description="Total number of jobs")
    jobs_by_status: Dict[str, int] = Field(..., description="Job count by status")
    jobs_by_mode: Dict[str, int] = Field(..., description="Job count by processing mode")
    average_processing_time: float = Field(..., description="Average processing time in seconds")
    queue_length: int = Field(..., description="Current queue length")
    active_workers: int = Field(..., description="Number of active workers")
    
    # Recent activity (last 24 hours)
    jobs_completed_24h: int = Field(..., description="Jobs completed in last 24 hours")
    jobs_failed_24h: int = Field(..., description="Jobs failed in last 24 hours")
    average_wait_time: float = Field(..., description="Average queue wait time in seconds")


class ProcessingModeInfo(BaseModel):
    """Processing mode information."""
    
    mode: str = Field(..., description="Processing mode name")
    display_name: str = Field(..., description="Human-readable mode name")
    description: str = Field(..., description="Mode description")
    requires_reference: bool = Field(..., description="Whether mode requires reference file")
    estimated_duration: float = Field(..., description="Estimated processing duration in seconds")
    settings_schema: Dict[str, Any] = Field(..., description="JSON schema for settings")


class ProcessingModesResponse(BaseModel):
    """Available processing modes response."""
    
    modes: List[ProcessingModeInfo] = Field(..., description="Available processing modes")
    default_mode: str = Field(..., description="Default processing mode")


class QueueStatusResponse(BaseModel):
    """Processing queue status response."""
    
    total_queued: int = Field(..., description="Total jobs in queue")
    by_queue: Dict[str, int] = Field(..., description="Jobs by queue name")
    by_priority: Dict[str, int] = Field(..., description="Jobs by priority level")
    estimated_wait_time: float = Field(..., description="Estimated wait time in seconds")
    active_workers: int = Field(..., description="Number of active workers")
    worker_capacity: int = Field(..., description="Total worker capacity")


# Type aliases for API responses
ProcessingJobAPIResponse = APIResponse[ProcessingJobResponse]
ProcessingJobListAPIResponse = APIResponse[ProcessingJobListResponse]
ProcessingJobDetailAPIResponse = APIResponse[ProcessingJobDetailResponse]
JobProgressAPIResponse = APIResponse[JobProgressResponse]
ProcessingStatsAPIResponse = APIResponse[ProcessingStatsResponse]
ProcessingModesAPIResponse = APIResponse[ProcessingModesResponse]
QueueStatusAPIResponse = APIResponse[QueueStatusResponse]