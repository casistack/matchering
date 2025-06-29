"""
File management tasks for Enhanced Matchering API.

This module contains Celery tasks for file operations, validation,
and cleanup.
"""

import asyncio
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging
import mimetypes
import shutil

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.models.audio import AudioFile
from app.core.exceptions import AudioFileError, StorageError
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileTask(Task):
    """Base class for file management tasks with database integration."""
    
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


@celery_app.task(bind=True, base=FileTask, name="validate_uploaded_file")
def validate_uploaded_file(self: FileTask, file_path: str, original_filename: str) -> Dict[str, Any]:
    """
    Validate uploaded audio file and create database record.
    
    Args:
        file_path: Path to the uploaded file
        original_filename: Original filename from upload
        
    Returns:
        dict: Validation results and file metadata
    """
    return asyncio.run(self._validate_uploaded_file_async(file_path, original_filename))


async def _validate_uploaded_file_async(self: FileTask, file_path: str, original_filename: str) -> Dict[str, Any]:
    """Async implementation of file validation."""
    session = await self.get_session()
    
    try:
        file_path_obj = Path(file_path)
        
        logger.info(f"Validating uploaded file: {file_path}")
        
        # Basic file validation
        if not file_path_obj.exists():
            raise AudioFileError(f"Uploaded file does not exist: {file_path}", "FILE_NOT_EXISTS", {"file_path": file_path})
        
        # Get file stats
        file_stats = file_path_obj.stat()
        file_size = file_stats.st_size
        
        # Validate file size
        if file_size > settings.MAX_FILE_SIZE:
            raise AudioFileError(
                f"File too large: {file_size} bytes (max: {settings.MAX_FILE_SIZE})",
                "FILE_TOO_LARGE",
                {"file_size": file_size, "max_size": settings.MAX_FILE_SIZE}
            )
        
        # Validate file format
        file_extension = file_path_obj.suffix.lower()
        if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
            raise AudioFileError(
                f"Unsupported file format: {file_extension}",
                "UNSUPPORTED_FORMAT",
                {"format": file_extension, "allowed_formats": settings.ALLOWED_AUDIO_FORMATS}
            )
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not mime_type.startswith('audio/'):
            mime_type = f"audio/{file_extension[1:]}"  # Fallback MIME type
        
        # Calculate file checksum
        checksum = await _calculate_file_checksum(file_path_obj)
        
        # Check for duplicate files
        from sqlalchemy import select
        existing_query = select(AudioFile).where(AudioFile.checksum == checksum)
        result = await session.execute(existing_query)
        existing_file = result.scalar_one_or_none()
        
        if existing_file:
            logger.info(f"Duplicate file detected: {checksum}")
            return {
                "status": "duplicate",
                "existing_file_id": str(existing_file.id),
                "message": "File already exists in database"
            }
        
        # Extract basic audio properties (placeholder)
        audio_properties = await _extract_basic_audio_properties(file_path_obj)
        
        # Generate unique filename for storage
        unique_filename = await _generate_unique_filename(original_filename)
        
        # Move file to final storage location
        final_path = settings.UPLOAD_DIR / unique_filename
        shutil.move(file_path, final_path)
        
        # Create database record
        audio_file = AudioFile(
            id=uuid.uuid4(),
            filename=unique_filename,
            original_filename=original_filename,
            file_path=str(final_path),
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            format=file_extension[1:],  # Remove the dot
            sample_rate=audio_properties.get("sample_rate", 44100),
            bit_depth=audio_properties.get("bit_depth"),
            channels=audio_properties.get("channels", 2),
            duration=audio_properties.get("duration", 0.0),
            processing_eligible=False  # Will be set to True after analysis
        )
        
        session.add(audio_file)
        await session.commit()
        
        logger.info(f"File validation completed successfully: {str(audio_file.id)}")
        
        return {
            "status": "validated",
            "file_id": str(audio_file.id),
            "filename": unique_filename,
            "file_size": file_size,
            "format": audio_properties.get("format"),
            "duration": audio_properties.get("duration"),
            "checksum": checksum
        }
        
    except Exception as e:
        logger.error(f"File validation failed for {file_path}: {str(e)}")
        # Clean up uploaded file on error
        try:
            if Path(file_path).exists():
                Path(file_path).unlink()
        except Exception:
            pass
        raise
    finally:
        await self.close_session()


@celery_app.task(bind=True, base=FileTask, name="cleanup_temporary_files")
def cleanup_temporary_files(self: FileTask, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up temporary files older than specified age.
    
    Args:
        max_age_hours: Maximum age of files to keep in hours
        
    Returns:
        dict: Cleanup results
    """
    return asyncio.run(self._cleanup_temporary_files_async(max_age_hours))


async def _cleanup_temporary_files_async(self: FileTask, max_age_hours: int) -> Dict[str, Any]:
    """Async implementation of temporary file cleanup."""
    try:
        from datetime import timedelta
        
        cleanup_before = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Define temporary directories to clean
        temp_dirs = [
            Path("/tmp"),
            settings.UPLOAD_DIR / "temp",
            settings.RESULTS_DIR / "temp"
        ]
        
        cleaned_files = []
        total_size_freed = 0
        
        for temp_dir in temp_dirs:
            if not temp_dir.exists():
                continue
            
            for file_path in temp_dir.glob("**/*"):
                if not file_path.is_file():
                    continue
                
                # Check if file is old enough
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime > cleanup_before:
                    continue
                
                # Check if it's a temporary file (starts with temp_ or has .tmp extension)
                if not (file_path.name.startswith("temp_") or file_path.suffix == ".tmp"):
                    continue
                
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    cleaned_files.append(str(file_path))
                    total_size_freed += file_size
                    logger.debug(f"Cleaned temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean file {file_path}: {e}")
        
        logger.info(f"Cleanup completed: {len(cleaned_files)} files, {total_size_freed} bytes freed")
        
        return {
            "status": "completed",
            "files_cleaned": len(cleaned_files),
            "size_freed_bytes": total_size_freed,
            "cleaned_files": cleaned_files[:10]  # First 10 files for logging
        }
        
    except Exception as e:
        logger.error(f"Temporary file cleanup failed: {str(e)}")
        raise


@celery_app.task(bind=True, base=FileTask, name="archive_processed_files")
def archive_processed_files(self: FileTask, days_old: int = 30) -> Dict[str, Any]:
    """
    Archive processed files older than specified days.
    
    Args:
        days_old: Archive files older than this many days
        
    Returns:
        dict: Archive results
    """
    return asyncio.run(self._archive_processed_files_async(days_old))


async def _archive_processed_files_async(self: FileTask, days_old: int) -> Dict[str, Any]:
    """Async implementation of file archiving."""
    session = await self.get_session()
    
    try:
        from datetime import timedelta
        from sqlalchemy import select
        
        archive_before = datetime.utcnow() - timedelta(days=days_old)
        
        # Find old completed processing jobs
        from app.models.processing import ProcessingJob, JobStatus
        
        query = select(ProcessingJob).where(
            ProcessingJob.status == JobStatus.COMPLETED,
            ProcessingJob.completed_at < archive_before
        )
        result = await session.execute(query)
        old_jobs = result.scalars().all()
        
        archived_files = []
        archive_dir = settings.RESULTS_DIR / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        for job in old_jobs:
            if not job.output_file_path:
                continue
            
            output_path = Path(job.output_file_path)
            if not output_path.exists():
                continue
            
            # Create archive path
            archive_path = archive_dir / f"{job.id}_{output_path.name}"
            
            try:
                shutil.move(str(output_path), str(archive_path))
                
                # Update job record with archive path
                job.output_file_path = str(archive_path)
                archived_files.append(str(archive_path))
                
                logger.debug(f"Archived file: {output_path} -> {archive_path}")
                
            except Exception as e:
                logger.warning(f"Failed to archive file {output_path}: {e}")
        
        await session.commit()
        
        logger.info(f"Archiving completed: {len(archived_files)} files archived")
        
        return {
            "status": "completed",
            "files_archived": len(archived_files),
            "archive_directory": str(archive_dir),
            "archived_files": archived_files[:10]  # First 10 files for logging
        }
        
    except Exception as e:
        logger.error(f"File archiving failed: {str(e)}")
        raise
    finally:
        await self.close_session()


# Helper functions for file operations

async def _calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of file."""
    hash_sha256 = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    
    return hash_sha256.hexdigest()


async def _extract_basic_audio_properties(file_path: Path) -> Dict[str, Any]:
    """
    Extract basic audio properties from file (placeholder).
    
    In production, this would use libraries like:
    - soundfile for basic properties
    - librosa for advanced analysis
    - mutagen for metadata
    """
    # Placeholder implementation
    # In reality, would use soundfile.info() or similar
    
    file_extension = file_path.suffix.lower()
    
    # Default properties based on common formats
    properties = {
        "format": file_extension[1:],
        "sample_rate": 44100,
        "channels": 2,
        "bit_depth": 16,
        "duration": 180.0  # 3 minutes default
    }
    
    # Format-specific defaults
    if file_extension in [".mp3"]:
        properties.update({
            "bit_depth": None,  # MP3 doesn't have bit depth
            "bitrate": 320000   # 320 kbps default
        })
    elif file_extension in [".flac"]:
        properties.update({
            "bit_depth": 24,
            "sample_rate": 96000
        })
    elif file_extension in [".wav", ".aiff"]:
        properties.update({
            "bit_depth": 24,
            "sample_rate": 48000
        })
    
    return properties


async def _generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename for storage."""
    file_path = Path(original_filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{timestamp}_{unique_id}_{file_path.stem}{file_path.suffix}"


# Export tasks
__all__ = [
    "validate_uploaded_file",
    "cleanup_temporary_files", 
    "archive_processed_files",
    "FileTask"
]