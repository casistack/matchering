"""
Enterprise Logging Middleware for FastAPI
Captures all requests and responses with enterprise logging system.
"""

import time
import json
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.utils.enterprise_logger import enterprise_logger, log_error


class EnterpriseLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture all HTTP requests and responses with enterprise logging.
    
    This middleware ensures that ALL FastAPI validation errors (422) and other
    critical events are captured in the enterprise logging system, even when
    they occur before reaching endpoint code.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request through enterprise logging context."""
        start_time = time.time()
        
        # Extract request information
        request_data = {
            "endpoint": str(request.url.path),
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "content_type": request.headers.get("content-type", "unknown"),
            "content_length": request.headers.get("content-length", "0")
        }
        
        # Use proper enterprise logging context with async context manager
        async with enterprise_logger.async_request_context(request_data):
            try:
                # Process the request
                response = await call_next(request)
                
                # Calculate request duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log different response types
                await self._log_response(request_data, response, duration_ms)
                
                return response
                
            except Exception as e:
                # Log unhandled exceptions
                duration_ms = (time.time() - start_time) * 1000
                
                log_error(
                    "Unhandled exception in request processing",
                    error=str(e),
                    error_type=type(e).__name__,
                    context={
                        **request_data,
                        "duration_ms": duration_ms,
                        "exception_details": self._format_exception(e)
                    }
                )
                raise
    
    async def _log_response(self, request_data: Dict[str, Any], response: Response, duration_ms: float):
        """Log response based on status code."""
        
        # Base response context
        response_context = {
            **request_data,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "response_headers": dict(response.headers)
        }
        
        if response.status_code == 422:
            # Critical: Capture all 422 validation errors
            await self._log_validation_error(response_context, response)
            
        elif response.status_code >= 400:
            # Log other client/server errors
            log_error(
                f"HTTP {response.status_code} error response",
                error=f"Request failed with status {response.status_code}",
                error_type="HTTPError",
                context=response_context
            )
            
        elif response.status_code >= 200 and response.status_code < 300:
            # Log successful requests to enterprise logger
            enterprise_logger.logger.info(
                f"Request completed successfully",
                event_type="request_success",
                **response_context
            )
    
    async def _log_validation_error(self, context: Dict[str, Any], response: Response):
        """Log 422 validation errors with detailed information."""
        
        # Try to extract validation error details from response body
        error_details = "Validation failed"
        try:
            if hasattr(response, 'body'):
                # For JSONResponse, try to parse error details
                if isinstance(response, JSONResponse):
                    error_details = f"Validation error: {str(response.body)[:500]}"
        except Exception:
            pass
        
        log_error(
            "FastAPI validation error (422)",
            error=error_details,
            error_type="ValidationError", 
            context={
                **context,
                "validation_failure": True,
                "critical_error": True
            }
        )
        
        # Also log as a user action for tracking
        enterprise_logger.log_user_action(
            "validation_error_occurred",
            {
                "endpoint": context["endpoint"],
                "method": context["method"], 
                "status_code": 422,
                "error_type": "validation_failure",
                "duration_ms": context["duration_ms"]
            }
        )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _format_exception(self, exception: Exception) -> Dict[str, Any]:
        """Format exception for logging."""
        return {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "exception_args": list(exception.args) if exception.args else []
        }