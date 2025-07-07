#!/usr/bin/env python3
"""
Test the full Redis bridge flow end-to-end
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_full_flow():
    print("=== Testing Full Redis Bridge Flow ===")
    
    # Messages received
    received_messages = []
    
    def test_handler(job_id: str, message_data):
        print(f"📨 Handler received: job_id={job_id}, message={message_data}")
        received_messages.append((job_id, message_data))
    
    try:
        from app.utils.redis_bridge import get_redis_bridge, publish_progress_update
        
        # Step 1: Get bridge and add handler
        bridge = await get_redis_bridge()
        handler_id = bridge.register_message_handler(test_handler)
        
        # Step 2: Start listening
        await bridge.start_listening()
        print("✅ Bridge listening started")
        
        # Step 3: Give it a moment to establish subscription
        await asyncio.sleep(0.5)
        
        # Step 4: Publish a message using the convenience function
        print("\n--- Publishing test message ---")
        result = await publish_progress_update("test-job-flow", {
            "progress_percentage": 75.0,
            "message": "Test progress message",
            "stage": "testing"
        })
        print(f"✅ Publish result: {result}")
        
        # Step 5: Wait for message to be received
        await asyncio.sleep(1.0)
        
        # Step 6: Check if we received it
        print(f"\n--- Results ---")
        print(f"Messages received: {len(received_messages)}")
        for job_id, message in received_messages:
            print(f"  - Job: {job_id}")
            print(f"    Message: {message}")
        
        # Step 7: Test WebSocket manager integration
        print(f"\n--- Testing WebSocket Manager Integration ---")
        from app.api.v1.endpoints.processing import websocket_manager
        
        # Check if WebSocket manager is initialized
        if websocket_manager.redis_bridge:
            print("✅ WebSocket manager has Redis bridge")
            print(f"   Is listening: {websocket_manager.redis_bridge.is_listening}")
            print(f"   Handlers: {len(websocket_manager.redis_bridge.message_handlers)}")
        else:
            print("❌ WebSocket manager has no Redis bridge")
            
            # Try to initialize it
            init_result = await websocket_manager.initialize()
            print(f"   Initialization result: {init_result}")
        
    except Exception as e:
        print(f"❌ Full flow test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_flow())