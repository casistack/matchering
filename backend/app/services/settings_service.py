"""
Settings service layer for user preferences and model configuration.

Provides enterprise-grade settings management with caching, validation, and analytics.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import logging

from app.models.user_preferences import UserPreferences, ModelPerformanceHistory, UserSettingsProfile
from app.schemas.settings import (
    ModelPreferencesSchema, UserSettingsProfileSchema, AvailableModelInfoSchema,
    SettingsConfigResponse, ModelPreferencesUpdateSchema, UserSettingsProfileCreateSchema,
    UserSettingsProfileUpdateSchema, SettingsUpdateResponse, ProfileSelectionResponse,
    UserSettingsAnalyticsSchema, ModelPerformanceInfoSchema, SystemStatusResponse,
    ModelSelectionStrategy, QualityPreference, FallbackStrategy, ModelType
)

logger = logging.getLogger(__name__)


class SettingsService:
    """Enterprise settings service with caching and analytics."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._model_cache: Dict[str, Any] = {}
        self._system_defaults_cache: Optional[ModelPreferencesSchema] = None
    
    async def get_user_configuration(
        self, 
        anonymous_id: Optional[str] = None, 
        user_id: Optional[str] = None
    ) -> SettingsConfigResponse:
        """Get complete user settings configuration."""
        logger.info(f"Getting user configuration for anonymous_id={anonymous_id}, user_id={user_id}")
        
        # Get or create user preferences
        current_profile = await self._get_or_create_user_preferences(anonymous_id, user_id)
        
        # Get available profiles
        available_profiles = await self.list_profiles(anonymous_id, user_id)
        
        # Get available models (cached)
        available_models = await self.get_available_models()
        
        # Get system defaults
        system_defaults = await self._get_system_defaults()
        
        # Get feature flags
        feature_flags = await self._get_feature_flags()
        
        return SettingsConfigResponse(
            current_profile=current_profile,
            available_profiles=available_profiles,
            available_models=available_models,
            system_defaults=system_defaults,
            feature_flags=feature_flags
        )
    
    async def update_preferences(
        self,
        preferences: ModelPreferencesUpdateSchema,
        anonymous_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> SettingsUpdateResponse:
        """Update user model preferences."""
        logger.info(f"Updating preferences for anonymous_id={anonymous_id}, user_id={user_id}")
        
        # Get existing preferences
        user_prefs = await self._get_or_create_user_preferences(anonymous_id, user_id)
        
        # Update preferences with provided values
        update_data = {}
        if preferences.preferred_strategy is not None:
            update_data['preferred_strategy'] = preferences.preferred_strategy.value
        if preferences.ensemble_weights is not None:
            update_data['ensemble_weights'] = preferences.ensemble_weights
        if preferences.quality_preference is not None:
            update_data['quality_preference'] = preferences.quality_preference.value
        if preferences.enable_experimental is not None:
            update_data['enable_experimental'] = preferences.enable_experimental
        if preferences.confidence_threshold is not None:
            update_data['confidence_threshold'] = preferences.confidence_threshold
        if preferences.max_processing_time is not None:
            update_data['max_processing_time'] = preferences.max_processing_time
        if preferences.fallback_strategy is not None:
            update_data['fallback_strategy'] = preferences.fallback_strategy.value
        if preferences.custom_settings is not None:
            # Merge with existing custom settings
            existing_custom = user_prefs.advanced_settings or {}
            existing_custom.update(preferences.custom_settings)
            update_data['advanced_settings'] = existing_custom
        
        # Update timestamps
        update_data['updated_at'] = datetime.utcnow()
        update_data['last_used'] = datetime.utcnow()
        
        # Apply updates to database
        stmt = (
            update(UserPreferences)
            .where(UserPreferences.id == user_prefs.id)
            .values(**update_data)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Get updated profile
        updated_profile = await self._get_user_preferences_by_id(user_prefs.id)
        
        return SettingsUpdateResponse(
            profile=updated_profile,
            cache_invalidated=True,
            message="Preferences updated successfully"
        )
    
    async def create_profile(
        self,
        profile_data: UserSettingsProfileCreateSchema,
        anonymous_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> UserSettingsProfileSchema:
        """Create a new settings profile."""
        logger.info(f"Creating profile '{profile_data.name}' for anonymous_id={anonymous_id}, user_id={user_id}")
        
        # Create base user preferences
        user_prefs = UserPreferences(
            anonymous_id=anonymous_id,
            user_id=user_id,
            preferred_strategy=profile_data.preferences.preferred_strategy.value,
            ensemble_weights=profile_data.preferences.ensemble_weights,
            quality_preference=profile_data.preferences.quality_preference.value,
            enable_experimental=profile_data.preferences.enable_experimental,
            confidence_threshold=profile_data.preferences.confidence_threshold,
            max_processing_time=profile_data.preferences.max_processing_time,
            fallback_strategy=profile_data.preferences.fallback_strategy.value,
            profile_name=profile_data.name,
            profile_description=profile_data.description,
            is_custom=True,
            advanced_settings=profile_data.preferences.custom_settings
        )
        
        self.db.add(user_prefs)
        await self.db.flush()  # Get the ID
        
        # Create profile entry
        profile = UserSettingsProfile(
            user_preferences_id=user_prefs.id,
            name=profile_data.name,
            description=profile_data.description,
            is_system_profile=False,
            is_active=False,
            configuration={
                "preferred_strategy": profile_data.preferences.preferred_strategy.value,
                "ensemble_weights": profile_data.preferences.ensemble_weights,
                "quality_preference": profile_data.preferences.quality_preference.value,
                "enable_experimental": profile_data.preferences.enable_experimental,
                "confidence_threshold": profile_data.preferences.confidence_threshold,
                "max_processing_time": profile_data.preferences.max_processing_time,
                "fallback_strategy": profile_data.preferences.fallback_strategy.value,
                "custom_settings": profile_data.preferences.custom_settings
            }
        )
        
        self.db.add(profile)
        await self.db.commit()
        
        return await self._convert_to_schema(user_prefs)
    
    async def list_profiles(
        self,
        anonymous_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[UserSettingsProfileSchema]:
        """List all settings profiles for a user."""
        stmt = select(UserPreferences).where(
            or_(
                UserPreferences.anonymous_id == anonymous_id,
                UserPreferences.user_id == user_id
            )
        )
        
        result = await self.db.execute(stmt)
        profiles = result.scalars().all()
        
        return [await self._convert_to_schema(profile) for profile in profiles]
    
    async def select_profile(
        self,
        profile_id: str,
        anonymous_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ProfileSelectionResponse:
        """Select a settings profile as active."""
        logger.info(f"Selecting profile {profile_id} for anonymous_id={anonymous_id}, user_id={user_id}")
        
        # Get current active profile
        current_active = await self._get_or_create_user_preferences(anonymous_id, user_id)
        previous_profile_id = str(current_active.id)
        
        # Deactivate current profile
        await self.db.execute(
            update(UserPreferences)
            .where(UserPreferences.id == current_active.id)
            .values(is_default=False, last_used=datetime.utcnow())
        )
        
        # Activate new profile
        await self.db.execute(
            update(UserPreferences)
            .where(UserPreferences.id == profile_id)
            .values(is_default=True, last_used=datetime.utcnow(), usage_count=UserPreferences.usage_count + 1)
        )
        
        await self.db.commit()
        
        # Get updated profile
        active_profile = await self._get_user_preferences_by_id(profile_id)
        
        return ProfileSelectionResponse(
            active_profile=active_profile,
            previous_profile_id=previous_profile_id,
            message=f"Profile '{active_profile.name}' is now active"
        )
    
    async def delete_profile(
        self,
        profile_id: str,
        anonymous_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete a settings profile."""
        logger.info(f"Deleting profile {profile_id} for anonymous_id={anonymous_id}, user_id={user_id}")
        
        # Ensure user owns this profile
        stmt = select(UserPreferences).where(
            and_(
                UserPreferences.id == profile_id,
                or_(
                    UserPreferences.anonymous_id == anonymous_id,
                    UserPreferences.user_id == user_id
                )
            )
        )
        
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise ValueError("Profile not found or access denied")
        
        if profile.is_default:
            raise ValueError("Cannot delete the active profile")
        
        # Delete profile and related data
        await self.db.execute(delete(UserSettingsProfile).where(UserSettingsProfile.user_preferences_id == profile_id))
        await self.db.execute(delete(UserPreferences).where(UserPreferences.id == profile_id))
        await self.db.commit()
        
        return True
    
    async def get_available_models(self) -> List[AvailableModelInfoSchema]:
        """Get information about all available AI models."""
        if self._model_cache:
            return list(self._model_cache.values())
        
        # Build available models list
        models = [
            AvailableModelInfoSchema(
                id="huggingface_ensemble",
                name="HuggingFace Ensemble",
                description="Pre-trained DistilHuBERT + Wav2Vec2 ensemble for accurate genre detection",
                type=ModelType.HUGGINGFACE,
                performance=ModelPerformanceInfoSchema(
                    average_processing_time=1200,
                    accuracy=0.92,
                    memory_usage=1024,
                    gpu_required=True,
                    supported_genres=["hiphop", "rock", "pop", "electronic", "classical", "jazz", "blues", "country", "reggae", "metal"]
                ),
                is_available=True,
                requirements=["CUDA 12.4+", "8GB GPU Memory"],
                version="1.0.0",
                provider="HuggingFace"
            ),
            AvailableModelInfoSchema(
                id="ast_model",
                name="Audio Spectrogram Transformer",
                description="Transformer-based model for audio classification with 768-dim features",
                type=ModelType.AST,
                performance=ModelPerformanceInfoSchema(
                    average_processing_time=800,
                    accuracy=0.87,
                    memory_usage=512,
                    gpu_required=True,
                    supported_genres=["hiphop", "rock", "pop", "electronic", "classical", "jazz", "blues", "country", "reggae", "metal"]
                ),
                is_available=True,
                requirements=["CUDA 12.4+", "4GB GPU Memory"],
                version="1.0.0",
                provider="MIT"
            ),
            AvailableModelInfoSchema(
                id="fallback_classifier",
                name="Fallback Classifier",
                description="CPU-based audio characteristics analysis for reliable fallback",
                type=ModelType.CUSTOM,
                performance=ModelPerformanceInfoSchema(
                    average_processing_time=200,
                    accuracy=0.65,
                    memory_usage=128,
                    gpu_required=False,
                    supported_genres=["hiphop", "rock", "pop", "electronic", "classical", "jazz"]
                ),
                is_available=True,
                requirements=["CPU only"],
                version="1.0.0",
                provider="Matchering"
            )
        ]
        
        # Cache the models
        self._model_cache = {model.id: model for model in models}
        
        return models
    
    async def get_analytics(
        self,
        anonymous_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> UserSettingsAnalyticsSchema:
        """Get user settings usage analytics."""
        logger.info(f"Getting analytics for anonymous_id={anonymous_id}, user_id={user_id}, days={days}")
        
        # Get user preferences
        user_prefs = await self._get_or_create_user_preferences(anonymous_id, user_id)
        
        # Get performance history for the period
        start_date = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(ModelPerformanceHistory)
            .where(
                and_(
                    ModelPerformanceHistory.user_preferences_id == user_prefs.id,
                    ModelPerformanceHistory.created_at >= start_date
                )
            )
        )
        
        result = await self.db.execute(stmt)
        history = result.scalars().all()
        
        # Calculate analytics
        total_jobs = len(history)
        avg_processing_time = sum(h.processing_time for h in history) / max(total_jobs, 1)
        
        # Model usage distribution
        model_usage = {}
        for h in history:
            model_usage[h.model_used] = model_usage.get(h.model_used, 0) + 1
        
        # Most used model
        most_used_model = max(model_usage.items(), key=lambda x: x[1])[0] if model_usage else None
        
        # Quality ratings (from satisfaction scores)
        quality_ratings = {}
        for h in history:
            if h.user_satisfaction:
                model = h.model_used
                if model not in quality_ratings:
                    quality_ratings[model] = []
                quality_ratings[model].append(float(h.user_satisfaction))
        
        # Average quality ratings
        avg_quality_ratings = {
            model: sum(ratings) / len(ratings) 
            for model, ratings in quality_ratings.items()
        }
        
        return UserSettingsAnalyticsSchema(
            total_processing_jobs=total_jobs,
            average_processing_time=avg_processing_time,
            most_used_model=most_used_model,
            model_usage_distribution=model_usage,
            quality_ratings=avg_quality_ratings,
            performance_trends={},  # TODO: Implement trending analysis
            period_days=days
        )
    
    async def get_system_status(self) -> SystemStatusResponse:
        """Get system status for settings service."""
        available_models = await self.get_available_models()
        
        # Count active users (users with activity in last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        stmt = select(func.count(UserPreferences.id)).where(UserPreferences.last_used >= week_ago)
        result = await self.db.execute(stmt)
        active_users = result.scalar() or 0
        
        return SystemStatusResponse(
            available_models_count=len(available_models),
            active_users_count=active_users,
            cache_hit_rate=0.95,  # TODO: Implement actual cache metrics
            average_response_time=120.0,  # TODO: Implement actual metrics
            feature_flags=await self._get_feature_flags(),
            last_updated=datetime.utcnow()
        )
    
    # Private helper methods
    async def _get_or_create_user_preferences(
        self, 
        anonymous_id: Optional[str], 
        user_id: Optional[str]
    ) -> UserSettingsProfileSchema:
        """Get or create user preferences with default values."""
        stmt = select(UserPreferences).where(
            or_(
                and_(UserPreferences.anonymous_id == anonymous_id, anonymous_id is not None),
                and_(UserPreferences.user_id == user_id, user_id is not None)
            )
        ).where(UserPreferences.is_default == True)
        
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return await self._convert_to_schema(existing)
        
        # Create default preferences
        defaults = await self._get_system_defaults()
        new_prefs = UserPreferences(
            anonymous_id=anonymous_id,
            user_id=user_id,
            preferred_strategy=defaults.preferred_strategy.value,
            ensemble_weights=defaults.ensemble_weights,
            quality_preference=defaults.quality_preference.value,
            enable_experimental=defaults.enable_experimental,
            confidence_threshold=defaults.confidence_threshold,
            max_processing_time=defaults.max_processing_time,
            fallback_strategy=defaults.fallback_strategy.value,
            profile_name="Default",
            is_default=True,
            advanced_settings=defaults.custom_settings
        )
        
        self.db.add(new_prefs)
        await self.db.commit()
        
        return await self._convert_to_schema(new_prefs)
    
    async def _get_user_preferences_by_id(self, preferences_id: str) -> UserSettingsProfileSchema:
        """Get user preferences by ID."""
        stmt = select(UserPreferences).where(UserPreferences.id == preferences_id)
        result = await self.db.execute(stmt)
        prefs = result.scalar_one()
        return await self._convert_to_schema(prefs)
    
    async def _convert_to_schema(self, prefs: UserPreferences) -> UserSettingsProfileSchema:
        """Convert UserPreferences model to schema."""
        return UserSettingsProfileSchema(
            id=str(prefs.id),
            name=prefs.profile_name,
            description=prefs.profile_description,
            preferred_strategy=ModelSelectionStrategy(prefs.preferred_strategy),
            ensemble_weights=prefs.ensemble_weights,
            quality_preference=QualityPreference(prefs.quality_preference),
            enable_experimental=prefs.enable_experimental,
            confidence_threshold=prefs.confidence_threshold,
            max_processing_time=prefs.max_processing_time,
            fallback_strategy=FallbackStrategy(prefs.fallback_strategy),
            advanced_settings=prefs.advanced_settings or {},
            feature_flags=prefs.feature_flags or {},
            is_default=prefs.is_default,
            is_custom=prefs.is_custom,
            usage_count=prefs.usage_count,
            created_at=prefs.created_at,
            updated_at=prefs.updated_at,
            last_used=prefs.last_used
        )
    
    async def _get_system_defaults(self) -> ModelPreferencesSchema:
        """Get system default settings."""
        if self._system_defaults_cache:
            return self._system_defaults_cache
        
        defaults = ModelPreferencesSchema(
            preferred_strategy=ModelSelectionStrategy.AUTO,
            ensemble_weights={"huggingface": 0.70, "ast": 0.25, "fallback": 0.05},
            quality_preference=QualityPreference.BALANCED,
            enable_experimental=False,
            confidence_threshold=0.6,
            max_processing_time=5000,
            fallback_strategy=FallbackStrategy.GRACEFUL,
            custom_settings={}
        )
        
        self._system_defaults_cache = defaults
        return defaults
    
    async def _get_feature_flags(self) -> Dict[str, bool]:
        """Get current feature flags."""
        return {
            "enable_huggingface_models": True,
            "enable_experimental_models": False,
            "enable_custom_ensemble_weights": True,
            "enable_performance_analytics": True,
            "enable_a_b_testing": False,
            "enable_user_feedback": True
        }