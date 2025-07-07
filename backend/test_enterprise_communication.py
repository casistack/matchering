#!/usr/bin/env python3
"""
Enterprise Communication End-to-End Test
Tests the complete Redis Pub/Sub WebSocket bridge communication flow
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

class EnterpriseCommunicationTest:
    """Test enterprise Redis Pub/Sub WebSocket bridge communication"""
    
    def __init__(self, base_url="http://localhost:8000", ws_url="ws://localhost:8000"):
        self.base_url = base_url
        self.ws_url = ws_url
        self.job_id = None
        self.messages_received = []
        self.test_results = {
            "backend_available": False,
            "redis_available": False,
            "websocket_connected": False,
            "job_created": False,
            "progress_updates_received": 0,
            "job_completed": False,
            "communication_working": False
        }
    
    async def test_backend_health(self):
        """Test if backend is running and healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.test_results["backend_available"] = True
                logger.info("✅ Backend health check passed")
                return True
            else:
                logger.error(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Backend not available: {e}")
            return False
    
    async def test_redis_health(self):
        """Test if Redis communication is working"""
        try:
            response = requests.get(f"{self.base_url}/health/communication", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("redis_available", False):
                    self.test_results["redis_available"] = True
                    logger.info("✅ Redis communication bridge available")
                    return True
                else:
                    logger.warning("⚠️ Redis communication bridge not available - will use fallback")
                    return False
            else:
                logger.error(f"❌ Communication health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Communication health check error: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        try:
            # Create a dummy job ID for testing
            self.job_id = "test_comm_" + str(int(time.time()))
            ws_uri = f"{self.ws_url}/api/v1/processing/ws/{self.job_id}"
            
            logger.info(f"🔌 Connecting to WebSocket: {ws_uri}")
            
            async with websockets.connect(ws_uri) as websocket:
                # Wait for connection established message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    if data.get("type") == "connection_established":
                        self.test_results["websocket_connected"] = True
                        logger.info("✅ WebSocket connection established successfully")
                        return True
                    else:
                        logger.error(f"❌ Unexpected WebSocket message: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    logger.error("❌ WebSocket connection timeout")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def test_auto_processing_job(self):
        """Test creating an AUTO mode processing job"""
        try:
            # First upload a test file
            test_file_path = "/home/masterp/Seafile/sourcery-mac/mypythonai/matchering/Testuploads/Ice King.wav"
            
            if not os.path.exists(test_file_path):
                logger.error(f"❌ Test file not found: {test_file_path}")
                return False
            
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
                logger.error(f"❌ File upload failed: {response.status_code} - {response.text}")
                return False
            
            upload_result = response.json()
            if not upload_result.get("success"):
                logger.error(f"❌ Upload not successful: {upload_result}")
                return False
            
            file_id = upload_result["data"]["id"]
            logger.info(f"✅ File uploaded successfully: {file_id}")
            
            # Create processing job
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
            
            logger.info("🚀 Creating AUTO mode processing job...")
            
            response = requests.post(
                f"{self.base_url}/api/v1/processing/jobs",
                json=job_data,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Job creation failed: {response.status_code} - {response.text}")
                return False
            
            job_result = response.json()
            if not job_result.get("success"):
                logger.error(f"❌ Job creation not successful: {job_result}")
                return False
            
            self.job_id = job_result["data"]["id"]
            self.test_results["job_created"] = True
            logger.info(f"✅ Processing job created: {self.job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Job creation failed: {e}")
            return False
    
    async def test_real_time_communication(self):
        """Test real-time communication during job processing"""
        try:
            if not self.job_id:
                logger.error("❌ No job ID available for WebSocket testing")
                return False
            
            ws_uri = f"{self.ws_url}/api/v1/processing/ws/{self.job_id}"
            logger.info(f"🔌 Connecting to WebSocket for real-time updates: {ws_uri}")
            
            async with websockets.connect(ws_uri) as websocket:
                # Wait for connection established
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    logger.info(f"📨 Connection message: {data.get('type', 'unknown')}")
                    
                except asyncio.TimeoutError:
                    logger.error("❌ WebSocket connection timeout")
                    return False
                
                # Listen for progress updates for up to 60 seconds
                start_time = time.time()
                timeout = 60  # seconds
                
                logger.info("👂 Listening for real-time progress updates...")
                
                while time.time() - start_time < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5)
                        data = json.loads(message)
                        
                        message_type = data.get("type", "unknown")
                        self.messages_received.append(data)
                        
                        logger.info(f"📨 Received: {message_type}")
                        
                        if message_type == "processing_progress":
                            self.test_results["progress_updates_received"] += 1
                            payload = data.get("payload", {})
                            progress = payload.get("progress_percentage", 0)
                            stage = payload.get("current_stage", "unknown")
                            logger.info(f"📊 Progress: {progress}% - {stage}")
                        
                        elif message_type == "job_completed":
                            self.test_results["job_completed"] = True
                            logger.info("🎉 Job completed successfully!")
                            break
                        
                        elif message_type == "job_failed":
                            logger.error("❌ Job failed during processing")
                            break
                            
                    except asyncio.TimeoutError:
                        # No message received in timeout period, continue waiting
                        continue
                    except Exception as e:
                        logger.error(f"❌ WebSocket message error: {e}")
                        break
                
                # Evaluate communication success
                if self.test_results["progress_updates_received"] > 0:
                    self.test_results["communication_working"] = True
                    logger.info(f"✅ Real-time communication working! Received {self.test_results['progress_updates_received']} progress updates")
                    return True
                else:
                    logger.error("❌ No progress updates received - communication not working")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Real-time communication test failed: {e}")
            return False
    
    def print_test_summary(self):
        """Print comprehensive test results"""
        print("\n" + "="*60)
        print("🧪 ENTERPRISE COMMUNICATION TEST RESULTS")
        print("="*60)
        
        results = self.test_results
        
        print(f"Backend Available:          {'✅' if results['backend_available'] else '❌'}")
        print(f"Redis Bridge Available:     {'✅' if results['redis_available'] else '⚠️  (fallback mode)'}")
        print(f"WebSocket Connected:        {'✅' if results['websocket_connected'] else '❌'}")
        print(f"Job Created:                {'✅' if results['job_created'] else '❌'}")
        print(f"Progress Updates Received:  {results['progress_updates_received']}")
        print(f"Job Completed:              {'✅' if results['job_completed'] else '❌'}")
        print(f"Communication Working:      {'✅' if results['communication_working'] else '❌'}")
        
        print("\n" + "="*60)
        
        if results["communication_working"]:
            print("🎉 SUCCESS: Enterprise Redis Pub/Sub communication bridge is working!")
            print("   Real-time updates are successfully bridging Celery → Redis → FastAPI → WebSocket")
        else:
            print("❌ FAILURE: Enterprise communication bridge not working properly")
            print("   Please check Redis connection and bridge implementation")
        
        print("\n📊 Message Summary:")
        for i, msg in enumerate(self.messages_received, 1):
            msg_type = msg.get("type", "unknown")
            if msg_type == "processing_progress":
                progress = msg.get("payload", {}).get("progress_percentage", 0)
                print(f"   {i}. {msg_type}: {progress}%")
            else:
                print(f"   {i}. {msg_type}")
        
        print("="*60)

async def main():
    """Run the complete enterprise communication test"""
    print("🧪 Starting Enterprise Communication End-to-End Test")
    print("Testing Redis Pub/Sub WebSocket bridge for real-time updates")
    print("="*60)
    
    test = EnterpriseCommunicationTest()
    
    # Test sequence
    tests = [
        ("Backend Health", test.test_backend_health),
        ("Redis Communication", test.test_redis_health),
        ("WebSocket Connection", test.test_websocket_connection),
        ("AUTO Processing Job", test.test_auto_processing_job),
        ("Real-time Communication", test.test_real_time_communication),
    ]
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            success = await test_func()
            if not success:
                print(f"❌ {test_name} failed - stopping test sequence")
                break
        except Exception as e:
            print(f"❌ {test_name} error: {e}")
            break
    
    # Print summary
    test.print_test_summary()
    
    # Return exit code based on communication success
    return 0 if test.test_results["communication_working"] else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)