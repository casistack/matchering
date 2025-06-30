"""
Hybrid Processing API Endpoints.

This module provides FastAPI endpoints for the hybrid processing engine,
including real-time WebSocket progress updates and comprehensive processing orchestration.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import (
    APIRouter, 
    Depends, 
    File, 
    Form,
    HTTPException, 
    UploadFile, 
    WebSocket,
    WebSocketDisconnect,
    status,
    BackgroundTasks
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.ai.hybrid_processing_engine import (
    HybridProcessingEngine,
    HybridProcessingRequest,
    HybridProcessingResult,
    ProcessingMode,
    ProcessingProgress
)
from app.ai.production_model_manager import ProductionModelManager
from app.core.database import get_db
from app.utils.file_utils import save_uploaded_file
from app.models.processing import ProcessingJob, JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Hybrid Processing"])

# Global processing engine instance
processing_engine: Optional[HybridProcessingEngine] = None
active_websockets: Dict[str, WebSocket] = {}


def get_processing_engine() -> HybridProcessingEngine:
    """Get or create the processing engine instance."""
    global processing_engine
    if processing_engine is None:
        try:
            processing_engine = HybridProcessingEngine()
            # Note: Initialization will be done asynchronously
            logger.info("Hybrid processing engine created")
        except Exception as e:
            logger.error(f"Failed to create processing engine: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Processing engine initialization failed"
            )
    return processing_engine


class HybridProcessingJobRequest(BaseModel):
    """Request model for creating a hybrid processing job."""
    
    processing_mode: ProcessingMode = Field(default=ProcessingMode.HYBRID)
    ai_model_preference: str = Field(default="auto")
    ai_intensity: float = Field(default=0.7, ge=0.0, le=1.0)
    reference_influence: float = Field(default=0.5, ge=0.0, le=1.0)
    ai_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    reference_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    adaptive_blending: bool = Field(default=True)
    preserve_dynamics: bool = Field(default=True)
    target_loudness_lufs: float = Field(default=-14.0, ge=-30.0, le=-6.0)
    target_sample_rate: int = Field(default=44100)
    output_format: str = Field(default="wav")
    enable_quality_validation: bool = Field(default=True)
    enable_real_time_progress: bool = Field(default=True)
    max_processing_time: float = Field(default=300.0, gt=0.0, le=600.0)


class HybridProcessingJobResponse(BaseModel):
    """Response model for hybrid processing job creation."""
    
    job_id: str
    status: str
    processing_mode: ProcessingMode
    estimated_duration: float
    websocket_url: str
    created_at: str


class ProcessingStatusResponse(BaseModel):
    """Response model for processing status."""
    
    job_id: str
    status: str
    progress_percentage: float
    current_stage: str
    message: str
    processing_time: float
    estimated_remaining: Optional[float] = None
    metadata: Dict = Field(default_factory=dict)


@router.post("/jobs", response_model=HybridProcessingJobResponse)
async def create_processing_job(
    request: HybridProcessingJobRequest,
    input_file: UploadFile = File(..., description="Input audio file"),
    reference_file: Optional[UploadFile] = File(None, description="Reference audio file (required for reference/hybrid modes)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new hybrid processing job.
    
    This endpoint accepts audio files and processing parameters,
    creates a background processing job, and returns a job ID
    for tracking progress via WebSocket.
    """
    try:
        # Validate files
        if not input_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input file is required"
            )
        
        if request.processing_mode in [ProcessingMode.REFERENCE_ONLY, ProcessingMode.HYBRID]:
            if not reference_file or not reference_file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Reference file is required for {request.processing_mode.value} mode"
                )
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded files
        input_path = await save_uploaded_file(input_file, f"input_{job_id}")
        reference_path = None
        if reference_file:
            reference_path = await save_uploaded_file(reference_file, f"reference_{job_id}")
        
        # Create output path
        output_dir = Path("temp") / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"output_{job_id}.{request.output_format}"
        
        # Create processing request
        processing_request = HybridProcessingRequest(
            input_file_path=str(input_path),
            reference_file_path=str(reference_path) if reference_path else None,
            output_file_path=str(output_path),
            processing_mode=request.processing_mode,
            ai_model_preference=request.ai_model_preference,
            ai_intensity=request.ai_intensity,
            reference_influence=request.reference_influence,
            ai_weight=request.ai_weight,
            reference_weight=request.reference_weight,
            adaptive_blending=request.adaptive_blending,
            preserve_dynamics=request.preserve_dynamics,
            target_loudness_lufs=request.target_loudness_lufs,
            target_sample_rate=request.target_sample_rate,
            output_format=request.output_format,
            enable_quality_validation=request.enable_quality_validation,
            enable_real_time_progress=request.enable_real_time_progress,
            max_processing_time=request.max_processing_time
        )
        
        # Create database job record
        job = ProcessingJob(
            id=job_id,
            input_file_path=str(input_path),
            reference_file_path=str(reference_path) if reference_path else None,
            output_file_path=str(output_path),
            processing_mode=request.processing_mode.value,
            status=JobStatus.PENDING,
            metadata={
                "ai_model_preference": request.ai_model_preference,
                "ai_intensity": request.ai_intensity,
                "processing_parameters": request.dict()
            }
        )
        
        db.add(job)
        await db.commit()
        
        # Start background processing
        background_tasks.add_task(
            process_audio_background,
            job_id,
            processing_request
        )
        
        # Estimate processing duration
        estimated_duration = estimate_processing_duration(request.processing_mode, input_file.size)
        
        return HybridProcessingJobResponse(
            job_id=job_id,
            status="pending",
            processing_mode=request.processing_mode,
            estimated_duration=estimated_duration,
            websocket_url=f"/api/v1/hybrid-processing/ws/{job_id}",
            created_at=job.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to create processing job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create processing job: {str(e)}"
        )


@router.get("/jobs/{job_id}/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the current status of a processing job."""
    try:
        # Get job from database
        job = await db.get(ProcessingJob, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing job not found"
            )
        
        # Calculate processing time
        processing_time = 0.0
        if job.started_at:
            from datetime import datetime
            if job.completed_at:
                processing_time = (job.completed_at - job.started_at).total_seconds()
            else:
                processing_time = (datetime.utcnow() - job.started_at).total_seconds()
        
        # Get latest progress
        latest_progress = None
        if job.progress:
            latest_progress = job.progress[-1] if isinstance(job.progress, list) else job.progress
        
        progress_percentage = latest_progress.get('percentage', 0.0) if latest_progress else 0.0
        current_stage = latest_progress.get('stage', 'pending') if latest_progress else 'pending'
        message = latest_progress.get('message', 'Job pending') if latest_progress else 'Job pending'
        
        # Estimate remaining time
        estimated_remaining = None
        if progress_percentage > 0 and job.status == JobStatus.PROCESSING:
            estimated_total = processing_time / (progress_percentage / 100.0)
            estimated_remaining = max(0, estimated_total - processing_time)
        
        return ProcessingStatusResponse(
            job_id=job_id,
            status=job.status.value,
            progress_percentage=progress_percentage,
            current_stage=current_stage,
            message=message,
            processing_time=processing_time,
            estimated_remaining=estimated_remaining,
            metadata=job.metadata or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get processing status"
        )


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time processing progress updates.
    
    Clients can connect to this endpoint to receive live updates
    about processing progress, including stage changes, percentages,
    and detailed metadata.
    """
    await websocket.accept()
    active_websockets[job_id] = websocket
    
    try:
        logger.info(f"WebSocket connected for job {job_id}")
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "job_id": job_id,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client messages (like ping/pong)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client messages
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from client: {message}")
                    
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({
                    "type": "keepalive",
                    "timestamp": asyncio.get_event_loop().time()
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        # Clean up
        if job_id in active_websockets:
            del active_websockets[job_id]


@router.get("/jobs")
async def list_processing_jobs(
    limit: int = 10,
    offset: int = 0,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List processing jobs with optional filtering."""
    try:
        from sqlalchemy import select
        
        query = select(ProcessingJob).offset(offset).limit(limit).order_by(ProcessingJob.created_at.desc())
        
        if status_filter:
            query = query.where(ProcessingJob.status == status_filter)
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return [
            {
                "job_id": job.id,
                "status": job.status.value,
                "processing_mode": job.processing_mode,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "metadata": job.metadata
            }
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"Failed to list processing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list processing jobs"
        )


@router.delete("/jobs/{job_id}")
async def cancel_processing_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a processing job."""
    try:
        job = await db.get(ProcessingJob, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing job not found"
            )
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status: {job.status.value}"
            )
        
        # Update job status
        job.status = JobStatus.CANCELLED
        await db.commit()
        
        # Notify WebSocket clients
        if job_id in active_websockets:
            await active_websockets[job_id].send_json({
                "type": "job_cancelled",
                "job_id": job_id,
                "timestamp": asyncio.get_event_loop().time()
            })
        
        return {"message": "Job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel processing job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel processing job"
        )


@router.get("/engine/status")
async def get_engine_status():
    """Get the status of the processing engine."""
    try:
        engine = get_processing_engine()
        
        # Get model manager stats if available
        stats = {}
        if hasattr(engine, 'model_manager') and engine.model_manager:
            stats = engine.model_manager.get_memory_stats()
        
        return {
            "engine_initialized": engine is not None,
            "active_websockets": len(active_websockets),
            "device": engine.device if engine else "unknown",
            "model_stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get engine status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get engine status"
        )


async def process_audio_background(job_id: str, request: HybridProcessingRequest):
    """Background task for processing audio."""
    from app.core.database import AsyncSessionLocal
    
    session = AsyncSessionLocal()
    
    try:
        # Update job status to processing
        job = await session.get(ProcessingJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found in database")
            return
        
        job.status = JobStatus.PROCESSING
        job.started_at = asyncio.get_event_loop().time()
        await session.commit()
        
        # Initialize processing engine if needed
        engine = get_processing_engine()
        if not hasattr(engine, '_initialized') or not engine._initialized:
            await engine.initialize()
            engine._initialized = True
        
        # Add progress callback for WebSocket updates
        async def progress_callback(progress: ProcessingProgress):
            # Update database
            if not job.progress:
                job.progress = []
            elif not isinstance(job.progress, list):
                job.progress = [job.progress]
            
            job.progress.append({
                "stage": progress.stage.value,
                "percentage": progress.percentage,
                "message": progress.message,
                "timestamp": progress.timestamp,
                "metadata": progress.metadata
            })
            await session.commit()
            
            # Send WebSocket update
            if job_id in active_websockets:
                try:
                    await active_websockets[job_id].send_json({
                        "type": "progress_update",
                        "job_id": job_id,
                        "stage": progress.stage.value,
                        "percentage": progress.percentage,
                        "message": progress.message,
                        "timestamp": progress.timestamp,
                        "metadata": progress.metadata
                    })
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket update: {e}")
        
        engine.add_progress_callback(progress_callback)
        
        # Process audio
        result = await engine.process_audio(request)
        
        # Update job with results
        if result.success:
            job.status = JobStatus.COMPLETED
            job.output_file_path = str(result.output_path) if result.output_path else None
            job.metadata.update({
                "processing_time": result.processing_time,
                "applied_parameters": result.applied_parameters.dict(),
                "quality_metrics": result.quality_metrics,
                "ai_confidence": result.ai_confidence,
                "reference_influence": result.reference_influence
            })
        else:
            job.status = JobStatus.FAILED
            job.error_message = result.error_message
        
        job.completed_at = asyncio.get_event_loop().time()
        await session.commit()
        
        # Send final WebSocket update
        if job_id in active_websockets:
            try:
                await active_websockets[job_id].send_json({
                    "type": "job_completed" if result.success else "job_failed",
                    "job_id": job_id,
                    "success": result.success,
                    "processing_time": result.processing_time,
                    "output_path": str(result.output_path) if result.output_path else None,
                    "error_message": result.error_message,
                    "metadata": result.metadata,
                    "timestamp": asyncio.get_event_loop().time()
                })
            except Exception as e:
                logger.warning(f"Failed to send final WebSocket update: {e}")
        
        logger.info(f"Processing job {job_id} completed: {result.success}")
        
    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {e}")
        
        # Update job status to failed
        try:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = asyncio.get_event_loop().time()
            await session.commit()
            
            # Send error WebSocket update
            if job_id in active_websockets:
                await active_websockets[job_id].send_json({
                    "type": "job_failed",
                    "job_id": job_id,
                    "success": False,
                    "error_message": str(e),
                    "timestamp": asyncio.get_event_loop().time()
                })
        except Exception as update_error:
            logger.error(f"Failed to update job status after error: {update_error}")
    
    finally:
        await session.close()


def estimate_processing_duration(mode: ProcessingMode, file_size: int) -> float:
    """Estimate processing duration based on mode and file size."""
    # Base time estimates (in seconds)
    base_times = {
        ProcessingMode.AI_ONLY: 30.0,
        ProcessingMode.REFERENCE_ONLY: 20.0,
        ProcessingMode.HYBRID: 45.0
    }
    
    # Adjust based on file size (rough estimate)
    size_factor = max(1.0, file_size / (10 * 1024 * 1024))  # 10MB baseline
    
    return base_times.get(mode, 30.0) * size_factor