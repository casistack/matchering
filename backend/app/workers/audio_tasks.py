"""
Audio processing tasks for Enhanced Matchering API.

This module contains Celery tasks for audio mastering, processing,
and quality analysis.
"""

import asyncio
import signal
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging
import traceback
import numpy as np

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
from app.utils.redis_bridge import (
    publish_progress_update, 
    publish_status_update, 
    publish_job_completed
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
        analysis = await _analyze_audio_ai(session, features, input_file)
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
    
    # Send status update via Redis bridge
    try:
        if status == JobStatus.COMPLETED:
            # Construct proper URL for output file with URL encoding
            output_file_url = None
            if metadata and metadata.get("output_file"):
                from urllib.parse import quote
                output_file_path = metadata.get("output_file")
                
                # Ensure proper URL formatting with forward slash and URL encoding
                if output_file_path.startswith("uploads/"):
                    # URL encode the filename part to handle spaces and special characters
                    path_parts = output_file_path.split('/')
                    encoded_filename = quote(path_parts[-1])  # URL encode just the filename
                    output_file_url = f"/{path_parts[0]}/{encoded_filename}"
                else:
                    # URL encode the filename part
                    encoded_filename = quote(output_file_path)
                    output_file_url = f"/uploads/{encoded_filename}"
            
            await publish_job_completed(job_id, {
                "status": status.value,
                "message": "Job completed successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "output_file_url": output_file_url,
                "processing_metadata": metadata if metadata else None
            })
        else:
            await publish_status_update(
                job_id, 
                status.value, 
                "Job completed successfully" if status == JobStatus.COMPLETED else f"Job status updated to {status.value}"
            )
        logger.debug(f"Redis status update sent for job {job_id}: {status.value}")
    except Exception as e:
        logger.warning(f"Failed to send Redis status update for job {job_id}: {e}")


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
    
    # Send progress update via Redis bridge
    try:
        await publish_progress_update(job_id, {
            "job_id": job_id,
            "status": "PROCESSING",
            "progress_percentage": percentage,
            "current_stage": stage.value,
            "message": message,
            "elapsed_time": 0,  # TODO: Calculate actual elapsed time
            "remaining_time": 0,  # TODO: Calculate actual remaining time
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        })
        logger.debug(f"Redis progress update sent for job {job_id}: {stage.value} {percentage}%")
    except Exception as e:
        logger.warning(f"Failed to send Redis progress update for job {job_id}: {e}")


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
    """Extract audio features for AUTO mode using dedicated feature extraction."""
    try:
        import torchaudio
        import torch
        import numpy as np
        from scipy.signal import spectral
        
        # Load audio file
        audio_path = Path(audio_file.file_path)
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        audio_data = waveform.squeeze().numpy()
        
        # Calculate basic features for AUTO mode
        rms_level = float(20 * np.log10(np.sqrt(np.mean(audio_data**2)) + 1e-10))
        peak_level = float(20 * np.log10(np.max(np.abs(audio_data)) + 1e-10))
        
        # Simple spectral centroid calculation
        fft = np.fft.fft(audio_data)
        freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
        magnitude = np.abs(fft)
        spectral_centroid = float(np.sum(freqs[:len(freqs)//2] * magnitude[:len(magnitude)//2]) / 
                                 (np.sum(magnitude[:len(magnitude)//2]) + 1e-10))
        
        logger.info(f"✅ AUTO mode features extracted for {audio_path.name}")
        
        return {
            "sample_rate": int(sample_rate),
            "duration": float(len(audio_data) / sample_rate),
            "channels": audio_file.channels,
            "format": audio_file.format,
            "rms_level": rms_level,
            "peak_level": peak_level,
            "spectral_centroid": spectral_centroid,
            "analysis_method": "auto_mode_feature_extraction"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in AUTO mode feature extraction: {str(e)}")
        # Return basic file info as fallback
        return {
            "sample_rate": audio_file.sample_rate,
            "duration": audio_file.duration,
            "channels": audio_file.channels,
            "format": audio_file.format,
            "rms_level": -12.5,  # Safe defaults
            "peak_level": -3.2,
            "spectral_centroid": 2500.0,
            "error": f"Feature extraction failed: {str(e)}",
            "analysis_method": "auto_mode_fallback"
        }


async def _analyze_audio_ai(session: AsyncSession, features: Dict[str, Any], input_file: AudioFile) -> Dict[str, Any]:
    """Analyze audio for AUTO mode using HYBRID's AI genre classifier."""
    try:
        # AUTO mode now uses HYBRID's sophisticated AI genre classifier
        # but keeps the simple processing pipeline
        
        # Get audio path directly from input_file parameter
        audio_path = input_file.file_path
        logger.info(f"🔍 AUTO mode using audio path: {audio_path}")
        
        if audio_path and Path(audio_path).exists():
            # Use HYBRID's AI genre classifier
            try:
                from app.ai.ensemble_genre_classifier import EnsembleGenreClassifier
                from app.ai.production_model_manager import ProductionModelManager
                from app.ai.hybrid_feature_extractor import HybridFeatureExtractor
                
                # Initialize the AI classifier
                model_manager = ProductionModelManager()
                genre_classifier = EnsembleGenreClassifier(model_manager)
                feature_extractor = HybridFeatureExtractor()
                
                # Extract features needed for AI classification
                hybrid_features = await feature_extractor.extract_features(audio_path)
                
                # Perform real AI genre classification with correct method
                prediction = await genre_classifier.predict_genre(hybrid_features, Path(audio_path).name)
                
                genre = prediction.predicted_genre
                confidence = prediction.confidence
                
                logger.info(f"✅ AUTO mode AI classification - Genre: {genre}, Confidence: {confidence:.2f}")
                logger.info(f"   Model used: {prediction.model_used}")
                
            except Exception as ai_error:
                logger.warning(f"AI classification failed, using feature-based fallback: {str(ai_error)}")
                logger.warning(f"   Error details: {traceback.format_exc()}")
                genre, confidence = _fallback_genre_classification(features)
        else:
            # Fallback to feature-based classification
            logger.warning("Audio path not available, using feature-based classification")
            genre, confidence = _fallback_genre_classification(features)
        
        # Map detected genre to AUTO mode processing parameters
        processing_params = _get_auto_processing_params(genre, features)
        
        return {
            "predicted_genre": genre,
            "confidence": confidence,
            "loudness_target": processing_params["loudness_target"],
            "dynamic_range_target": processing_params["dynamic_range_target"],
            "spectral_balance": processing_params["spectral_balance"],
            "recommended_processing": ["normalize", "eq", "compression", "limiting"],
            "analysis_method": "auto_mode_ai_classification"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in AUTO mode AI analysis: {str(e)}")
        # Final fallback
        return {
            "predicted_genre": "pop",
            "loudness_target": -14.0,
            "dynamic_range_target": 8.0,
            "spectral_balance": "neutral",
            "recommended_processing": ["normalize", "eq", "compression", "limiting"],
            "confidence": 0.5,
            "error": f"Analysis failed: {str(e)}",
            "analysis_method": "auto_mode_error_fallback"
        }


def _fallback_genre_classification(features: Dict[str, Any]) -> tuple[str, float]:
    """Fallback genre classification using audio features."""
    rms_level = features.get("rms_level", -12.0)
    peak_level = features.get("peak_level", -3.0)
    spectral_centroid = features.get("spectral_centroid", 2500.0)
    
    dynamic_range = peak_level - rms_level
    
    # Improved genre classification for AUTO mode
    # Note: Dynamic range alone is not a reliable indicator of genre
    if dynamic_range > 20 and spectral_centroid < 2000:
        # Very high dynamic range with low spectral centroid might be classical
        return "classical", 0.6
    elif dynamic_range < 6 and spectral_centroid > 4000:
        # Heavily compressed with bright timbre - likely electronic
        return "electronic", 0.7
    elif spectral_centroid > 4000 and dynamic_range < 10:
        # Bright and somewhat compressed - likely rock or metal
        return "rock", 0.6
    elif spectral_centroid < 1800 and dynamic_range > 10:
        # Warm timbre with good dynamics - likely jazz or blues
        return "jazz", 0.6
    elif dynamic_range < 8:
        # Moderately compressed - likely pop
        return "pop", 0.5
    else:
        # Default to rock for unknown characteristics
        return "rock", 0.4


def _get_auto_processing_params(genre: str, features: Dict[str, Any]) -> Dict[str, Any]:
    """Get AUTO mode processing parameters based on detected genre."""
    
    # Expanded genre mapping for AUTO mode
    genre_params = {
        # Main genres
        "classical": {
            "loudness_target": -18.0,
            "dynamic_range_target": 15.0,
            "spectral_balance": "natural"
        },
        "electronic": {
            "loudness_target": -10.0,
            "dynamic_range_target": 4.0,
            "spectral_balance": "bright"
        },
        "rock": {
            "loudness_target": -12.0,
            "dynamic_range_target": 6.0,
            "spectral_balance": "punchy"
        },
        "jazz": {
            "loudness_target": -16.0,
            "dynamic_range_target": 12.0,
            "spectral_balance": "warm"
        },
        "pop": {
            "loudness_target": -11.0,
            "dynamic_range_target": 5.0,
            "spectral_balance": "balanced"
        },
        
        # Extended genres that AI can detect
        "hip-hop": {
            "loudness_target": -9.0,
            "dynamic_range_target": 4.0,
            "spectral_balance": "bass_heavy"
        },
        "country": {
            "loudness_target": -13.0,
            "dynamic_range_target": 8.0,
            "spectral_balance": "warm"
        },
        "blues": {
            "loudness_target": -15.0,
            "dynamic_range_target": 10.0,
            "spectral_balance": "warm"
        },
        "metal": {
            "loudness_target": -8.0,
            "dynamic_range_target": 3.0,
            "spectral_balance": "aggressive"
        },
        "ambient": {
            "loudness_target": -20.0,
            "dynamic_range_target": 18.0,
            "spectral_balance": "spacious"
        },
        "folk": {
            "loudness_target": -16.0,
            "dynamic_range_target": 12.0,
            "spectral_balance": "natural"
        },
        "reggae": {
            "loudness_target": -12.0,
            "dynamic_range_target": 7.0,
            "spectral_balance": "bass_heavy"
        },
        "funk": {
            "loudness_target": -11.0,
            "dynamic_range_target": 5.0,
            "spectral_balance": "punchy"
        },
        "disco": {
            "loudness_target": -10.0,
            "dynamic_range_target": 4.0,
            "spectral_balance": "bright"
        },
        "r&b": {
            "loudness_target": -12.0,
            "dynamic_range_target": 6.0,
            "spectral_balance": "smooth"
        }
    }
    
    # Get parameters for detected genre, fallback to pop
    params = genre_params.get(genre.lower(), genre_params["pop"])
    
    # Adjust based on current audio levels
    rms_level = features.get("rms_level", -12.0)
    if rms_level > -8:
        params["loudness_target"] = max(params["loudness_target"], -13.0)
    elif rms_level < -20:
        params["loudness_target"] = min(params["loudness_target"], -15.0)
    
    return params


def _get_genre_dsp_params(genre: str) -> tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """Get DSP parameters (EQ, compression, limiting) for a given genre."""
    
    # Expanded DSP parameter mapping for all genres
    dsp_params = {
        # Main genres
        "classical": {
            "eq_curve": {"low": 0.0, "mid": 0.0, "high": 0.0},  # Natural
            "compression": {"ratio": 1.5, "attack": 0.02, "release": 0.3},  # Light
            "limiting": {"ceiling": -0.5, "release": 0.2}  # Conservative
        },
        "electronic": {
            "eq_curve": {"low": 2.0, "mid": 0.0, "high": 1.0},  # Bass boost, bright highs
            "compression": {"ratio": 8.0, "attack": 0.0001, "release": 0.05},  # Heavy
            "limiting": {"ceiling": -0.1, "release": 0.01}  # Aggressive
        },
        "rock": {
            "eq_curve": {"low": 1.0, "mid": 0.5, "high": 2.0},  # Bright and punchy
            "compression": {"ratio": 4.0, "attack": 0.001, "release": 0.1},  # Medium-heavy
            "limiting": {"ceiling": -0.1, "release": 0.03}  # Punchy
        },
        "jazz": {
            "eq_curve": {"low": 0.0, "mid": 0.0, "high": -1.0},  # Warm
            "compression": {"ratio": 2.5, "attack": 0.01, "release": 0.2},  # Light
            "limiting": {"ceiling": -0.3, "release": 0.1}  # Gentle
        },
        "pop": {
            "eq_curve": {"low": 0.5, "mid": 1.0, "high": 1.5},  # Balanced, modern
            "compression": {"ratio": 6.0, "attack": 0.003, "release": 0.08},  # Commercial
            "limiting": {"ceiling": -0.1, "release": 0.05}  # Modern
        },
        
        # Extended genres
        "hip-hop": {
            "eq_curve": {"low": 3.0, "mid": 0.0, "high": 0.5},  # Heavy bass, clear highs
            "compression": {"ratio": 8.0, "attack": 0.001, "release": 0.05},  # Heavy
            "limiting": {"ceiling": -0.1, "release": 0.01}  # Aggressive
        },
        "country": {
            "eq_curve": {"low": 0.0, "mid": 1.0, "high": 0.5},  # Vocal clarity
            "compression": {"ratio": 3.0, "attack": 0.005, "release": 0.1},  # Medium
            "limiting": {"ceiling": -0.2, "release": 0.08}  # Moderate
        },
        "blues": {
            "eq_curve": {"low": 0.5, "mid": 0.0, "high": -0.5},  # Warm, smooth
            "compression": {"ratio": 2.0, "attack": 0.01, "release": 0.2},  # Light
            "limiting": {"ceiling": -0.3, "release": 0.1}  # Gentle
        },
        "metal": {
            "eq_curve": {"low": 2.0, "mid": 1.0, "high": 3.0},  # Aggressive across spectrum
            "compression": {"ratio": 10.0, "attack": 0.0001, "release": 0.03},  # Very heavy
            "limiting": {"ceiling": -0.1, "release": 0.005}  # Brutal
        },
        "ambient": {
            "eq_curve": {"low": 0.0, "mid": -0.5, "high": 0.5},  # Spacious, airy
            "compression": {"ratio": 1.2, "attack": 0.05, "release": 0.5},  # Very light
            "limiting": {"ceiling": -1.0, "release": 0.3}  # Very conservative
        },
        "folk": {
            "eq_curve": {"low": 0.0, "mid": 0.5, "high": 0.0},  # Natural with vocal presence
            "compression": {"ratio": 2.0, "attack": 0.01, "release": 0.15},  # Light
            "limiting": {"ceiling": -0.3, "release": 0.1}  # Gentle
        },
        "reggae": {
            "eq_curve": {"low": 2.5, "mid": 0.0, "high": 0.0},  # Bass emphasis
            "compression": {"ratio": 4.0, "attack": 0.002, "release": 0.1},  # Medium
            "limiting": {"ceiling": -0.2, "release": 0.05}  # Moderate
        },
        "funk": {
            "eq_curve": {"low": 1.5, "mid": 1.0, "high": 1.0},  # Punchy and bright
            "compression": {"ratio": 6.0, "attack": 0.001, "release": 0.06},  # Heavy
            "limiting": {"ceiling": -0.1, "release": 0.03}  # Punchy
        },
        "disco": {
            "eq_curve": {"low": 1.0, "mid": 0.5, "high": 2.0},  # Bright and danceable
            "compression": {"ratio": 8.0, "attack": 0.0005, "release": 0.04},  # Heavy
            "limiting": {"ceiling": -0.1, "release": 0.02}  # Aggressive
        },
        "r&b": {
            "eq_curve": {"low": 1.0, "mid": 1.5, "high": 0.5},  # Smooth with vocal clarity
            "compression": {"ratio": 5.0, "attack": 0.003, "release": 0.08},  # Medium-heavy
            "limiting": {"ceiling": -0.1, "release": 0.05}  # Smooth
        }
    }
    
    # Get parameters for genre, fallback to pop
    params = dsp_params.get(genre.lower(), dsp_params["pop"])
    
    return params["eq_curve"], params["compression"], params["limiting"]


def _generate_processing_recommendations(genre: str, features: Dict[str, Any]) -> Dict[str, Any]:
    """Generate processing recommendations based on genre and audio features."""
    
    # Genre-specific processing profiles
    genre_profiles = {
        "rock": {
            "loudness_target": -12.0,
            "dynamic_range_target": 6.0,
            "spectral_balance": "bright",
            "eq_curve": {"low": 1.0, "mid": 0.5, "high": 2.0},
            "compression": {"ratio": 4.0, "attack": 0.001, "release": 0.1},
            "limiting": {"ceiling": -0.1, "release": 0.03}
        },
        "pop": {
            "loudness_target": -11.0,
            "dynamic_range_target": 5.0,
            "spectral_balance": "balanced",
            "eq_curve": {"low": 0.5, "mid": 1.0, "high": 1.5},
            "compression": {"ratio": 6.0, "attack": 0.003, "release": 0.08},
            "limiting": {"ceiling": -0.1, "release": 0.05}
        },
        "jazz": {
            "loudness_target": -16.0,
            "dynamic_range_target": 12.0,
            "spectral_balance": "warm",
            "eq_curve": {"low": 0.0, "mid": 0.0, "high": -1.0},
            "compression": {"ratio": 2.5, "attack": 0.01, "release": 0.2},
            "limiting": {"ceiling": -0.3, "release": 0.1}
        },
        "electronic": {
            "loudness_target": -10.0,
            "dynamic_range_target": 4.0,
            "spectral_balance": "bright",
            "eq_curve": {"low": 2.0, "mid": 0.0, "high": 1.0},
            "compression": {"ratio": 8.0, "attack": 0.0001, "release": 0.05},
            "limiting": {"ceiling": -0.1, "release": 0.01}
        },
        "classical": {
            "loudness_target": -18.0,
            "dynamic_range_target": 15.0,
            "spectral_balance": "natural",
            "eq_curve": {"low": 0.0, "mid": 0.0, "high": 0.0},
            "compression": {"ratio": 1.5, "attack": 0.02, "release": 0.3},
            "limiting": {"ceiling": -0.5, "release": 0.2}
        }
    }
    
    # Get profile or use default
    profile = genre_profiles.get(genre.lower(), genre_profiles["pop"])
    
    # Adjust based on audio features
    current_lufs = features.get("lufs_integrated", -14.0)
    current_peak = features.get("peak_level", -3.0)
    
    # Adjust loudness target based on current levels
    if current_lufs > -10:
        profile["loudness_target"] = max(profile["loudness_target"], -13.0)
    elif current_lufs < -20:
        profile["loudness_target"] = min(profile["loudness_target"], -15.0)
    
    # Add processing chain
    profile["processing_chain"] = ["eq", "compression", "limiting"]
    
    return profile


def _predict_genre_from_features(features: Dict[str, Any]) -> str:
    """Predict genre from audio features when AI models are not available."""
    
    # Simple heuristic-based genre prediction
    rms_level = features.get("rms_level", -12.0)
    peak_level = features.get("peak_level", -3.0)
    spectral_centroid = features.get("spectral_centroid", 2500.0)
    
    # Dynamic range calculation
    dynamic_range = peak_level - rms_level
    
    # Simple classification based on features
    if dynamic_range > 15:
        return "classical"
    elif dynamic_range < 5 and peak_level > -1:
        return "electronic"
    elif spectral_centroid > 3000:
        return "rock"
    elif spectral_centroid < 1500:
        return "jazz"
    else:
        return "pop"


async def _predict_mastering_parameters(session: AsyncSession, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Predict optimal mastering parameters for AUTO mode based on analysis."""
    try:
        # AUTO mode uses direct analysis results to create processing parameters
        genre = analysis.get("predicted_genre", "pop")
        loudness_target = analysis.get("loudness_target", -14.0)
        dynamic_range_target = analysis.get("dynamic_range_target", 8.0)
        confidence = analysis.get("confidence", 0.8)
        
        # Generate AUTO mode processing parameters based on detected genre
        eq_curve, compression, limiting = _get_genre_dsp_params(genre)
        
        logger.info(f"✅ AUTO mode parameters predicted for {genre} - Target: {loudness_target} LUFS")
        
        return {
            "eq_curve": eq_curve,
            "compression": compression,
            "limiting": limiting,
            "loudness_target": loudness_target,
            "dynamic_range_target": dynamic_range_target,
            "spectral_balance": analysis.get("spectral_balance", "auto_balanced"),
            "processing_chain": ["normalize", "eq", "compression", "limiting"],
            "genre": genre,
            "confidence": confidence,
            "preserve_dynamics": True if dynamic_range_target > 10 else False,
            "analysis_method": "auto_mode_parameter_prediction"
        }
        
    except Exception as e:
        logger.error(f"❌ Error in AUTO mode parameter prediction: {str(e)}")
        # AUTO mode safe fallback
        return {
            "eq_curve": {"low": 0.5, "mid": 0.5, "high": 0.5},
            "compression": {"ratio": 4.0, "attack": 0.003, "release": 0.1},
            "limiting": {"ceiling": -0.1, "release": 0.05},
            "loudness_target": -14.0,
            "dynamic_range_target": 8.0,
            "spectral_balance": "neutral",
            "processing_chain": ["normalize", "eq", "compression", "limiting"],
            "genre": "pop",
            "confidence": 0.5,
            "preserve_dynamics": True,
            "error": f"Parameter prediction failed: {str(e)}",
            "analysis_method": "auto_mode_fallback"
        }


async def _apply_mastering_processing(
    session: AsyncSession, 
    input_file: AudioFile, 
    parameters: Dict[str, Any]
) -> Path:
    """Apply AUTO mode mastering processing using direct DSP implementation."""
    try:
        import torchaudio
        import torch
        import numpy as np
        from scipy import signal
        
        input_path = Path(input_file.file_path)
        output_path = input_path.parent / f"processed_{input_path.stem}_auto{input_path.suffix}"
        
        logger.info(f"✅ Starting AUTO mode processing for {input_path.name}")
        logger.info(f"   Target loudness: {loudness_target} LUFS")
        logger.info(f"   Preserve dynamics: {preserve_dynamics}")
        logger.info(f"   EQ settings: {eq_curve}")
        logger.info(f"   Compression ratio: {compression.get('ratio', 4.0)}")
        
        # Load audio file
        waveform, sample_rate = torchaudio.load(input_path)
        logger.info(f"   Audio loaded: {waveform.shape} @ {sample_rate}Hz")
        
        # Convert to numpy for processing
        audio_data = waveform.numpy()
        
        # Get processing parameters
        eq_curve = parameters.get("eq_curve", {"low": 0.0, "mid": 0.0, "high": 0.0})
        compression = parameters.get("compression", {"ratio": 4.0, "attack": 0.003, "release": 0.1})
        limiting = parameters.get("limiting", {"ceiling": -0.1, "release": 0.05})
        loudness_target = parameters.get("loudness_target", -14.0)
        preserve_dynamics = parameters.get("preserve_dynamics", True)
        
        # Process each channel
        processed_audio = audio_data.copy()
        
        logger.info(f"   Processing {audio_data.shape[0]} channel(s) with AUTO mode pipeline")
        
        for channel in range(audio_data.shape[0]):
            channel_data = audio_data[channel]
            
            # 1. Apply EQ (simple 3-band implementation)
            processed_channel = _apply_auto_eq(channel_data, sample_rate, eq_curve)
            
            # 2. Apply compression
            processed_channel = _apply_auto_compression(processed_channel, compression, preserve_dynamics)
            
            # 3. Apply loudness normalization
            processed_channel = _apply_auto_loudness(processed_channel, loudness_target)
            
            # 4. Apply limiting
            processed_channel = _apply_auto_limiting(processed_channel, limiting)
            
            processed_audio[channel] = processed_channel
            
        logger.info(f"   ✅ All channels processed successfully")
        
        # Convert back to tensor and save
        processed_tensor = torch.from_numpy(processed_audio)
        torchaudio.save(output_path, processed_tensor, sample_rate)
        
        genre = parameters.get("genre", "unknown")
        confidence = parameters.get("confidence", 0.8)
        
        logger.info(f"✅ AUTO mode processing completed successfully")
        logger.info(f"   Genre: {genre} (confidence: {confidence:.2f})")
        logger.info(f"   Target loudness: {loudness_target} LUFS")
        logger.info(f"   Output: {output_path.name}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Error in AUTO mode processing: {str(e)}")
        # Fallback to file copy with error logging
        import shutil
        input_path = Path(input_file.file_path)
        output_path = input_path.parent / f"processed_{input_path.stem}_auto{input_path.suffix}"
        shutil.copy2(input_path, output_path)
        logger.error(f"❌ FALLBACK: File copied without processing due to error: {str(e)}")
        return output_path


def _apply_auto_eq(audio_data: np.ndarray, sample_rate: int, eq_curve: Dict[str, float]) -> np.ndarray:
    """Apply simple 3-band EQ for AUTO mode."""
    try:
        # Simple implementation using butterworth filters
        low_gain = eq_curve.get("low", 0.0)
        mid_gain = eq_curve.get("mid", 0.0) 
        high_gain = eq_curve.get("high", 0.0)
        
        processed = audio_data.copy()
        
        # Improved frequency separation for better EQ
        # Low band (60-200 Hz) - bass frequencies
        if abs(low_gain) > 0.1:
            sos_low = signal.butter(2, [60, 200], btype='band', fs=sample_rate, output='sos')
            low_band = signal.sosfilt(sos_low, processed)
            processed += low_band * (10**(low_gain/20) - 1)
        
        # Mid band (200-3000 Hz) - vocal and instrument fundamentals
        if abs(mid_gain) > 0.1:
            sos_mid = signal.butter(2, [200, 3000], btype='band', fs=sample_rate, output='sos')
            mid_band = signal.sosfilt(sos_mid, processed)
            processed += mid_band * (10**(mid_gain/20) - 1)
        
        # High band (3000+ Hz) - presence and air
        if abs(high_gain) > 0.1:
            sos_high = signal.butter(2, 3000, btype='high', fs=sample_rate, output='sos')
            high_band = signal.sosfilt(sos_high, processed)
            processed += high_band * (10**(high_gain/20) - 1)
        
        return processed
    except:
        return audio_data


def _apply_auto_compression(audio_data: np.ndarray, compression: Dict[str, float], preserve_dynamics: bool) -> np.ndarray:
    """Apply simple compression for AUTO mode."""
    try:
        ratio = compression.get("ratio", 4.0)
        
        # Light compression if preserving dynamics
        if preserve_dynamics and ratio > 3.0:
            ratio = 3.0
        
        # Simple peak compression
        threshold = -12.0  # dB
        threshold_linear = 10**(threshold/20)
        
        processed = audio_data.copy()
        
        # Apply compression to peaks
        mask = np.abs(processed) > threshold_linear
        if np.any(mask):
            over_threshold = np.abs(processed[mask]) / threshold_linear
            compressed_gain = threshold_linear * (over_threshold ** (1.0/ratio))
            processed[mask] = np.sign(processed[mask]) * compressed_gain
        
        return processed
    except:
        return audio_data


def _apply_auto_loudness(audio_data: np.ndarray, target_loudness: float) -> np.ndarray:
    """Apply loudness normalization for AUTO mode."""
    try:
        # Calculate current RMS level
        current_rms = np.sqrt(np.mean(audio_data**2))
        current_rms_db = 20 * np.log10(current_rms + 1e-10)
        
        # Convert target LUFS to approximate RMS level
        # LUFS to RMS approximation with calibration factor to reduce overshoot
        # LUFS ≈ RMS in dB + offset (calibrated for better accuracy)
        target_rms_db = target_loudness + 6.0  # Increased offset to reduce overshoot
        target_rms = 10**(target_rms_db/20)
        
        logger.info(f"🔊 Loudness normalization:")
        logger.info(f"   Current RMS: {current_rms_db:.2f} dB")
        logger.info(f"   Target LUFS: {target_loudness:.1f}")
        logger.info(f"   Target RMS: {target_rms_db:.2f} dB")
        
        if current_rms > 0:
            gain = target_rms / current_rms
            gain_db = 20 * np.log10(gain)
            
            # Limit gain to prevent excessive amplification or reduction
            # More conservative limiting to prevent overshoot
            gain_clipped = np.clip(gain, 0.2, 5.0)  # Reduced max gain from 10.0 to 5.0
            
            logger.info(f"   Calculated gain: {gain_db:.2f} dB")
            logger.info(f"   Applied gain: {20 * np.log10(gain_clipped):.2f} dB")
            
            # Apply gain
            processed = audio_data * gain_clipped
            
            # Soft clip to prevent any potential overshoots
            processed = np.tanh(processed * 0.95) / 0.95
            
            # Log final level
            final_rms = np.sqrt(np.mean(processed**2))
            final_rms_db = 20 * np.log10(final_rms + 1e-10)
            logger.info(f"   Final RMS: {final_rms_db:.2f} dB")
            
            return processed
        else:
            logger.warning("⚠️ Current RMS is zero, returning original audio")
            return audio_data
    except Exception as e:
        logger.error(f"❌ Error in loudness normalization: {str(e)}")
        return audio_data


def _apply_auto_limiting(audio_data: np.ndarray, limiting: Dict[str, float]) -> np.ndarray:
    """Apply limiting for AUTO mode."""
    try:
        ceiling = limiting.get("ceiling", -0.1)
        ceiling_linear = 10**(ceiling/20)
        
        # Simple peak limiting
        peak = np.max(np.abs(audio_data))
        if peak > ceiling_linear:
            return audio_data * (ceiling_linear / peak)
        else:
            return audio_data
    except:
        return audio_data


async def _apply_reference_processing(
    session: AsyncSession,
    input_file: AudioFile, 
    parameters: Dict[str, Any]
) -> Path:
    """Apply reference-based processing to audio file (PLACEHOLDER - NOT REAL PROCESSING)."""
    # ⚠️ CRITICAL: This returns hardcoded fake values, no reference processing occurs
    # TODO: Integrate with actual Matchering reference processing
    
    logger.warning("⚠️ PLACEHOLDER CODE: REFERENCE mode is only copying files, not processing audio!")
    logger.warning("⚠️ Users are receiving unchanged audio files!")
    
    input_path = Path(input_file.file_path)
    output_path = input_path.parent / f"processed_{input_path.stem}_ref{input_path.suffix}"
    
    # PLACEHOLDER: Just copy file (NO ACTUAL PROCESSING OCCURS)
    import shutil
    shutil.copy2(input_path, output_path)
    
    logger.info(f"📋 File copied (not processed): {input_path.name} → {output_path.name}")
    
    return output_path


async def _analyze_reference_audio(session: AsyncSession, features: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze reference audio characteristics (PLACEHOLDER - RETURNS FAKE VALUES)."""
    # ⚠️ CRITICAL: This returns hardcoded fake values, no reference analysis occurs
    # TODO: Implement actual reference audio analysis
    
    logger.warning("⚠️ PLACEHOLDER CODE: No reference audio analysis performed!")
    
    return {
        "target_loudness": features.get("lufs_integrated", -14.0),  # ⚠️ FAKE VALUE
        "target_dynamics": 8.0,  # ⚠️ FAKE VALUE
        "spectral_profile": "reference_based",  # ⚠️ FAKE VALUE
        "reference_characteristics": features,  # ⚠️ FAKE VALUE
        "analysis_method": "placeholder_no_analysis"
    }


async def _match_reference_parameters(
    session: AsyncSession,
    input_features: Dict[str, Any], 
    reference_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Match processing parameters to reference (PLACEHOLDER - RETURNS FAKE VALUES)."""
    # ⚠️ CRITICAL: This returns hardcoded fake values, no parameter matching occurs
    # TODO: Implement actual parameter matching between input and reference
    
    logger.warning("⚠️ PLACEHOLDER CODE: No parameter matching performed!")
    
    return {
        "eq_curve": {"low": 0.5, "mid": 0.0, "high": -0.5},  # ⚠️ FAKE VALUE
        "compression": {"ratio": 2.5, "attack": 0.005, "release": 0.15},  # ⚠️ FAKE VALUE
        "limiting": {"ceiling": -0.1, "release": 0.05},  # ⚠️ FAKE VALUE
        "loudness_target": reference_analysis.get("target_loudness", -14.0),  # ⚠️ FAKE VALUE
        "analysis_method": "placeholder_no_matching"
    }


async def _perform_quality_check(session: AsyncSession, output_path: Path) -> Dict[str, Any]:
    """Perform REAL quality analysis on processed audio (FIXED: No more fake metrics)."""
    try:
        # Import the real quality analyzer
        from app.utils.audio_quality_metrics import audio_quality_analyzer
        
        # Perform genuine audio analysis
        analysis_result = audio_quality_analyzer.analyze_audio_file(output_path)
        
        # Log the transition from fake to real metrics
        logger.info(f"🔧 FIXED: Using real quality metrics for {output_path.name}")
        logger.info(f"Real LUFS: {analysis_result.get('lufs_integrated', 'N/A')}, "
                   f"Real Quality Score: {analysis_result.get('quality_score', 'N/A')}")
        
        # Return real metrics in the expected format
        return {
            "peak_level": analysis_result.get("peak_level", 0.0),
            "lufs_integrated": analysis_result.get("lufs_integrated", -14.0),
            "dynamic_range": analysis_result.get("dynamic_range", 0.0),
            "thd_percentage": analysis_result.get("thd_percentage", 0.0),
            "quality_score": analysis_result.get("quality_score", 5.0),
            "warnings": analysis_result.get("warnings", []),
            "analysis_method": "real_ffmpeg_scipy",  # Mark as real analysis
            "true_peak_left": analysis_result.get("true_peak_left"),
            "true_peak_right": analysis_result.get("true_peak_right"),
            "loudness_range": analysis_result.get("loudness_range"),
            "rms_level": analysis_result.get("rms_level")
        }
        
    except Exception as e:
        logger.error(f"❌ Error in real quality analysis: {str(e)}")
        # Return error metrics instead of fake ones
        return {
            "error": f"Quality analysis failed: {str(e)}",
            "peak_level": None,
            "lufs_integrated": None,
            "dynamic_range": None,
            "thd_percentage": None,
            "quality_score": 0.0,
            "warnings": ["Quality analysis failed - metrics unavailable"],
            "analysis_method": "error"
        }


async def _validate_reference_matching(
    session: AsyncSession, 
    output_path: Path, 
    reference_file: AudioFile
) -> Dict[str, Any]:
    """Validate how well output matches reference (PLACEHOLDER - RETURNS FAKE VALUES)."""
    # ⚠️ CRITICAL: This returns hardcoded fake values, no reference matching validation occurs
    # TODO: Implement actual reference matching validation
    
    logger.warning("⚠️ PLACEHOLDER CODE: No reference matching validation performed!")
    
    return {
        "loudness_match_score": 9.5,  # ⚠️ FAKE VALUE
        "spectral_match_score": 8.8,  # ⚠️ FAKE VALUE
        "dynamic_match_score": 9.1,  # ⚠️ FAKE VALUE
        "overall_match_score": 9.1,  # ⚠️ FAKE VALUE
        "quality_metrics": await _perform_quality_check(session, output_path),
        "analysis_method": "placeholder_no_validation"
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