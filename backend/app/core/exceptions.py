"""
Custom exceptions for Enhanced Matchering API.

Provides type-safe error handling with proper API response formatting.
"""

from datetime import datetime
from typing import Optional, Any, Dict
import uuid


class MatcheringException(Exception):
    """Base exception class for all Matchering API errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.error_id = str(uuid.uuid4())


class ValidationError(MatcheringException):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ) -> None:
        details = {"field": field, "value": value} if field else {}
        super().__init__(message, "VALIDATION_ERROR", details, **kwargs)


class AudioFileError(ValidationError):
    """Raised when audio file validation or processing fails."""
    
    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        file_size: Optional[int] = None,
        **kwargs
    ) -> None:
        details = {"filename": filename, "file_size": file_size}
        super().__init__(message, details=details, **kwargs)


class ProcessingError(MatcheringException):
    """Raised when audio processing fails."""
    
    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {"job_id": job_id, "stage": stage}
        super().__init__(message, "PROCESSING_ERROR", details, **kwargs)


class JobNotFoundError(MatcheringException):
    """Raised when a processing job is not found."""
    
    def __init__(self, job_id: str, **kwargs) -> None:
        message = f"Processing job not found: {job_id}"
        details = {"job_id": job_id}
        super().__init__(message, "JOB_NOT_FOUND", details, **kwargs)


class JobStateError(MatcheringException):
    """Raised when a job operation is invalid for current state."""
    
    def __init__(
        self,
        message: str,
        job_id: str,
        current_state: str,
        expected_state: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {
            "job_id": job_id,
            "current_state": current_state,
            "expected_state": expected_state
        }
        super().__init__(message, "JOB_STATE_ERROR", details, **kwargs)


class StorageError(MatcheringException):
    """Raised when file storage operations fail."""
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {"file_path": file_path, "operation": operation}
        super().__init__(message, "STORAGE_ERROR", details, **kwargs)


class DatabaseError(MatcheringException):
    """Raised when database operations fail."""
    
    def __init__(
        self,
        message: str,
        table: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        details = {"table": table, "operation": operation}
        super().__init__(message, "DATABASE_ERROR", details, **kwargs)


class ExternalServiceError(MatcheringException):
    """Raised when external service calls fail."""
    
    def __init__(
        self,
        message: str,
        service: str,
        status_code: Optional[int] = None,
        **kwargs
    ) -> None:
        details = {"service": service, "status_code": status_code}
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details, **kwargs)


class RateLimitError(MatcheringException):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs
    ) -> None:
        details = {"retry_after": retry_after}
        super().__init__(message, "RATE_LIMIT_ERROR", details, **kwargs)