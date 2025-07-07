#!/usr/bin/env python3
"""
Complete end-to-end test of AUTO mode processing with WebSocket monitoring.
"""

import asyncio
import json
import websockets
import requests
import time

async def test_end_to_end():
    print('🧪 Testing Complete End-to-End AUTO Mode Pipeline')
    print('=' * 60)
    
    # Step 1: Create a processing job via API
    print('📝 Step 1: Creating processing job via API...')
    job_data = {
        'input_file_id': 'ccb9b7e1-cb72-4598-9d45-cde2d33d61e9',
        'processing_mode': 'auto',
        'settings': {'quality': 'standard'},
        'priority': 1
    }
    
    response = requests.post('http://localhost:8000/api/v1/processing/jobs', json=job_data)
    if response.status_code != 200:
        print(f'❌ API Error: {response.status_code} - {response.text}')
        return
    
    job_response = response.json()
    job_id = job_response['data']['id']
    print(f'✅ Job created successfully: {job_id}')
    
    # Step 2: Connect WebSocket IMMEDIATELY after job creation
    print(f'🔌 Step 2: Connecting WebSocket for job {job_id}...')
    uri = f'ws://localhost:8000/api/v1/processing/ws/{job_id}'
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f'✅ WebSocket connected to: {uri}')
            
            # Receive initial connection message
            initial_msg = await websocket.recv()
            initial_data = json.loads(initial_msg)
            print(f'📨 Initial message: {initial_data["type"]}')
            
            # Wait for processing messages with timeout
            messages_received = []
            timeout_seconds = 15
            start_time = time.time()
            
            print(f'⏱️  Waiting for progress messages (timeout: {timeout_seconds}s)...')
            
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
                    elif msg_type == 'job_failed':
                        print(f'❌ Job failed: {data["payload"].get("error", "Unknown error")}')
                        break
                    else:
                        print(f'📨 Message: {msg_type}')
                        
                except asyncio.TimeoutError:
                    # Check job status via API
                    status_response = requests.get(f'http://localhost:8000/api/v1/processing/jobs/{job_id}')
                    if status_response.status_code == 200:
                        job_status = status_response.json()['data']['job']
                        current_status = job_status['status']
                        progress = job_status.get('progress_percentage', 0)
                        print(f'📋 API Status Check: {current_status} ({progress}%)')
                        
                        if current_status in ['COMPLETED', 'FAILED']:
                            print(f'🔍 Job finished via API but no WebSocket completion message received')
                            break
                    continue
            
            print(f'📊 Total WebSocket messages received: {len(messages_received)}')
            for i, msg in enumerate(messages_received):
                print(f'   {i+1}. {msg.get("type", "unknown")} - {msg.get("payload", {}).get("message", "")}')
                
    except Exception as e:
        print(f'❌ WebSocket error: {e}')
    
    # Step 3: Final status check
    print(f'🔍 Step 3: Final status check via API...')
    final_response = requests.get(f'http://localhost:8000/api/v1/processing/jobs/{job_id}')
    if final_response.status_code == 200:
        final_job = final_response.json()['data']['job']
        print(f'📋 Final Status: {final_job["status"]} ({final_job.get("progress_percentage", 0)}%)')
        if final_job['current_stage']:
            print(f'📋 Final Stage: {final_job["current_stage"]}')
        if final_job.get('processing_duration'):
            print(f'⏱️  Processing Duration: {final_job["processing_duration"]}s')
    
    print('🏁 End-to-end test complete!')

if __name__ == "__main__":
    asyncio.run(test_end_to_end())