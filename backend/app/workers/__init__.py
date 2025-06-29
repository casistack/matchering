"""
Celery workers for Enhanced Matchering API.

This package contains all Celery tasks for audio processing, file management,
and maintenance operations.
"""

from app.core.celery_app import celery_app

__all__ = ["celery_app"]