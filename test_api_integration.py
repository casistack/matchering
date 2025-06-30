#!/usr/bin/env python3
"""
Test script for API integration validation.

This script tests that the hybrid AI API is properly integrated
with the main FastAPI application router.
"""

import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_router_integration():
    """Test that hybrid AI router is integrated with main API."""
    logger.info("Testing API router integration...")
    
    try:
        # Add backend path
        backend_path = Path(__file__).parent / "backend"
        sys.path.append(str(backend_path))
        
        from backend.app.api.v1.api import api_router
        
        # Check that the hybrid AI router is included
        found_hybrid_ai = False
        
        # FastAPI router routes are in the routes attribute
        for route in api_router.routes:
            if hasattr(route, 'path') and '/hybrid-ai' in str(route.path):
                found_hybrid_ai = True
                logger.info(f"✓ Found hybrid AI route: {route.path}")
        
        if not found_hybrid_ai:
            # Check through nested routers
            for route in api_router.routes:
                if hasattr(route, 'path_regex') and '/hybrid-ai' in str(route.path_regex):
                    found_hybrid_ai = True
                    logger.info(f"✓ Found hybrid AI route (regex): {route.path_regex}")
        
        if found_hybrid_ai:
            logger.info("✓ Hybrid AI router successfully integrated")
            return True
        else:
            logger.error("❌ Hybrid AI router not found in main API")
            return False
        
    except Exception as e:
        logger.error(f"API router integration test failed: {e}")
        return False


def test_endpoint_availability():
    """Test that hybrid AI endpoints are available."""
    logger.info("Testing endpoint availability...")
    
    try:
        backend_path = Path(__file__).parent / "backend"
        sys.path.append(str(backend_path))
        
        from backend.app.api.v1.endpoints.hybrid_ai import router
        
        expected_endpoints = [
            "extract-hybrid-features",
            "select-model", 
            "predict-parameters",
            "process-hybrid",
            "model-performance",
            "available-models",
            "health"
        ]
        
        found_endpoints = []
        for route in router.routes:
            if hasattr(route, 'path'):
                # Remove the prefix to get the endpoint name
                endpoint_path = route.path.replace('/hybrid-ai/', '').replace('/', '')
                if endpoint_path in expected_endpoints:
                    found_endpoints.append(endpoint_path)
                    logger.info(f"✓ Found endpoint: {endpoint_path}")
        
        missing_endpoints = set(expected_endpoints) - set(found_endpoints)
        if missing_endpoints:
            logger.error(f"❌ Missing endpoints: {list(missing_endpoints)}")
            return False
        
        logger.info(f"✓ All {len(expected_endpoints)} endpoints found")
        return True
        
    except Exception as e:
        logger.error(f"Endpoint availability test failed: {e}")
        return False


def test_schema_compatibility():
    """Test that schemas are compatible."""
    logger.info("Testing schema compatibility...")
    
    try:
        backend_path = Path(__file__).parent / "backend"
        sys.path.append(str(backend_path))
        
        # Test importing the request/response models
        from backend.app.api.v1.endpoints.hybrid_ai import (
            HybridMasteringRequest,
            HybridMasteringResponse,
            ModelSelectionResponse,
            ModelPerformanceResponse
        )
        
        # Test creating instances
        request = HybridMasteringRequest()
        logger.info(f"✓ HybridMasteringRequest default: {request.model_preference}")
        
        # Test that required imports work
        from backend.app.ai.hybrid_feature_extractor import AudioCharacteristics
        from backend.app.ai.mastering_model import MasteringParameters
        
        logger.info("✓ All schema imports successful")
        return True
        
    except Exception as e:
        logger.error(f"Schema compatibility test failed: {e}")
        return False


def test_file_structure():
    """Test that all required files are present."""
    logger.info("Testing file structure...")
    
    try:
        backend_path = Path(__file__).parent / "backend"
        
        required_files = [
            "app/api/v1/api.py",
            "app/api/v1/endpoints/hybrid_ai.py",
            "app/ai/hybrid_feature_extractor.py",
            "app/ai/mastering_model.py",
            "app/utils/file_utils.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = backend_path / file_path
            if full_path.exists():
                logger.info(f"✓ Found: {file_path}")
            else:
                missing_files.append(file_path)
                logger.error(f"❌ Missing: {file_path}")
        
        if missing_files:
            logger.error(f"Missing files: {missing_files}")
            return False
        
        logger.info("✓ All required files present")
        return True
        
    except Exception as e:
        logger.error(f"File structure test failed: {e}")
        return False


def run_integration_tests():
    """Run comprehensive integration tests."""
    logger.info("Starting API Integration Tests...")
    logger.info("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Schema Compatibility", test_schema_compatibility),
        ("Endpoint Availability", test_endpoint_availability),
        ("API Router Integration", test_api_router_integration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ FAILED: {test_name} - {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL INTEGRATION TESTS PASSED! API is ready for deployment.")
    elif passed >= total * 0.8:
        logger.info("⚠️  Most integration tests passed. Minor issues may exist.")
    else:
        logger.info("❌ Multiple integration tests failed. Review implementation.")
    
    return results


if __name__ == "__main__":
    results = run_integration_tests()
    
    # Return appropriate exit code
    passed = sum(results.values())
    total = len(results)
    success_rate = passed / total if total > 0 else 0
    
    if success_rate >= 0.8:  # 80% success rate
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure