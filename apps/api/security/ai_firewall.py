"""
AI Firewall — Pattern-based threat detection + configurable block lists.
Analyzes every request for SQL injection, XSS, path traversal, and command injection.
"""

from __future__ import annotations

import os
import re

import structlog
from fastapi import Request, HTTPException

logger = structlog.get_logger(__name__)

# Pre-compiled regex for common attack signatures (case-insensitive)
_ATTACK_PATTERNS: list[re.Pattern] = [
    re.compile(r"UNION\s+(ALL\s+)?SELECT", re.IGNORECASE),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"<script[\s>]", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"\.\./", re.IGNORECASE),
    re.compile(r";\s*(ls|cat|rm|curl|wget|bash|sh|cmd)\b", re.IGNORECASE),
    re.compile(r"(\|\||&&)\s*(ls|cat|rm|curl|wget|bash|sh)", re.IGNORECASE),
    re.compile(r"SELECT\s+.*\s+FROM\s+.*\s+WHERE", re.IGNORECASE),
    re.compile(r"INSERT\s+INTO\s+", re.IGNORECASE),
    re.compile(r"(onload|onerror|onmouseover)\s*=", re.IGNORECASE),
]

# Paths exempt from firewall inspection
_EXEMPT_PATHS: frozenset[str] = frozenset({"/health", "/docs", "/redoc", "/openapi.json"})


def _contains_attack(text: str) -> bool:
    """Return True if any attack pattern matches the text."""
    return any(pattern.search(text) for pattern in _ATTACK_PATTERNS)


async def ai_firewall_check(request: Request, call_next):
    """Block requests that match known attack signatures."""
    if os.getenv("ENABLE_AI_FIREWALL", "false").lower() != "true":
        return await call_next(request)

    if request.url.path in _EXEMPT_PATHS:
        return await call_next(request)

    # Check URL + query params
    full_url = str(request.url)
    if _contains_attack(full_url):
        logger.critical("firewall.blocked_url", url=full_url, ip=request.client.host if request.client else "unknown")
        raise HTTPException(status_code=403, detail="Forbidden: Suspicious request blocked by AI firewall")

    # Check request body for mutating methods
    if request.method in {"POST", "PUT", "PATCH"}:
        try:
            body = await request.body()
            body_str = body.decode("utf-8", errors="ignore")
            if _contains_attack(body_str):
                logger.critical(
                    "firewall.blocked_body",
                    path=request.url.path,
                    method=request.method,
                    ip=request.client.host if request.client else "unknown",
                )
                raise HTTPException(status_code=403, detail="Forbidden: Suspicious payload blocked by AI firewall")
        except HTTPException:
            raise
        except Exception:
            pass  # Don't block on body-read failures

    return await call_next(request)
