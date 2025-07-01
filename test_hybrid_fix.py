#!/usr/bin/env python3
"""
Test script for hybrid AI processing fixes.

This script tests the API response format and validates that the fixes are working correctly.
"""

import requests
import json
import time
from pathlib import Path


def test_hybrid_ai_health():
    """Test hybrid AI health endpoint."""
    try:
        response = requests.get('http://localhost:8000/api/v1/hybrid-ai/health')
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Health response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"Health check error: {e}")
        return False


def test_available_models():
    """Test available models endpoint."""
    try:
        response = requests.get('http://localhost:8000/api/v1/hybrid-ai/available-models')
        print(f"Available models status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Models response structure: {list(data.keys())}")
            
            # Check if response follows API format
            expected_keys = ['success', 'data', 'error', 'timestamp', 'requestId']
            has_api_format = all(key in data for key in expected_keys)
            print(f"Follows API response format: {has_api_format}")
            
            if has_api_format and data['success']:
                print(f"Available models: {data['data']['total_available']}")
                return True
            else:
                print(f"API format issue: {data}")
                return False
        else:
            print(f"Available models failed: {response.text}")
            return False
    except Exception as e:
        print(f"Available models error: {e}")
        return False


def test_hybrid_processing_format():
    """Test that hybrid processing would return correct format (without actual file)."""
    try:
        # Create a small test file
        test_file_path = Path("test_audio.txt")
        test_file_path.write_text("dummy audio data for format testing")
        
        # Test just the format by checking what happens with wrong file type
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_audio.txt', f, 'text/plain')}
            data = {
                'model_preference': 'auto',
                'processing_mode': 'hybrid',
                'intensity_level': 'medium',
                'preserve_dynamics': 'true',
                'target_loudness_lufs': '-14.0'
            }
            
            response = requests.post(
                'http://localhost:8000/api/v1/hybrid-ai/process-hybrid',
                files=files,
                data=data
            )
            
            print(f"Process hybrid status: {response.status_code}")
            
            if response.status_code in [400, 500]:  # Expected for wrong file type
                # Should still return proper API format even for errors
                try:
                    data = response.json()
                    expected_keys = ['success', 'data', 'error', 'timestamp', 'requestId']
                    has_api_format = all(key in data for key in expected_keys)
                    print(f"Error response follows API format: {has_api_format}")
                    print(f"Error response: {json.dumps(data, indent=2)}")
                    return has_api_format
                except:
                    print("Error response is not JSON")
                    print(f"Raw response: {response.text}")
                    return False
            else:
                print(f"Unexpected response: {response.text}")
                return False
                
    except Exception as e:
        print(f"Process hybrid test error: {e}")
        return False
    finally:
        # Clean up
        if test_file_path.exists():
            test_file_path.unlink()


def main():
    """Run all tests."""
    print("=== Testing Hybrid AI Processing Fixes ===")
    print(f"Test time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Health Check", test_hybrid_ai_health),
        ("Available Models", test_available_models),
        ("Processing Format", test_hybrid_processing_format)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"Result: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"Test exception: {e}")
            results.append((test_name, False))
        print()
    
    print("=== Summary ===")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, result in results if result)
    total_tests = len(results)
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)