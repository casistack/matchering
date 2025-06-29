"""
Celery application configuration for Enhanced Matchering API.

This module sets up Celery for distributed task processing, including
audio processing tasks, job management, and progress tracking.
"""

from celery import Celery
from celery.signals import worker_init, worker_shutdown
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery application instance
celery_app = Celery("matchering_tasks")

# Configure Celery from application settings
celery_app.conf.update(
    # Broker and result backend configuration
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    
    # Task configuration
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,  # Results expire after 1 hour
    
    # Task routing and execution
    task_default_queue="matchering_default",
    task_routes={
        "app.workers.audio_tasks.*": {"queue": "audio_processing"},
        "app.workers.analysis_tasks.*": {"queue": "audio_analysis"},
        "app.workers.file_tasks.*": {"queue": "file_operations"},
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,  # Process one task at a time for memory management
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
    worker_disable_rate_limits=False,
    
    # Task execution configuration
    task_acks_late=True,  # Acknowledge tasks only after completion
    task_reject_on_worker_lost=True,  # Retry tasks if worker crashes
    task_compression="gzip",  # Compress large task payloads
    
    # Result backend configuration
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
        "retry_policy": {
            "timeout": 5.0
        }
    },
    
    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,       # 10 minutes hard limit
    
    # Beat scheduler configuration (for periodic tasks)
    beat_schedule={
        "cleanup_old_results": {
            "task": "app.workers.maintenance_tasks.cleanup_old_results",
            "schedule": 3600.0,  # Run every hour
        },
        "update_job_metrics": {
            "task": "app.workers.maintenance_tasks.update_job_metrics", 
            "schedule": 300.0,   # Run every 5 minutes
        },
    },
    timezone="UTC",
)

# Import task modules to register them with Celery
celery_app.autodiscover_tasks([
    "app.workers.audio_tasks",
    "app.workers.analysis_tasks", 
    "app.workers.file_tasks",
    "app.workers.maintenance_tasks"
], force=True)


@worker_init.connect
def worker_init_handler(sender: Any = None, **kwargs: Any) -> None:
    """Initialize worker process."""
    logger.info(f"Worker {sender} initialized")
    # Initialize any worker-specific resources here
    # e.g., audio processing libraries, ML models, etc.


@worker_shutdown.connect  
def worker_shutdown_handler(sender: Any = None, **kwargs: Any) -> None:
    """Clean up worker process resources."""
    logger.info(f"Worker {sender} shutting down")
    # Clean up any worker-specific resources here
    # e.g., close audio files, release ML models, etc.


def create_celery_app() -> Celery:
    """
    Create and configure Celery application.
    
    Returns:
        Celery: Configured Celery application instance
    """
    return celery_app


# Health check task for monitoring
@celery_app.task(name="health_check")
def health_check() -> dict[str, Any]:
    """
    Health check task for monitoring worker availability.
    
    Returns:
        dict: Health status information
    """
    import platform
    from datetime import datetime
    import os
    
    # Try to import psutil for advanced metrics, fallback to basic info
    try:
        import psutil
        worker_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
        }
    except ImportError:
        worker_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "process_id": os.getpid(),
        }
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "worker_info": worker_info
    }


# Export the configured Celery app
__all__ = ["celery_app", "create_celery_app", "health_check"]