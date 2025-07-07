"""
Redis Pub/Sub Bridge for WebSocket Communication
Solves multiprocessing isolation between FastAPI and Celery workers
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)

class RedisWebSocketBridge:
    """
    Enterprise-grade Redis Pub/Sub bridge for WebSocket communication across processes.
    
    Solves the multiprocessing isolation issue where:
    - FastAPI process manages WebSocket connections
    - Celery workers run in separate processes and cannot access WebSocket connections
    - This bridge allows Celery workers to publish to Redis
    - FastAPI subscribes to Redis and forwards to WebSocket clients
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.connection_pool: Optional[ConnectionPool] = None
        self.publisher: Optional[redis.Redis] = None
        self.subscriber: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.message_handlers: Dict[str, Callable] = {}
        self.is_listening = False
        
    async def initialize(self):
        """Initialize Redis connections for publishing and subscribing"""
        try:
            # Create connection pool for efficient connection management
            self.connection_pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=10,
                decode_responses=True
            )
            
            # Separate connections for pub/sub operations
            self.publisher = redis.Redis(connection_pool=self.connection_pool)
            self.subscriber = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connections
            await self.publisher.ping()
            await self.subscriber.ping()
            
            logger.info("🔗 Redis WebSocket bridge initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis bridge: {str(e)}")
            return False
    
    async def close(self):
        """Clean up Redis connections"""
        try:
            if self.is_listening:
                await self.stop_listening()
                
            if self.pubsub:
                await self.pubsub.close()
                
            if self.publisher:
                await self.publisher.close()
                
            if self.subscriber:
                await self.subscriber.close()
                
            if self.connection_pool:
                await self.connection_pool.disconnect()
                
            logger.info("🔗 Redis WebSocket bridge closed")
            
        except Exception as e:
            logger.error(f"❌ Error closing Redis bridge: {str(e)}")
    
    async def publish_websocket_message(self, job_id: str, message: Dict[str, Any]):
        """
        Publish WebSocket message to Redis channel (used by Celery workers)
        
        Args:
            job_id: The processing job ID
            message: WebSocket message payload
        """
        try:
            if not self.publisher:
                logger.error("❌ Redis publisher not initialized")
                return False
                
            channel = f"websocket:job:{job_id}"
            
            # Add metadata for message tracking
            message_with_meta = {
                "job_id": job_id,
                "timestamp": asyncio.get_event_loop().time(),
                "source": "celery_worker",
                **message
            }
            
            message_json = json.dumps(message_with_meta)
            
            # Publish to Redis
            result = await self.publisher.publish(channel, message_json)
            
            if result > 0:
                logger.info(f"📡 Published WebSocket message to Redis for job {job_id}: {message.get('type', 'unknown')}")
                return True
            else:
                logger.warning(f"⚠️ No subscribers for WebSocket message job {job_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to publish WebSocket message for job {job_id}: {str(e)}")
            return False
    
    def register_message_handler(self, handler: Callable[[str, Dict[str, Any]], None]):
        """
        Register handler for incoming WebSocket messages (used by FastAPI)
        
        Args:
            handler: Function to handle incoming messages (job_id, message_data)
        """
        handler_id = f"handler_{len(self.message_handlers)}"
        self.message_handlers[handler_id] = handler
        logger.info(f"🔧 Registered WebSocket message handler: {handler_id}")
        return handler_id
    
    def unregister_message_handler(self, handler_id: str):
        """Remove message handler"""
        if handler_id in self.message_handlers:
            del self.message_handlers[handler_id]
            logger.info(f"🔧 Unregistered WebSocket message handler: {handler_id}")
    
    async def start_listening(self, job_pattern: str = "websocket:job:*"):
        """
        Start listening for WebSocket messages on Redis (used by FastAPI)
        
        Args:
            job_pattern: Redis pattern to subscribe to (default: all job WebSocket messages)
        """
        try:
            if self.is_listening:
                logger.warning("⚠️ Redis bridge already listening")
                return
                
            if not self.subscriber:
                logger.error("❌ Redis subscriber not initialized")
                return
                
            # Create pubsub instance
            self.pubsub = self.subscriber.pubsub()
            
            # Subscribe to job WebSocket channels
            await self.pubsub.psubscribe(job_pattern)
            
            self.is_listening = True
            logger.info(f"👂 Started listening for WebSocket messages on pattern: {job_pattern}")
            
            # Start background task to process messages
            asyncio.create_task(self._message_listener())
            
        except Exception as e:
            logger.error(f"❌ Failed to start Redis listening: {str(e)}")
            self.is_listening = False
    
    async def stop_listening(self):
        """Stop listening for Redis messages"""
        try:
            self.is_listening = False
            
            if self.pubsub:
                await self.pubsub.punsubscribe()
                
            logger.info("👂 Stopped listening for WebSocket messages")
            
        except Exception as e:
            logger.error(f"❌ Error stopping Redis listening: {str(e)}")
    
    async def _message_listener(self):
        """Background task to process incoming Redis messages"""
        try:
            if not self.pubsub:
                logger.error("❌ PubSub not initialized for message listening")
                return
                
            logger.info("👂 Redis message listener started")
            
            async for message in self.pubsub.listen():
                if not self.is_listening:
                    break
                    
                # Skip subscription confirmation messages
                if message['type'] != 'pmessage':
                    continue
                    
                try:
                    # Parse the message
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    # Extract job ID from channel name
                    job_id = channel.split(':')[-1]
                    
                    logger.info(f"📨 Received WebSocket message from Redis for job {job_id}: {data.get('type', 'unknown')}")
                    
                    # Forward to all registered handlers
                    for handler_id, handler in self.message_handlers.items():
                        try:
                            await handler(job_id, data)
                        except Exception as e:
                            logger.error(f"❌ Error in WebSocket handler {handler_id}: {str(e)}")
                            
                except Exception as e:
                    logger.error(f"❌ Error processing Redis message: {str(e)}")
                    
        except Exception as e:
            logger.error(f"❌ Redis message listener error: {str(e)}")
        finally:
            logger.info("👂 Redis message listener stopped")

# Global bridge instance
_redis_bridge: Optional[RedisWebSocketBridge] = None

async def get_redis_bridge() -> RedisWebSocketBridge:
    """Get or create the global Redis bridge instance"""
    global _redis_bridge
    
    if _redis_bridge is None:
        _redis_bridge = RedisWebSocketBridge()
        success = await _redis_bridge.initialize()
        if not success:
            raise RuntimeError("Failed to initialize Redis WebSocket bridge")
    
    return _redis_bridge

async def cleanup_redis_bridge():
    """Clean up the global Redis bridge instance"""
    global _redis_bridge
    
    if _redis_bridge:
        await _redis_bridge.close()
        _redis_bridge = None

@asynccontextmanager
async def redis_bridge_context():
    """Context manager for Redis bridge lifecycle"""
    bridge = await get_redis_bridge()
    try:
        yield bridge
    finally:
        # Don't close here, let the global cleanup handle it
        pass

# Convenience functions for common operations
async def publish_progress_update(job_id: str, progress_data: Dict[str, Any]):
    """Publish progress update via Redis bridge"""
    bridge = await get_redis_bridge()
    return await bridge.publish_websocket_message(job_id, {
        "type": "processing_progress",
        "payload": progress_data
    })

async def publish_status_update(job_id: str, status: str, message: str = ""):
    """Publish status update via Redis bridge"""
    bridge = await get_redis_bridge()
    return await bridge.publish_websocket_message(job_id, {
        "type": "status_update",
        "payload": {
            "job_id": job_id,
            "status": status,
            "message": message
        }
    })

async def publish_job_completed(job_id: str, result_data: Dict[str, Any]):
    """Publish job completion via Redis bridge"""
    bridge = await get_redis_bridge()
    return await bridge.publish_websocket_message(job_id, {
        "type": "job_completed",
        "payload": {
            "job_id": job_id,
            **result_data
        }
    })