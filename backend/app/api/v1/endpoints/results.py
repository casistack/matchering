"""
Processing results and download endpoints.

Handles result retrieval, file downloads, and result metadata.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
import os
from pathlib import Path

from app.core.database import get_db
from app.core.exceptions import JobNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/download/{filename}")
async def download_result_by_filename(filename: str) -> FileResponse:
    """
    Download a processed audio file by filename.
    
    Args:
        filename: Name of the processed audio file
        
    Returns:
        FileResponse: Processed audio file
        
    Raises:
        HTTPException: If file not found
    """
    logger.info(f"Download requested for filename: {filename}")
    
    # Look for the file in results directory
    results_dir = Path("results")
    file_path = results_dir / filename
    
    logger.info(f"Looking for file: {file_path.absolute()}")
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path.absolute()}")
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    file_size = file_path.stat().st_size
    logger.info(f"Serving file: {file_path} ({file_size} bytes)")
    
    return FileResponse(
        path=str(file_path),
        media_type="audio/wav",
        filename=filename
    )


@router.get("/{job_id}")
async def get_processing_results(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get processing results for a completed job.
    
    Args:
        job_id: Processing job identifier
        db: Database session
        
    Returns:
        dict: Processing results with metadata
        
    Raises:
        JobNotFoundError: If job not found
        HTTPException: If job not completed
    """
    # Placeholder implementation
    logger.info(f"Retrieving results for job: {job_id}")
    
    return {
        "success": True,
        "data": {
            "jobId": job_id,
            "status": "completed",
            "result": {
                "success": True,
                "outputPath": f"/results/{job_id}/mastered.wav",
                "metadata": {
                    "filename": "mastered.wav",
                    "format": "wav",
                    "sampleRate": 44100,
                    "bitDepth": 24,
                    "channels": 2,
                    "duration": 180.5,
                    "fileSize": 12345678,
                    "checksum": "abc123def456"
                },
                "metrics": {
                    "rms": 0.75,
                    "peak": 0.95,
                    "dynamicRange": 8.5,
                    "spectralCentroid": 2500.0,
                    "lufs": -14.2,
                    "truePeak": -0.1
                },
                "processingTime": 45000
            },
            "downloadUrl": f"/api/v1/results/{job_id}/download"
        },
        "error": None,
        "timestamp": "",
        "requestId": "placeholder-request-id"
    }


@router.get("/{job_id}/download")
async def download_result(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    """
    Download the processed audio file.
    
    Args:
        job_id: Processing job identifier
        db: Database session
        
    Returns:
        FileResponse: Processed audio file
        
    Raises:
        JobNotFoundError: If job not found
        HTTPException: If file not available
    """
    logger.info(f"Download requested for job: {job_id}")
    
    # Look for processed files in results directory (relative to backend directory)
    results_dir = Path("results")
    logger.info(f"Looking for files in: {results_dir.absolute()}")
    
    if not results_dir.exists():
        logger.error(f"Results directory does not exist: {results_dir.absolute()}")
        raise HTTPException(status_code=404, detail="Results directory not found")
    
    # Try to find the processed file for this job
    # Look for files ending with _mastered.wav
    mastered_files = list(results_dir.glob("*_mastered.wav"))
    logger.info(f"Found {len(mastered_files)} mastered files: {[f.name for f in mastered_files]}")
    
    if not mastered_files:
        logger.error(f"No mastered files found in {results_dir}")
        raise HTTPException(status_code=404, detail="Processed file not found")
    
    # For now, return the most recent mastered file
    # TODO: Implement proper job-to-file mapping in database
    most_recent_file = max(mastered_files, key=lambda f: f.stat().st_mtime)
    
    if not most_recent_file.exists():
        logger.error(f"File not found: {most_recent_file}")
        raise HTTPException(status_code=404, detail="Processed file not found")
    
    file_size = most_recent_file.stat().st_size
    logger.info(f"Serving file: {most_recent_file} ({file_size} bytes)")
    
    return FileResponse(
        path=str(most_recent_file),
        media_type="audio/wav",
        filename=most_recent_file.name
    )


@router.get("/{job_id}/metadata")
async def get_result_metadata(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get detailed metadata for processing results.
    
    Args:
        job_id: Processing job identifier
        db: Database session
        
    Returns:
        dict: Detailed result metadata
    """
    # Placeholder implementation
    return {
        "success": True,
        "data": {
            "jobId": job_id,
            "processingInfo": {
                "mode": "auto",
                "settings": {
                    "intensity": "medium",
                    "eqStyle": "balanced",
                    "preserveDynamics": True,
                    "targetLoudness": -14
                },
                "aiParameters": {
                    "eqCurve": [0.1, 0.2, 0.0, -0.1, 0.3],
                    "compression": {"ratio": 3.2, "attack": 5, "release": 50},
                    "limiting": {"threshold": -0.5, "release": 30}
                },
                "processingStages": [
                    {"stage": "validation", "duration": 1.2, "status": "completed"},
                    {"stage": "feature_extraction", "duration": 8.5, "status": "completed"},
                    {"stage": "ai_analysis", "duration": 12.3, "status": "completed"},
                    {"stage": "audio_processing", "duration": 22.8, "status": "completed"},
                    {"stage": "quality_check", "duration": 0.8, "status": "completed"},
                    {"stage": "finalization", "duration": 0.4, "status": "completed"}
                ]
            }
        },
        "error": None,
        "timestamp": "",
        "requestId": "placeholder-request-id"
    }