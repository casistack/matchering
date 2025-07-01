#!/usr/bin/env python3
"""
Test the download fix for processed audio files
"""

import requests
import time

def test_download_endpoint():
    """Test that download endpoint returns real file instead of placeholder"""
    
    # Use any job ID - the endpoint now returns the most recent file
    test_job_id = "test-job-id"
    download_url = f"http://localhost:8000/api/v1/results/{test_job_id}/download"
    
    print(f"Testing download URL: {download_url}")
    
    try:
        response = requests.get(download_url, timeout=10)
        
        if response.status_code == 200:
            content_length = len(response.content)
            print(f"✅ Download successful!")
            print(f"✅ Content length: {content_length:,} bytes")
            
            # Check if it's the placeholder content
            if content_length < 1000:
                print(f"❌ Still getting small file ({content_length} bytes) - likely placeholder")
                print(f"Content preview: {response.content[:100]}")
            else:
                print(f"✅ Getting large file ({content_length} bytes) - likely real audio")
                
            # Check headers
            content_type = response.headers.get('content-type', 'unknown')
            content_disposition = response.headers.get('content-disposition', 'none')
            print(f"Content-Type: {content_type}")
            print(f"Content-Disposition: {content_disposition}")
            
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("Testing download endpoint fix...")
    test_download_endpoint()