#!/usr/bin/env python3
"""
Test WebSocket manager initialization and Redis listening
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_websocket_manager():
    print("=== Testing WebSocket Manager ===")
    
    # Test 1: Import WebSocket manager
    print("\n1. Testing WebSocket manager import...")
    try:
        from app.api.v1.endpoints.processing import websocket_manager
        print("✅ WebSocket manager imported successfully")
        print(f"   Manager instance: {websocket_manager}")
    except Exception as e:
        print(f"❌ WebSocket manager import failed: {e}")
        return

    # Test 2: Check initial state
    print("\n2. Checking initial state...")
    print(f"   Active connections: {websocket_manager.active_connections}")
    print(f"   Redis bridge: {websocket_manager.redis_bridge}")
    print(f"   Redis handler ID: {websocket_manager.redis_handler_id}")
    print(f"   Is listening: {getattr(websocket_manager, 'is_listening', 'N/A')}")

    # Test 3: Try to initialize
    print("\n3. Testing initialization...")
    try:
        result = await websocket_manager.initialize()
        print(f"✅ WebSocket manager initialization result: {result}")
        
        # Check state after initialization
        print(f"   Redis bridge after init: {websocket_manager.redis_bridge}")
        print(f"   Redis handler ID after init: {websocket_manager.redis_handler_id}")
        
        if websocket_manager.redis_bridge:
            print(f"   Redis bridge is listening: {websocket_manager.redis_bridge.is_listening}")
            print(f"   Redis bridge message handlers: {len(websocket_manager.redis_bridge.message_handlers)}")
            
    except Exception as e:
        print(f"❌ WebSocket manager initialization failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Test message handling
    print("\n4. Testing message handling...")
    try:
        # Simulate a Redis message
        test_message = {
            "type": "test_message",
            "payload": {"test": "data"}
        }
        
        await websocket_manager._handle_redis_message("test-job-789", test_message)
        print("✅ Message handling successful")
        
    except Exception as e:
        print(f"❌ Message handling failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_websocket_manager())