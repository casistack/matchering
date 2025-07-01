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
import asyncio
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
    
    logger.info("Enhanced Matchering API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Enhanced Matchering API...")
    
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