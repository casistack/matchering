"""
Request handling utilities for Enhanced Matchering API.

Contains functions for request processing, response formatting, and client handling.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, TypeVar
from fastapi import Request
from app.schemas.common import APIResponse

T = TypeVar('T')


def generate_request_id() -> str:
    """
    Generate unique request identifier.
    
    Returns:
        str: Unique request ID
    """
    return str(uuid.uuid4())


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Client IP address
    """
    # Check for forwarded headers (reverse proxy setup)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP in case of multiple proxies
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


def create_api_response(
    data: Optional[T] = None,
    success: bool = True,
    error: Optional[str] = None,
    request_id: Optional[str] = None
) -> APIResponse[T]:
    """
    Create standardized API response.
    
    Args:
        data: Response data
        success: Whether request was successful
        error: Error message if request failed
        request_id: Request identifier
        
    Returns:
        APIResponse: Formatted API response
    """
    return APIResponse[T](
        success=success,
        data=data,
        error=error,
        timestamp=datetime.utcnow(),
        request_id=request_id or generate_request_id()
    )


def extract_user_agent(request: Request) -> str:
    """
    Extract user agent from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: User agent string
    """
    return request.headers.get("user-agent", "unknown")


def get_content_length(request: Request) -> Optional[int]:
    """
    Get content length from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[int]: Content length in bytes
    """
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            return int(content_length)
        except ValueError:
            return None
    return None


def is_multipart_request(request: Request) -> bool:
    """
    Check if request contains multipart form data.
    
    Args:
        request: FastAPI request object
        
    Returns:
        bool: True if request is multipart
    """
    content_type = request.headers.get("content-type", "")
    return content_type.startswith("multipart/form-data")


def extract_request_metadata(request: Request) -> Dict[str, Any]:
    """
    Extract comprehensive request metadata for logging.
    
    Args:
        request: FastAPI request object
        
    Returns:
        dict: Request metadata
    """
    return {
        "method": request.method,
        "url": str(request.url),
        "client_ip": get_client_ip(request),
        "user_agent": extract_user_agent(request),
        "content_type": request.headers.get("content-type"),
        "content_length": get_content_length(request),
        "is_multipart": is_multipart_request(request),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "timestamp": datetime.utcnow().isoformat()
    }


def create_error_response(
    error_message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> APIResponse[None]:
    """
    Create standardized error response.
    
    Args:
        error_message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details
        request_id: Request identifier
        
    Returns:
        APIResponse: Error response
    """
    error_data = {
        "message": error_message,
        "code": error_code,
        "details": details or {}
    }
    
    return create_api_response(
        data=None,
        success=False,
        error=error_data,
        request_id=request_id
    )


def create_pagination_response(
    items: list,
    total: int,
    skip: int,
    limit: int,
    request_id: Optional[str] = None
) -> APIResponse[Dict[str, Any]]:
    """
    Create paginated response.
    
    Args:
        items: List of items for current page
        total: Total number of items
        skip: Number of items skipped
        limit: Maximum items per page
        request_id: Request identifier
        
    Returns:
        APIResponse: Paginated response
    """
    has_more = (skip + len(items)) < total
    
    data = {
        "items": items,
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": has_more,
            "current_page": (skip // limit) + 1 if limit > 0 else 1,
            "total_pages": ((total - 1) // limit) + 1 if limit > 0 and total > 0 else 1
        }
    }
    
    return create_api_response(data=data, request_id=request_id)


def validate_request_size(request: Request, max_size: int) -> bool:
    """
    Validate request content length against maximum allowed size.
    
    Args:
        request: FastAPI request object
        max_size: Maximum allowed size in bytes
        
    Returns:
        bool: True if request size is valid
        
    Raises:
        ValueError: If request is too large
    """
    content_length = get_content_length(request)
    if content_length and content_length > max_size:
        raise ValueError(f"Request too large: {content_length} bytes (max: {max_size})")
    
    return True


def create_task_response(
    task_id: str,
    task_type: str,
    status: str = "pending",
    message: Optional[str] = None,
    request_id: Optional[str] = None
) -> APIResponse[Dict[str, Any]]:
    """
    Create response for background task initiation.
    
    Args:
        task_id: Celery task identifier
        task_type: Type of task (validation, analysis, processing)
        status: Initial task status
        message: Optional status message
        request_id: Request identifier
        
    Returns:
        APIResponse: Task response
    """
    data = {
        "task_id": task_id,
        "task_type": task_type,
        "status": status,
        "message": message,
        "created_at": datetime.utcnow().isoformat()
    }
    
    return create_api_response(data=data, request_id=request_id)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_duration(duration_seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        duration_seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if duration_seconds < 60:
        return f"{duration_seconds:.1f}s"
    elif duration_seconds < 3600:
        minutes = int(duration_seconds // 60)
        seconds = duration_seconds % 60
        return f"{minutes}m {seconds:.0f}s"
    else:
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"