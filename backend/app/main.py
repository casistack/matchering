"""
Enhanced Matchering FastAPI Application

Main application entry point for the AI-powered audio mastering backend.
Follows the architecture specified in docs/architecture/enhanced-matchering-architecture.md
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator
from pathlib import Path

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import ValidationError, ProcessingError
from app.models import Base
from app.middleware.enterprise_logging import EnterpriseLoggingMiddleware
from app.utils.enterprise_logger import log_error

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
    
    # Perform enterprise job recovery
    try:
        logger.info("Performing enterprise job recovery...")
        from app.utils.job_recovery import startup_job_recovery
        recovery_stats = await startup_job_recovery()
        logger.info(f"Job recovery completed: {recovery_stats}")
        app.state.job_recovery_stats = recovery_stats
    except Exception as e:
        logger.error(f"Job recovery failed: {e}")
        app.state.job_recovery_stats = {"error": str(e)}
    
    # Initialize AI models for production
    if settings.ENABLE_AI_MODELS:
        try:
            logger.info("Initializing AI models...")
            from app.ai.production_model_manager import ProductionModelManager
            
            # Create global model manager instance
            model_manager = ProductionModelManager()
            app.state.model_manager = model_manager
            
            # Preload essential models with retry logic
            essential_models = ["ast", "wav2vec2", "clap"]
            max_retries = 3
            retry_delay = 5  # seconds
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Loading AI models (attempt {attempt + 1}/{max_retries})...")
                    results = await model_manager.preload_models(essential_models)
                    
                    successful_models = [model for model, success in results.items() if success]
                    failed_models = [model for model, success in results.items() if not success]
                    
                    if failed_models:
                        logger.warning(f"Failed to load models: {failed_models}")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                            continue
                    else:
                        logger.info(f"✅ All essential models loaded successfully: {successful_models}")
                        break
                        
                except Exception as e:
                    logger.error(f"Model loading attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.error("Failed to load AI models after all retries. AI features may be limited.")
            
            # Store model status in app state
            app.state.models_initialized = len(successful_models) > 0
            app.state.available_models = successful_models
            
        except Exception as e:
            logger.error(f"Critical error during AI model initialization: {e}")
            app.state.models_initialized = False
            app.state.available_models = []
    else:
        logger.info("AI models disabled by configuration")
        app.state.models_initialized = False
        app.state.available_models = []
    
    # Initialize WebSocket manager with Redis bridge
    try:
        logger.info("Initializing WebSocket manager with Redis bridge...")
        from app.api.v1.endpoints.processing import websocket_manager
        websocket_init_success = await websocket_manager.initialize()
        app.state.websocket_manager_initialized = websocket_init_success
        if websocket_init_success:
            logger.info("✅ WebSocket manager with Redis bridge initialized successfully")
        else:
            logger.warning("⚠️ WebSocket manager initialization failed - real-time updates may not work")
    except Exception as e:
        logger.error(f"❌ Failed to initialize WebSocket manager: {e}")
        app.state.websocket_manager_initialized = False
    
    logger.info("Enhanced Matchering API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enhanced Matchering API...")
    
    # Clean up WebSocket manager and Redis bridge
    try:
        if getattr(app.state, 'websocket_manager_initialized', False):
            logger.info("Cleaning up WebSocket manager...")
            from app.api.v1.endpoints.processing import websocket_manager
            await websocket_manager.cleanup()
            from app.utils.redis_bridge import cleanup_redis_bridge
            await cleanup_redis_bridge()
            logger.info("✅ WebSocket manager cleaned up")
    except Exception as e:
        logger.error(f"❌ Error cleaning up WebSocket manager: {e}")
    
    # Clean up AI models
    if hasattr(app.state, 'model_manager') and app.state.model_manager:
        logger.info("Cleaning up AI models...")
        # The model manager will handle cleanup in its destructor
        app.state.model_manager = None
    
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

# Enterprise logging middleware (before CORS to capture all requests)
app.add_middleware(EnterpriseLoggingMiddleware)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI automatic request validation errors (422)."""
    # Log to enterprise logging system
    log_error(
        "FastAPI request validation failed",
        error=str(exc),
        error_type="RequestValidationError",
        context={
            "endpoint": str(request.url.path),
            "method": request.method,
            "validation_errors": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else "unknown"
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "error": "Request validation failed",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat(),
            "requestId": getattr(request.state, "request_id", "unknown"),
        }
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle custom validation errors with proper API response format."""
    # Log to enterprise logging system
    log_error(
        "Custom validation error handled",
        error=str(exc),
        error_type="ValidationError",
        context={
            "endpoint": str(request.url.path),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=422,  # Changed from 400 to 422 for consistency
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


# Enterprise job health check endpoint
@app.get("/health/jobs")
async def job_health_check() -> dict:
    """Enterprise job processing health check endpoint."""
    try:
        from app.utils.job_recovery import health_check_jobs
        health_stats = await health_check_jobs()
        return {
            "status": "healthy" if health_stats["healthy"] else "unhealthy",
            "service": "job-processing",
            "stats": health_stats,
            "startup_recovery": getattr(app.state, "job_recovery_stats", {})
        }
    except Exception as e:
        logger.error(f"Job health check failed: {e}")
        return {
            "status": "error",
            "service": "job-processing", 
            "error": str(e)
        }


# Enterprise communication health check endpoint
@app.get("/health/communication")
async def communication_health_check() -> dict:
    """Enterprise communication system health check endpoint."""
    try:
        from app.utils.redis_bridge import get_redis_bridge
        from app.api.v1.endpoints.processing import websocket_manager
        
        # Check Redis bridge health
        redis_available = False
        try:
            bridge = await get_redis_bridge()
            redis_available = bridge is not None
        except Exception as e:
            logger.warning(f"Redis bridge check failed: {e}")
        
        # Check WebSocket manager status
        websocket_initialized = getattr(app.state, "websocket_manager_initialized", False)
        
        # Count active WebSocket connections
        active_connections = len(websocket_manager.active_connections) if hasattr(websocket_manager, 'active_connections') else 0
        
        return {
            "status": "healthy" if redis_available else "degraded",
            "service": "communication-bridge",
            "redis_available": redis_available,
            "websocket_manager_initialized": websocket_initialized,
            "active_websocket_connections": active_connections,
            "fallback_mode": not redis_available
        }
        
    except Exception as e:
        logger.error(f"Communication health check failed: {e}")
        return {
            "status": "error",
            "service": "communication-bridge",
            "error": str(e)
        }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static files for serving processed audio files
uploads_dir = Path(settings.UPLOAD_DIR).resolve()
uploads_dir.mkdir(exist_ok=True)  # Ensure the directory exists
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Debug endpoint to check CORS configuration
@app.get("/debug/cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration."""
    return {
        "cors_origins": settings.CORS_ORIGINS,
        "allowed_hosts": settings.ALLOWED_HOSTS,
        "debug": settings.DEBUG
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )