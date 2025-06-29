"""
Audio upload and management endpoints for Enhanced Matchering API.

Handles file uploads, validation, analysis, and audio metadata management.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.core.database import get_db
from app.core.exceptions import AudioFileError, ValidationError, StorageError
from app.models.audio import AudioFile, AudioMetadata
from app.schemas.audio import (
    AudioFileAPIResponse, 
    AudioFileListAPIResponse, 
    AudioUploadAPIResponse,
    AudioFileDetailAPIResponse,
    DuplicateFileAPIResponse,
    AudioUploadRequest
)
from app.schemas.common import PaginationParams
from app.utils.file_utils import save_uploaded_file, validate_audio_file, calculate_file_checksum
from app.utils.validation_utils import validate_file_format, validate_file_size, validate_pagination_params
from app.utils.request_utils import (
    generate_request_id, 
    get_client_ip, 
    create_api_response,
    create_error_response,
    create_pagination_response,
    extract_request_metadata
)
from app.workers.file_tasks import validate_uploaded_file
from app.workers.analysis_tasks import analyze_audio_file

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=AudioUploadAPIResponse)
async def upload_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio file to upload"),
    processing_mode: str = Form("auto", description="Processing mode (auto, reference, hybrid)"),
    auto_analyze: bool = Form(True, description="Automatically analyze uploaded file"),
    db: AsyncSession = Depends(get_db)
) -> AudioUploadAPIResponse:
    """
    Upload audio file for processing.
    
    This endpoint handles file upload, validation, and optionally triggers
    automatic analysis. The file is validated for format, size, and duplicates.
    
    Args:
        request: HTTP request object
        background_tasks: FastAPI background tasks
        file: Audio file to upload
        processing_mode: Processing mode (auto, reference, hybrid)
        auto_analyze: Whether to automatically analyze the file
        db: Database session
        
    Returns:
        AudioUploadAPIResponse: Upload response with file metadata
        
    Raises:
        HTTPException: If upload fails due to validation or storage errors
    """
    request_id = generate_request_id()
    client_ip = get_client_ip(request)
    
    logger.info(f"Audio upload started - File: {file.filename}, Client: {client_ip}, Request: {request_id}")
    
    try:
        # Validate request
        if not file.filename:
            raise ValidationError("No filename provided", "NO_FILENAME", {})
        
        # Validate file format
        validate_file_format(file.filename)
        
        # Validate processing mode
        from app.utils.validation_utils import validate_processing_mode
        validate_processing_mode(processing_mode)
        
        # Log request metadata
        request_metadata = extract_request_metadata(request)
        logger.debug(f"Upload request metadata: {request_metadata}")
        
        # Save uploaded file
        file_path, checksum = await save_uploaded_file(file)
        
        # Validate the saved file
        validation_result = await validate_audio_file(file_path, file)
        
        # Check for duplicate files
        existing_file_query = select(AudioFile).where(AudioFile.checksum == checksum)
        existing_file_result = await db.execute(existing_file_query)
        existing_file = existing_file_result.scalar_one_or_none()
        
        if existing_file:
            # File already exists, clean up the duplicate
            try:
                file_path.unlink()
            except Exception:
                pass
            
            logger.info(f"Duplicate file detected: {checksum[:8]}... (existing: {existing_file.id})")
            
            return create_api_response(
                data={
                    "file_id": existing_file.id,
                    "filename": existing_file.filename,
                    "original_filename": existing_file.original_filename,
                    "file_size": existing_file.file_size,
                    "format": existing_file.format,
                    "upload_status": "duplicate",
                    "validation_task_id": None,
                    "analysis_task_id": None,
                    "processing_eligible": existing_file.processing_eligible,
                    "duration": existing_file.duration,
                    "sample_rate": existing_file.sample_rate,
                    "channels": existing_file.channels,
                    "upload_timestamp": existing_file.upload_timestamp,
                    "checksum": existing_file.checksum
                },
                request_id=request_id
            )
        
        # Create database record
        audio_file = AudioFile(
            id=uuid.uuid4(),
            filename=file_path.name,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=validation_result["file_size"],
            mime_type=validation_result["mime_type"],
            checksum=checksum,
            format=validation_result["format"],
            sample_rate=validation_result["audio_properties"].get("sample_rate", 44100),
            bit_depth=validation_result["audio_properties"].get("bit_depth"),
            channels=validation_result["audio_properties"].get("channels", 2),
            duration=validation_result["audio_properties"].get("duration", 0.0),
            processing_eligible=False  # Will be set to True after analysis
        )
        
        db.add(audio_file)
        await db.commit()
        await db.refresh(audio_file)
        
        # Trigger background tasks
        validation_task_id = None
        analysis_task_id = None
        
        if auto_analyze:
            # Start analysis task
            analysis_task = analyze_audio_file.delay(str(audio_file.id))
            analysis_task_id = analysis_task.id
            logger.info(f"Started analysis task {analysis_task_id} for file {audio_file.id}")
        
        logger.info(f"Audio upload completed - File ID: {audio_file.id}, Size: {audio_file.file_size} bytes")
        
        return create_api_response(
            data={
                "file_id": audio_file.id,
                "filename": audio_file.filename,
                "original_filename": audio_file.original_filename,
                "file_size": audio_file.file_size,
                "format": audio_file.format,
                "upload_status": "completed",
                "validation_task_id": validation_task_id,
                "analysis_task_id": analysis_task_id,
                "processing_eligible": audio_file.processing_eligible,
                "duration": audio_file.duration,
                "sample_rate": audio_file.sample_rate,
                "channels": audio_file.channels,
                "upload_timestamp": audio_file.upload_timestamp,
                "checksum": audio_file.checksum
            },
            request_id=request_id
        )
        
    except ValidationError as e:
        logger.warning(f"Upload validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except StorageError as e:
        logger.error(f"Upload storage failed: {e.message}")
        raise HTTPException(status_code=500, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Upload failed with unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "Internal server error during upload",
                "error_code": "UPLOAD_ERROR",
                "request_id": request_id
            }
        )


@router.get("/files", response_model=AudioFileListAPIResponse)
async def list_audio_files(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    format_filter: Optional[str] = None,
    processing_eligible_only: bool = False,
    db: AsyncSession = Depends(get_db)
) -> AudioFileListAPIResponse:
    """
    List uploaded audio files with pagination and filtering.
    
    Args:
        request: HTTP request object
        skip: Number of files to skip for pagination
        limit: Maximum number of files to return
        format_filter: Filter by audio format (wav, mp3, flac, etc.)
        processing_eligible_only: Only return files eligible for processing
        db: Database session
        
    Returns:
        AudioFileListAPIResponse: Paginated list of audio files
        
    Raises:
        HTTPException: If validation fails
    """
    request_id = generate_request_id()
    
    try:
        # Validate pagination parameters
        validate_pagination_params(skip, limit)
        
        # Build query
        query = select(AudioFile)
        count_query = select(func.count(AudioFile.id))
        
        # Apply filters
        if format_filter:
            query = query.where(AudioFile.format == format_filter.lower())
            count_query = count_query.where(AudioFile.format == format_filter.lower())
        
        if processing_eligible_only:
            query = query.where(AudioFile.processing_eligible == True)
            count_query = count_query.where(AudioFile.processing_eligible == True)
        
        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(AudioFile.upload_timestamp.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        audio_files = result.scalars().all()
        
        # Convert to response models
        file_responses = []
        for audio_file in audio_files:
            file_responses.append({
                "id": audio_file.id,
                "filename": audio_file.filename,
                "original_filename": audio_file.original_filename,
                "file_path": audio_file.file_path,
                "file_size": audio_file.file_size,
                "mime_type": audio_file.mime_type,
                "checksum": audio_file.checksum,
                "format": audio_file.format,
                "sample_rate": audio_file.sample_rate,
                "bit_depth": audio_file.bit_depth,
                "channels": audio_file.channels,
                "duration": audio_file.duration,
                "upload_timestamp": audio_file.upload_timestamp,
                "processing_eligible": audio_file.processing_eligible
            })
        
        return create_pagination_response(
            items=file_responses,
            total=total,
            skip=skip,
            limit=limit,
            request_id=request_id
        )
        
    except ValidationError as e:
        logger.warning(f"List validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"List files failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve audio files",
                "error_code": "LIST_ERROR",
                "request_id": request_id
            }
        )


@router.get("/files/{file_id}", response_model=AudioFileDetailAPIResponse)
async def get_audio_file(
    file_id: str,
    request: Request,
    include_metadata: bool = True,
    include_processing_jobs: bool = False,
    db: AsyncSession = Depends(get_db)
) -> AudioFileDetailAPIResponse:
    """
    Get detailed audio file information by ID.
    
    Args:
        file_id: Audio file identifier (UUID)
        request: HTTP request object
        include_metadata: Include audio analysis metadata
        include_processing_jobs: Include associated processing jobs
        db: Database session
        
    Returns:
        AudioFileDetailAPIResponse: Detailed audio file information
        
    Raises:
        HTTPException: If file not found or invalid UUID
    """
    request_id = generate_request_id()
    
    try:
        # Validate UUID format
        from app.utils.validation_utils import validate_uuid_string
        validate_uuid_string(file_id, "file_id")
        
        # Query audio file
        query = select(AudioFile).where(AudioFile.id == uuid.UUID(file_id))
        result = await db.execute(query)
        audio_file = result.scalar_one_or_none()
        
        if not audio_file:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Audio file not found: {file_id}",
                    "error_code": "FILE_NOT_FOUND",
                    "request_id": request_id
                }
            )
        
        # Build response
        file_response = {
            "id": audio_file.id,
            "filename": audio_file.filename,
            "original_filename": audio_file.original_filename,
            "file_path": audio_file.file_path,
            "file_size": audio_file.file_size,
            "mime_type": audio_file.mime_type,
            "checksum": audio_file.checksum,
            "format": audio_file.format,
            "sample_rate": audio_file.sample_rate,
            "bit_depth": audio_file.bit_depth,
            "channels": audio_file.channels,
            "duration": audio_file.duration,
            "upload_timestamp": audio_file.upload_timestamp,
            "processing_eligible": audio_file.processing_eligible
        }
        
        metadata_response = None
        if include_metadata:
            # Query metadata
            metadata_query = select(AudioMetadata).where(AudioMetadata.audio_file_id == audio_file.id)
            metadata_result = await db.execute(metadata_query)
            metadata = metadata_result.scalar_one_or_none()
            
            if metadata:
                metadata_response = {
                    "id": metadata.id,
                    "audio_file_id": metadata.audio_file_id,
                    "rms_level": metadata.rms_level,
                    "peak_level": metadata.peak_level,
                    "dynamic_range": metadata.dynamic_range,
                    "spectral_centroid": metadata.spectral_centroid,
                    "spectral_rolloff": metadata.spectral_rolloff,
                    "zero_crossing_rate": metadata.zero_crossing_rate,
                    "lufs_integrated": metadata.lufs_integrated,
                    "lufs_short_term": metadata.lufs_short_term,
                    "lufs_momentary": metadata.lufs_momentary,
                    "true_peak": metadata.true_peak,
                    "mfcc_features": metadata.mfcc_features,
                    "spectral_features": metadata.spectral_features,
                    "tempo_features": metadata.tempo_features,
                    "analysis_version": metadata.analysis_version,
                    "analysis_timestamp": metadata.analysis_timestamp,
                    "analysis_duration": metadata.analysis_duration
                }
        
        processing_jobs = []
        if include_processing_jobs:
            # Query processing jobs
            from app.models.processing import ProcessingJob
            jobs_query = select(ProcessingJob).where(ProcessingJob.input_file_id == audio_file.id)
            jobs_result = await db.execute(jobs_query)
            jobs = jobs_result.scalars().all()
            
            for job in jobs:
                processing_jobs.append({
                    "id": job.id,
                    "status": job.status.value,
                    "processing_mode": job.processing_mode.value,
                    "created_at": job.created_at,
                    "progress_percentage": job.progress_percentage
                })
        
        return create_api_response(
            data={
                "file": file_response,
                "metadata": metadata_response,
                "processing_jobs": processing_jobs
            },
            request_id=request_id
        )
        
    except ValidationError as e:
        logger.warning(f"Get file validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Get file failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to retrieve audio file",
                "error_code": "GET_FILE_ERROR",
                "request_id": request_id
            }
        )


@router.get("/files/{file_id}/stream")
async def stream_audio_file(
    file_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """
    Stream audio file content for playback.
    
    Args:
        file_id: Audio file identifier (UUID)
        request: HTTP request object
        db: Database session
        
    Returns:
        FileResponse: Audio file content with appropriate headers
        
    Raises:
        HTTPException: If file not found or inaccessible
    """
    request_id = generate_request_id()
    
    try:
        # Validate UUID format
        from app.utils.validation_utils import validate_uuid_string
        validate_uuid_string(file_id, "file_id")
        
        # Query audio file
        query = select(AudioFile).where(AudioFile.id == uuid.UUID(file_id))
        result = await db.execute(query)
        audio_file = result.scalar_one_or_none()
        
        if not audio_file:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Audio file not found: {file_id}",
                    "error_code": "FILE_NOT_FOUND",
                    "request_id": request_id
                }
            )
        
        # Check if physical file exists
        file_path = Path(audio_file.file_path)
        if not file_path.exists():
            logger.error(f"Physical file missing: {file_path}")
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Audio file content not found: {file_id}",
                    "error_code": "FILE_CONTENT_NOT_FOUND", 
                    "request_id": request_id
                }
            )
        
        # Determine media type based on file format
        media_type_map = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "flac": "audio/flac",
            "aiff": "audio/aiff",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg"
        }
        
        media_type = media_type_map.get(audio_file.format.lower(), "audio/wav")
        
        logger.info(f"Streaming audio file: {file_id} ({file_path.name})")
        
        # Return file response with proper headers for audio streaming
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=audio_file.original_filename,
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
                "X-File-ID": str(audio_file.id),
                "X-Request-ID": request_id
            }
        )
        
    except ValidationError as e:
        logger.warning(f"Stream validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Stream file failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to stream audio file",
                "error_code": "STREAM_ERROR",
                "request_id": request_id
            }
        )


@router.delete("/files/{file_id}")
async def delete_audio_file(
    file_id: str,
    request: Request,
    force: bool = False,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Delete audio file and associated data.
    
    Args:
        file_id: Audio file identifier (UUID)
        request: HTTP request object
        force: Force deletion even if file has processing jobs
        db: Database session
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If file not found or deletion fails
    """
    request_id = generate_request_id()
    
    try:
        # Validate UUID format
        from app.utils.validation_utils import validate_uuid_string
        validate_uuid_string(file_id, "file_id")
        
        # Query audio file
        query = select(AudioFile).where(AudioFile.id == uuid.UUID(file_id))
        result = await db.execute(query)
        audio_file = result.scalar_one_or_none()
        
        if not audio_file:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Audio file not found: {file_id}",
                    "error_code": "FILE_NOT_FOUND",
                    "request_id": request_id
                }
            )
        
        # Check for active processing jobs
        if not force:
            from app.models.processing import ProcessingJob, JobStatus
            active_jobs_query = select(func.count(ProcessingJob.id)).where(
                ProcessingJob.input_file_id == audio_file.id,
                ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.QUEUED, JobStatus.PROCESSING])
            )
            active_jobs_result = await db.execute(active_jobs_query)
            active_jobs_count = active_jobs_result.scalar()
            
            if active_jobs_count > 0:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": f"Cannot delete file with {active_jobs_count} active processing jobs. Use force=true to override.",
                        "error_code": "ACTIVE_JOBS_EXIST",
                        "request_id": request_id,
                        "active_jobs": active_jobs_count
                    }
                )
        
        # Delete physical file
        file_path = Path(audio_file.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted physical file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete physical file {file_path}: {e}")
        
        # Delete database records (cascade will handle related records)
        await db.delete(audio_file)
        await db.commit()
        
        logger.info(f"Audio file deleted: {file_id}")
        
        return create_api_response(
            data={
                "file_id": file_id,
                "filename": audio_file.filename,
                "deleted": True,
                "deleted_at": datetime.utcnow().isoformat()
            },
            request_id=request_id
        )
        
    except ValidationError as e:
        logger.warning(f"Delete validation failed: {e.message}")
        raise HTTPException(status_code=400, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Delete file failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to delete audio file",
                "error_code": "DELETE_ERROR",
                "request_id": request_id
            }
        )


@router.post("/check-duplicate", response_model=DuplicateFileAPIResponse)
async def check_duplicate_file(
    request: Request,
    file: UploadFile = File(..., description="Audio file to check"),
    db: AsyncSession = Depends(get_db)
) -> DuplicateFileAPIResponse:
    """
    Check if uploaded file is a duplicate without saving it.
    
    Args:
        request: HTTP request object
        file: Audio file to check
        db: Database session
        
    Returns:
        DuplicateFileAPIResponse: Duplicate check result
    """
    request_id = generate_request_id()
    
    try:
        # Calculate checksum of uploaded file
        content = await file.read()
        await file.seek(0)  # Reset file position
        
        import hashlib
        checksum = hashlib.sha256(content).hexdigest()
        
        # Check for existing file with same checksum
        query = select(AudioFile).where(AudioFile.checksum == checksum)
        result = await db.execute(query)
        existing_file = result.scalar_one_or_none()
        
        if existing_file:
            return create_api_response(
                data={
                    "is_duplicate": True,
                    "existing_file_id": existing_file.id,
                    "existing_filename": existing_file.filename,
                    "checksum": checksum,
                    "message": f"File already exists as '{existing_file.filename}'"
                },
                request_id=request_id
            )
        else:
            return create_api_response(
                data={
                    "is_duplicate": False,
                    "existing_file_id": None,
                    "existing_filename": None,
                    "checksum": checksum,
                    "message": "File is unique and can be uploaded"
                },
                request_id=request_id
            )
    
    except Exception as e:
        logger.error(f"Duplicate check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Failed to check for duplicate file",
                "error_code": "DUPLICATE_CHECK_ERROR",
                "request_id": request_id
            }
        )