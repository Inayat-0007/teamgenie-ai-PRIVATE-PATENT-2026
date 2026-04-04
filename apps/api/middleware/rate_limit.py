"""
Rate Limiter — Redis-based per-IP rate limiting.
Free: 100 req/min | Premium: 1000 req/min
"""

from fastapi import Request, HTTPException
import os
import time


async def rate_limit_middleware(request: Request, call_next):
    """Check rate limits using Redis."""
    if request.url.path in {"/health", "/docs", "/redoc"}:
        return await call_next(request)

    identifier = request.client.host if request.client else "unknown"
    key = f"rl:{identifier}:{int(time.time() / 60)}"

    try:
        cache = getattr(request.app.state, "cache", None)
        if cache and cache.redis:
            current = await cache.incr(key)
            if current == 1:
                await cache.expire(key, 60)

            limit = int(os.getenv("RATE_LIMIT_FREE_TIER", "100"))

            if current > limit:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded ({limit} req/min). Upgrade to premium.",
                        "limit": limit,
                        "used": current,
                        "reset_in_seconds": 60 - int(time.time() % 60),
                    },
                )
    except HTTPException:
        raise
    except Exception:
        pass  # Don't block requests if Redis is down

    response = await call_next(request)
    return response
