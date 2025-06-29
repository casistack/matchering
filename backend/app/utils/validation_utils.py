"""
Validation utilities for Enhanced Matchering API.

Contains validation functions for files, formats, and user input.
"""

import re
from pathlib import Path
from typing import List, Optional
from app.core.config import settings
from app.core.exceptions import ValidationError


def validate_file_format(filename: str, allowed_formats: Optional[List[str]] = None) -> bool:
    """
    Validate file format based on extension.
    
    Args:
        filename: Name of the file
        allowed_formats: List of allowed extensions (defaults to settings)
        
    Returns:
        bool: True if format is valid
        
    Raises:
        ValidationError: If format is not allowed
    """
    if allowed_formats is None:
        allowed_formats = settings.ALLOWED_AUDIO_FORMATS
    
    file_path = Path(filename)
    file_extension = file_path.suffix.lower()
    
    if not file_extension:
        raise ValidationError("File has no extension", "NO_EXTENSION", {"filename": filename})
    
    if file_extension not in allowed_formats:
        raise ValidationError(
            f"Unsupported file format: {file_extension}",
            "UNSUPPORTED_FORMAT",
            {
                "format": file_extension,
                "allowed_formats": allowed_formats,
                "filename": filename
            }
        )
    
    return True


def validate_file_size(file_size: int, max_size: Optional[int] = None) -> bool:
    """
    Validate file size against maximum allowed size.
    
    Args:
        file_size: Size of file in bytes
        max_size: Maximum allowed size in bytes (defaults to settings)
        
    Returns:
        bool: True if size is valid
        
    Raises:
        ValidationError: If file is too large
    """
    if max_size is None:
        max_size = settings.MAX_FILE_SIZE
    
    if file_size <= 0:
        raise ValidationError("File is empty", "FILE_EMPTY", {"file_size": file_size})
    
    if file_size > max_size:
        raise ValidationError(
            f"File too large: {file_size} bytes (max: {max_size})",
            "FILE_TOO_LARGE",
            {
                "file_size": file_size,
                "max_size": max_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "max_size_mb": round(max_size / (1024 * 1024), 2)
            }
        )
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage and display.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name
    
    # Replace dangerous characters with underscores
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(dangerous_chars, '_', filename)
    
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure filename isn't too long
    if len(sanitized) > 255:
        file_path = Path(sanitized)
        # Keep extension and truncate name
        name_limit = 255 - len(file_path.suffix) - 1
        sanitized = f"{file_path.stem[:name_limit]}{file_path.suffix}"
    
    # Ensure filename isn't empty or just extension
    if not sanitized or sanitized.startswith('.'):
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        if sanitized.startswith('.'):
            sanitized = f"file_{unique_id}{sanitized}"
        else:
            sanitized = f"file_{unique_id}"
    
    return sanitized


def validate_processing_mode(mode: str) -> bool:
    """
    Validate processing mode.
    
    Args:
        mode: Processing mode string
        
    Returns:
        bool: True if mode is valid
        
    Raises:
        ValidationError: If mode is not supported
    """
    allowed_modes = ['auto', 'reference', 'hybrid']
    
    if mode not in allowed_modes:
        raise ValidationError(
            f"Invalid processing mode: {mode}",
            "INVALID_PROCESSING_MODE",
            {
                "mode": mode,
                "allowed_modes": allowed_modes
            }
        )
    
    return True


def validate_priority(priority: int) -> bool:
    """
    Validate job priority value.
    
    Args:
        priority: Priority value (1-10)
        
    Returns:
        bool: True if priority is valid
        
    Raises:
        ValidationError: If priority is out of range
    """
    if not isinstance(priority, int) or priority < 1 or priority > 10:
        raise ValidationError(
            f"Invalid priority: {priority}. Must be integer between 1 and 10",
            "INVALID_PRIORITY",
            {
                "priority": priority,
                "min_priority": 1,
                "max_priority": 10
            }
        )
    
    return True


def validate_audio_settings(settings_dict: dict, processing_mode: str) -> bool:
    """
    Validate processing settings based on mode.
    
    Args:
        settings_dict: Processing settings dictionary
        processing_mode: Processing mode
        
    Returns:
        bool: True if settings are valid
        
    Raises:
        ValidationError: If settings are invalid
    """
    # Basic validation for common settings
    if "quality" in settings_dict:
        quality = settings_dict["quality"]
        allowed_qualities = ["draft", "standard", "high", "maximum"]
        if quality not in allowed_qualities:
            raise ValidationError(
                f"Invalid quality setting: {quality}",
                "INVALID_QUALITY",
                {
                    "quality": quality,
                    "allowed_qualities": allowed_qualities
                }
            )
    
    if "loudness_target" in settings_dict:
        loudness_target = settings_dict["loudness_target"]
        if not isinstance(loudness_target, (int, float)) or loudness_target < -30 or loudness_target > 0:
            raise ValidationError(
                f"Invalid loudness target: {loudness_target}. Must be between -30 and 0 LUFS",
                "INVALID_LOUDNESS_TARGET",
                {
                    "loudness_target": loudness_target,
                    "min_lufs": -30,
                    "max_lufs": 0
                }
            )
    
    # Mode-specific validation
    if processing_mode == "reference":
        # Reference mode might require specific settings
        pass
    elif processing_mode == "auto":
        # Auto mode might have different requirements
        pass
    elif processing_mode == "hybrid":
        # Hybrid mode might combine requirements
        pass
    
    return True


def validate_pagination_params(skip: int, limit: int) -> bool:
    """
    Validate pagination parameters.
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        bool: True if parameters are valid
        
    Raises:
        ValidationError: If parameters are invalid
    """
    if skip < 0:
        raise ValidationError(
            f"Skip must be non-negative, got: {skip}",
            "INVALID_SKIP",
            {"skip": skip}
        )
    
    if limit < 1 or limit > 1000:
        raise ValidationError(
            f"Limit must be between 1 and 1000, got: {limit}",
            "INVALID_LIMIT",
            {
                "limit": limit,
                "min_limit": 1,
                "max_limit": 1000
            }
        )
    
    return True


def validate_uuid_string(uuid_string: str, field_name: str = "UUID") -> bool:
    """
    Validate UUID string format.
    
    Args:
        uuid_string: UUID string to validate
        field_name: Name of the field for error messages
        
    Returns:
        bool: True if UUID is valid
        
    Raises:
        ValidationError: If UUID format is invalid
    """
    import uuid
    
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        raise ValidationError(
            f"Invalid {field_name} format: {uuid_string}",
            "INVALID_UUID",
            {
                "uuid_string": uuid_string,
                "field_name": field_name
            }
        )


def validate_filename_length(filename: str, max_length: int = 255) -> bool:
    """
    Validate filename length.
    
    Args:
        filename: Filename to validate
        max_length: Maximum allowed length
        
    Returns:
        bool: True if length is valid
        
    Raises:
        ValidationError: If filename is too long
    """
    if len(filename) > max_length:
        raise ValidationError(
            f"Filename too long: {len(filename)} characters (max: {max_length})",
            "FILENAME_TOO_LONG",
            {
                "filename": filename,
                "length": len(filename),
                "max_length": max_length
            }
        )
    
    return True


def validate_content_type(content_type: str, allowed_types: Optional[List[str]] = None) -> bool:
    """
    Validate HTTP content type.
    
    Args:
        content_type: Content type to validate
        allowed_types: List of allowed content types
        
    Returns:
        bool: True if content type is valid
        
    Raises:
        ValidationError: If content type is not allowed
    """
    if allowed_types is None:
        allowed_types = [
            "audio/wav", "audio/wave", "audio/x-wav",
            "audio/mpeg", "audio/mp3",
            "audio/flac",
            "audio/aiff", "audio/x-aiff",
            "audio/mp4", "audio/m4a"
        ]
    
    # Extract main content type (ignore parameters)
    main_type = content_type.split(';')[0].strip().lower()
    
    if main_type not in allowed_types:
        raise ValidationError(
            f"Unsupported content type: {content_type}",
            "UNSUPPORTED_CONTENT_TYPE",
            {
                "content_type": content_type,
                "allowed_types": allowed_types
            }
        )
    
    return True