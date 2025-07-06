"""
Enterprise-grade logging system for Matchering AI Enhancement Project.

Provides structured logging with correlation IDs, request tracking,
performance metrics, and comprehensive debugging capabilities.
"""

import json
import time
import uuid
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

import structlog
from structlog import configure, get_logger
from structlog.processors import JSONRenderer, TimeStamper, add_log_level, StackInfoRenderer


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Event type enumeration for categorizing log events."""
    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    AUDIO_UPLOAD = "audio_upload"
    PROCESSING_START = "processing_start"
    PROCESSING_END = "processing_end"
    AI_PREDICTION = "ai_prediction"
    MATCHERING_CONFIG = "matchering_config"
    MATCHERING_PROCESSING = "matchering_processing"
    QUALITY_METRICS = "quality_metrics"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"


@dataclass
class RequestContext:
    """Request context for correlation and tracking."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "client_ip": self.client_ip,
            "user_agent": self.user_agent,
            "endpoint": self.endpoint,
            "method": self.method,
            "start_time": self.start_time
        }


@dataclass
class ProcessingContext:
    """Processing context for tracking audio processing workflows."""
    job_id: str
    audio_file: str
    processing_mode: str
    user_settings: Dict[str, Any]
    start_time: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "job_id": self.job_id,
            "audio_file": self.audio_file,
            "processing_mode": self.processing_mode,
            "user_settings": self.user_settings,
            "start_time": self.start_time
        }


class EnterpriseLogger:
    """Enterprise-grade logger with structured logging and correlation tracking."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(EnterpriseLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        
        # Create log directories first
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self._setup_logging()
        self._request_contexts = threading.local()
        self._processing_contexts = threading.local()
        
        # Application logger
        self.logger = get_logger("matchering.enterprise")
        
        # Specialized loggers
        self.request_logger = get_logger("matchering.requests")
        self.processing_logger = get_logger("matchering.processing")
        self.quality_logger = get_logger("matchering.quality")
        self.performance_logger = get_logger("matchering.performance")
        self.error_logger = get_logger("matchering.errors")
        
    def _setup_logging(self):
        """Setup structured logging configuration."""
        
        # Configure structlog
        configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                TimeStamper(fmt="iso"),
                StackInfoRenderer(),
                structlog.processors.format_exc_info,
                JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Setup file handlers
        self._setup_file_handlers()
    
    def _setup_file_handlers(self):
        """Setup file handlers for different log types."""
        
        # Main application log
        app_handler = logging.FileHandler(self.log_dir / "application.log")
        app_handler.setLevel(logging.INFO)
        
        # Request/response log
        request_handler = logging.FileHandler(self.log_dir / "requests.log")
        request_handler.setLevel(logging.INFO)
        
        # Processing log 
        processing_handler = logging.FileHandler(self.log_dir / "processing.log")
        processing_handler.setLevel(logging.INFO)
        
        # Quality assessment log
        quality_handler = logging.FileHandler(self.log_dir / "quality.log")
        quality_handler.setLevel(logging.INFO)
        
        # Performance metrics log
        performance_handler = logging.FileHandler(self.log_dir / "performance.log")
        performance_handler.setLevel(logging.INFO)
        
        # Error log
        error_handler = logging.FileHandler(self.log_dir / "errors.log")
        error_handler.setLevel(logging.WARNING)
        
        # Add handlers to loggers
        logging.getLogger("matchering.enterprise").addHandler(app_handler)
        logging.getLogger("matchering.requests").addHandler(request_handler)
        logging.getLogger("matchering.processing").addHandler(processing_handler)
        logging.getLogger("matchering.quality").addHandler(quality_handler)
        logging.getLogger("matchering.performance").addHandler(performance_handler)
        logging.getLogger("matchering.errors").addHandler(error_handler)
    
    @contextmanager
    def request_context(self, request_data: Dict[str, Any]):
        """Context manager for request tracking."""
        
        context = RequestContext(
            user_id=request_data.get("user_id"),
            session_id=request_data.get("session_id"),
            client_ip=request_data.get("client_ip"),
            user_agent=request_data.get("user_agent"),
            endpoint=request_data.get("endpoint"),
            method=request_data.get("method")
        )
        
        self._request_contexts.current = context
        
        # Log request start
        self.log_request_start(context, request_data)
        
        try:
            yield context
        except Exception as e:
            self.log_error("Request failed", error=str(e), context=context.to_dict())
            raise
        finally:
            # Log request end
            self.log_request_end(context)
            self._request_contexts.current = None

    @asynccontextmanager
    async def async_request_context(self, request_data: Dict[str, Any]):
        """
        Async context manager for request tracking.
        
        This method provides an async version of request_context for use in
        async contexts like FastAPI middleware. It provides the same functionality
        as the synchronous version but is compatible with async/await syntax.
        
        Args:
            request_data: Dictionary containing request information (endpoint, method, etc.)
            
        Yields:
            RequestContext: The context object for the current request
        """
        
        context = RequestContext(
            user_id=request_data.get("user_id"),
            session_id=request_data.get("session_id"),
            client_ip=request_data.get("client_ip"),
            user_agent=request_data.get("user_agent"),
            endpoint=request_data.get("endpoint"),
            method=request_data.get("method")
        )
        
        self._request_contexts.current = context
        
        # Log request start
        self.log_request_start(context, request_data)
        
        try:
            yield context
        except Exception as e:
            self.log_error("Request failed", error=str(e), context=context.to_dict())
            raise
        finally:
            # Log request end
            self.log_request_end(context)
            self._request_contexts.current = None
    
    @contextmanager  
    def processing_context(self, job_id: str, audio_file: str, 
                          processing_mode: str, user_settings: Dict[str, Any]):
        """Context manager for processing tracking."""
        
        context = ProcessingContext(
            job_id=job_id,
            audio_file=audio_file,
            processing_mode=processing_mode,
            user_settings=user_settings
        )
        
        self._processing_contexts.current = context
        
        # Log processing start
        self.log_processing_start(context)
        
        try:
            yield context
        except Exception as e:
            self.log_error("Processing failed", error=str(e), context=context.to_dict())
            raise
        finally:
            # Log processing end
            self.log_processing_end(context)
            self._processing_contexts.current = None
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Get base context for all logs."""
        base = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "matchering-ai",
            "version": "2025.07.01"
        }
        
        # Add request context if available
        if hasattr(self._request_contexts, 'current') and self._request_contexts.current:
            base.update(self._request_contexts.current.to_dict())
        
        # Add processing context if available
        if hasattr(self._processing_contexts, 'current') and self._processing_contexts.current:
            base.update(self._processing_contexts.current.to_dict())
        
        return base
    
    def _merge_log_context(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge log data with base context without duplicating keys."""
        base_context = self._get_base_context()
        
        # Remove duplicate keys from base_context
        merged_context = {k: v for k, v in base_context.items() if k not in log_data}
        merged_context.update(log_data)
        
        return merged_context
    
    def log_request_start(self, context: RequestContext, request_data: Dict[str, Any]):
        """Log request start."""
        # Merge contexts without duplicating keys
        base_context = self._get_base_context()
        context_dict = context.to_dict()
        
        # Remove duplicate keys from base_context
        merged_context = {k: v for k, v in base_context.items() if k not in context_dict}
        merged_context.update(context_dict)
        
        self.request_logger.info(
            "Request started",
            event_type=EventType.REQUEST_START.value,
            request_data=request_data,
            **merged_context
        )
    
    def log_request_end(self, context: RequestContext):
        """Log request end."""
        duration = time.time() - context.start_time
        
        # Merge contexts without duplicating keys
        base_context = self._get_base_context()
        context_dict = context.to_dict()
        
        # Remove duplicate keys from base_context
        merged_context = {k: v for k, v in base_context.items() if k not in context_dict}
        merged_context.update(context_dict)
        
        self.request_logger.info(
            "Request completed",
            event_type=EventType.REQUEST_END.value,
            duration_ms=duration * 1000,
            **merged_context
        )
    
    def log_audio_upload(self, filename: str, file_size: int, mime_type: str, 
                        checksum: str, audio_metadata: Dict[str, Any]):
        """Log audio file upload."""
        log_data = {
            "filename": filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "checksum": checksum,
            "audio_metadata": audio_metadata
        }
        
        self.processing_logger.info(
            "Audio file uploaded",
            event_type=EventType.AUDIO_UPLOAD.value,
            **self._merge_log_context(log_data)
        )
    
    def log_processing_start(self, context: ProcessingContext):
        """Log processing start."""
        # Merge contexts without duplicating keys
        base_context = self._get_base_context()
        context_dict = context.to_dict()
        
        # Remove duplicate keys from base_context
        merged_context = {k: v for k, v in base_context.items() if k not in context_dict}
        merged_context.update(context_dict)
        
        self.processing_logger.info(
            "Audio processing started",
            event_type=EventType.PROCESSING_START.value,
            **merged_context
        )
    
    def log_processing_end(self, context: ProcessingContext, 
                          output_file: str = None, output_size: int = None):
        """Log processing end."""
        duration = time.time() - context.start_time
        
        # Merge contexts without duplicating keys
        base_context = self._get_base_context()
        context_dict = context.to_dict()
        
        # Remove duplicate keys from base_context
        merged_context = {k: v for k, v in base_context.items() if k not in context_dict}
        merged_context.update(context_dict)
        
        self.processing_logger.info(
            "Audio processing completed",
            event_type=EventType.PROCESSING_END.value,
            duration_ms=duration * 1000,
            output_file=output_file,
            output_size=output_size,
            **merged_context
        )
    
    def log_user_settings(self, settings: Dict[str, Any], settings_source: str = "frontend"):
        """Log user settings and preferences."""
        # Merge contexts without duplicating keys
        base_context = self._get_base_context()
        log_data = {
            "user_settings": settings,
            "settings_source": settings_source,
            "settings_validation": {
                "intensity_level": settings.get("intensity_level", "not_set"),
                "eq_style": settings.get("eq_style", "not_set"), 
                "target_loudness_lufs": settings.get("target_loudness_lufs", "not_set"),
                "preserve_dynamics": settings.get("preserve_dynamics", "not_set"),
                "processing_mode": settings.get("processing_mode", "not_set")
            }
        }
        
        # Remove duplicate keys from base_context
        merged_context = {k: v for k, v in base_context.items() if k not in log_data}
        merged_context.update(log_data)
        
        self.logger.info(
            "User settings captured",
            event_type=EventType.USER_ACTION.value,
            **merged_context
        )
    
    def log_ai_prediction(self, model_used: str, predicted_parameters: Dict[str, Any],
                         confidence: float, audio_characteristics: Dict[str, Any]):
        """Log AI model predictions."""
        
        # Analyze EQ curve
        eq_curve = predicted_parameters.get("eq_curve", [])
        eq_analysis = {
            "eq_curve_length": len(eq_curve),
            "eq_curve_is_flat": all(x == 0.0 for x in eq_curve) if eq_curve else True,
            "eq_curve_min": min(eq_curve) if eq_curve else 0.0,
            "eq_curve_max": max(eq_curve) if eq_curve else 0.0,
            "eq_curve_average": sum(eq_curve) / len(eq_curve) if eq_curve else 0.0
        }
        
        log_data = {
            "model_used": model_used,
            "predicted_parameters": predicted_parameters,
            "confidence": confidence,
            "audio_characteristics": audio_characteristics,
            "eq_analysis": eq_analysis,
            "parameter_analysis": {
                "compression_ratio": predicted_parameters.get("compression_ratio"),
                "limiting_threshold": predicted_parameters.get("limiting_threshold"),
                "limiting_ceiling": predicted_parameters.get("limiting_ceiling"),
                "predicted_genre": predicted_parameters.get("predicted_genre")
            }
        }
        
        self.processing_logger.info(
            "AI prediction completed",
            event_type=EventType.AI_PREDICTION.value,
            **self._merge_log_context(log_data)
        )
    
    def log_matchering_config(self, config: Dict[str, Any], user_settings: Dict[str, Any],
                             config_source: str = "ai_guided"):
        """Log Matchering configuration."""
        log_data = {
            "matchering_config": config,
            "user_settings_applied": user_settings,
            "config_source": config_source,
            "config_analysis": {
                "loudness_max_peak": config.get("loudness_max_peak"),
                "limiter_max_amplification_db": config.get("limiter_max_amplification_db"),
                "limiter_attack_coefficient": config.get("limiter_attack_coefficient"),
                "preserve_dynamics": config.get("preserve_dynamics")
            }
        }
        
        self.processing_logger.info(
            "Matchering configuration created",
            event_type=EventType.MATCHERING_CONFIG.value,
            **self._merge_log_context(log_data)
        )
    
    def log_quality_metrics(self, original_metrics: Dict[str, Any], 
                           processed_metrics: Dict[str, Any],
                           improvements: Dict[str, Any],
                           metrics_source: str = "calculated"):
        """Log quality metrics and improvements."""
        log_data = {
            "original_metrics": original_metrics,
            "processed_metrics": processed_metrics,
            "improvements": improvements,
            "metrics_source": metrics_source,
            "quality_analysis": {
                "lufs_improvement": improvements.get("lufs_improvement"),
                "peak_level_change": improvements.get("peak_level_change"),
                "dynamic_range_change": improvements.get("dynamic_range_change"),
                "overall_improvement_score": improvements.get("overall_score")
            }
        }
        
        self.quality_logger.info(
            "Quality metrics calculated",
            event_type=EventType.QUALITY_METRICS.value,
            **self._merge_log_context(log_data)
        )
    
    def log_performance_metric(self, metric_name: str, value: float, 
                              unit: str = "ms", tags: Dict[str, Any] = None):
        """Log performance metrics."""
        log_data = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "tags": tags or {}
        }
        
        self.performance_logger.info(
            "Performance metric recorded",
            event_type=EventType.PERFORMANCE_METRIC.value,
            **self._merge_log_context(log_data)
        )
    
    def log_error(self, message: str, error: str = None, 
                 error_type: str = None, context: Dict[str, Any] = None):
        """Log errors with full context."""
        log_data = {
            "error": error,
            "error_type": error_type,
            "error_context": context or {}
        }
        
        self.error_logger.error(
            message,
            event_type=EventType.ERROR_OCCURRED.value,
            **self._merge_log_context(log_data)
        )
    
    def log_user_action(self, action: str, details: Dict[str, Any]):
        """Log user actions for UX analysis."""
        log_data = {
            "action": action,
            "action_details": details
        }
        
        self.logger.info(
            f"User action: {action}",
            event_type=EventType.USER_ACTION.value,
            **self._merge_log_context(log_data)
        )
    
    def get_request_id(self) -> Optional[str]:
        """Get current request ID."""
        if hasattr(self._request_contexts, 'current') and self._request_contexts.current:
            return self._request_contexts.current.request_id
        return None
    
    def get_job_id(self) -> Optional[str]:
        """Get current job ID."""
        if hasattr(self._processing_contexts, 'current') and self._processing_contexts.current:
            return self._processing_contexts.current.job_id
        return None


# Global logger instance
enterprise_logger = EnterpriseLogger()


# Convenience functions
def log_request_start(request_data: Dict[str, Any]):
    """Convenience function for request start logging."""
    return enterprise_logger.request_context(request_data)

def log_user_settings(settings: Dict[str, Any], source: str = "frontend"):
    """Convenience function for user settings logging."""
    enterprise_logger.log_user_settings(settings, source)

def log_ai_prediction(model_used: str, predicted_parameters: Dict[str, Any], confidence: float, 
                     audio_characteristics: Dict[str, Any]):
    """Convenience function for AI prediction logging."""
    enterprise_logger.log_ai_prediction(model_used, predicted_parameters, confidence, audio_characteristics)

def log_matchering_config(config: Dict[str, Any], user_settings: Dict[str, Any]):
    """Convenience function for Matchering config logging."""
    enterprise_logger.log_matchering_config(config, user_settings)

def log_quality_metrics(original: Dict[str, Any], processed: Dict[str, Any], 
                       improvements: Dict[str, Any]):
    """Convenience function for quality metrics logging."""
    enterprise_logger.log_quality_metrics(original, processed, improvements)

def log_performance(metric: str, value: float, unit: str = "ms", tags: Dict[str, Any] = None):
    """Convenience function for performance logging."""
    enterprise_logger.log_performance_metric(metric, value, unit, tags)

def log_error(message: str, error: str = None, error_type: str = None, 
             context: Dict[str, Any] = None):
    """Convenience function for error logging."""
    enterprise_logger.log_error(message, error, error_type, context)

def log_user_action(action: str, details: Dict[str, Any]):
    """Convenience function for user action logging."""
    enterprise_logger.log_user_action(action, details)