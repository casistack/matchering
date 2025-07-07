"""
API v1 router configuration for Enhanced Matchering API.

Aggregates all API endpoints with proper versioning and organization.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import ai, audio, processing, results, hybrid_ai, hybrid_processing, settings, job_recovery

# Create main API router
api_router = APIRouter()

# Include endpoint routers with appropriate prefixes
api_router.include_router(
    ai.router,
    prefix="/ai",
    tags=["ai"],
)

api_router.include_router(
    audio.router,
    prefix="/audio",
    tags=["audio"],
)

api_router.include_router(
    processing.router,
    prefix="/processing",
    tags=["processing"],
)

api_router.include_router(
    results.router,
    prefix="/results",
    tags=["results"],
)

api_router.include_router(
    hybrid_ai.router,
    prefix="/hybrid-ai",
    tags=["hybrid-ai"],
)

api_router.include_router(
    hybrid_processing.router,
    prefix="/hybrid-processing",
    tags=["hybrid-processing"],
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["settings"],
)

api_router.include_router(
    job_recovery.router,
    prefix="/jobs",
    tags=["job-recovery"],
)