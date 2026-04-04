"""
Cache Service — Upstash Redis wrapper with connection management.
"""

import os
from typing import Optional


class CacheService:
    """Redis cache wrapper for Upstash (serverless) or local Redis."""

    def __init__(self):
        self.redis = None
        self.url = os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379")

    async def connect(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(self.url, decode_responses=True)
            await self.redis.ping()
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}. Running without cache.")
            self.redis = None

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[str]:
        if not self.redis:
            return None
        return await self.redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 300):
        if not self.redis:
            return
        await self.redis.setex(key, ttl, value)

    async def delete(self, key: str):
        if not self.redis:
            return
        await self.redis.delete(key)

    async def incr(self, key: str) -> int:
        if not self.redis:
            return 0
        return await self.redis.incr(key)

    async def expire(self, key: str, seconds: int):
        if not self.redis:
            return
        await self.redis.expire(key, seconds)
