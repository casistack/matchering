"""
Settings API endpoints for user preferences and model configuration.

Provides enterprise-grade RESTful API for settings management with validation and caching.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import logging

from app.core.database import get_db
from app.services.settings_service import SettingsService
from app.schemas.settings import (
    SettingsConfigResponse, ModelPreferencesUpdateSchema, UserSettingsProfileSchema,
    UserSettingsProfileCreateSchema, UserSettingsProfileUpdateSchema, SettingsUpdateResponse,
    ProfileSelectionResponse, AvailableModelInfoSchema, UserSettingsAnalyticsSchema,
    SystemStatusResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/config", response_model=SettingsConfigResponse)
async def get_user_settings_configuration(
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete user settings configuration including profiles, models, and defaults.
    
    Returns:
        - Current active profile settings
        - Available user profiles
        - Available AI models with performance info
        - System default settings
        - Feature flags
    """
    logger.info(f"Getting settings config for anonymous_id={anonymous_id}, user_id={user_id}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    try:
        service = SettingsService(db)
        config = await service.get_user_configuration(anonymous_id, user_id)
        return config
    except Exception as e:
        logger.error(f"Error getting settings config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve settings configuration"
        )


@router.put("/preferences", response_model=SettingsUpdateResponse)
async def update_user_preferences(
    preferences: ModelPreferencesUpdateSchema,
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user model preferences.
    
    Args:
        preferences: Updated preference values (only provided fields will be updated)
        anonymous_id: Anonymous user identifier
        user_id: Authenticated user identifier
    
    Returns:
        Updated user profile with success status
    """
    logger.info(f"Updating preferences for anonymous_id={anonymous_id}, user_id={user_id}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    try:
        service = SettingsService(db)
        result = await service.update_preferences(preferences, anonymous_id, user_id)
        return result
    except ValueError as e:
        logger.warning(f"Validation error updating preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )


@router.post("/profiles", response_model=UserSettingsProfileSchema)
async def create_settings_profile(
    profile: UserSettingsProfileCreateSchema,
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new settings profile.
    
    Args:
        profile: Profile configuration including name, description, and preferences
        anonymous_id: Anonymous user identifier
        user_id: Authenticated user identifier
    
    Returns:
        Created profile information
    """
    logger.info(f"Creating profile '{profile.name}' for anonymous_id={anonymous_id}, user_id={user_id}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    try:
        service = SettingsService(db)
        created_profile = await service.create_profile(profile, anonymous_id, user_id)
        return created_profile
    except ValueError as e:
        logger.warning(f"Validation error creating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile"
        )


@router.get("/profiles", response_model=List[UserSettingsProfileSchema])
async def list_settings_profiles(
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all settings profiles for a user.
    
    Args:
        anonymous_id: Anonymous user identifier
        user_id: Authenticated user identifier
    
    Returns:
        List of user's settings profiles
    """
    logger.info(f"Listing profiles for anonymous_id={anonymous_id}, user_id={user_id}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    try:
        service = SettingsService(db)
        profiles = await service.list_profiles(anonymous_id, user_id)
        return profiles
    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list profiles"
        )


@router.put("/profiles/{profile_id}/select", response_model=ProfileSelectionResponse)
async def select_settings_profile(
    profile_id: str,
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Select a settings profile as active.
    
    Args:
        profile_id: ID of the profile to activate
        anonymous_id: Anonymous user identifier
        user_id: Authenticated user identifier
    
    Returns:
        Selection response with active profile information
    """
    logger.info(f"Selecting profile {profile_id} for anonymous_id={anonymous_id}, user_id={user_id}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    try:
        service = SettingsService(db)
        result = await service.select_profile(profile_id, anonymous_id, user_id)
        return result
    except ValueError as e:
        logger.warning(f"Error selecting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error selecting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to select profile"
        )


@router.put("/profiles/{profile_id}", response_model=UserSettingsProfileSchema)
async def update_settings_profile(
    profile_id: str,
    profile_update: UserSettingsProfileUpdateSchema,
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing settings profile.
    
    Args:
        profile_id: ID of the profile to update
        profile_update: Updated profile data
        anonymous_id: Anonymous user identifier
        user_id: Authenticated user identifier
    
    Returns:
        Updated profile information
    """
    logger.info(f"Updating profile {profile_id} for anonymous_id={anonymous_id}, user_id={user_id}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    # TODO: Implement update profile functionality in service
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Profile update functionality not yet implemented"
    )


@router.delete("/profiles/{profile_id}")
async def delete_settings_profile(
    profile_id: str,
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a settings profile.
    
    Args:
        profile_id: ID of the profile to delete
        anonymous_id: Anonymous user identifier
        user_id: Authenticated user identifier
    
    Returns:
        Success confirmation
    """
    logger.info(f"Deleting profile {profile_id} for anonymous_id={anonymous_id}, user_id={user_id}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    try:
        service = SettingsService(db)
        success = await service.delete_profile(profile_id, anonymous_id, user_id)
        if success:
            return {"success": True, "message": "Profile deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
    except ValueError as e:
        logger.warning(f"Error deleting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete profile"
        )


@router.get("/models", response_model=List[AvailableModelInfoSchema])
async def get_available_models():
    """
    Get information about all available AI models.
    
    Returns:
        List of available models with performance information and requirements
    """
    logger.info("Getting available models information")
    
    try:
        service = SettingsService(None)  # No DB needed for model info
        models = await service.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available models"
        )


@router.get("/analytics", response_model=UserSettingsAnalyticsSchema)
async def get_settings_analytics(
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user settings usage analytics.
    
    Args:
        anonymous_id: Anonymous user identifier
        user_id: Authenticated user identifier
        days: Number of days to analyze (1-365)
    
    Returns:
        Analytics data including usage patterns, model performance, and trends
    """
    logger.info(f"Getting analytics for anonymous_id={anonymous_id}, user_id={user_id}, days={days}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    try:
        service = SettingsService(db)
        analytics = await service.get_analytics(anonymous_id, user_id, days)
        return analytics
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get system status for settings service.
    
    Returns:
        System status including model availability, user metrics, and performance data
    """
    logger.info("Getting system status")
    
    try:
        service = SettingsService(db)
        status_info = await service.get_system_status()
        return status_info
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.post("/reset-defaults")
async def reset_to_defaults(
    anonymous_id: Optional[str] = Query(None, description="Anonymous user identifier"),
    user_id: Optional[str] = Query(None, description="Authenticated user identifier"),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset user preferences to system defaults.
    
    Args:
        anonymous_id: Anonymous user identifier
        user_id: Authenticated user identifier
    
    Returns:
        Success confirmation with reset profile
    """
    logger.info(f"Resetting to defaults for anonymous_id={anonymous_id}, user_id={user_id}")
    
    if not anonymous_id and not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either anonymous_id or user_id must be provided"
        )
    
    try:
        service = SettingsService(db)
        system_defaults = await service._get_system_defaults()
        
        # Convert to update schema
        update_schema = ModelPreferencesUpdateSchema(
            preferred_strategy=system_defaults.preferred_strategy,
            ensemble_weights=system_defaults.ensemble_weights,
            quality_preference=system_defaults.quality_preference,
            enable_experimental=system_defaults.enable_experimental,
            confidence_threshold=system_defaults.confidence_threshold,
            max_processing_time=system_defaults.max_processing_time,
            fallback_strategy=system_defaults.fallback_strategy,
            custom_settings=system_defaults.custom_settings
        )
        
        result = await service.update_preferences(update_schema, anonymous_id, user_id)
        return result
    except Exception as e:
        logger.error(f"Error resetting to defaults: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset to defaults"
        )