"""
Configuration management for Enhanced Matchering API.

Handles environment-specific settings with proper type safety and validation.
Based on the architecture specifications in docs/architecture/enhanced-matchering-architecture.md
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables with MATCHERING_ prefix.
    """
    
    # Application settings
    APP_NAME: str = "Enhanced Matchering API"
    VERSION: str = "3.0.0"
    DEBUG: bool = Field(default=False, env="MATCHERING_DEBUG")
    HOST: str = Field(default="127.0.0.1", env="MATCHERING_HOST")
    PORT: int = Field(default=8000, env="MATCHERING_PORT")
    
    # Security settings
    SECRET_KEY: str = Field(default="", description="Security secret key")
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="MATCHERING_ALLOWED_HOSTS"
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="MATCHERING_CORS_ORIGINS"
    )
    
    # Database settings
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./matchering.db",
        env="MATCHERING_DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="MATCHERING_DATABASE_ECHO")
    
    # Redis settings for Celery
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="MATCHERING_REDIS_URL"
    )
    
    # Celery settings
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        env="MATCHERING_CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        env="MATCHERING_CELERY_RESULT_BACKEND"
    )
    
    # File storage settings
    UPLOAD_DIR: Path = Field(
        default=Path("./uploads"),
        env="MATCHERING_UPLOAD_DIR"
    )
    RESULTS_DIR: Path = Field(
        default=Path("./results"),
        env="MATCHERING_RESULTS_DIR"
    )
    MAX_FILE_SIZE: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        env="MATCHERING_MAX_FILE_SIZE"
    )
    ALLOWED_AUDIO_FORMATS: List[str] = Field(
        default=[".wav", ".mp3", ".flac", ".aiff"],
        env="MATCHERING_ALLOWED_AUDIO_FORMATS"
    )
    
    # Processing settings
    MAX_CONCURRENT_JOBS: int = Field(
        default=5,
        env="MATCHERING_MAX_CONCURRENT_JOBS"
    )
    JOB_TIMEOUT_SECONDS: int = Field(
        default=300,  # 5 minutes
        env="MATCHERING_JOB_TIMEOUT_SECONDS"
    )
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="MATCHERING_LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="MATCHERING_LOG_FORMAT"
    )
    
    @validator("SECRET_KEY")
    def secret_key_required(cls, v: str) -> str:
        """Ensure secret key is provided for security."""
        if not v:
            raise ValueError("SECRET_KEY must be provided")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("UPLOAD_DIR", "RESULTS_DIR")
    def create_directories(cls, v: Path) -> Path:
        """Ensure upload and results directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("ALLOWED_AUDIO_FORMATS")
    def validate_audio_formats(cls, v: List[str]) -> List[str]:
        """Ensure audio formats start with dot."""
        return [fmt if fmt.startswith('.') else f'.{fmt}' for fmt in v]
    
    @validator("CORS_ORIGINS", "ALLOWED_HOSTS")
    def parse_comma_separated(cls, v) -> List[str]:
        """Parse comma-separated environment variables."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


class DevelopmentSettings(Settings):
    """Development-specific settings."""
    
    DEBUG: bool = True
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # Use SQLite for development
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev_matchering.db"


class ProductionSettings(Settings):
    """Production-specific settings."""
    
    DEBUG: bool = False
    DATABASE_ECHO: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Production should use PostgreSQL
    DATABASE_URL: str = Field(env="MATCHERING_DATABASE_URL")
    
    @validator("DATABASE_URL")
    def production_database_required(cls, v: str) -> str:
        """Ensure production uses proper database."""
        if v.startswith("sqlite"):
            raise ValueError("Production environment must use PostgreSQL")
        return v


class TestingSettings(Settings):
    """Testing-specific settings."""
    
    DEBUG: bool = True
    DATABASE_ECHO: bool = False
    LOG_LEVEL: str = "WARNING"
    
    # Use in-memory SQLite for testing
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    UPLOAD_DIR: Path = Path("./test_uploads")
    RESULTS_DIR: Path = Path("./test_results")


def get_settings() -> Settings:
    """
    Get application settings based on environment.
    
    Returns appropriate settings class based on MATCHERING_ENVIRONMENT variable.
    """
    env = os.getenv("MATCHERING_ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()