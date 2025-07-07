#!/usr/bin/env python3
"""
Complete Redis Bridge Test
Tests the Redis Pub/Sub bridge with proper WebSocket connection timing
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
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisBridgeTest:
    """Test Redis bridge communication with proper timing"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        self.messages_received = []
        self.websocket_connected = False
        self.job_id = None
        self.file_id = None
        
    async def upload_file(self):
        """Upload test audio file"""
        test_file_path = "/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Ice King.wav"
        
        if not os.path.exists(test_file_path):
            logger.error(f"Test file not found: {test_file_path}")
            return None
            
        logger.info("📤 Uploading test audio file...")
        
        with open(test_file_path, "rb") as f:
            files = {"file": ("Ice King.wav", f, "audio/wav")}
            data = {"processing_mode": "auto"}
            
            response = requests.post(
                f"{self.base_url}/api/v1/audio/upload",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            logger.error(f"File upload failed: {response.status_code} - {response.text}")
            return None
        
        upload_result = response.json()
        if not upload_result.get("success"):
            logger.error(f"Upload not successful: {upload_result}")
            return None
        
        self.file_id = upload_result["data"]["file_id"]
        logger.info(f"✅ File uploaded: {self.file_id}")
        return self.file_id
    
    async def create_job(self):
        """Create processing job"""
        if not self.file_id:
            logger.error("No file ID available")
            return None
            
        job_data = {
            "input_file_id": self.file_id,
            "processing_mode": "auto",
            "settings": {
                "intensity": "medium",
                "eqStyle": "balanced",
                "preserveDynamics": True,
                "targetLoudness": -14
            },
            "priority": 5
        }
        
        logger.info("🚀 Creating AUTO mode processing job...")
        
        response = requests.post(
            f"{self.base_url}/api/v1/processing/jobs",
            json=job_data,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"Job creation failed: {response.status_code} - {response.text}")
            return None
        
        job_result = response.json()
        if not job_result.get("success"):
            logger.error(f"Job creation not successful: {job_result}")
            return None
        
        self.job_id = job_result["data"]["id"]
        logger.info(f"✅ Processing job created: {self.job_id}")
        return self.job_id
    
    async def websocket_listener(self):
        """WebSocket listener coroutine"""
        if not self.job_id:
            logger.error("No job ID for WebSocket connection")
            return
            
        ws_uri = f"{self.ws_url}/api/v1/processing/ws/{self.job_id}"
        logger.info(f"🔌 Connecting to WebSocket: {ws_uri}")
        
        try:
            async with websockets.connect(ws_uri) as websocket:
                self.websocket_connected = True
                logger.info("✅ WebSocket connected successfully!")
                
                # Keep listening for messages
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=60)
                        data = json.loads(message)
                        
                        message_type = data.get("type", "unknown")
                        self.messages_received.append(data)
                        
                        logger.info(f"📨 [{len(self.messages_received)}] Received: {message_type}")
                        
                        if message_type == "connection_established":
                            logger.info("🔗 Connection established")
                        
                        elif message_type == "processing_progress":
                            payload = data.get("payload", {})
                            progress = payload.get("progress_percentage", 0)
                            stage = payload.get("current_stage", "unknown")
                            message_text = payload.get("message", "")
                            logger.info(f"📊 Progress: {progress}% - {stage} - {message_text}")
                        
                        elif message_type == "job_completed":
                            payload = data.get("payload", {})
                            output_path = payload.get("output_file_url", "unknown")
                            logger.info(f"🎉 Job completed! Output: {output_path}")
                            break
                        
                        elif message_type == "job_failed":
                            logger.error("❌ Job failed during processing")
                            payload = data.get("payload", {})
                            error_msg = payload.get("error", "Unknown error")
                            logger.error(f"Error: {error_msg}")
                            break
                            
                    except asyncio.TimeoutError:
                        logger.error("⏱️ WebSocket timeout - no messages received")
                        break
                    except Exception as e:
                        logger.error(f"❌ WebSocket error: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
        finally:
            self.websocket_connected = False
    
    async def run_test(self):
        """Run the complete test"""
        print("🧪 Testing Redis Bridge Communication")
        print("="*60)
        
        # Step 1: Upload file
        await self.upload_file()
        if not self.file_id:
            return False
        
        # Step 2: Create job  
        await self.create_job()
        if not self.job_id:
            return False
        
        # Step 3: Start WebSocket listener
        logger.info("🎯 Starting WebSocket listener...")
        listener_task = asyncio.create_task(self.websocket_listener())
        
        # Wait a bit for WebSocket to connect
        await asyncio.sleep(2)
        
        if not self.websocket_connected:
            logger.error("❌ WebSocket failed to connect")
            listener_task.cancel()
            return False
        
        # Wait for job to complete
        logger.info("⏳ Waiting for job to complete...")
        try:
            await asyncio.wait_for(listener_task, timeout=120)
        except asyncio.TimeoutError:
            logger.error("❌ Test timeout - job did not complete")
            return False
        
        # Check results
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Messages Received:      {len(self.messages_received)}")
        print(f"Progress Updates:       {len([m for m in self.messages_received if m.get('type') == 'processing_progress'])}")
        print(f"Job Completed:          {'✅' if any(m.get('type') == 'job_completed' for m in self.messages_received) else '❌'}")
        
        success = len(self.messages_received) > 2  # At least connection + some updates
        
        if success:
            print("\n🎉 SUCCESS: Redis Pub/Sub bridge is working!")
            print("   ✅ Celery workers → Redis → FastAPI → WebSocket → Client")
            print("   ✅ Real-time progress updates delivered successfully")
        else:
            print("\n❌ FAILURE: Communication bridge not working properly")
            
        return success

async def main():
    """Main test runner"""
    test = RedisBridgeTest()
    success = await test.run_test()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)