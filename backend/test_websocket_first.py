#!/usr/bin/env python3
"""
Enhanced test: Connect WebSocket BEFORE creating job to test registration timing.
"""

import asyncio
import json
import websockets
import requests
import time
import uuid

async def test_websocket_first():
    print('🧪 Testing WebSocket-First Connection Strategy')
    print('=' * 60)
    
    # Generate a job ID that we'll use
    future_job_id = str(uuid.uuid4())
    print(f'📋 Pre-generating job ID: {future_job_id}')
    
    # Step 1: Connect WebSocket FIRST using the future job ID
    print(f'🔌 Step 1: Connecting WebSocket BEFORE creating job...')
    uri = f'ws://localhost:8000/api/v1/processing/ws/{future_job_id}'
    
    try:
        # Open WebSocket connection BEFORE creating job
        print(f'🤝 Attempting WebSocket connection to: {uri}')
        websocket = await websockets.connect(uri)
        print(f'✅ WebSocket connected (pre-job creation)')
        
        # Receive initial connection message
        initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        initial_data = json.loads(initial_msg)
        print(f'📨 Initial message: {initial_data["type"]}')
        
        # Step 2: Now create the job with the pre-connected WebSocket
        print(f'📝 Step 2: Creating job with pre-connected WebSocket...')
        
        # Create job using the same ID we connected WebSocket to
        job_data = {
            'input_file_id': 'ccb9b7e1-cb72-4598-9d45-cde2d33d61e9',
            'processing_mode': 'auto',
            'settings': {'quality': 'standard'},
            'priority': 1
        }
        
        # Note: This will create a job with different ID, but we can test the concept
        response = requests.post('http://localhost:8000/api/v1/processing/jobs', json=job_data)
        if response.status_code == 200:
            job_response = response.json()
            actual_job_id = job_response['data']['id']
            print(f'✅ Job created: {actual_job_id}')
            print(f'⚠️  Note: Job ID differs from WebSocket ID ({future_job_id})')
        else:
            print(f'❌ Job creation failed: {response.status_code} - {response.text}')
            await websocket.close()
            return
        
        # Step 3: Listen for messages on pre-connected WebSocket
        print(f'👂 Step 3: Listening for messages on pre-connected WebSocket...')
        messages_received = []
        timeout_seconds = 10
        start_time = time.time()
        
        while (time.time() - start_time) < timeout_seconds:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                data = json.loads(message)
                messages_received.append(data)
                
                msg_type = data.get('type', 'unknown')
                if msg_type == 'processing_progress':
                    progress = data['payload'].get('progress_percentage', 0)
                    stage = data['payload'].get('current_stage', 'unknown')
                    print(f'📊 Progress: {progress}% - {stage}')
                elif msg_type == 'job_completed':
                    print(f'🎉 Job completed!')
                    break
                else:
                    print(f'📨 Message: {msg_type}')
                    
            except asyncio.TimeoutError:
                # Check if job processing is done via API
                status_response = requests.get(f'http://localhost:8000/api/v1/processing/jobs/{actual_job_id}')
                if status_response.status_code == 200:
                    job_status = status_response.json()['data']['job']
                    current_status = job_status['status']
                    progress = job_status.get('progress_percentage', 0)
                    print(f'📋 API Status: {current_status} ({progress}%)')
                    
                    if current_status in ['COMPLETED', 'FAILED']:
                        print(f'🔍 Job finished but no WebSocket messages received')
                        break
                continue
        
        print(f'📊 Total messages received: {len(messages_received)}')
        for i, msg in enumerate(messages_received):
            print(f'   {i+1}. {msg.get("type", "unknown")}')
        
        await websocket.close()
        
    except Exception as e:
        print(f'❌ WebSocket connection failed: {e}')
    
    print('🏁 WebSocket-first test complete!')

if __name__ == "__main__":
    asyncio.run(test_websocket_first())