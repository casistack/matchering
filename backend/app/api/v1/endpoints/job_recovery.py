"""
Job Recovery API endpoints for Enhanced Matchering API.

Provides enterprise-grade job recovery and monitoring capabilities.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.job_recovery import startup_job_recovery, health_check_jobs
from app.utils.request_utils import generate_request_id, create_api_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/recovery/startup")
async def trigger_startup_recovery(request: Request) -> Dict[str, Any]:
    """
    Manually trigger startup job recovery procedure.
    
    This endpoint allows administrators to manually run the job recovery
    process without restarting the service. Useful for cleaning up stuck
    jobs during operation.
    
    Returns:
        Dict containing recovery statistics and actions taken
    """
    request_id = generate_request_id()
    
    try:
        logger.info(f"Manual startup recovery triggered - Request: {request_id}")
        recovery_stats = await startup_job_recovery()
        
        logger.info(f"Manual recovery completed: {recovery_stats}")
        return create_api_response(
            data={
                "recovery_type": "startup_recovery",
                "triggered_manually": True,
                "stats": recovery_stats
            },
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Manual recovery failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Job recovery failed",
                "error_code": "RECOVERY_ERROR",
                "request_id": request_id,
                "error": str(e)
            }
        )


@router.get("/health")
async def get_job_health(request: Request) -> Dict[str, Any]:
    """
    Get comprehensive job processing health status.
    
    Returns:
        Dict containing health metrics and recommendations
    """
    request_id = generate_request_id()
    
    try:
        health_stats = await health_check_jobs()
        
        return create_api_response(
            data={
                "health_check_type": "job_processing",
                "healthy": health_stats["healthy"],
                "stats": health_stats
            },
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Job health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Job health check failed",
                "error_code": "HEALTH_CHECK_ERROR",
                "request_id": request_id,
                "error": str(e)
            }
        )


@router.get("/status")
async def get_recovery_status(request: Request) -> Dict[str, Any]:
    """
    Get current job recovery system status and configuration.
    
    Returns:
        Dict containing recovery system status
    """
    request_id = generate_request_id()
    
    from app.utils.job_recovery import job_recovery_manager
    
    return create_api_response(
        data={
            "recovery_system_status": "active",
            "configuration": {
                "recovery_timeout_minutes": job_recovery_manager.recovery_timeout_minutes,
                "startup_grace_period_minutes": job_recovery_manager.startup_grace_period_minutes
            },
            "capabilities": [
                "orphaned_job_detection",
                "stuck_job_recovery", 
                "startup_recovery",
                "health_monitoring",
                "celery_cleanup"
            ]
        },
        request_id=request_id
    )