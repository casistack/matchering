#!/usr/bin/env python3
"""
Test Redis subscription behavior specifically
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_redis_subscription():
    print("=== Testing Redis Subscription ===")
    
    # Test 1: Get Redis bridge and check subscription
    try:
        from app.utils.redis_bridge import get_redis_bridge
        
        bridge = await get_redis_bridge()
        print(f"✅ Bridge created: {bridge}")
        
        # Check if already listening
        print(f"   Is listening: {bridge.is_listening}")
        print(f"   PubSub: {bridge.pubsub}")
        
        # Start listening
        await bridge.start_listening()
        print(f"   After start_listening - Is listening: {bridge.is_listening}")
        print(f"   After start_listening - PubSub: {bridge.pubsub}")
        
        # Give it a moment to establish subscription
        await asyncio.sleep(0.5)
        
        # Now test if subscription is active by checking Redis directly
        import redis.asyncio as redis
        test_client = redis.Redis.from_url("redis://localhost:6379", decode_responses=True)
        
        # Check subscribers again
        numsub = await test_client.pubsub_numsub("websocket:job:*")
        print(f"   Subscribers after start_listening: {numsub}")
        
        # Try to get pattern subscribers (different method)
        channels = await test_client.pubsub_channels("websocket:*")
        print(f"   Channels matching websocket pattern: {channels}")
        
        # Test actual publishing
        result = await test_client.publish("websocket:job:test-subscription", '{"type": "test"}')
        print(f"   PUBLISH result: {result}")
        
        await test_client.close()
        
    except Exception as e:
        print(f"❌ Subscription test failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Manually test pubsub
    print("\n=== Manual PubSub Test ===")
    try:
        import redis.asyncio as redis
        
        # Create separate publisher and subscriber
        publisher = redis.Redis.from_url("redis://localhost:6379", decode_responses=True)
        subscriber = redis.Redis.from_url("redis://localhost:6379", decode_responses=True)
        
        # Create pubsub and subscribe
        pubsub = subscriber.pubsub()
        await pubsub.psubscribe("websocket:job:*")
        
        print("✅ Manual subscription created")
        
        # Wait a moment for subscription to be established
        await asyncio.sleep(0.1)
        
        # Check subscription count
        numsub = await publisher.pubsub_numsub("websocket:job:*")
        print(f"   Manual subscription count: {numsub}")
        
        # Test publishing
        result = await publisher.publish("websocket:job:manual-test", '{"type": "manual_test"}')
        print(f"   Manual PUBLISH result: {result}")
        
        # Try to receive the message
        message = await pubsub.get_message(timeout=1.0)
        print(f"   Received message: {message}")
        
        # Clean up
        await pubsub.punsubscribe("websocket:job:*")
        await pubsub.close()
        await publisher.close()
        await subscriber.close()
        
    except Exception as e:
        print(f"❌ Manual pubsub test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_redis_subscription())