"""
Cache Service — Upstash Redis wrapper with connection management.
Gracefully degrades when Redis is unavailable.
"""

from __future__ import annotations

import os
from contextlib import suppress

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache wrapper for Upstash (serverless) or local Redis."""

    def __init__(self):
        self.redis = None
        self.url = os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379")

    async def connect(self):
        """Initialize async Redis connection with health-check ping."""
        try:
            import redis.asyncio as aioredis

            self.redis = aioredis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            await self.redis.ping()
            logger.info("cache.connected", url=self.url[:30] + "...")
        except Exception as exc:
            logger.warning("cache.connect_failed", error=str(exc))
            self.redis = None

    async def disconnect(self):
        """Cleanly close the Redis connection."""
        if self.redis:
            try:
                await self.redis.close()
                logger.info("cache.disconnected")
            except Exception:
                pass
            finally:
                self.redis = None

    async def get(self, key: str) -> str | None:
        """Get a cached value. Returns None on miss or if Redis is unavailable."""
        if not self.redis:
            return None
        try:
            return await self.redis.get(key)
        except Exception as exc:
            logger.debug("cache.get_error", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: str, ttl: int = 300):
        """Set a cached value with TTL (default 5 minutes)."""
        if not self.redis:
            return
        try:
            await self.redis.setex(key, ttl, value)
        except Exception as exc:
            logger.debug("cache.set_error", key=key, error=str(exc))

    async def delete(self, key: str):
        """Delete a cached key."""
        if not self.redis:
            return
        try:
            await self.redis.delete(key)
        except Exception as exc:
            logger.debug("cache.delete_error", key=key, error=str(exc))

    async def incr(self, key: str) -> int:
        """Atomically increment a counter. Returns 0 if Redis is unavailable."""
        if not self.redis:
            return 0
        try:
            return await self.redis.incr(key)
        except Exception:
            return 0

    async def expire(self, key: str, seconds: int):
        """Set TTL on an existing key."""
        if not self.redis:
            return
        with suppress(Exception):
            await self.redis.expire(key, seconds)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis:
            return False
        try:
            return bool(await self.redis.exists(key))
        except Exception:
            return False
