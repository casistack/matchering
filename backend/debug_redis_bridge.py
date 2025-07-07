#!/usr/bin/env python3
"""
Debug script to understand Redis bridge behavior
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_redis_bridge():
    print("=== Testing Redis Bridge ===")
    
    # Test 1: Import and basic functionality
    print("\n1. Testing imports...")
    try:
        from app.utils.redis_bridge import get_redis_bridge, publish_progress_update
        print("✅ Imports successful")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return

    # Test 2: Get bridge instance
    print("\n2. Getting Redis bridge instance...")
    try:
        bridge = await get_redis_bridge()
        print(f"✅ Bridge instance created: {bridge}")
        print(f"   Redis URL: {bridge.redis_url}")
        print(f"   Publisher: {bridge.publisher}")
        print(f"   Subscriber: {bridge.subscriber}")
    except Exception as e:
        print(f"❌ Bridge creation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 3: Test direct publish
    print("\n3. Testing direct publish...")
    try:
        result = await bridge.publish_websocket_message("test-job-123", {
            "type": "test_message",
            "payload": {"test": "data"}
        })
        print(f"✅ Direct publish result: {result}")
    except Exception as e:
        print(f"❌ Direct publish failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Test convenience function
    print("\n4. Testing convenience function...")
    try:
        result = await publish_progress_update("test-job-456", {
            "progress_percentage": 50.0,
            "message": "Testing progress"
        })
        print(f"✅ Convenience function result: {result}")
    except Exception as e:
        print(f"❌ Convenience function failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 5: Check Redis connection
    print("\n5. Testing Redis connection...")
    try:
        pong = await bridge.publisher.ping()
        print(f"✅ Redis ping successful: {pong}")
    except Exception as e:
        print(f"❌ Redis ping failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 6: Test Redis publish command directly
    print("\n6. Testing Redis publish directly...")
    try:
        result = await bridge.publisher.publish("test-channel", "test-message")
        print(f"✅ Direct Redis publish result: {result}")
    except Exception as e:
        print(f"❌ Direct Redis publish failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_redis_bridge())