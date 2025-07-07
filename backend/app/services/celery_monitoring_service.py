"""
Celery monitoring service for Enhanced Matchering API.

Provides enterprise-grade monitoring of Celery workers, queues, and task status.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

from celery import Celery
import redis
from redis.exceptions import ConnectionError

from app.core.celery_app import celery_app
from app.core.config import settings
from app.schemas.settings import CeleryStatusSchema, CeleryWorkerStatusSchema

logger = logging.getLogger(__name__)


class CeleryMonitoringService:
    """Enterprise Celery monitoring service."""
    
    def __init__(self):
        self.celery_app = celery_app
        self._redis_client: Optional[redis.Redis] = None
        self._worker_cache: Dict[str, Any] = {}
        self._cache_ttl = 30  # Cache worker data for 30 seconds
        self._last_cache_update: Optional[datetime] = None
    
    async def get_celery_status(self) -> CeleryStatusSchema:
        """Get comprehensive Celery system status."""
        logger.info("Getting Celery system status")
        
        try:
            # Get broker status first
            broker_status = await self._get_broker_status()
            
            # Get worker information
            workers_info = await self._get_workers_info()
            
            # Get queue information
            queue_info = await self._get_queue_info()
            
            # Get task statistics
            task_stats = await self._get_task_statistics()
            
            # Build worker status list
            worker_statuses = []
            active_workers = 0
            offline_workers = 0
            total_active_tasks = 0
            
            for worker_id, worker_data in workers_info.items():
                status = self._determine_worker_status(worker_data)
                
                if status == "online":
                    active_workers += 1
                elif status == "offline":
                    offline_workers += 1
                
                worker_status = CeleryWorkerStatusSchema(
                    worker_id=worker_id,
                    hostname=worker_data.get("hostname", worker_id),
                    status=status,
                    active_tasks=worker_data.get("active", 0),
                    processed_tasks=worker_data.get("processed", 0),
                    load_average=worker_data.get("loadavg", []),
                    memory_usage=worker_data.get("memory", {}),
                    queues=worker_data.get("active_queues", []),
                    last_heartbeat=worker_data.get("heartbeat")
                )
                worker_statuses.append(worker_status)
                total_active_tasks += worker_data.get("active", 0)
            
            return CeleryStatusSchema(
                total_workers=len(workers_info),
                active_workers=active_workers,
                offline_workers=offline_workers,
                pending_tasks=queue_info.get("total_pending", 0),
                active_tasks=total_active_tasks,
                failed_tasks_recent=task_stats.get("failed_recent", 0),
                queue_lengths=queue_info.get("queue_lengths", {}),
                workers=worker_statuses,
                broker_status=broker_status,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting Celery status: {e}")
            # Return a basic status with error information
            return CeleryStatusSchema(
                total_workers=0,
                active_workers=0,
                offline_workers=0,
                pending_tasks=0,
                active_tasks=0,
                failed_tasks_recent=0,
                queue_lengths={},
                workers=[],
                broker_status="unknown",
                last_updated=datetime.utcnow()
            )
    
    async def _get_broker_status(self) -> str:
        """Check Redis broker connection status."""
        try:
            if not self._redis_client:
                self._redis_client = redis.from_url(settings.CELERY_BROKER_URL)
            
            # Test the connection with a simple ping
            await asyncio.get_event_loop().run_in_executor(
                None, self._redis_client.ping
            )
            return "connected"
            
        except ConnectionError:
            logger.warning("Redis broker connection failed")
            return "disconnected"
        except Exception as e:
            logger.error(f"Error checking broker status: {e}")
            return "unknown"
    
    async def _get_workers_info(self) -> Dict[str, Any]:
        """Get information about active Celery workers."""
        try:
            # Check cache first
            if self._is_cache_valid():
                return self._worker_cache
            
            # Get fresh worker data
            inspect = self.celery_app.control.inspect()
            
            # Run inspect operations in executor to avoid blocking
            stats = await asyncio.get_event_loop().run_in_executor(
                None, inspect.stats
            )
            active = await asyncio.get_event_loop().run_in_executor(
                None, inspect.active
            )
            registered = await asyncio.get_event_loop().run_in_executor(
                None, inspect.registered
            )
            
            # Combine worker information
            workers_info = {}
            
            if stats:
                for worker_id, worker_stats in stats.items():
                    # Get system load average (Linux only)
                    load_avg = []
                    try:
                        with open("/proc/loadavg", "r") as f:
                            load_data = f.read().strip().split()[:3]
                            load_avg = [float(x) for x in load_data]
                    except (FileNotFoundError, ValueError, IndexError):
                        # Fallback for non-Linux systems or if file is unavailable
                        load_avg = []
                    
                    workers_info[worker_id] = {
                        "hostname": worker_stats.get("broker", {}).get("hostname", worker_id),
                        "processed": worker_stats.get("total", {}).get("tasks.total", 0),
                        "active": len(active.get(worker_id, [])) if active else 0,
                        "loadavg": load_avg,
                        "memory": {
                            "rss": worker_stats.get("rusage", {}).get("maxrss", 0),
                            "percent": 0  # Would need psutil for accurate memory percentage
                        },
                        "active_queues": list(registered.get(worker_id, {}).keys()) if registered and isinstance(registered.get(worker_id), dict) else [],
                        "heartbeat": datetime.utcnow()  # Approximation - would need more detailed monitoring
                    }
            
            # Update cache
            self._worker_cache = workers_info
            self._last_cache_update = datetime.utcnow()
            
            return workers_info
            
        except Exception as e:
            logger.error(f"Error getting workers info: {e}")
            return {}
    
    async def _get_queue_info(self) -> Dict[str, Any]:
        """Get information about task queues."""
        try:
            if not self._redis_client:
                self._redis_client = redis.from_url(settings.CELERY_BROKER_URL)
            
            # Get queue lengths for known queues
            queue_names = [
                "matchering_default",
                "audio_processing", 
                "audio_analysis",
                "file_operations"
            ]
            
            queue_lengths = {}
            total_pending = 0
            
            for queue_name in queue_names:
                try:
                    length = await asyncio.get_event_loop().run_in_executor(
                        None, self._redis_client.llen, queue_name
                    )
                    queue_lengths[queue_name] = length
                    total_pending += length
                except Exception as e:
                    logger.warning(f"Could not get length for queue {queue_name}: {e}")
                    queue_lengths[queue_name] = 0
            
            return {
                "queue_lengths": queue_lengths,
                "total_pending": total_pending
            }
            
        except Exception as e:
            logger.error(f"Error getting queue info: {e}")
            return {"queue_lengths": {}, "total_pending": 0}
    
    async def _get_task_statistics(self) -> Dict[str, Any]:
        """Get task execution statistics."""
        try:
            # For now, return basic stats
            # In a full implementation, this would query task result backend
            # and analyze recent task execution results
            
            return {
                "failed_recent": 0,  # Would query Redis for failed tasks in last hour
                "completed_recent": 0,
                "average_execution_time": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting task statistics: {e}")
            return {"failed_recent": 0}
    
    def _determine_worker_status(self, worker_data: Dict[str, Any]) -> str:
        """Determine if a worker is online, offline, or unknown."""
        if not worker_data:
            return "unknown"
        
        # Check if worker has recent heartbeat (within last 60 seconds)
        heartbeat = worker_data.get("heartbeat")
        if heartbeat and isinstance(heartbeat, datetime):
            time_since_heartbeat = datetime.utcnow() - heartbeat
            if time_since_heartbeat.total_seconds() < 60:
                return "online"
            elif time_since_heartbeat.total_seconds() < 300:  # 5 minutes
                return "offline"
        
        # If we have processed tasks, assume online (fallback)
        if worker_data.get("processed", 0) > 0:
            return "online"
        
        return "unknown"
    
    def _is_cache_valid(self) -> bool:
        """Check if the worker cache is still valid."""
        if not self._last_cache_update:
            return False
        
        time_since_update = datetime.utcnow() - self._last_cache_update
        return time_since_update.total_seconds() < self._cache_ttl
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a quick health check of the Celery system."""
        try:
            broker_status = await self._get_broker_status()
            
            # Try to get basic worker stats quickly
            inspect = self.celery_app.control.inspect()
            stats = await asyncio.get_event_loop().run_in_executor(
                None, inspect.stats
            )
            
            worker_count = len(stats) if stats else 0
            
            return {
                "status": "healthy" if broker_status == "connected" and worker_count > 0 else "degraded",
                "broker_connected": broker_status == "connected",
                "workers_available": worker_count > 0,
                "worker_count": worker_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {
                "status": "unhealthy",
                "broker_connected": False,
                "workers_available": False,
                "worker_count": 0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Export service instance
__all__ = ["CeleryMonitoringService"]