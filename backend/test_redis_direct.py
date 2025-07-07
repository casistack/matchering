#!/usr/bin/env python3
"""
Test Redis connection directly to see what instance we're connecting to
"""

import asyncio
import redis.asyncio as redis

async def test_redis_direct():
    print("=== Testing Redis Direct Connection ===")
    
    # Test the same connection the bridge uses
    try:
        client = redis.Redis.from_url("redis://localhost:6379", decode_responses=True)
        
        # Test basic connection
        pong = await client.ping()
        print(f"✅ Redis ping: {pong}")
        
        # Get Redis info
        info = await client.info()
        print(f"✅ Redis version: {info.get('redis_version', 'unknown')}")
        print(f"✅ Connected clients: {info.get('connected_clients', 'unknown')}")
        print(f"✅ Used memory: {info.get('used_memory_human', 'unknown')}")
        
        # Test publishing to a test channel
        print("\n--- Testing Redis PUBLISH ---")
        result = await client.publish("test-channel", "test-message")
        print(f"✅ PUBLISH result (subscribers): {result}")
        
        # Test publishing to a WebSocket-style channel
        result = await client.publish("websocket:job:test-123", '{"type": "test", "payload": {"message": "test"}}')
        print(f"✅ PUBLISH to websocket channel result: {result}")
        
        # List current channels with subscribers
        channels = await client.pubsub_channels()
        print(f"✅ Active channels: {channels}")
        
        # List current subscribers
        numsub = await client.pubsub_numsub("websocket:job:*")
        print(f"✅ Subscribers to websocket pattern: {numsub}")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_redis_direct())