"""
File handling utilities for Enhanced Matchering API.

Contains functions for file upload, validation, and management.
"""

import hashlib
import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
import logging

from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import AudioFileError, StorageError

logger = logging.getLogger(__name__)


async def save_uploaded_file(upload_file: UploadFile, destination_dir: Optional[Path] = None) -> Tuple[Path, str]:
    """
    Save uploaded file to storage directory.
    
    Args:
        upload_file: FastAPI UploadFile instance
        destination_dir: Optional destination directory (defaults to UPLOAD_DIR)
        
    Returns:
        tuple: (file_path, checksum) of saved file
        
    Raises:
        StorageError: If file cannot be saved
        AudioFileError: If file validation fails
    """
    if destination_dir is None:
        destination_dir = settings.UPLOAD_DIR
    
    # Ensure destination directory exists
    destination_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    unique_filename = generate_unique_filename(upload_file.filename or "upload")
    file_path = destination_dir / unique_filename
    
    try:
        # Calculate checksum while saving file
        hash_sha256 = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'wb') as f:
            # Read file in chunks to handle large files efficiently
            while chunk := await upload_file.read(8192):
                hash_sha256.update(chunk)
                await f.write(chunk)
        
        checksum = hash_sha256.hexdigest()
        
        # Reset file position for any subsequent reads
        await upload_file.seek(0)
        
        logger.info(f"File saved successfully: {file_path} (checksum: {checksum[:8]}...)")
        
        return file_path, checksum
        
    except Exception as e:
        # Clean up partially saved file
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        
        logger.error(f"Failed to save uploaded file: {e}")
        raise StorageError(f"Failed to save uploaded file: {str(e)}", "FILE_SAVE_ERROR", {"filename": upload_file.filename})


async def validate_audio_file(file_path: Path, upload_file: UploadFile) -> dict:
    """
    Validate uploaded audio file.
    
    Args:
        file_path: Path to saved file
        upload_file: Original upload file object
        
    Returns:
        dict: Validation results with file properties
        
    Raises:
        AudioFileError: If validation fails
    """
    if not file_path.exists():
        raise AudioFileError(f"File does not exist: {file_path}", "FILE_NOT_EXISTS", {"file_path": str(file_path)})
    
    # Get file stats
    file_stats = file_path.stat()
    file_size = file_stats.st_size
    
    # Validate file size
    if file_size > settings.MAX_FILE_SIZE:
        raise AudioFileError(
            f"File too large: {file_size} bytes (max: {settings.MAX_FILE_SIZE})",
            "FILE_TOO_LARGE",
            {"file_size": file_size, "max_size": settings.MAX_FILE_SIZE}
        )
    
    if file_size == 0:
        raise AudioFileError("File is empty", "FILE_EMPTY", {"file_path": str(file_path)})
    
    # Validate file format
    file_extension = file_path.suffix.lower()
    if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
        raise AudioFileError(
            f"Unsupported file format: {file_extension}",
            "UNSUPPORTED_FORMAT",
            {"format": file_extension, "allowed_formats": settings.ALLOWED_AUDIO_FORMATS}
        )
    
    # Get MIME type
    mime_type = get_file_mime_type(file_path)
    
    # Basic audio properties validation (placeholder)
    # In production, would use soundfile or librosa for actual validation
    audio_properties = await extract_basic_audio_properties(file_path)
    
    return {
        "file_size": file_size,
        "format": file_extension[1:],  # Remove the dot
        "mime_type": mime_type,
        "audio_properties": audio_properties,
        "validation_status": "valid"
    }


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate unique filename for storage.
    
    Args:
        original_filename: Original uploaded filename
        
    Returns:
        str: Unique filename
    """
    # Sanitize the original filename
    safe_filename = sanitize_filename(original_filename)
    
    file_path = Path(safe_filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    # Construct unique filename: timestamp_uniqueid_originalname.ext
    return f"{timestamp}_{unique_id}_{file_path.stem}{file_path.suffix}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace potentially dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    
    sanitized = filename
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Ensure filename isn't too long (max 255 chars for most filesystems)
    if len(sanitized) > 255:
        file_path = Path(sanitized)
        # Keep extension and truncate name
        name_limit = 255 - len(file_path.suffix) - 1
        sanitized = f"{file_path.stem[:name_limit]}{file_path.suffix}"
    
    # Ensure filename isn't empty
    if not sanitized or sanitized.isspace():
        sanitized = f"upload_{uuid.uuid4().hex[:8]}"
    
    return sanitized


async def calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of file.
    
    Args:
        file_path: Path to file
        
    Returns:
        str: SHA-256 checksum hex string
    """
    hash_sha256 = hashlib.sha256()
    
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(8192):
            hash_sha256.update(chunk)
    
    return hash_sha256.hexdigest()


def get_file_mime_type(file_path: Path) -> str:
    """
    Get MIME type for file.
    
    Args:
        file_path: Path to file
        
    Returns:
        str: MIME type
    """
    mime_type, _ = mimetypes.guess_type(str(file_path))
    
    if not mime_type or not mime_type.startswith('audio/'):
        # Fallback based on file extension
        extension = file_path.suffix.lower()
        mime_type_map = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.flac': 'audio/flac',
            '.aiff': 'audio/aiff',
            '.aif': 'audio/aiff',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg'
        }
        mime_type = mime_type_map.get(extension, f"audio/{extension[1:]}")
    
    return mime_type


async def extract_basic_audio_properties(file_path: Path) -> dict:
    """
    Extract basic audio properties from file.
    
    This is a placeholder implementation. In production, would use
    libraries like soundfile, librosa, or mutagen for actual analysis.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        dict: Basic audio properties
    """
    file_extension = file_path.suffix.lower()
    
    # Default properties based on common formats
    properties = {
        "sample_rate": 44100,
        "channels": 2,
        "bit_depth": 16,
        "duration": 180.0,  # 3 minutes default
        "estimated": True   # Indicates these are estimated values
    }
    
    # Format-specific defaults
    if file_extension == '.mp3':
        properties.update({
            "bit_depth": None,  # MP3 doesn't have bit depth
            "bitrate": 320000,  # 320 kbps default
            "vbr": False        # Constant bitrate assumed
        })
    elif file_extension == '.flac':
        properties.update({
            "bit_depth": 24,
            "sample_rate": 96000,
            "compression_level": 5
        })
    elif file_extension in ['.wav', '.aiff']:
        properties.update({
            "bit_depth": 24,
            "sample_rate": 48000
        })
    
    # In production, would use actual audio analysis:
    # import soundfile as sf
    # try:
    #     info = sf.info(file_path)
    #     properties = {
    #         "sample_rate": info.samplerate,
    #         "channels": info.channels,
    #         "duration": info.duration,
    #         "format": info.format,
    #         "subtype": info.subtype,
    #         "estimated": False
    #     }
    # except Exception as e:
    #     logger.warning(f"Could not extract audio properties: {e}")
    
    return properties


async def create_temporary_file(content: bytes, suffix: str = ".tmp") -> Path:
    """
    Create temporary file with content.
    
    Args:
        content: File content
        suffix: File suffix
        
    Returns:
        Path: Path to temporary file
    """
    temp_dir = settings.UPLOAD_DIR / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    temp_filename = f"temp_{uuid.uuid4().hex}{suffix}"
    temp_path = temp_dir / temp_filename
    
    async with aiofiles.open(temp_path, 'wb') as f:
        await f.write(content)
    
    return temp_path


async def cleanup_temporary_files(max_age_hours: int = 24) -> int:
    """
    Clean up temporary files older than specified age.
    
    Args:
        max_age_hours: Maximum age in hours
        
    Returns:
        int: Number of files cleaned up
    """
    temp_dir = settings.UPLOAD_DIR / "temp"
    if not temp_dir.exists():
        return 0
    
    from datetime import timedelta
    cleanup_before = datetime.utcnow() - timedelta(hours=max_age_hours)
    
    cleaned_count = 0
    for file_path in temp_dir.glob("temp_*"):
        if not file_path.is_file():
            continue
        
        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        if file_mtime < cleanup_before:
            try:
                file_path.unlink()
                cleaned_count += 1
                logger.debug(f"Cleaned temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean temporary file {file_path}: {e}")
    
    return cleaned_count