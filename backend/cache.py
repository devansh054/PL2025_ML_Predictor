"""Redis cache configuration and utilities."""

import os
import json
import pickle
from typing import Any, Optional
import redis.asyncio as redis
from datetime import timedelta


class CacheManager:
    """Redis cache manager for the application."""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        self.redis_client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False
        )
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Any:
        """Get value from cache."""
        if not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        if not self.redis_client:
            await self.connect()
        
        try:
            serialized_value = pickle.dumps(value)
            await self.redis_client.setex(key, expire, serialized_value)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def get_prediction_cache_key(self, home_team: str, away_team: str) -> str:
        """Generate cache key for predictions."""
        return f"prediction:{home_team}:{away_team}"
    
    async def get_team_stats_cache_key(self, team: str) -> str:
        """Generate cache key for team statistics."""
        return f"team_stats:{team}"
    
    async def get_model_performance_cache_key(self) -> str:
        """Generate cache key for model performance."""
        return "model_performance:latest"


# Global cache instance
cache_manager = CacheManager()
