"""
Audio processing job management endpoints for Enhanced Matchering API.

Handles job creation, status tracking, queue management, and real-time progress updates.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import ValidationError, JobNotFoundError, JobStateError
from app.models.processing import ProcessingJob, JobProgress, JobStatus, ProcessingMode, ProcessingStage
from app.models.audio import AudioFile
from app.schemas.processing import (
    ProcessingJobCreate, 
    ProcessingJobAPIResponse, 
    ProcessingJobListAPIResponse,
    ProcessingJobDetailAPIResponse,
    ProcessingStatsAPIResponse,
    ProcessingModesAPIResponse,
    QueueStatusAPIResponse,
    ProcessingJobResponse,
    JobProgressResponse,
    ProcessingJobDetailResponse,
    ProcessingStatsResponse,
    ProcessingModesResponse,
    QueueStatusResponse,
    ProcessingModeInfo
)
from app.utils.request_utils import (
    generate_request_id, 
    get_client_ip, 
    create_api_response,
    create_error_response,
    create_pagination_response,
    create_task_response
)
from app.utils.validation_utils import validate_uuid_string, validate_pagination_params, validate_processing_mode
from app.workers.audio_tasks import process_audio_auto_master, process_audio_reference_master

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket connection manager
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Connect a WebSocket for a specific job."""
        logger.error(f"[DEBUG] WebSocketManager.connect called for job {job_id}")
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.error(f"[DEBUG] WebSocket connected for job {job_id}. Total connections: {len(self.active_connections[job_id])}")
        logger.info(f"WebSocket connected for job {job_id}. Total connections: {len(self.active_connections[job_id])}")
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """Disconnect a WebSocket for a specific job."""
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
                logger.info(f"WebSocket disconnected for job {job_id}. Remaining connections: {len(self.active_connections[job_id])}")
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
    
    async def broadcast_to_job(self, job_id: str, message: Dict):
        """Broadcast message to all WebSocket connections for a specific job."""
        if job_id not in self.active_connections:
            logger.warning(f"No active WebSocket connections for job {job_id}")
            return
        
        message_text = json.dumps(message)
        disconnected_connections = []
        
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                disconnected_connections.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection, job_id)

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

async def broadcast_message(job_id: str, message: Dict):
    """Public function to broadcast messages to WebSocket clients."""
    await websocket_manager.broadcast_to_job(job_id, message)


@router.post("/jobs/debug", response_model=Dict)
async def debug_processing_job(
    request: Request,
    raw_data: Dict = Body(...)
) -> Dict:
    """Debug endpoint to see what data frontend is sending."""
    request_id = generate_request_id()
    client_ip = get_client_ip(request)
    
    logger.info(f"Debug: Raw data received from {client_ip}, Request: {request_id}")
    logger.info(f"Debug: Raw data content: {json.dumps(raw_data, indent=2)}")
    
    return {
        "success": True,
        "request_id": request_id,
        "client_ip": client_ip,
        "raw_data": raw_data,
        "message": "Debug data logged successfully"
    }


@router.post("/jobs", response_model=ProcessingJobAPIResponse)
async def create_processing_job(
    request: Request,
    job_data: ProcessingJobCreate,
    db: AsyncSession = Depends(get_db)
) -> ProcessingJobAPIResponse:
    """
    Create a new processing job.
    
    Args:
        request: HTTP request object
        job_data: Processing job creation data
        db: Database session
        
    Returns:
        ProcessingJobAPIResponse: Created job information
        
    Raises:
        HTTPException: If job creation fails
    """
    request_id = generate_request_id()
    client_ip = get_client_ip(request)
    
    logger.info(f"Creating processing job - Mode: {job_data.processing_mode}, Client: {client_ip}, Request: {request_id}")
    
    # Debug: Log the actual job data received
    logger.info(f"Job data received: {job_data.model_dump()}")
    
    try:
        # Validate input file exists
        input_file_query = select(AudioFile).where(AudioFile.id == job_data.input_file_id)
        input_file_result = await db.execute(input_file_query)
        input_file = input_file_result.scalar_one_or_none()
        
        if not input_file:
            raise ValidationError(
                f"Input file not found: {job_data.input_file_id}",
                "INPUT_FILE_NOT_FOUND",
                {"input_file_id": str(job_data.input_file_id)}
            )
        
        # Check if input file is processing eligible
        if not input_file.processing_eligible:
            raise ValidationError(
                "Input file is not eligible for processing (analysis required)",
                "FILE_NOT_ELIGIBLE",
                {"input_file_id": str(job_data.input_file_id)}
            )
        
        # Validate reference file for reference mode
        reference_file = None
        if job_data.processing_mode == "reference":
            if not job_data.reference_file_id:
                raise ValidationError(
                    "Reference file required for reference mastering mode",
                    "REFERENCE_FILE_REQUIRED",
                    {"processing_mode": job_data.processing_mode}
                )
            
            reference_file_query = select(AudioFile).where(AudioFile.id == job_data.reference_file_id)
            reference_file_result = await db.execute(reference_file_query)
            reference_file = reference_file_result.scalar_one_or_none()
            
            if not reference_file:
                raise ValidationError(
                    f"Reference file not found: {job_data.reference_file_id}",
                    "REFERENCE_FILE_NOT_FOUND",
                    {"reference_file_id": str(job_data.reference_file_id)}
                )
        
        # Check for existing active jobs for the same input file
        active_job_query = select(ProcessingJob).where(
            and_(
                ProcessingJob.input_file_id == job_data.input_file_id,
                ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING])
            )
        )
        active_job_result = await db.execute(active_job_query)
        existing_job = active_job_result.scalar_one_or_none()
        
        if existing_job:
            logger.warning(f"Active job already exists for file {job_data.input_file_id}: {existing_job.id}")
            raise ValidationError(
                f"File already has an active processing job: {existing_job.id}",
                "ACTIVE_JOB_EXISTS",
                {
                    "existing_job_id": str(existing_job.id),
                    "existing_job_status": existing_job.status.value
                }
            )
        
        # Calculate queue position
        queue_count_query = select(func.count(ProcessingJob.id)).where(
            ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED])
        )
        queue_count_result = await db.execute(queue_count_query)
        queue_position = queue_count_result.scalar() + 1
        
        # Create processing job
        processing_job = ProcessingJob(
            id=uuid.uuid4(),
            input_file_id=job_data.input_file_id,
            reference_file_id=job_data.reference_file_id,
            processing_mode=ProcessingMode(job_data.processing_mode),
            settings=job_data.settings,
            status=JobStatus.PENDING,
            queue_position=queue_position,
            priority=job_data.priority
        )
        
        db.add(processing_job)
        await db.commit()
        await db.refresh(processing_job)
        
        # Start appropriate background task
        task_id = None
        if job_data.processing_mode == "auto":
            task = process_audio_auto_master.delay(str(processing_job.id))
            task_id = task.id
        elif job_data.processing_mode == "reference":
            task = process_audio_reference_master.delay(str(processing_job.id))
            task_id = task.id
        elif job_data.processing_mode == "hybrid":
            # Redirect to hybrid AI endpoint
            logger.info(f"Redirecting hybrid processing to hybrid AI endpoint for job: {processing_job.id}")
            # For now, use auto mastering as fallback
            task = process_audio_auto_master.delay(str(processing_job.id))
            task_id = task.id
        
        logger.info(f"Processing job created: {processing_job.id}, Task: {task_id}")
        
        # Create response
        job_response = ProcessingJobResponse(
            id=processing_job.id,
            input_file_id=processing_job.input_file_id,
            reference_file_id=processing_job.reference_file_id,
            output_file_path=processing_job.output_file_path,
            processing_mode=processing_job.processing_mode.value,
            settings=processing_job.settings,
            status=processing_job.status.value,
            queue_position=processing_job.queue_position,
            priority=processing_job.priority,
            created_at=processing_job.created_at,
            started_at=processing_job.started_at,
            completed_at=processing_job.completed_at,
            current_stage=processing_job.current_stage.value if processing_job.current_stage else None,
            progress_percentage=processing_job.progress_percentage,
            estimated_completion=processing_job.estimated_completion,
            result_metadata=processing_job.result_metadata,
            error_message=processing_job.error_message,
            error_code=processing_job.error_code,
            retry_count=processing_job.retry_count,
            processing_duration=processing_job.processing_duration,
            cpu_time=processing_job.cpu_time,
            memory_peak=processing_job.memory_peak
        )
        
        return create_api_response(data=job_response, request_id=request_id)
        
    except ValidationError as e:
        logger.warning(f"Job creation validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Job creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to create processing job",
                "error_code": "JOB_CREATION_ERROR",
                "request_id": request_id
            }
        )


@router.get("/jobs", response_model=ProcessingJobListAPIResponse)
async def list_processing_jobs(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of jobs to return"),
    status_filter: Optional[str] = Query(None, description="Filter by job status"),
    mode_filter: Optional[str] = Query(None, description="Filter by processing mode"),
    input_file_id: Optional[str] = Query(None, description="Filter by input file ID"),
    db: AsyncSession = Depends(get_db)
) -> ProcessingJobListAPIResponse:
    """
    List processing jobs with pagination and filtering.
    
    Args:
        request: HTTP request object
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        status_filter: Filter by job status
        mode_filter: Filter by processing mode
        input_file_id: Filter by input file ID
        db: Database session
        
    Returns:
        ProcessingJobListAPIResponse: Paginated list of jobs
    """
    request_id = generate_request_id()
    
    try:
        # Validate pagination
        validate_pagination_params(skip, limit)
        
        # Build query
        query = select(ProcessingJob)
        count_query = select(func.count(ProcessingJob.id))
        
        # Apply filters
        if status_filter:
            try:
                status = JobStatus(status_filter)
                query = query.where(ProcessingJob.status == status)
                count_query = count_query.where(ProcessingJob.status == status)
            except ValueError:
                raise ValidationError(
                    f"Invalid status filter: {status_filter}",
                    "INVALID_STATUS_FILTER",
                    {"status_filter": status_filter, "valid_statuses": [s.value for s in JobStatus]}
                )
        
        if mode_filter:
            validate_processing_mode(mode_filter)
            mode = ProcessingMode(mode_filter)
            query = query.where(ProcessingJob.processing_mode == mode)
            count_query = count_query.where(ProcessingJob.processing_mode == mode)
        
        if input_file_id:
            validate_uuid_string(input_file_id, "input_file_id")
            query = query.where(ProcessingJob.input_file_id == uuid.UUID(input_file_id))
            count_query = count_query.where(ProcessingJob.input_file_id == uuid.UUID(input_file_id))
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(ProcessingJob.created_at.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        # Convert to response models
        job_responses = []
        for job in jobs:
            job_responses.append(ProcessingJobResponse(
                id=job.id,
                input_file_id=job.input_file_id,
                reference_file_id=job.reference_file_id,
                output_file_path=job.output_file_path,
                processing_mode=job.processing_mode.value,
                settings=job.settings,
                status=job.status.value,
                queue_position=job.queue_position,
                priority=job.priority,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                current_stage=job.current_stage.value if job.current_stage else None,
                progress_percentage=job.progress_percentage,
                estimated_completion=job.estimated_completion,
                result_metadata=job.result_metadata,
                error_message=job.error_message,
                error_code=job.error_code,
                retry_count=job.retry_count,
                processing_duration=job.processing_duration,
                cpu_time=job.cpu_time,
                memory_peak=job.memory_peak
            ))
        
        return create_pagination_response(
            items=job_responses,
            total=total,
            skip=skip,
            limit=limit,
            request_id=request_id
        )
        
    except ValidationError as e:
        logger.warning(f"List jobs validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"List jobs failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve processing jobs",
                "error_code": "LIST_JOBS_ERROR",
                "request_id": request_id
            }
        )


@router.get("/jobs/{job_id}", response_model=ProcessingJobDetailAPIResponse)
async def get_processing_job(
    job_id: str,
    request: Request,
    include_progress: bool = Query(True, description="Include progress history"),
    include_files: bool = Query(True, description="Include file information"),
    db: AsyncSession = Depends(get_db)
) -> ProcessingJobDetailAPIResponse:
    """
    Get detailed processing job information.
    
    Args:
        job_id: Processing job identifier
        request: HTTP request object
        include_progress: Include progress history
        include_files: Include file information
        db: Database session
        
    Returns:
        ProcessingJobDetailAPIResponse: Detailed job information
    """
    request_id = generate_request_id()
    
    try:
        # Validate UUID
        validate_uuid_string(job_id, "job_id")
        
        # Query job
        query = select(ProcessingJob).where(ProcessingJob.id == uuid.UUID(job_id))
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Processing job not found: {job_id}",
                    "error_code": "JOB_NOT_FOUND",
                    "request_id": request_id
                }
            )
        
        # Build job response
        job_response = ProcessingJobResponse(
            id=job.id,
            input_file_id=job.input_file_id,
            reference_file_id=job.reference_file_id,
            output_file_path=job.output_file_path,
            processing_mode=job.processing_mode.value,
            settings=job.settings,
            status=job.status.value,
            queue_position=job.queue_position,
            priority=job.priority,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            current_stage=job.current_stage.value if job.current_stage else None,
            progress_percentage=job.progress_percentage,
            estimated_completion=job.estimated_completion,
            result_metadata=job.result_metadata,
            error_message=job.error_message,
            error_code=job.error_code,
            retry_count=job.retry_count,
            processing_duration=job.processing_duration,
            cpu_time=job.cpu_time,
            memory_peak=job.memory_peak
        )
        
        # Get progress history
        progress_history = []
        if include_progress:
            progress_query = select(JobProgress).where(
                JobProgress.job_id == job.id
            ).order_by(JobProgress.timestamp.asc())
            progress_result = await db.execute(progress_query)
            progress_entries = progress_result.scalars().all()
            
            for progress in progress_entries:
                progress_history.append(JobProgressResponse(
                    id=progress.id,
                    job_id=progress.job_id,
                    stage=progress.stage.value,
                    progress_percentage=progress.progress_percentage,
                    message=progress.message,
                    timestamp=progress.timestamp,
                    stage_started_at=progress.stage_started_at,
                    stage_duration=progress.stage_duration,
                    details=progress.details,
                    warnings=progress.warnings
                ))
        
        # Get file information
        input_file_info = None
        reference_file_info = None
        output_file_info = None
        
        if include_files:
            # Input file
            input_file_query = select(AudioFile).where(AudioFile.id == job.input_file_id)
            input_file_result = await db.execute(input_file_query)
            input_file = input_file_result.scalar_one_or_none()
            
            if input_file:
                input_file_info = {
                    "id": input_file.id,
                    "filename": input_file.filename,
                    "original_filename": input_file.original_filename,
                    "file_size": input_file.file_size,
                    "format": input_file.format,
                    "duration": input_file.duration
                }
            
            # Reference file
            if job.reference_file_id:
                reference_file_query = select(AudioFile).where(AudioFile.id == job.reference_file_id)
                reference_file_result = await db.execute(reference_file_query)
                reference_file = reference_file_result.scalar_one_or_none()
                
                if reference_file:
                    reference_file_info = {
                        "id": reference_file.id,
                        "filename": reference_file.filename,
                        "original_filename": reference_file.original_filename,
                        "file_size": reference_file.file_size,
                        "format": reference_file.format,
                        "duration": reference_file.duration
                    }
            
            # Output file info (from result metadata)
            if job.result_metadata and "output_file" in job.result_metadata:
                output_file_info = job.result_metadata["output_file"]
        
        detail_response = ProcessingJobDetailResponse(
            job=job_response,
            progress_history=progress_history,
            input_file=input_file_info,
            reference_file=reference_file_info,
            output_file=output_file_info
        )
        
        return create_api_response(data=detail_response, request_id=request_id)
        
    except ValidationError as e:
        logger.warning(f"Get job validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Get job failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve processing job",
                "error_code": "GET_JOB_ERROR",
                "request_id": request_id
            }
        )


@router.post("/jobs/{job_id}/cancel")
async def cancel_processing_job(
    job_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Cancel a processing job.
    
    Args:
        job_id: Processing job identifier
        request: HTTP request object
        db: Database session
        
    Returns:
        dict: Cancellation confirmation
    """
    request_id = generate_request_id()
    
    try:
        # Validate UUID
        validate_uuid_string(job_id, "job_id")
        
        # Get job
        query = select(ProcessingJob).where(ProcessingJob.id == uuid.UUID(job_id))
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Processing job not found: {job_id}",
                    "error_code": "JOB_NOT_FOUND",
                    "request_id": request_id
                }
            )
        
        # Check if job can be cancelled
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": f"Cannot cancel job with status: {job.status.value}",
                    "error_code": "JOB_NOT_CANCELLABLE",
                    "request_id": request_id,
                    "current_status": job.status.value
                }
            )
        
        # Update job status
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        job.error_message = "Job cancelled by user"
        job.error_code = "USER_CANCELLED"
        
        await db.commit()
        
        # TODO: Cancel the actual Celery task
        # from app.core.celery_app import celery_app
        # celery_app.control.revoke(task_id, terminate=True)
        
        logger.info(f"Processing job cancelled: {job_id}")
        
        return create_api_response(
            data={
                "job_id": job_id,
                "status": "cancelled",
                "message": "Job cancelled successfully",
                "cancelled_at": job.completed_at.isoformat()
            },
            request_id=request_id
        )
        
    except ValidationError as e:
        logger.warning(f"Cancel job validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Cancel job failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to cancel processing job",
                "error_code": "CANCEL_JOB_ERROR",
                "request_id": request_id
            }
        )


@router.get("/queue/status", response_model=QueueStatusAPIResponse)
async def get_queue_status(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> QueueStatusAPIResponse:
    """
    Get processing queue status.
    
    Args:
        request: HTTP request object
        db: Database session
        
    Returns:
        QueueStatusAPIResponse: Queue status information
    """
    request_id = generate_request_id()
    
    try:
        # Get total queued jobs
        queued_query = select(func.count(ProcessingJob.id)).where(
            ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED])
        )
        queued_result = await db.execute(queued_query)
        total_queued = queued_result.scalar()
        
        # Get jobs by priority
        priority_query = select(
            ProcessingJob.priority,
            func.count(ProcessingJob.id).label('count')
        ).where(
            ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED])
        ).group_by(ProcessingJob.priority)
        
        priority_result = await db.execute(priority_query)
        by_priority = {str(row.priority): row.count for row in priority_result}
        
        # Estimate wait time (simplified calculation)
        avg_processing_time = 300  # 5 minutes default
        estimated_wait_time = total_queued * avg_processing_time
        
        # Worker info (placeholder - would get from Celery in production)
        active_workers = 4
        worker_capacity = 8
        
        queue_status = QueueStatusResponse(
            total_queued=total_queued,
            by_queue={"default": total_queued},  # Single queue for now
            by_priority=by_priority,
            estimated_wait_time=estimated_wait_time,
            active_workers=active_workers,
            worker_capacity=worker_capacity
        )
        
        return create_api_response(data=queue_status, request_id=request_id)
        
    except Exception as e:
        logger.error(f"Get queue status failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve queue status",
                "error_code": "QUEUE_STATUS_ERROR",
                "request_id": request_id
            }
        )


@router.get("/stats", response_model=ProcessingStatsAPIResponse)
async def get_processing_stats(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ProcessingStatsAPIResponse:
    """
    Get processing statistics.
    
    Args:
        request: HTTP request object
        db: Database session
        
    Returns:
        ProcessingStatsAPIResponse: Processing statistics
    """
    request_id = generate_request_id()
    
    try:
        # Total jobs
        total_query = select(func.count(ProcessingJob.id))
        total_result = await db.execute(total_query)
        total_jobs = total_result.scalar()
        
        # Jobs by status
        status_query = select(
            ProcessingJob.status,
            func.count(ProcessingJob.id).label('count')
        ).group_by(ProcessingJob.status)
        
        status_result = await db.execute(status_query)
        jobs_by_status = {row.status.value: row.count for row in status_result}
        
        # Jobs by mode
        mode_query = select(
            ProcessingJob.processing_mode,
            func.count(ProcessingJob.id).label('count')
        ).group_by(ProcessingJob.processing_mode)
        
        mode_result = await db.execute(mode_query)
        jobs_by_mode = {row.processing_mode.value: row.count for row in mode_result}
        
        # Average processing time
        avg_time_query = select(func.avg(ProcessingJob.processing_duration)).where(
            and_(
                ProcessingJob.status == JobStatus.COMPLETED,
                ProcessingJob.processing_duration.is_not(None)
            )
        )
        avg_time_result = await db.execute(avg_time_query)
        average_processing_time = avg_time_result.scalar() or 0.0
        
        # Queue length
        queue_query = select(func.count(ProcessingJob.id)).where(
            ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED])
        )
        queue_result = await db.execute(queue_query)
        queue_length = queue_result.scalar()
        
        # 24-hour stats
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        completed_24h_query = select(func.count(ProcessingJob.id)).where(
            and_(
                ProcessingJob.status == JobStatus.COMPLETED,
                ProcessingJob.completed_at >= twenty_four_hours_ago
            )
        )
        completed_24h_result = await db.execute(completed_24h_query)
        jobs_completed_24h = completed_24h_result.scalar()
        
        failed_24h_query = select(func.count(ProcessingJob.id)).where(
            and_(
                ProcessingJob.status == JobStatus.FAILED,
                ProcessingJob.completed_at >= twenty_four_hours_ago
            )
        )
        failed_24h_result = await db.execute(failed_24h_query)
        jobs_failed_24h = failed_24h_result.scalar()
        
        stats = ProcessingStatsResponse(
            total_jobs=total_jobs,
            jobs_by_status=jobs_by_status,
            jobs_by_mode=jobs_by_mode,
            average_processing_time=average_processing_time,
            queue_length=queue_length,
            active_workers=4,  # Placeholder
            jobs_completed_24h=jobs_completed_24h,
            jobs_failed_24h=jobs_failed_24h,
            average_wait_time=queue_length * 300  # Simplified calculation
        )
        
        return create_api_response(data=stats, request_id=request_id)
        
    except Exception as e:
        logger.error(f"Get processing stats failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve processing statistics",
                "error_code": "STATS_ERROR",
                "request_id": request_id
            }
        )


@router.get("/modes", response_model=ProcessingModesAPIResponse)
async def get_processing_modes(
    request: Request
) -> ProcessingModesAPIResponse:
    """
    Get available processing modes.
    
    Args:
        request: HTTP request object
        
    Returns:
        ProcessingModesAPIResponse: Available processing modes
    """
    request_id = generate_request_id()
    
    modes = [
        ProcessingModeInfo(
            mode="auto",
            display_name="AI Auto-Mastering",
            description="Fully automated mastering using AI analysis and parameter prediction",
            requires_reference=False,
            estimated_duration=180.0,
            settings_schema={
                "type": "object",
                "properties": {
                    "quality": {
                        "type": "string",
                        "enum": ["draft", "standard", "high", "maximum"],
                        "default": "standard"
                    },
                    "loudness_target": {
                        "type": "number",
                        "minimum": -30,
                        "maximum": 0,
                        "default": -14
                    }
                }
            }
        ),
        ProcessingModeInfo(
            mode="reference",
            display_name="Reference-Based Mastering",
            description="Traditional reference-based mastering using target audio characteristics",
            requires_reference=True,
            estimated_duration=240.0,
            settings_schema={
                "type": "object",
                "properties": {
                    "quality": {
                        "type": "string",
                        "enum": ["draft", "standard", "high", "maximum"],
                        "default": "high"
                    },
                    "matching_strength": {
                        "type": "number",
                        "minimum": 0.1,
                        "maximum": 1.0,
                        "default": 0.8
                    }
                }
            }
        ),
        ProcessingModeInfo(
            mode="hybrid",
            display_name="Hybrid Processing",
            description="Combines AI analysis with reference-based techniques for optimal results",
            requires_reference=False,
            estimated_duration=300.0,
            settings_schema={
                "type": "object",
                "properties": {
                    "quality": {
                        "type": "string",
                        "enum": ["standard", "high", "maximum"],
                        "default": "high"
                    },
                    "ai_weight": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.7
                    }
                }
            }
        )
    ]
    
    modes_response = ProcessingModesResponse(
        modes=modes,
        default_mode="auto"
    )
    
    return create_api_response(data=modes_response, request_id=request_id)


@router.websocket("/ws/{job_id}")
async def websocket_job_updates(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress updates.
    
    Args:
        websocket: WebSocket connection
        job_id: Processing job identifier
    """
    try:
        logger.error(f"[DEBUG] WebSocket connection attempt for job {job_id}")
        print(f"[DEBUG] WebSocket connection attempt for job {job_id}")
        
        # Validate job exists
        validate_uuid_string(job_id, "job_id")
        
        # Connect to WebSocket manager
        logger.error(f"[DEBUG] Connecting WebSocket for job {job_id}")
        await websocket_manager.connect(websocket, job_id)
        logger.error(f"[DEBUG] WebSocket connected successfully for job {job_id}")
        
        # Send initial status
        initial_status = {
            "type": "connection_established",
            "payload": {
                "job_id": job_id,
                "message": "Connected to job progress updates"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        
        await websocket.send_text(json.dumps(initial_status))
        
        # Keep connection alive and listen for disconnect
        import asyncio
        try:
            while True:
                # Wait for any data (typically disconnect)
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info(f"WebSocket connection closed for job: {job_id}")
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for job: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        try:
            error_data = {
                "type": "error",
                "payload": {
                    "job_id": job_id,
                    "error": "Connection error occurred",
                    "error_code": "WEBSOCKET_ERROR"
                },
                "timestamp": datetime.utcnow().isoformat(),
                "message_id": str(uuid.uuid4())
            }
            await websocket.send_text(json.dumps(error_data))
        except:
            pass
    finally:
        # Ensure cleanup
        websocket_manager.disconnect(websocket, job_id)