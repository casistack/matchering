"""
Test script for Settings API functionality.

Validates the enterprise-grade settings implementation.
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.services.settings_service import SettingsService
from app.schemas.settings import ModelPreferencesUpdateSchema, ModelSelectionStrategy, QualityPreference


async def test_settings_service():
    """Test the settings service functionality."""
    print("🧪 Testing Settings Service...")
    
    # Create test database
    engine = create_async_engine("sqlite+aiosqlite:///test_settings.db", echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        service = SettingsService(session)
        test_anonymous_id = str(uuid.uuid4())
        
        print(f"📝 Testing with anonymous_id: {test_anonymous_id}")
        
        # Test 1: Get user configuration (should create default)
        print("1️⃣ Testing get_user_configuration...")
        config = await service.get_user_configuration(anonymous_id=test_anonymous_id)
        assert config.current_profile is not None
        assert config.current_profile.name == "Default"
        assert config.current_profile.preferred_strategy == ModelSelectionStrategy.AUTO
        print("   ✅ Default configuration created successfully")
        
        # Test 2: Update preferences
        print("2️⃣ Testing update_preferences...")
        update_data = ModelPreferencesUpdateSchema(
            preferred_strategy=ModelSelectionStrategy.QUALITY,
            quality_preference=QualityPreference.QUALITY,
            confidence_threshold=0.8,
            max_processing_time=7000
        )
        
        result = await service.update_preferences(update_data, anonymous_id=test_anonymous_id)
        assert result.success is True
        assert result.profile.preferred_strategy == ModelSelectionStrategy.QUALITY
        assert result.profile.confidence_threshold == 0.8
        print("   ✅ Preferences updated successfully")
        
        # Test 3: Get available models
        print("3️⃣ Testing get_available_models...")
        models = await service.get_available_models()
        assert len(models) >= 3  # Should have at least huggingface, ast, fallback
        model_ids = [m.id for m in models]
        assert "huggingface_ensemble" in model_ids
        assert "ast_model" in model_ids
        assert "fallback_classifier" in model_ids
        print(f"   ✅ Found {len(models)} available models")
        
        # Test 4: Get analytics
        print("4️⃣ Testing get_analytics...")
        analytics = await service.get_analytics(anonymous_id=test_anonymous_id, days=30)
        assert analytics.total_processing_jobs == 0  # No jobs yet
        assert analytics.period_days == 30
        print("   ✅ Analytics retrieved successfully")
        
        # Test 5: Get system status
        print("5️⃣ Testing get_system_status...")
        status = await service.get_system_status()
        assert status.available_models_count >= 3
        assert isinstance(status.feature_flags, dict)
        assert "enable_huggingface_models" in status.feature_flags
        print("   ✅ System status retrieved successfully")
        
        print("\n🎉 All settings service tests passed!")
        return True


async def main():
    """Run all tests."""
    try:
        await test_settings_service()
        print("\n✨ Settings API implementation is enterprise-ready!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())