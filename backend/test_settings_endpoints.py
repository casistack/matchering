"""
Comprehensive test suite for Settings API endpoints.

Tests all enterprise settings functionality with proper validation.
"""

import asyncio
import uuid
import json
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db


async def override_get_db():
    """Override database dependency for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///test_endpoints.db", echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


def test_settings_api_endpoints():
    """Test all settings API endpoints comprehensively."""
    print("🧪 Testing Settings API Endpoints...")
    
    client = TestClient(app)
    test_anonymous_id = str(uuid.uuid4())
    
    print(f"📝 Testing with anonymous_id: {test_anonymous_id}")
    
    # Test 1: Get user configuration (creates default)
    print("1️⃣ Testing GET /api/v1/settings/config...")
    response = client.get(f"/api/v1/settings/config?anonymous_id={test_anonymous_id}")
    assert response.status_code == 200
    config_data = response.json()
    
    assert "current_profile" in config_data
    assert "available_profiles" in config_data
    assert "available_models" in config_data
    assert "system_defaults" in config_data
    assert "feature_flags" in config_data
    
    current_profile = config_data["current_profile"]
    assert current_profile["name"] == "Default"
    assert current_profile["preferred_strategy"] == "auto"
    print("   ✅ Configuration retrieved and default profile created")
    
    # Test 2: Get available models
    print("2️⃣ Testing GET /api/v1/settings/models...")
    response = client.get("/api/v1/settings/models")
    assert response.status_code == 200
    models = response.json()
    
    assert len(models) >= 3
    model_ids = [m["id"] for m in models]
    assert "huggingface_ensemble" in model_ids
    assert "ast_model" in model_ids
    assert "fallback_classifier" in model_ids
    
    # Validate model structure
    hf_model = next(m for m in models if m["id"] == "huggingface_ensemble")
    assert hf_model["type"] == "huggingface"
    assert "performance" in hf_model
    assert hf_model["performance"]["gpu_required"] is True
    print(f"   ✅ Found {len(models)} models with correct structure")
    
    # Test 3: Update preferences
    print("3️⃣ Testing PUT /api/v1/settings/preferences...")
    update_data = {
        "preferred_strategy": "quality",
        "quality_preference": "quality",
        "confidence_threshold": 0.8,
        "max_processing_time": 7000,
        "ensemble_weights": {
            "huggingface": 0.8,
            "ast": 0.15,
            "fallback": 0.05
        }
    }
    
    response = client.put(
        f"/api/v1/settings/preferences?anonymous_id={test_anonymous_id}",
        json=update_data
    )
    assert response.status_code == 200
    update_result = response.json()
    
    assert update_result["success"] is True
    assert update_result["profile"]["preferred_strategy"] == "quality"
    assert update_result["profile"]["confidence_threshold"] == 0.8
    assert update_result["cache_invalidated"] is True
    print("   ✅ Preferences updated successfully")
    
    # Test 4: Create new profile
    print("4️⃣ Testing POST /api/v1/settings/profiles...")
    profile_data = {
        "name": "High Quality",
        "description": "Maximum quality processing profile",
        "preferences": {
            "preferred_strategy": "quality",
            "ensemble_weights": {
                "huggingface": 0.9,
                "ast": 0.08,
                "fallback": 0.02
            },
            "quality_preference": "quality",
            "enable_experimental": True,
            "confidence_threshold": 0.9,
            "max_processing_time": 8000,
            "fallback_strategy": "strict",
            "custom_settings": {
                "enable_advanced_processing": True
            }
        }
    }
    
    response = client.post(
        f"/api/v1/settings/profiles?anonymous_id={test_anonymous_id}",
        json=profile_data
    )
    assert response.status_code == 200
    created_profile = response.json()
    
    assert created_profile["name"] == "High Quality"
    assert created_profile["preferred_strategy"] == "quality"
    assert created_profile["enable_experimental"] is True
    assert created_profile["is_custom"] is True
    print("   ✅ Profile created successfully")
    
    new_profile_id = created_profile["id"]
    
    # Test 5: List profiles
    print("5️⃣ Testing GET /api/v1/settings/profiles...")
    response = client.get(f"/api/v1/settings/profiles?anonymous_id={test_anonymous_id}")
    assert response.status_code == 200
    profiles = response.json()
    
    assert len(profiles) >= 2  # Default + newly created
    profile_names = [p["name"] for p in profiles]
    assert "Default" in profile_names
    assert "High Quality" in profile_names
    print(f"   ✅ Listed {len(profiles)} profiles")
    
    # Test 6: Select profile
    print("6️⃣ Testing PUT /api/v1/settings/profiles/{profile_id}/select...")
    response = client.put(
        f"/api/v1/settings/profiles/{new_profile_id}/select?anonymous_id={test_anonymous_id}"
    )
    assert response.status_code == 200
    selection_result = response.json()
    
    assert selection_result["success"] is True
    assert selection_result["active_profile"]["id"] == new_profile_id
    assert selection_result["active_profile"]["name"] == "High Quality"
    assert selection_result["previous_profile_id"] is not None
    print("   ✅ Profile selected successfully")
    
    # Test 7: Get analytics
    print("7️⃣ Testing GET /api/v1/settings/analytics...")
    response = client.get(f"/api/v1/settings/analytics?anonymous_id={test_anonymous_id}&days=30")
    assert response.status_code == 200
    analytics = response.json()
    
    assert "total_processing_jobs" in analytics
    assert "average_processing_time" in analytics
    assert "model_usage_distribution" in analytics
    assert "period_days" in analytics
    assert analytics["period_days"] == 30
    print("   ✅ Analytics retrieved successfully")
    
    # Test 8: Get system status
    print("8️⃣ Testing GET /api/v1/settings/system/status...")
    response = client.get("/api/v1/settings/system/status")
    assert response.status_code == 200
    status = response.json()
    
    assert "available_models_count" in status
    assert "active_users_count" in status
    assert "feature_flags" in status
    assert "last_updated" in status
    assert status["available_models_count"] >= 3
    print("   ✅ System status retrieved successfully")
    
    # Test 9: Reset to defaults
    print("9️⃣ Testing POST /api/v1/settings/reset-defaults...")
    response = client.post(f"/api/v1/settings/reset-defaults?anonymous_id={test_anonymous_id}")
    assert response.status_code == 200
    reset_result = response.json()
    
    assert reset_result["success"] is True
    assert reset_result["profile"]["preferred_strategy"] == "auto"  # Back to default
    assert reset_result["profile"]["confidence_threshold"] == 0.6  # Default value
    print("   ✅ Reset to defaults successful")
    
    # Test 10: Delete profile
    print("🔟 Testing DELETE /api/v1/settings/profiles/{profile_id}...")
    response = client.delete(
        f"/api/v1/settings/profiles/{new_profile_id}?anonymous_id={test_anonymous_id}"
    )
    assert response.status_code == 200
    delete_result = response.json()
    
    assert delete_result["success"] is True
    assert "deleted successfully" in delete_result["message"]
    print("   ✅ Profile deleted successfully")
    
    # Test 11: Error handling - missing anonymous_id
    print("1️⃣1️⃣ Testing error handling...")
    response = client.get("/api/v1/settings/config")  # No anonymous_id
    assert response.status_code == 400
    error_data = response.json()
    assert "anonymous_id or user_id must be provided" in error_data["detail"]
    print("   ✅ Error handling working correctly")
    
    # Test 12: Validation - invalid ensemble weights
    print("1️⃣2️⃣ Testing validation...")
    invalid_data = {
        "ensemble_weights": {
            "huggingface": 0.5,
            "ast": 0.3,
            "fallback": 0.1  # Sum = 0.9, should fail validation
        }
    }
    
    response = client.put(
        f"/api/v1/settings/preferences?anonymous_id={test_anonymous_id}",
        json=invalid_data
    )
    assert response.status_code == 400
    print("   ✅ Validation working correctly")
    
    print("\n🎉 All Settings API endpoint tests passed!")
    return True


def main():
    """Run all endpoint tests."""
    try:
        test_settings_api_endpoints()
        print("\n✨ Settings API endpoints are enterprise-ready!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()