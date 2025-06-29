"""
Enhanced Matchering FastAPI Application

Main application entry point for the AI-powered audio mastering backend.
Follows the architecture specified in docs/architecture/enhanced-matchering-architecture.md
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import ValidationError, ProcessingError
from app.models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting Enhanced Matchering API...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created/verified")
    logger.info("Enhanced Matchering API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enhanced Matchering API...")
    await engine.dispose()
    logger.info("Enhanced Matchering API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Enhanced Matchering API",
    description="AI-powered audio mastering API with reference-based and auto-mastering capabilities",
    version="3.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Security middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors with proper API response format."""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "data": None,
            "error": str(exc),
            "timestamp": exc.timestamp,
            "requestId": getattr(request.state, "request_id", "unknown"),
        }
    )


@app.exception_handler(ProcessingError)
async def processing_exception_handler(request: Request, exc: ProcessingError) -> JSONResponse:
    """Handle processing errors with proper API response format."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": str(exc),
            "timestamp": exc.timestamp,
            "requestId": getattr(request.state, "request_id", "unknown"),
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors with proper logging and response."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": "Internal server error",
            "timestamp": "",
            "requestId": getattr(request.state, "request_id", "unknown"),
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "enhanced-matchering-api",
        "version": "3.0.0"
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )