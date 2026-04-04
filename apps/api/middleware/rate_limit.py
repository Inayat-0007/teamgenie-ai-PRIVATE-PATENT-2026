"""
Rate Limiter — Redis-based per-IP rate limiting.
Free: 100 req/min | Premium: 1000 req/min
"""

from __future__ import annotations

import os
import time

import structlog
from fastapi import Request, HTTPException

logger = structlog.get_logger(__name__)

# Routes exempt from rate limiting
_EXEMPT_PATHS: frozenset[str] = frozenset({"/health", "/docs", "/redoc", "/openapi.json"})


async def rate_limit_middleware(request: Request, call_next):
    """Check per-IP rate limits via Redis sliding window."""
    if request.url.path in _EXEMPT_PATHS:
        return await call_next(request)

    identifier = request.client.host if request.client else "unknown"
    window = int(time.time() / 60)
    key = f"rl:{identifier}:{window}"

    try:
        cache = getattr(request.app.state, "cache", None)
        if cache and cache.redis:
            current = await cache.incr(key)
            if current == 1:
                await cache.expire(key, 60)

            # Tier-aware limits
            user_tier = getattr(request.state, "user_tier", "free")
            limit = int(
                os.getenv("RATE_LIMIT_PAID_TIER", "1000")
                if user_tier != "free"
                else os.getenv("RATE_LIMIT_FREE_TIER", "100")
            )

            remaining = max(0, limit - current)
            reset_in = 60 - int(time.time() % 60)

            # Attach standard rate-limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_in)

            if current > limit:
                logger.warning("rate_limit.exceeded", ip=identifier, used=current, limit=limit)
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded ({limit} req/min). Upgrade to premium.",
                        "limit": limit,
                        "used": current,
                        "reset_in_seconds": reset_in,
                    },
                    headers={"Retry-After": str(reset_in)},
                )

            return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.debug("rate_limit.redis_unavailable", error=str(exc))

    return await call_next(request)
