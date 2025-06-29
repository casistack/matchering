"""
AI Service for feature caching and model management.

This module provides services for caching audio features,
managing AI models, and coordinating AI processing tasks.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Optional, Any
import redis.asyncio as aioredis

from app.ai.feature_extractor import AudioFeatures
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class AIService:
    """Service for AI model management and feature caching."""
    
    def __init__(self, redis_url: str = None):
        """Initialize AI service with Redis connection."""
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[aioredis.Redis] = None
        self.feature_cache_ttl = 3600  # 1 hour
        self.feature_cache_prefix = "ai:features:"
        
        # Performance tracking
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_extractions = 0
        
    async def initialize(self):
        """Initialize Redis connection and service components."""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False  # Keep binary for feature data
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("AI Service initialized with Redis connection")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Service: {str(e)}")
            raise
    
    async def cache_features(self, feature_hash: str, features: AudioFeatures) -> bool:
        """
        Cache extracted audio features.
        
        Args:
            feature_hash: Unique hash for the features
            features: AudioFeatures object to cache
            
        Returns:
            True if cached successfully
        """
        try:
            if not self.redis_client:
                await self.initialize()
            
            # Serialize features to JSON
            features_json = features.model_dump_json()
            
            # Cache with TTL
            cache_key = f"{self.feature_cache_prefix}{feature_hash}"
            await self.redis_client.setex(
                cache_key,
                self.feature_cache_ttl,
                features_json
            )
            
            logger.debug(f"Cached features: {feature_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache features {feature_hash}: {str(e)}")
            return False
    
    async def get_cached_features(self, feature_hash: str) -> Optional[AudioFeatures]:
        """
        Retrieve cached audio features.
        
        Args:
            feature_hash: Hash of the features to retrieve
            
        Returns:
            AudioFeatures object if found, None otherwise
        """
        try:
            if not self.redis_client:
                await self.initialize()
            
            cache_key = f"{self.feature_cache_prefix}{feature_hash}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                self._cache_hits += 1
                features = AudioFeatures.model_validate_json(cached_data.decode('utf-8'))
                logger.debug(f"Cache hit for features: {feature_hash}")
                return features
            else:
                self._cache_misses += 1
                logger.debug(f"Cache miss for features: {feature_hash}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve cached features {feature_hash}: {str(e)}")
            self._cache_misses += 1
            return None
    
    async def delete_cached_features(self, feature_hash: str) -> bool:
        """
        Delete cached features.
        
        Args:
            feature_hash: Hash of features to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            if not self.redis_client:
                await self.initialize()
            
            cache_key = f"{self.feature_cache_prefix}{feature_hash}"
            deleted = await self.redis_client.delete(cache_key)
            
            logger.debug(f"Deleted cached features: {feature_hash}")
            return deleted > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cached features {feature_hash}: {str(e)}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get feature cache statistics.
        
        Returns:
            Dictionary with cache performance metrics
        """
        try:
            if not self.redis_client:
                await self.initialize()
            
            # Get cache keys count
            pattern = f"{self.feature_cache_prefix}*"
            cache_keys = await self.redis_client.keys(pattern)
            total_cached = len(cache_keys)
            
            # Calculate cache hit rate
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = self._cache_hits / max(total_requests, 1)
            
            # Get memory usage (approximate)
            memory_info = await self.redis_client.memory_usage(pattern) if cache_keys else 0
            
            # Sample feature size (from first cached item)
            avg_feature_size = 0
            if cache_keys:
                sample_data = await self.redis_client.get(cache_keys[0])
                if sample_data:
                    avg_feature_size = len(sample_data) / 1024  # KB
            
            return {
                "total_cached_features": total_cached,
                "cache_hit_rate": hit_rate,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_size_mb": memory_info / (1024 * 1024) if memory_info else 0,
                "average_feature_size_kb": avg_feature_size,
                "total_extractions": self._total_extractions
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {
                "total_cached_features": 0,
                "cache_hit_rate": 0.0,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_size_mb": 0.0,
                "average_feature_size_kb": 0.0,
                "total_extractions": self._total_extractions
            }
    
    async def cleanup_cache(self, max_age_hours: int = 24, max_size_mb: int = 1000) -> Dict[str, int]:
        """
        Clean up old or excessive cache entries.
        
        Args:
            max_age_hours: Maximum age of cache entries
            max_size_mb: Maximum total cache size
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            if not self.redis_client:
                await self.initialize()
            
            pattern = f"{self.feature_cache_prefix}*"
            cache_keys = await self.redis_client.keys(pattern)
            
            deleted_count = 0
            total_size_before = 0
            total_size_after = 0
            
            # Calculate total size before cleanup
            for key in cache_keys:
                size = await self.redis_client.memory_usage(key)
                if size:
                    total_size_before += size
            
            # Remove expired entries (TTL-based cleanup)
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for key in cache_keys:
                ttl = await self.redis_client.ttl(key)
                
                # Delete if TTL indicates old entry
                if ttl > 0 and (self.feature_cache_ttl - ttl) > max_age_seconds:
                    await self.redis_client.delete(key)
                    deleted_count += 1
                else:
                    # Count remaining size
                    size = await self.redis_client.memory_usage(key)
                    if size:
                        total_size_after += size
            
            # If still over size limit, remove oldest entries
            if total_size_after > max_size_mb * 1024 * 1024:
                remaining_keys = await self.redis_client.keys(pattern)
                
                # Sort by TTL (oldest first)
                key_ttls = []
                for key in remaining_keys:
                    ttl = await self.redis_client.ttl(key)
                    key_ttls.append((key, ttl))
                
                key_ttls.sort(key=lambda x: x[1])  # Oldest TTL first
                
                # Delete oldest until under size limit
                for key, ttl in key_ttls:
                    if total_size_after <= max_size_mb * 1024 * 1024:
                        break
                    
                    size = await self.redis_client.memory_usage(key)
                    await self.redis_client.delete(key)
                    deleted_count += 1
                    if size:
                        total_size_after -= size
            
            logger.info(f"Cache cleanup: deleted {deleted_count} entries, "
                       f"size reduced from {total_size_before/1024/1024:.1f}MB to {total_size_after/1024/1024:.1f}MB")
            
            return {
                "deleted_entries": deleted_count,
                "size_before_mb": total_size_before / 1024 / 1024,
                "size_after_mb": total_size_after / 1024 / 1024,
                "remaining_entries": len(await self.redis_client.keys(pattern))
            }
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")
            return {
                "deleted_entries": 0,
                "size_before_mb": 0,
                "size_after_mb": 0,
                "remaining_entries": 0
            }
    
    async def store_processing_state(self, job_id: str, state: Dict[str, Any]) -> bool:
        """
        Store processing state for job tracking.
        
        Args:
            job_id: Processing job ID
            state: State information to store
            
        Returns:
            True if stored successfully
        """
        try:
            if not self.redis_client:
                await self.initialize()
            
            state_key = f"ai:processing:{job_id}"
            state_json = json.dumps(state)
            
            # Store with shorter TTL (processing jobs are temporary)
            await self.redis_client.setex(state_key, 1800, state_json)  # 30 minutes
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store processing state {job_id}: {str(e)}")
            return False
    
    async def get_processing_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve processing state.
        
        Args:
            job_id: Processing job ID
            
        Returns:
            State dictionary if found
        """
        try:
            if not self.redis_client:
                await self.initialize()
            
            state_key = f"ai:processing:{job_id}"
            state_data = await self.redis_client.get(state_key)
            
            if state_data:
                return json.loads(state_data.decode('utf-8'))
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get processing state {job_id}: {str(e)}")
            return None
    
    async def increment_extraction_count(self):
        """Increment total extraction counter."""
        self._total_extractions += 1
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("AI Service Redis connection closed")


# Global AI service instance
_ai_service: Optional[AIService] = None


async def get_ai_service() -> AIService:
    """Get or create AI service instance."""
    global _ai_service
    
    if _ai_service is None:
        _ai_service = AIService()
        await _ai_service.initialize()
    
    return _ai_service


async def cleanup_ai_service():
    """Cleanup AI service on shutdown."""
    global _ai_service
    
    if _ai_service:
        await _ai_service.close()
        _ai_service = None