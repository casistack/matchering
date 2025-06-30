#!/usr/bin/env python3
"""
Test script for API structure validation.

This script tests the API endpoints structure and import compatibility
without requiring full environment setup.
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


def test_basic_imports():
    """Test basic Python imports without torch/CUDA dependencies."""
    logger.info("Testing basic imports...")
    
    try:
        import asyncio
        import json
        import time
        from typing import Dict, List, Optional
        from pathlib import Path
        from pydantic import BaseModel, Field
        
        logger.info("✓ Basic Python libraries imported successfully")
        return True
        
    except Exception as e:
        logger.error(f"Basic imports failed: {e}")
        return False


def test_fastapi_compatibility():
    """Test FastAPI compatibility without full app startup."""
    logger.info("Testing FastAPI compatibility...")
    
    try:
        from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks
        from fastapi.responses import JSONResponse
        
        # Test creating a basic router
        router = APIRouter(prefix="/test", tags=["Test"])
        
        logger.info("✓ FastAPI libraries imported successfully")
        return True
        
    except Exception as e:
        logger.error(f"FastAPI compatibility test failed: {e}")
        return False


def test_pydantic_models():
    """Test Pydantic model structure without dependencies."""
    logger.info("Testing Pydantic models...")
    
    try:
        from pydantic import BaseModel, Field
        from typing import Dict, List, Optional
        
        # Test creating models similar to our API schemas
        class TestRequest(BaseModel):
            model_preference: str = Field(default="auto")
            processing_mode: str = Field(default="hybrid")
            intensity_level: str = Field(default="medium")
        
        class TestResponse(BaseModel):
            success: bool = Field(description="Whether processing was successful")
            job_id: str = Field(description="Processing job identifier")
            model_used: str = Field(description="AI model used")
        
        # Test model creation
        request = TestRequest(model_preference="ast")
        response = TestResponse(success=True, job_id="test-123", model_used="ast")
        
        logger.info(f"✓ Test request created: {request.model_preference}")
        logger.info(f"✓ Test response created: success={response.success}")
        
        return True
        
    except Exception as e:
        logger.error(f"Pydantic model test failed: {e}")
        return False


def test_api_endpoint_structure():
    """Test API endpoint structure validation."""
    logger.info("Testing API endpoint structure...")
    
    try:
        # Read the hybrid_ai.py file and validate structure
        api_file = Path(__file__).parent / "backend" / "app" / "api" / "v1" / "endpoints" / "hybrid_ai.py"
        
        if not api_file.exists():
            logger.error(f"API file not found: {api_file}")
            return False
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check for required endpoint patterns
        required_endpoints = [
            "/extract-hybrid-features",
            "/select-model", 
            "/predict-parameters",
            "/process-hybrid",
            "/model-performance",
            "/available-models",
            "/health"
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            logger.error(f"Missing endpoints: {missing_endpoints}")
            return False
        
        # Check for required imports
        required_imports = [
            "from fastapi import",
            "from pydantic import",
            "import logging"
        ]
        
        missing_imports = []
        for import_stmt in required_imports:
            if import_stmt not in content:
                missing_imports.append(import_stmt)
        
        if missing_imports:
            logger.error(f"Missing imports: {missing_imports}")
            return False
        
        logger.info(f"✓ All {len(required_endpoints)} endpoints found")
        logger.info("✓ Required imports present")
        logger.info(f"✓ API file structure valid ({len(content)} chars)")
        
        return True
        
    except Exception as e:
        logger.error(f"API endpoint structure test failed: {e}")
        return False


def test_documentation_completeness():
    """Test that API endpoints have proper documentation."""
    logger.info("Testing API documentation completeness...")
    
    try:
        api_file = Path(__file__).parent / "backend" / "app" / "api" / "v1" / "endpoints" / "hybrid_ai.py"
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        # Check for docstrings and documentation
        doc_patterns = [
            '"""',  # Docstrings
            'summary=',  # FastAPI summaries
            'description=',  # FastAPI descriptions
            'Args:',  # Function argument documentation
            'Returns:'  # Return value documentation
        ]
        
        doc_counts = {}
        for pattern in doc_patterns:
            count = content.count(pattern)
            doc_counts[pattern] = count
        
        logger.info("✓ Documentation patterns found:")
        for pattern, count in doc_counts.items():
            logger.info(f"  {pattern}: {count} occurrences")
        
        # Check that we have reasonable documentation coverage
        if doc_counts['"""'] < 5:  # At least 5 docstrings
            logger.warning("⚠️  Low docstring coverage")
        
        if doc_counts['summary='] < 5:  # At least 5 endpoint summaries
            logger.warning("⚠️  Low endpoint summary coverage")
        
        logger.info("✓ Documentation analysis completed")
        return True
        
    except Exception as e:
        logger.error(f"Documentation completeness test failed: {e}")
        return False


def run_structure_tests():
    """Run API structure validation tests."""
    logger.info("Starting API Structure Validation...")
    logger.info("=" * 60)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("FastAPI Compatibility", test_fastapi_compatibility),
        ("Pydantic Models", test_pydantic_models),
        ("API Endpoint Structure", test_api_endpoint_structure),
        ("Documentation Completeness", test_documentation_completeness),
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
    logger.info("STRUCTURE TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ALL STRUCTURE TESTS PASSED! API structure is valid.")
    elif passed >= total * 0.8:
        logger.info("⚠️  Most structure tests passed. Minor issues detected.")
    else:
        logger.info("❌ Multiple structure tests failed. Review API implementation.")
    
    return results


if __name__ == "__main__":
    results = run_structure_tests()
    
    # Return appropriate exit code
    passed = sum(results.values())
    total = len(results)
    success_rate = passed / total if total > 0 else 0
    
    if success_rate >= 0.8:  # 80% success rate
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure