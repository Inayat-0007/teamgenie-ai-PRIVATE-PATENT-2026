"""
Rate Limiter — Redis-based per-IP rate limiting with in-memory fallback.
Free: 100 req/min | Premium: 1000 req/min

DEFECT #5 FIX: When Redis is unavailable, the old code passed ALL requests
through with zero rate limiting (silent bypass). Now falls back to an
in-memory sliding window counter per-IP.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Dict, List

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from fastapi import Request, HTTPException

# Routes exempt from rate limiting (health probes + monitoring — Performance Fix 2.2)
_EXEMPT_PATHS: frozenset[str] = frozenset({"/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json"})

# ---------------------------------------------------------------------------
# In-memory fallback rate limiter (used when Redis is unavailable)
# ---------------------------------------------------------------------------
_inmem_counters: Dict[str, List[float]] = defaultdict(list)
_INMEM_WINDOW_SECONDS = 60


def _inmem_check(identifier: str, limit: int) -> tuple[int, int]:
    """In-memory sliding window rate check.
    Returns (current_count, reset_in_seconds).
    """
    now = time.time()
    # Prune expired entries
    _inmem_counters[identifier] = [
        ts for ts in _inmem_counters[identifier]
        if now - ts < _INMEM_WINDOW_SECONDS
    ]
    _inmem_counters[identifier].append(now)
    current = len(_inmem_counters[identifier])
    # Approximate reset time
    if _inmem_counters[identifier]:
        oldest = _inmem_counters[identifier][0]
        reset_in = max(1, int(_INMEM_WINDOW_SECONDS - (now - oldest)))
    else:
        reset_in = _INMEM_WINDOW_SECONDS
    return current, reset_in


async def rate_limit_middleware(request: Request, call_next):
    """Check per-IP rate limits via Redis sliding window, with in-memory fallback."""
    if request.url.path in _EXEMPT_PATHS:
        return await call_next(request)

    identifier = request.client.host if request.client else "unknown"
    window = int(time.time() / 60)
    key = f"rl:{identifier}:{window}"

    # Determine tier-aware limit
    user_tier = getattr(request.state, "user_tier", "free")
    limit = int(
        os.getenv("RATE_LIMIT_PAID_TIER", "1000")
        if user_tier != "free"
        else os.getenv("RATE_LIMIT_FREE_TIER", "100")
    )

    try:
        cache = getattr(request.app.state, "cache", None)
        if cache and cache.redis:
            current = await cache.incr(key)
            if current == 1:
                await cache.expire(key, 60)

            remaining = max(0, limit - current)
            reset_in = 60 - int(time.time() % 60)

            # Block over-limit requests BEFORE serving — prevents wasted compute
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

            # Attach standard rate-limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_in)

            return response
        else:
            raise RuntimeError("Redis unavailable — using fallback")

    except HTTPException:
        raise
    except Exception as exc:
        # DEFECT #5 FIX: Fallback to in-memory rate limiting instead of passing through
        logger.warning("rate_limit.redis_unavailable_using_fallback", error=str(exc))
        
        current, reset_in = _inmem_check(identifier, limit)
        remaining = max(0, limit - current)
        
        if current > limit:
            logger.warning("rate_limit.exceeded_inmem", ip=identifier, used=current, limit=limit)
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
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_in)
        response.headers["X-RateLimit-Backend"] = "inmemory-fallback"
        return response
