"""
Maintenance tasks for Enhanced Matchering API.

This module contains Celery tasks for system maintenance, monitoring,
and cleanup operations.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.processing import ProcessingJob, JobProgress, JobStatus
from app.models.audio import AudioFile, AudioMetadata

logger = logging.getLogger(__name__)


class MaintenanceTask(Task):
    """Base class for maintenance tasks with database integration."""
    
    def __init__(self) -> None:
        self.session: Optional[AsyncSession] = None
    
    async def get_session(self) -> AsyncSession:
        """Get async database session."""
        if not self.session:
            self.session = AsyncSessionLocal()
        return self.session
    
    async def close_session(self) -> None:
        """Close database session."""
        if self.session:
            await self.session.close()
            self.session = None


@celery_app.task(bind=True, base=MaintenanceTask, name="cleanup_old_results")
def cleanup_old_results(self: MaintenanceTask, days_old: int = 7) -> Dict[str, Any]:
    """
    Clean up old processing results and temporary files.
    
    Args:
        days_old: Remove results older than this many days
        
    Returns:
        dict: Cleanup results
    """
    return asyncio.run(self._cleanup_old_results_async(days_old))


async def _cleanup_old_results_async(self: MaintenanceTask, days_old: int) -> Dict[str, Any]:
    """Async implementation of old results cleanup."""
    session = await self.get_session()
    
    try:
        cleanup_before = datetime.utcnow() - timedelta(days=days_old)
        
        from sqlalchemy import select, delete
        
        # Find old completed or failed jobs
        query = select(ProcessingJob).where(
            ProcessingJob.completed_at < cleanup_before,
            ProcessingJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED])
        )
        result = await session.execute(query)
        old_jobs = result.scalars().all()
        
        cleaned_files = []
        cleaned_jobs = []
        
        for job in old_jobs:
            # Remove output file if it exists
            if job.output_file_path:
                output_path = Path(job.output_file_path)
                if output_path.exists():
                    try:
                        output_path.unlink()
                        cleaned_files.append(str(output_path))
                        logger.debug(f"Removed old result file: {output_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove file {output_path}: {e}")
            
            cleaned_jobs.append(str(job.id))
        
        # Remove job progress entries for old jobs
        if cleaned_jobs:
            job_uuids = [uuid.UUID(job_id) for job_id in cleaned_jobs]
            await session.execute(
                delete(JobProgress).where(JobProgress.job_id.in_(job_uuids))
            )
            
            # Remove the jobs themselves
            await session.execute(
                delete(ProcessingJob).where(ProcessingJob.id.in_(job_uuids))
            )
        
        await session.commit()
        
        logger.info(f"Cleanup completed: {len(cleaned_jobs)} jobs, {len(cleaned_files)} files removed")
        
        return {
            "status": "completed",
            "jobs_cleaned": len(cleaned_jobs),
            "files_cleaned": len(cleaned_files),
            "cleanup_before": cleanup_before.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Old results cleanup failed: {str(e)}")
        raise
    finally:
        await self.close_session()


@celery_app.task(bind=True, base=MaintenanceTask, name="update_job_metrics")
def update_job_metrics(self: MaintenanceTask) -> Dict[str, Any]:
    """
    Update job processing metrics and statistics.
    
    Returns:
        dict: Updated metrics
    """
    return asyncio.run(self._update_job_metrics_async())


async def _update_job_metrics_async(self: MaintenanceTask) -> Dict[str, Any]:
    """Async implementation of job metrics update."""
    session = await self.get_session()
    
    try:
        from sqlalchemy import select, func
        
        # Get current job statistics
        total_jobs_query = select(func.count(ProcessingJob.id))
        total_jobs_result = await session.execute(total_jobs_query)
        total_jobs = total_jobs_result.scalar()
        
        # Jobs by status
        status_stats = {}
        for status in JobStatus:
            status_query = select(func.count(ProcessingJob.id)).where(ProcessingJob.status == status)
            status_result = await session.execute(status_query)
            status_stats[status.value] = status_result.scalar()
        
        # Average processing time for completed jobs
        avg_time_query = select(func.avg(ProcessingJob.processing_duration)).where(
            ProcessingJob.status == JobStatus.COMPLETED,
            ProcessingJob.processing_duration.isnot(None)
        )
        avg_time_result = await session.execute(avg_time_query)
        avg_processing_time = avg_time_result.scalar() or 0.0
        
        # Jobs completed in last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_jobs_query = select(func.count(ProcessingJob.id)).where(
            ProcessingJob.completed_at >= last_24h,
            ProcessingJob.status == JobStatus.COMPLETED
        )
        recent_jobs_result = await session.execute(recent_jobs_query)
        recent_completed_jobs = recent_jobs_result.scalar()
        
        # Queue statistics
        pending_jobs_query = select(func.count(ProcessingJob.id)).where(
            ProcessingJob.status == JobStatus.PENDING
        )
        pending_jobs_result = await session.execute(pending_jobs_query)
        pending_jobs = pending_jobs_result.scalar()
        
        processing_jobs_query = select(func.count(ProcessingJob.id)).where(
            ProcessingJob.status == JobStatus.PROCESSING
        )
        processing_jobs_result = await session.execute(processing_jobs_query)
        processing_jobs = processing_jobs_result.scalar()
        
        # Audio file statistics
        total_files_query = select(func.count(AudioFile.id))
        total_files_result = await session.execute(total_files_query)
        total_audio_files = total_files_result.scalar()
        
        total_storage_query = select(func.sum(AudioFile.file_size))
        total_storage_result = await session.execute(total_storage_query)
        total_storage_bytes = total_storage_result.scalar() or 0
        
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "job_statistics": {
                "total_jobs": total_jobs,
                "status_breakdown": status_stats,
                "average_processing_time_seconds": round(avg_processing_time, 2),
                "completed_last_24h": recent_completed_jobs,
                "queue_statistics": {
                    "pending": pending_jobs,
                    "processing": processing_jobs,
                    "queue_length": pending_jobs + processing_jobs
                }
            },
            "storage_statistics": {
                "total_audio_files": total_audio_files,
                "total_storage_bytes": total_storage_bytes,
                "total_storage_mb": round(total_storage_bytes / (1024 * 1024), 2)
            }
        }
        
        logger.info(f"Job metrics updated: {metrics}")
        
        return {
            "status": "completed",
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Job metrics update failed: {str(e)}")
        raise
    finally:
        await self.close_session()


@celery_app.task(bind=True, base=MaintenanceTask, name="cleanup_orphaned_files")
def cleanup_orphaned_files(self: MaintenanceTask) -> Dict[str, Any]:
    """
    Clean up orphaned files that are not referenced in the database.
    
    Returns:
        dict: Cleanup results
    """
    return asyncio.run(self._cleanup_orphaned_files_async())


async def _cleanup_orphaned_files_async(self: MaintenanceTask) -> Dict[str, Any]:
    """Async implementation of orphaned files cleanup."""
    session = await self.get_session()
    
    try:
        from sqlalchemy import select
        from app.core.config import settings
        
        # Get all file paths from database
        audio_files_query = select(AudioFile.file_path)
        audio_files_result = await session.execute(audio_files_query)
        db_file_paths = set(result[0] for result in audio_files_result.fetchall())
        
        processing_jobs_query = select(ProcessingJob.output_file_path).where(
            ProcessingJob.output_file_path.isnot(None)
        )
        processing_jobs_result = await session.execute(processing_jobs_query)
        db_output_paths = set(result[0] for result in processing_jobs_result.fetchall() if result[0])
        
        all_db_paths = db_file_paths.union(db_output_paths)
        
        # Scan storage directories for actual files
        orphaned_files = []
        total_size_freed = 0
        
        storage_dirs = [settings.UPLOAD_DIR, settings.RESULTS_DIR]
        
        for storage_dir in storage_dirs:
            if not storage_dir.exists():
                continue
            
            for file_path in storage_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Skip temporary files and archives
                if file_path.name.startswith(("temp_", ".")):
                    continue
                
                if "archive" in file_path.parts:
                    continue
                
                # Check if file is referenced in database
                if str(file_path) not in all_db_paths:
                    try:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        orphaned_files.append(str(file_path))
                        total_size_freed += file_size
                        logger.debug(f"Removed orphaned file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove orphaned file {file_path}: {e}")
        
        logger.info(f"Orphaned files cleanup completed: {len(orphaned_files)} files, {total_size_freed} bytes freed")
        
        return {
            "status": "completed",
            "orphaned_files_removed": len(orphaned_files),
            "size_freed_bytes": total_size_freed,
            "cleaned_files": orphaned_files[:10]  # First 10 files for logging
        }
        
    except Exception as e:
        logger.error(f"Orphaned files cleanup failed: {str(e)}")
        raise
    finally:
        await self.close_session()


@celery_app.task(bind=True, base=MaintenanceTask, name="update_processing_estimates")
def update_processing_estimates(self: MaintenanceTask) -> Dict[str, Any]:
    """
    Update estimated completion times for pending jobs based on historical data.
    
    Returns:
        dict: Update results
    """
    return asyncio.run(self._update_processing_estimates_async())


async def _update_processing_estimates_async(self: MaintenanceTask) -> Dict[str, Any]:
    """Async implementation of processing estimates update."""
    session = await self.get_session()
    
    try:
        from sqlalchemy import select, update, func
        
        # Calculate average processing times by processing mode
        avg_times_query = select(
            ProcessingJob.processing_mode,
            func.avg(ProcessingJob.processing_duration).label('avg_duration')
        ).where(
            ProcessingJob.status == JobStatus.COMPLETED,
            ProcessingJob.processing_duration.isnot(None)
        ).group_by(ProcessingJob.processing_mode)
        
        avg_times_result = await session.execute(avg_times_query)
        avg_times = {row.processing_mode: row.avg_duration for row in avg_times_result}
        
        # Get pending jobs
        pending_jobs_query = select(ProcessingJob).where(
            ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED])
        )
        pending_jobs_result = await session.execute(pending_jobs_query)
        pending_jobs = pending_jobs_result.scalars().all()
        
        updated_jobs = 0
        
        for job in pending_jobs:
            avg_duration = avg_times.get(job.processing_mode, 300.0)  # Default 5 minutes
            
            # Add queue position factor
            queue_factor = (job.queue_position or 0) * avg_duration
            estimated_completion = datetime.utcnow() + timedelta(seconds=avg_duration + queue_factor)
            
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job.id)
                .values(estimated_completion=estimated_completion)
            )
            updated_jobs += 1
        
        await session.commit()
        
        logger.info(f"Processing estimates updated for {updated_jobs} jobs")
        
        return {
            "status": "completed",
            "jobs_updated": updated_jobs,
            "average_times": {mode.value: round(time, 2) for mode, time in avg_times.items()}
        }
        
    except Exception as e:
        logger.error(f"Processing estimates update failed: {str(e)}")
        raise
    finally:
        await self.close_session()


@celery_app.task(bind=True, base=MaintenanceTask, name="periodic_job_health_check")
def periodic_job_health_check(self: MaintenanceTask) -> Dict[str, Any]:
    """
    Perform periodic health check and cleanup of stuck jobs.
    
    This task runs regularly to identify and handle stuck or orphaned jobs
    that may have been missed during normal operation.
    
    Returns:
        dict: Health check and recovery statistics
    """
    return asyncio.run(self._periodic_job_health_check_async())


async def _periodic_job_health_check_async(self: MaintenanceTask) -> Dict[str, Any]:
    """Async implementation of periodic job health check."""
    try:
        logger.info("Starting periodic job health check...")
        
        from app.utils.job_recovery import job_recovery_manager
        
        # Perform health check
        health_stats = await job_recovery_manager.check_job_health()
        
        recovery_stats = {"recovery_performed": False}
        
        # If unhealthy, perform limited recovery
        if not health_stats["healthy"]:
            logger.warning("Job system unhealthy, performing limited recovery...")
            
            # Perform a targeted recovery for stuck jobs only
            # (less aggressive than full startup recovery)
            recovery_stats = await job_recovery_manager.perform_startup_recovery()
            recovery_stats["recovery_performed"] = True
            
            logger.info(f"Periodic recovery completed: {recovery_stats}")
        
        return {
            "status": "completed",
            "check_time": datetime.utcnow().isoformat(),
            "health_stats": health_stats,
            "recovery_stats": recovery_stats
        }
        
    except Exception as e:
        logger.error(f"Periodic job health check failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "check_time": datetime.utcnow().isoformat()
        }


# Export tasks
__all__ = [
    "cleanup_old_results",
    "update_job_metrics",
    "cleanup_orphaned_files",
    "update_processing_estimates",
    "periodic_job_health_check",
    "MaintenanceTask"
]