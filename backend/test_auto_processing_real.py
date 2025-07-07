#!/usr/bin/env python3
"""
Real AUTO Processing Test
Tests the actual AUTO mode processing with Redis bridge communication
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
import requests
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_real_auto_processing():
    """Test real AUTO mode processing with Redis bridge communication"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Real AUTO Mode Processing with Redis Bridge")
    print("="*60)
    
    try:
        # Test file path
        test_file_path = "/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Ice King.wav"
        
        if not os.path.exists(test_file_path):
            print(f"❌ Test file not found: {test_file_path}")
            return False
        
        # Step 1: Upload file
        print("📤 Step 1: Uploading test audio file...")
        
        with open(test_file_path, "rb") as f:
            files = {"file": ("Ice King.wav", f, "audio/wav")}
            data = {"processing_mode": "auto"}
            
            response = requests.post(
                f"{base_url}/api/v1/audio/upload",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            print(f"❌ File upload failed: {response.status_code} - {response.text}")
            return False
        
        upload_result = response.json()
        print(f"Upload result: {upload_result}")
        
        if not upload_result.get("success"):
            print(f"❌ Upload not successful: {upload_result}")
            return False
        
        file_id = upload_result["data"]["file_id"]
        print(f"✅ File uploaded successfully: {file_id}")
        
        # Step 2: Create processing job
        job_data = {
            "input_file_id": file_id,
            "processing_mode": "auto",
            "settings": {
                "intensity": "medium",
                "eqStyle": "balanced",
                "preserveDynamics": True,
                "targetLoudness": -14
            },
            "priority": 5
        }
        
        print("🚀 Step 2: Creating AUTO mode processing job...")
        
        response = requests.post(
            f"{base_url}/api/v1/processing/jobs",
            json=job_data,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Job creation failed: {response.status_code} - {response.text}")
            return False
        
        job_result = response.json()
        if not job_result.get("success"):
            print(f"❌ Job creation not successful: {job_result}")
            return False
        
        job_id = job_result["data"]["id"]
        print(f"✅ Processing job created: {job_id}")
        
        # Step 3: Connect WebSocket for real-time updates
        print("🔌 Step 3: Connecting WebSocket for real-time updates...")
        
        ws_uri = f"ws://localhost:8000/api/v1/processing/ws/{job_id}"
        print(f"WebSocket URI: {ws_uri}")
        
        async with websockets.connect(ws_uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Listen for progress updates
            messages_received = 0
            job_completed = False
            start_time = time.time()
            timeout = 60  # seconds
            
            print("👂 Listening for real-time progress updates...")
            
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    message_type = data.get("type", "unknown")
                    messages_received += 1
                    
                    print(f"📨 [{messages_received}] Received: {message_type}")
                    
                    if message_type == "connection_established":
                        print("🔗 Connection established")
                    
                    elif message_type == "processing_progress":
                        payload = data.get("payload", {})
                        progress = payload.get("progress_percentage", 0)
                        stage = payload.get("current_stage", "unknown")
                        message_text = payload.get("message", "")
                        print(f"📊 Progress: {progress}% - {stage} - {message_text}")
                    
                    elif message_type == "job_completed":
                        job_completed = True
                        payload = data.get("payload", {})
                        output_path = payload.get("output_file_url", "unknown")
                        print(f"🎉 Job completed! Output: {output_path}")
                        break
                    
                    elif message_type == "job_failed":
                        print("❌ Job failed during processing")
                        payload = data.get("payload", {})
                        error_msg = payload.get("error", "Unknown error")
                        print(f"Error: {error_msg}")
                        break
                        
                except asyncio.TimeoutError:
                    # No message received in timeout period, continue waiting
                    print("⏳ Waiting for more updates...")
                    continue
                except Exception as e:
                    print(f"❌ WebSocket message error: {e}")
                    break
            
            # Summary
            print("\n" + "="*60)
            print("📊 TEST RESULTS SUMMARY")
            print("="*60)
            print(f"Messages Received:      {messages_received}")
            print(f"Job Completed:          {'✅' if job_completed else '❌'}")
            print(f"Real-time Updates:      {'✅' if messages_received > 1 else '❌'}")
            
            if job_completed and messages_received > 1:
                print("\n🎉 SUCCESS: Redis Pub/Sub bridge is working!")
                print("   ✅ Celery workers → Redis → FastAPI → WebSocket → Frontend")
                print("   ✅ Real-time progress updates delivered successfully")
                return True
            else:
                print("\n❌ FAILURE: Communication bridge not working properly")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_real_auto_processing())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)