"""
Enterprise Job Recovery System for Enhanced Matchering API.

Handles orphaned processing jobs that may become stuck due to service restarts,
worker crashes, or other system interruptions. Implements enterprise-grade
recovery procedures to maintain system integrity.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.processing import ProcessingJob, JobStatus, ProcessingMode
from app.models.audio import AudioFile
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class JobRecoveryManager:
    """
    Enterprise job recovery manager for handling orphaned and stuck processing jobs.
    
    This class provides comprehensive recovery capabilities including:
    - Orphaned job detection and cleanup
    - Stuck job timeout handling
    - Service restart recovery procedures
    - Health check and monitoring
    """
    
    def __init__(self):
        self.recovery_timeout_minutes = 30  # Jobs stuck longer than this are considered orphaned
        self.startup_grace_period_minutes = 5  # Grace period for jobs created recently
        
    async def perform_startup_recovery(self) -> Dict[str, Any]:
        """
        Perform comprehensive job recovery on service startup.
        
        This method should be called when the backend service starts to clean up
        any jobs that may have been orphaned due to service restarts or crashes.
        
        Returns:
            Dict containing recovery statistics and actions taken
        """
        logger.info("Starting enterprise job recovery procedure...")
        
        session = AsyncSessionLocal()
        recovery_stats = {
            "orphaned_jobs_found": 0,
            "orphaned_jobs_failed": 0,
            "stuck_jobs_found": 0,
            "stuck_jobs_recovered": 0,
            "active_jobs_validated": 0,
            "celery_tasks_cleaned": 0,
            "recovery_duration_seconds": 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Find and handle orphaned jobs (PENDING/QUEUED/PROCESSING)
            orphaned_jobs = await self._find_orphaned_jobs(session)
            recovery_stats["orphaned_jobs_found"] = len(orphaned_jobs)
            
            for job in orphaned_jobs:
                await self._handle_orphaned_job(session, job)
                recovery_stats["orphaned_jobs_failed"] += 1
                logger.info(f"Marked orphaned job {job.id} as FAILED")
            
            # Step 2: Find stuck jobs (created but not progressing)
            stuck_jobs = await self._find_stuck_jobs(session)
            recovery_stats["stuck_jobs_found"] = len(stuck_jobs)
            
            for job in stuck_jobs:
                success = await self._recover_stuck_job(session, job)
                if success:
                    recovery_stats["stuck_jobs_recovered"] += 1
                else:
                    recovery_stats["orphaned_jobs_failed"] += 1
            
            # Step 3: Validate remaining active jobs
            active_jobs = await self._get_active_jobs(session)
            for job in active_jobs:
                await self._validate_active_job(session, job)
                recovery_stats["active_jobs_validated"] += 1
            
            # Step 4: Clean up orphaned Celery tasks
            cleaned_tasks = await self._cleanup_orphaned_celery_tasks()
            recovery_stats["celery_tasks_cleaned"] = cleaned_tasks
            
            await session.commit()
            
            recovery_stats["recovery_duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Job recovery completed successfully: {recovery_stats}")
            return recovery_stats
            
        except Exception as e:
            logger.error(f"Job recovery failed: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def _find_orphaned_jobs(self, session: AsyncSession) -> List[ProcessingJob]:
        """Find jobs that are likely orphaned due to service restarts."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.recovery_timeout_minutes)
        
        query = select(ProcessingJob).where(
            and_(
                ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING]),
                ProcessingJob.created_at < cutoff_time
            )
        ).order_by(ProcessingJob.created_at.asc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def _find_stuck_jobs(self, session: AsyncSession) -> List[ProcessingJob]:
        """Find jobs that appear to be stuck in processing."""
        # Jobs that have been processing for too long
        processing_cutoff = datetime.utcnow() - timedelta(minutes=self.recovery_timeout_minutes)
        
        query = select(ProcessingJob).where(
            and_(
                ProcessingJob.status == JobStatus.PROCESSING,
                or_(
                    ProcessingJob.started_at < processing_cutoff,
                    ProcessingJob.started_at.is_(None)  # Processing but no start time
                )
            )
        )
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def _get_active_jobs(self, session: AsyncSession) -> List[ProcessingJob]:
        """Get all currently active jobs for validation."""
        query = select(ProcessingJob).where(
            ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING])
        )
        
        result = await session.execute(query)
        return result.scalars().all()
    
    async def _handle_orphaned_job(self, session: AsyncSession, job: ProcessingJob) -> None:
        """Mark an orphaned job as failed with appropriate error information."""
        error_message = f"Job orphaned during service restart - stuck in {job.status.value} for over {self.recovery_timeout_minutes} minutes"
        
        await session.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job.id)
            .values(
                status=JobStatus.FAILED,
                error_message=error_message,
                error_code="JOB_ORPHANED_ON_RESTART",
                completed_at=datetime.utcnow()
            )
        )
        
        logger.warning(f"Orphaned job {job.id} (mode: {job.processing_mode.value}) marked as failed")
    
    async def _recover_stuck_job(self, session: AsyncSession, job: ProcessingJob) -> bool:
        """
        Attempt to recover a stuck job or mark it as failed.
        
        Returns:
            bool: True if job was recovered, False if marked as failed
        """
        # For now, we'll mark stuck jobs as failed
        # In the future, this could attempt to restart the job
        error_message = f"Job stuck in processing for over {self.recovery_timeout_minutes} minutes"
        
        await session.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job.id)
            .values(
                status=JobStatus.FAILED,
                error_message=error_message,
                error_code="JOB_PROCESSING_TIMEOUT",
                completed_at=datetime.utcnow()
            )
        )
        
        logger.warning(f"Stuck job {job.id} marked as failed due to timeout")
        return False
    
    async def _validate_active_job(self, session: AsyncSession, job: ProcessingJob) -> None:
        """Validate that an active job is in a consistent state."""
        # Check if the input file still exists and is eligible
        query = select(AudioFile).where(AudioFile.id == job.input_file_id)
        result = await session.execute(query)
        audio_file = result.scalar_one_or_none()
        
        if not audio_file:
            # Input file no longer exists
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job.id)
                .values(
                    status=JobStatus.FAILED,
                    error_message="Input file no longer exists",
                    error_code="INPUT_FILE_MISSING",
                    completed_at=datetime.utcnow()
                )
            )
            logger.warning(f"Job {job.id} failed - input file missing")
        elif not audio_file.processing_eligible:
            # File not eligible for processing
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job.id)
                .values(
                    status=JobStatus.FAILED,
                    error_message="Input file not eligible for processing",
                    error_code="FILE_NOT_ELIGIBLE",
                    completed_at=datetime.utcnow()
                )
            )
            logger.warning(f"Job {job.id} failed - file not eligible")
    
    async def _cleanup_orphaned_celery_tasks(self) -> int:
        """Clean up orphaned Celery tasks that may be stuck in queues."""
        try:
            # Purge tasks from all relevant queues
            queues_to_purge = ['audio_processing', 'audio_analysis', 'file_operations', 'matchering_default']
            total_purged = 0
            
            for queue_name in queues_to_purge:
                try:
                    purged = celery_app.control.purge()
                    if purged:
                        total_purged += sum(purged.values())
                        logger.info(f"Purged {sum(purged.values())} tasks from queue {queue_name}")
                except Exception as e:
                    logger.warning(f"Failed to purge queue {queue_name}: {e}")
            
            return total_purged
            
        except Exception as e:
            logger.error(f"Failed to cleanup Celery tasks: {e}")
            return 0
    
    async def check_job_health(self) -> Dict[str, Any]:
        """
        Perform a health check on the job processing system.
        
        Returns:
            Dict containing health status and metrics
        """
        session = AsyncSessionLocal()
        
        try:
            health_stats = {
                "healthy": True,
                "active_jobs": 0,
                "stuck_jobs": 0,
                "recent_failures": 0,
                "queue_health": {},
                "recommendations": []
            }
            
            # Count active jobs
            active_query = select(ProcessingJob).where(
                ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING])
            )
            active_result = await session.execute(active_query)
            health_stats["active_jobs"] = len(active_result.scalars().all())
            
            # Check for stuck jobs
            stuck_jobs = await self._find_stuck_jobs(session)
            health_stats["stuck_jobs"] = len(stuck_jobs)
            
            if health_stats["stuck_jobs"] > 0:
                health_stats["healthy"] = False
                health_stats["recommendations"].append("Run job recovery to clear stuck jobs")
            
            # Check recent failures
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            failure_query = select(ProcessingJob).where(
                and_(
                    ProcessingJob.status == JobStatus.FAILED,
                    ProcessingJob.completed_at >= recent_cutoff
                )
            )
            failure_result = await session.execute(failure_query)
            health_stats["recent_failures"] = len(failure_result.scalars().all())
            
            # Check Celery worker health
            try:
                active_workers = celery_app.control.inspect().active()
                if active_workers:
                    health_stats["queue_health"]["workers_online"] = len(active_workers)
                    health_stats["queue_health"]["active_tasks"] = sum(
                        len(tasks) for tasks in active_workers.values()
                    )
                else:
                    health_stats["healthy"] = False
                    health_stats["recommendations"].append("No Celery workers detected")
            except Exception as e:
                health_stats["queue_health"]["error"] = str(e)
                health_stats["recommendations"].append("Celery inspection failed")
            
            return health_stats
            
        finally:
            await session.close()


# Global job recovery manager instance
job_recovery_manager = JobRecoveryManager()


async def startup_job_recovery() -> Dict[str, Any]:
    """
    Convenience function to perform startup job recovery.
    
    This should be called during application startup.
    """
    return await job_recovery_manager.perform_startup_recovery()


async def health_check_jobs() -> Dict[str, Any]:
    """
    Convenience function to perform job health check.
    """
    return await job_recovery_manager.check_job_health()


# Export the main functions and manager
__all__ = [
    "JobRecoveryManager",
    "job_recovery_manager", 
    "startup_job_recovery",
    "health_check_jobs"
]