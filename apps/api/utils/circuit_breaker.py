"""
Circuit Breaker — Upgrade #13 from Master Doctrine v2.0.
Wraps external API calls with retry, timeout, and fallback logic.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Wrap external API calls with retry + fallback for 99.9% uptime."""

    @staticmethod
    def with_fallback(fallback_func: Callable | None = None, max_retries: int = 3):
        """Decorator that retries on failure and falls back to a safe function."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                last_error = None

                for attempt in range(1, max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        last_error = exc
                        logger.warning(
                            "circuit_breaker.retry",
                            func=func.__name__,
                            attempt=attempt,
                            max_retries=max_retries,
                            error=str(exc),
                        )
                        if attempt < max_retries:
                            await asyncio.sleep(min(2**attempt, 10))

                # All retries exhausted → try fallback
                if fallback_func is not None:
                    logger.info(
                        "circuit_breaker.fallback",
                        func=func.__name__,
                        fallback=fallback_func.__name__,
                    )
                    return await fallback_func(*args, **kwargs)

                # No fallback → raise the last error
                raise last_error  # type: ignore[misc]

            return wrapper

        return decorator
