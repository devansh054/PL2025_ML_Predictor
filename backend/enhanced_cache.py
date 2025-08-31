"""Enhanced Redis caching layer with advanced patterns and optimization."""

import asyncio
import json
import pickle
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import structlog
import redis.asyncio as redis
from enum import Enum

logger = structlog.get_logger()

class CacheStrategy(Enum):
    """Cache invalidation strategies."""
    TTL = "ttl"
    LRU = "lru"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: datetime
    tags: List[str]
    size_bytes: int

class EnhancedCacheManager:
    """Advanced Redis cache manager with multiple strategies and patterns."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = "pl_predictor"):
        self.redis_url = redis_url
        self.prefix = prefix
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
        self.background_tasks: Dict[str, asyncio.Task] = {}
        
    async def connect(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Enhanced cache manager connected to Redis")
            
            # Start background maintenance tasks
            self.background_tasks["cleanup"] = asyncio.create_task(self._cleanup_expired_entries())
            self.background_tasks["stats"] = asyncio.create_task(self._update_cache_stats())
            
        except Exception as e:
            logger.warning("Redis not available, using local cache only", error=str(e))
            self.redis_client = None
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with fallback to local cache."""
        cache_key = self._make_key(key)
        
        try:
            # Try Redis first
            if self.redis_client:
                value = await self.redis_client.get(cache_key)
                if value is not None:
                    self.cache_stats["hits"] += 1
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return pickle.loads(value)
            
            # Fallback to local cache
            if cache_key in self.local_cache:
                entry = self.local_cache[cache_key]
                
                # Check if expired
                if entry.expires_at and datetime.now() > entry.expires_at:
                    del self.local_cache[cache_key]
                    self.cache_stats["evictions"] += 1
                else:
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    self.cache_stats["hits"] += 1
                    return entry.value
            
            self.cache_stats["misses"] += 1
            return default
            
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            self.cache_stats["misses"] += 1
            return default
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None, 
                  tags: List[str] = None, strategy: CacheStrategy = CacheStrategy.TTL) -> bool:
        """Set value in cache with advanced options."""
        cache_key = self._make_key(key)
        tags = tags or []
        
        try:
            # Serialize value
            if isinstance(value, (dict, list, str, int, float, bool)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = pickle.dumps(value)
            
            # Set in Redis
            if self.redis_client:
                if expire:
                    await self.redis_client.setex(cache_key, expire, serialized_value)
                else:
                    await self.redis_client.set(cache_key, serialized_value)
                
                # Store metadata
                metadata = {
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(seconds=expire)).isoformat() if expire else None,
                    "tags": json.dumps(tags),
                    "strategy": strategy.value,
                    "size_bytes": len(serialized_value)
                }
                await self.redis_client.hset(f"{cache_key}:meta", mapping=metadata)
                
                # Add to tag indexes
                for tag in tags:
                    await self.redis_client.sadd(f"{self.prefix}:tag:{tag}", cache_key)
            
            # Also store in local cache as backup
            expires_at = datetime.now() + timedelta(seconds=expire) if expire else None
            entry = CacheEntry(
                key=cache_key,
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at,
                access_count=0,
                last_accessed=datetime.now(),
                tags=tags,
                size_bytes=len(str(value))
            )
            self.local_cache[cache_key] = entry
            
            self.cache_stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        cache_key = self._make_key(key)
        
        try:
            deleted = False
            
            # Delete from Redis
            if self.redis_client:
                result = await self.redis_client.delete(cache_key)
                await self.redis_client.delete(f"{cache_key}:meta")
                deleted = bool(result)
            
            # Delete from local cache
            if cache_key in self.local_cache:
                del self.local_cache[cache_key]
                deleted = True
            
            if deleted:
                self.cache_stats["deletes"] += 1
            
            return deleted
            
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False
    
    async def _cleanup_expired_entries(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                # Clean up local cache
                current_time = datetime.now()
                expired_keys = [
                    key for key, entry in self.local_cache.items()
                    if entry.expires_at and current_time > entry.expires_at
                ]
                
                for key in expired_keys:
                    del self.local_cache[key]
                    self.cache_stats["evictions"] += 1
                
                if expired_keys:
                    logger.debug("Cleaned up expired local cache entries", count=len(expired_keys))
                
                await asyncio.sleep(60)  # Run every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cache cleanup task", error=str(e))
                await asyncio.sleep(60)
    
    async def _update_cache_stats(self):
        """Background task to update cache statistics."""
        while True:
            try:
                if self.redis_client:
                    # Get Redis info
                    info = await self.redis_client.info("memory")
                    self.cache_stats["redis_memory_used"] = info.get("used_memory", 0)
                    self.cache_stats["redis_memory_peak"] = info.get("used_memory_peak", 0)
                
                # Calculate hit rate
                total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
                if total_requests > 0:
                    self.cache_stats["hit_rate"] = self.cache_stats["hits"] / total_requests
                else:
                    self.cache_stats["hit_rate"] = 0.0
                
                self.cache_stats["local_cache_size"] = len(self.local_cache)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error updating cache stats", error=str(e))
                await asyncio.sleep(30)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            **self.cache_stats,
            "redis_connected": self.redis_client is not None,
            "local_cache_entries": len(self.local_cache),
            "background_tasks": len(self.background_tasks)
        }

# Global enhanced cache manager
enhanced_cache_manager = EnhancedCacheManager()
