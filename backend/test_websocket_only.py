#!/usr/bin/env python3
"""
Simple WebSocket Connection Test
Tests WebSocket connection and message receiving without job creation
"""

import asyncio
import json
import websockets
import time

async def test_websocket_connection():
    """Test WebSocket connection without creating a job"""
    
    # Use a dummy job ID to test WebSocket infrastructure 
    test_job_id = "test_ws_" + str(int(time.time()))
    ws_uri = f"ws://localhost:8000/api/v1/processing/ws/{test_job_id}"
    
    print(f"🔌 Connecting to WebSocket: {ws_uri}")
    
    try:
        async with websockets.connect(ws_uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Wait for connection established message
            message = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(message)
            print(f"📨 Received: {data}")
            
            # Keep connection alive for a bit to test
            print("⏳ Keeping connection alive for 30 seconds...")
            await asyncio.sleep(30)
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())