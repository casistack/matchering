"""
Audio processing tasks for Enhanced Matchering API.

This module contains Celery tasks for audio mastering, processing,
and quality analysis.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging
import traceback

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.processing import ProcessingJob, JobProgress, JobStatus, ProcessingStage
from app.models.audio import AudioFile, AudioMetadata
from app.core.exceptions import (
    AudioFileError, 
    ProcessingError, 
    JobNotFoundError,
    JobStateError
)

logger = logging.getLogger(__name__)


class AudioProcessingTask(Task):
    """Base class for audio processing tasks with database integration."""
    
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


@celery_app.task(bind=True, base=AudioProcessingTask, name="process_audio_auto_master")
def process_audio_auto_master(self: AudioProcessingTask, job_id: str) -> Dict[str, Any]:
    """
    Process audio file using AI-powered auto-mastering.
    
    Args:
        job_id: UUID string of the processing job
        
    Returns:
        dict: Processing results and metadata
    """
    return asyncio.run(_process_audio_auto_master_async(self, job_id))


async def _process_audio_auto_master_async(self: AudioProcessingTask, job_id: str) -> Dict[str, Any]:
    """Async implementation of auto-mastering task."""
    session = await self.get_session()
    
    try:
        # Small delay to allow frontend WebSocket connection to establish
        await asyncio.sleep(0.5)
        
        # Update job status to processing
        await _update_job_status(session, job_id, JobStatus.PROCESSING)
        
        # Stage 1: Validation
        await _update_progress(session, job_id, ProcessingStage.VALIDATION, 10.0, "Validating input file")
        input_file = await _validate_input_file(session, job_id)
        await asyncio.sleep(0.3)  # Allow WebSocket message to be sent
        
        # Stage 2: Feature Extraction  
        await _update_progress(session, job_id, ProcessingStage.FEATURE_EXTRACTION, 25.0, "Extracting audio features")
        features = await _extract_audio_features(session, input_file)
        await asyncio.sleep(0.3)
        
        # Stage 3: AI Analysis
        await _update_progress(session, job_id, ProcessingStage.AI_ANALYSIS, 50.0, "Analyzing audio characteristics")
        analysis = await _analyze_audio_ai(session, features)
        await asyncio.sleep(0.3)
        
        # Stage 4: Parameter Prediction
        await _update_progress(session, job_id, ProcessingStage.PARAMETER_PREDICTION, 70.0, "Predicting optimal parameters")
        parameters = await _predict_mastering_parameters(session, analysis)
        await asyncio.sleep(0.3)
        
        # Stage 5: Audio Processing
        await _update_progress(session, job_id, ProcessingStage.AUDIO_PROCESSING, 85.0, "Applying mastering processing")
        output_path = await _apply_mastering_processing(session, input_file, parameters)
        await asyncio.sleep(0.4)  # Longer delay for main processing
        
        # Stage 6: Quality Check
        await _update_progress(session, job_id, ProcessingStage.QUALITY_CHECK, 95.0, "Performing quality analysis")
        quality_metrics = await _perform_quality_check(session, output_path)
        await asyncio.sleep(0.3)
        
        # Stage 7: Finalization
        await _update_progress(session, job_id, ProcessingStage.FINALIZATION, 100.0, "Finalizing results")
        result_metadata = await _finalize_processing(session, job_id, output_path, quality_metrics)
        await asyncio.sleep(0.2)
        
        # Update job to completed
        await _update_job_status(session, job_id, JobStatus.COMPLETED, result_metadata)
        
        logger.info(f"Auto-mastering completed successfully for job {job_id}")
        return {
            "status": "completed",
            "job_id": job_id,
            "output_path": str(output_path),
            "metadata": result_metadata
        }
        
    except Exception as e:
        await _handle_processing_error(session, job_id, e)
        raise
    finally:
        await self.close_session()


@celery_app.task(bind=True, base=AudioProcessingTask, name="process_audio_reference_master")
def process_audio_reference_master(self: AudioProcessingTask, job_id: str) -> Dict[str, Any]:
    """
    Process audio file using reference-based mastering.
    
    Args:
        job_id: UUID string of the processing job
        
    Returns:
        dict: Processing results and metadata
    """
    return asyncio.run(_process_audio_reference_master_async(self, job_id))


async def _process_audio_reference_master_async(self: AudioProcessingTask, job_id: str) -> Dict[str, Any]:
    """Async implementation of reference-based mastering task."""
    session = await self.get_session()
    
    try:
        # Small delay to allow frontend WebSocket connection to establish
        await asyncio.sleep(0.5)
        
        # Update job status to processing
        await _update_job_status(session, job_id, JobStatus.PROCESSING)
        
        # Stage 1: Validation
        await _update_progress(session, job_id, ProcessingStage.VALIDATION, 10.0, "Validating input and reference files")
        input_file, reference_file = await _validate_reference_files(session, job_id)
        
        # Stage 2: Feature Extraction
        await _update_progress(session, job_id, ProcessingStage.FEATURE_EXTRACTION, 30.0, "Extracting features from both files")
        input_features = await _extract_audio_features(session, input_file)
        reference_features = await _extract_audio_features(session, reference_file)
        
        # Stage 3: Reference Analysis
        await _update_progress(session, job_id, ProcessingStage.AI_ANALYSIS, 55.0, "Analyzing reference characteristics")
        reference_analysis = await _analyze_reference_audio(session, reference_features)
        
        # Stage 4: Parameter Matching
        await _update_progress(session, job_id, ProcessingStage.PARAMETER_PREDICTION, 75.0, "Matching to reference parameters")
        parameters = await _match_reference_parameters(session, input_features, reference_analysis)
        
        # Stage 5: Audio Processing
        await _update_progress(session, job_id, ProcessingStage.AUDIO_PROCESSING, 90.0, "Applying reference-based processing")
        output_path = await _apply_reference_processing(session, input_file, parameters)
        
        # Stage 6: Quality Check
        await _update_progress(session, job_id, ProcessingStage.QUALITY_CHECK, 97.0, "Validating reference matching")
        quality_metrics = await _validate_reference_matching(session, output_path, reference_file)
        
        # Stage 7: Finalization
        await _update_progress(session, job_id, ProcessingStage.FINALIZATION, 100.0, "Finalizing results")
        result_metadata = await _finalize_processing(session, job_id, output_path, quality_metrics)
        
        # Update job to completed
        await _update_job_status(session, job_id, JobStatus.COMPLETED, result_metadata)
        
        logger.info(f"Reference mastering completed successfully for job {job_id}")
        return {
            "status": "completed", 
            "job_id": job_id,
            "output_path": str(output_path),
            "metadata": result_metadata
        }
        
    except Exception as e:
        await _handle_processing_error(session, job_id, e)
        raise
    finally:
        await self.close_session()


# Helper methods for audio processing tasks

async def _update_job_status(
    session: AsyncSession, 
    job_id: str, 
    status: JobStatus, 
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Update processing job status."""
    from sqlalchemy import select, update
    
    query = select(ProcessingJob).where(ProcessingJob.id == uuid.UUID(job_id))
    result = await session.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise JobNotFoundError(job_id)
    
    update_data = {"status": status}
    
    if status == JobStatus.PROCESSING:
        update_data["started_at"] = datetime.utcnow()
    elif status == JobStatus.COMPLETED:
        update_data["completed_at"] = datetime.utcnow()
        if metadata:
            update_data["result_metadata"] = metadata
    
    await session.execute(
        update(ProcessingJob)
        .where(ProcessingJob.id == uuid.UUID(job_id))
        .values(**update_data)
    )
    await session.commit()
    
    # Send WebSocket broadcast for status change
    try:
        from app.api.v1.endpoints.processing import broadcast_message
        websocket_message = {
            "type": "job_completed" if status == JobStatus.COMPLETED else "job_failed" if status == JobStatus.FAILED else "status_update",
            "payload": {
                "job_id": job_id,
                "status": status.value,
                "message": "Job completed successfully" if status == JobStatus.COMPLETED else f"Job status updated to {status.value}",
                "timestamp": datetime.utcnow().isoformat(),
                "output_file_url": metadata.get("output_file") if metadata and status == JobStatus.COMPLETED else None,
                "processing_metadata": metadata if status == JobStatus.COMPLETED else None
            }
        }
        await broadcast_message(job_id, websocket_message)
        logger.debug(f"WebSocket status broadcast sent for job {job_id}: {status.value}")
    except Exception as e:
        logger.warning(f"Failed to send WebSocket status update for job {job_id}: {e}")


async def _update_progress(
    session: AsyncSession,
    job_id: str,
    stage: ProcessingStage,
    percentage: float,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Update job progress."""
    from sqlalchemy import update
    
    # Update job current stage and progress
    await session.execute(
        update(ProcessingJob)
        .where(ProcessingJob.id == uuid.UUID(job_id))
        .values(
            current_stage=stage,
            progress_percentage=percentage
        )
    )
    
    # Add progress entry
    progress = JobProgress(
        id=uuid.uuid4(),
        job_id=uuid.UUID(job_id),
        stage=stage,
        progress_percentage=percentage,
        message=message,
        stage_started_at=datetime.utcnow(),
        details=details or {}
    )
    
    session.add(progress)
    await session.commit()
    
    # Send WebSocket broadcast to frontend
    try:
        from app.api.v1.endpoints.processing import broadcast_message
        websocket_message = {
            "type": "processing_progress",
            "payload": {
                "job_id": job_id,
                "status": "PROCESSING",
                "progress_percentage": percentage,
                "current_stage": stage.value,
                "message": message,
                "elapsed_time": 0,  # TODO: Calculate actual elapsed time
                "remaining_time": 0,  # TODO: Calculate actual remaining time
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
        }
        await broadcast_message(job_id, websocket_message)
        logger.debug(f"WebSocket progress broadcast sent for job {job_id}: {stage.value} {percentage}%")
    except Exception as e:
        logger.warning(f"Failed to send WebSocket progress update for job {job_id}: {e}")


async def _validate_input_file(session: AsyncSession, job_id: str) -> AudioFile:
    """Validate input file for processing."""
    from sqlalchemy import select
    
    # Get job and input file
    query = select(ProcessingJob).where(ProcessingJob.id == uuid.UUID(job_id))
    result = await session.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise JobNotFoundError(job_id)
    
    query = select(AudioFile).where(AudioFile.id == job.input_file_id)
    result = await session.execute(query)
    audio_file = result.scalar_one_or_none()
    
    if not audio_file:
        raise AudioFileError(f"Input file not found for job {job_id}", "INPUT_FILE_NOT_FOUND", {"job_id": job_id})
    
    # Validate file exists and is readable
    file_path = Path(audio_file.file_path)
    if not file_path.exists():
        raise AudioFileError(f"Input file does not exist: {file_path}", "FILE_NOT_EXISTS", {"file_path": str(file_path)})
    
    if not audio_file.processing_eligible:
        raise AudioFileError(f"File not eligible for processing: {file_path}", "FILE_NOT_ELIGIBLE", {"file_path": str(file_path)})
    
    return audio_file


async def _validate_reference_files(session: AsyncSession, job_id: str) -> tuple[AudioFile, AudioFile]:
    """Validate input and reference files for reference-based processing."""
    from sqlalchemy import select
    
    # Get job
    query = select(ProcessingJob).where(ProcessingJob.id == uuid.UUID(job_id))
    result = await session.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise JobNotFoundError(job_id)
    
    if not job.reference_file_id:
        raise ProcessingError(f"No reference file specified for job {job_id}", "NO_REFERENCE_FILE", {"job_id": job_id})
    
    # Validate input file
    input_file = await _validate_input_file(session, job_id)
    
    # Validate reference file
    query = select(AudioFile).where(AudioFile.id == job.reference_file_id)
    result = await session.execute(query)
    reference_file = result.scalar_one_or_none()
    
    if not reference_file:
        raise AudioFileError(f"Reference file not found for job {job_id}", "REFERENCE_FILE_NOT_FOUND", {"job_id": job_id})
    
    reference_path = Path(reference_file.file_path)
    if not reference_path.exists():
        raise AudioFileError(f"Reference file does not exist: {reference_path}", "FILE_NOT_EXISTS", {"file_path": str(reference_path)})
    
    return input_file, reference_file


# Placeholder implementations for audio processing functions
# These would integrate with the existing Matchering library

async def _extract_audio_features(session: AsyncSession, audio_file: AudioFile) -> Dict[str, Any]:
    """Extract audio features from file (placeholder)."""
    # TODO: Integrate with actual audio analysis library
    return {
        "sample_rate": audio_file.sample_rate,
        "duration": audio_file.duration,
        "channels": audio_file.channels,
        "format": audio_file.format,
        "rms_level": -12.5,  # Placeholder values
        "peak_level": -3.2,
        "lufs_integrated": -14.2,
        "spectral_centroid": 2500.0
    }


async def _analyze_audio_ai(session: AsyncSession, features: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze audio using AI models (placeholder)."""
    # TODO: Integrate with AI analysis models
    return {
        "loudness_target": -14.0,
        "dynamic_range_target": 8.0,
        "spectral_balance": "neutral",
        "recommended_processing": ["eq", "compression", "limiting"]
    }


async def _predict_mastering_parameters(session: AsyncSession, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Predict optimal mastering parameters (placeholder)."""
    # TODO: Integrate with parameter prediction models
    return {
        "eq_curve": {"low": 0.0, "mid": 0.0, "high": 0.0},
        "compression": {"ratio": 3.0, "attack": 0.003, "release": 0.1},
        "limiting": {"ceiling": -0.1, "release": 0.05},
        "loudness_target": analysis.get("loudness_target", -14.0)
    }


async def _apply_mastering_processing(
    session: AsyncSession, 
    input_file: AudioFile, 
    parameters: Dict[str, Any]
) -> Path:
    """Apply mastering processing to audio file (placeholder)."""
    # TODO: Integrate with actual Matchering processing
    input_path = Path(input_file.file_path)
    output_path = input_path.parent / f"processed_{input_path.stem}_auto{input_path.suffix}"
    
    # Placeholder: copy file (would be actual processing)
    import shutil
    shutil.copy2(input_path, output_path)
    
    return output_path


async def _apply_reference_processing(
    session: AsyncSession,
    input_file: AudioFile, 
    parameters: Dict[str, Any]
) -> Path:
    """Apply reference-based processing to audio file (placeholder)."""
    # TODO: Integrate with actual Matchering reference processing
    input_path = Path(input_file.file_path)
    output_path = input_path.parent / f"processed_{input_path.stem}_ref{input_path.suffix}"
    
    # Placeholder: copy file (would be actual processing)
    import shutil
    shutil.copy2(input_path, output_path)
    
    return output_path


async def _analyze_reference_audio(session: AsyncSession, features: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze reference audio characteristics (placeholder)."""
    return {
        "target_loudness": features.get("lufs_integrated", -14.0),
        "target_dynamics": 8.0,
        "spectral_profile": "reference_based",
        "reference_characteristics": features
    }


async def _match_reference_parameters(
    session: AsyncSession,
    input_features: Dict[str, Any], 
    reference_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Match processing parameters to reference (placeholder)."""
    return {
        "eq_curve": {"low": 0.5, "mid": 0.0, "high": -0.5},
        "compression": {"ratio": 2.5, "attack": 0.005, "release": 0.15},
        "limiting": {"ceiling": -0.1, "release": 0.05},
        "loudness_target": reference_analysis.get("target_loudness", -14.0)
    }


async def _perform_quality_check(session: AsyncSession, output_path: Path) -> Dict[str, Any]:
    """Perform quality analysis on processed audio (placeholder)."""
    return {
        "peak_level": -0.1,
        "lufs_integrated": -14.0,
        "dynamic_range": 8.0,
        "thd_percentage": 0.01,
        "quality_score": 9.2,
        "warnings": []
    }


async def _validate_reference_matching(
    session: AsyncSession, 
    output_path: Path, 
    reference_file: AudioFile
) -> Dict[str, Any]:
    """Validate how well output matches reference (placeholder)."""
    return {
        "loudness_match_score": 9.5,
        "spectral_match_score": 8.8,
        "dynamic_match_score": 9.1,
        "overall_match_score": 9.1,
        "quality_metrics": await _perform_quality_check(session, output_path)
    }


async def _finalize_processing(
    session: AsyncSession,
    job_id: str, 
    output_path: Path,
    quality_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """Finalize processing and update job with results."""
    from sqlalchemy import update
    
    # Update job with output file path
    await session.execute(
        update(ProcessingJob)
        .where(ProcessingJob.id == uuid.UUID(job_id))
        .values(
            output_file_path=str(output_path),
            processing_duration=(datetime.utcnow() - datetime.utcnow()).total_seconds()  # Placeholder
        )
    )
    await session.commit()
    
    return {
        "output_file": str(output_path),
        "quality_metrics": quality_metrics,
        "processing_completed_at": datetime.utcnow().isoformat(),
        "success": True
    }


async def _handle_processing_error(session: AsyncSession, job_id: str, error: Exception) -> None:
    """Handle processing errors and update job status."""
    from sqlalchemy import update
    
    error_message = str(error)
    error_code = getattr(error, 'error_code', 'PROCESSING_ERROR')
    
    logger.error(f"Processing failed for job {job_id}: {error_message}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Update job to failed status
    await session.execute(
        update(ProcessingJob)
        .where(ProcessingJob.id == uuid.UUID(job_id))
        .values(
            status=JobStatus.FAILED,
            error_message=error_message,
            error_code=error_code,
            completed_at=datetime.utcnow()
        )
    )
    await session.commit()


# Export tasks
__all__ = [
    "process_audio_auto_master",
    "process_audio_reference_master", 
    "AudioProcessingTask"
]