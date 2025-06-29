"""
Common Pydantic schemas for Enhanced Matchering API.

Contains base response models and common data structures.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from uuid import UUID

T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Base API response model."""
    
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if request failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    error_id: Optional[str] = Field(None, description="Unique error identifier")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of items to return")


class PaginationInfo(BaseModel):
    """Pagination information in responses."""
    
    total: int = Field(..., ge=0, description="Total number of items")
    skip: int = Field(..., ge=0, description="Number of items skipped")
    limit: int = Field(..., ge=1, description="Maximum items returned")
    has_more: bool = Field(..., description="Whether there are more items available")


class HealthStatus(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="API version")
    database: bool = Field(..., description="Database connectivity status")
    celery: bool = Field(..., description="Celery worker availability")
    redis: bool = Field(..., description="Redis broker connectivity")


class FileUploadStatus(BaseModel):
    """File upload status model."""
    
    file_id: UUID = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Upload status")
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Upload progress")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if upload failed")


class TaskStatus(BaseModel):
    """Background task status model."""
    
    task_id: str = Field(..., description="Celery task identifier")
    status: str = Field(..., description="Task status")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Task progress percentage")
    message: Optional[str] = Field(None, description="Current task message")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result if completed")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_at: datetime = Field(..., description="Task creation time")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")