"""
API v1 router configuration for Enhanced Matchering API.

Aggregates all API endpoints with proper versioning and organization.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import ai, audio, processing, results

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