"""
AI Firewall — Pattern-based threat detection + request hardening.
Analyzes every request for SQL injection, XSS, path traversal, command injection.

Security layers:
  1. Request body size enforcement (prevents resource exhaustion)
  2. Content-Type validation for mutating methods
  3. Header injection detection
  4. URL + query param pattern scanning
  5. Request body pattern scanning
  6. Per-IP violation tracking (in-memory, complements Redis rate limiter)
"""

from __future__ import annotations

import os
import re
import time
from collections import defaultdict
from typing import Dict, Tuple

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from fastapi import Request, HTTPException

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Max request body size: 1 MB (prevents payload bombs)
_MAX_BODY_BYTES = int(os.getenv("FIREWALL_MAX_BODY_BYTES", str(1 * 1024 * 1024)))

# Allowed content types for mutating methods
_ALLOWED_CONTENT_TYPES = frozenset({
    "application/json",
    "application/x-www-form-urlencoded",
    "multipart/form-data",
})

# Pre-compiled regex for common attack signatures (case-insensitive)
_ATTACK_PATTERNS: list[re.Pattern] = [
    # SQL Injection
    re.compile(r"UNION\s+(ALL\s+)?SELECT", re.IGNORECASE),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"SELECT\s+.*\s+FROM\s+.*\s+WHERE", re.IGNORECASE),
    re.compile(r"INSERT\s+INTO\s+", re.IGNORECASE),
    re.compile(r"DELETE\s+FROM\s+", re.IGNORECASE),
    re.compile(r"UPDATE\s+\w+\s+SET\s+", re.IGNORECASE),
    re.compile(r";\s*DROP\s+", re.IGNORECASE),
    re.compile(r"OR\s+1\s*=\s*1", re.IGNORECASE),
    re.compile(r"'\s*OR\s+'", re.IGNORECASE),
    # XSS
    re.compile(r"<script[\s>]", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"(onload|onerror|onmouseover|onfocus|onblur)\s*=", re.IGNORECASE),
    re.compile(r"<iframe[\s>]", re.IGNORECASE),
    re.compile(r"<embed[\s>]", re.IGNORECASE),
    re.compile(r"<object[\s>]", re.IGNORECASE),
    # Path Traversal
    re.compile(r"\.\./", re.IGNORECASE),
    re.compile(r"\.\.\%2[fF]", re.IGNORECASE),  # URL-encoded ../
    # Command Injection
    re.compile(r";\s*(ls|cat|rm|curl|wget|bash|sh|cmd|powershell)\b", re.IGNORECASE),
    re.compile(r"(\|\||&&)\s*(ls|cat|rm|curl|wget|bash|sh|powershell)", re.IGNORECASE),
    re.compile(r"`[^`]+`", re.IGNORECASE),  # Backtick command execution
    # SSRF patterns
    re.compile(r"https?://127\.0\.0\.1", re.IGNORECASE),
    re.compile(r"https?://localhost", re.IGNORECASE),
    re.compile(r"https?://0\.0\.0\.0", re.IGNORECASE),
    re.compile(r"https?://\[::1\]", re.IGNORECASE),
]

# Suspicious header patterns
_HEADER_ATTACK_PATTERNS: list[re.Pattern] = [
    re.compile(r"\r\n", re.IGNORECASE),  # HTTP header injection / CRLF
    re.compile(r"<script", re.IGNORECASE),
]

# Paths exempt from firewall inspection
_EXEMPT_PATHS: frozenset[str] = frozenset({"/health", "/docs", "/redoc", "/openapi.json", "/metrics"})

# ---------------------------------------------------------------------------
# In-memory per-IP violation tracker (complements Redis rate limiter)
# ---------------------------------------------------------------------------
_ip_violations: Dict[str, list] = defaultdict(list)
_IP_BAN_THRESHOLD = int(os.getenv("FIREWALL_BAN_THRESHOLD", "5"))  # violations before temp ban
_IP_BAN_WINDOW_SECONDS = 600  # 10 minute window


def _get_client_ip(request: Request) -> str:
    """Extract client IP with X-Forwarded-For validation.
    
    Audit Fix: Previously blindly trusted X-Forwarded-For from any source.
    Now only trusts the header when the direct connection is from a known proxy.
    Attackers could set X-Forwarded-For: 127.0.0.1 to bypass IP bans.
    """
    # Only trust X-Forwarded-For if the direct connection is from a trusted proxy
    trusted_proxies = set(
        os.getenv("TRUSTED_PROXIES", "127.0.0.1,10.0.0.0/8").split(",")
    )
    direct_ip = request.client.host if request.client else "unknown"
    
    # If direct connection is from a known proxy, trust X-Forwarded-For
    if direct_ip in trusted_proxies:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    
    return direct_ip


def _is_ip_banned(ip: str) -> bool:
    """Check if an IP has exceeded the violation threshold in the ban window."""
    now = time.time()
    # Clean old entries
    _ip_violations[ip] = [ts for ts in _ip_violations[ip] if now - ts < _IP_BAN_WINDOW_SECONDS]
    return len(_ip_violations[ip]) >= _IP_BAN_THRESHOLD


def _record_violation(ip: str) -> int:
    """Record a violation for an IP. Returns the current violation count."""
    _ip_violations[ip].append(time.time())
    return len(_ip_violations[ip])


def _contains_attack(text: str) -> bool:
    """Return True if any attack pattern matches the text."""
    return any(pattern.search(text) for pattern in _ATTACK_PATTERNS)


def _check_headers(request: Request) -> bool:
    """Return True if any header contains suspicious patterns."""
    for header_name, header_value in request.headers.items():
        # Skip standard binary/large headers
        if header_name.lower() in ("cookie", "authorization", "content-type", "host"):
            continue
        for pattern in _HEADER_ATTACK_PATTERNS:
            if pattern.search(header_value):
                return True
    return False


def _validate_content_type(request: Request) -> bool:
    """Validate Content-Type for mutating methods. Returns False if invalid."""
    content_type = request.headers.get("content-type", "")
    # Extract base type (ignore charset, boundary, etc.)
    base_type = content_type.split(";")[0].strip().lower()
    if not base_type:
        return False
    return base_type in _ALLOWED_CONTENT_TYPES


# ---------------------------------------------------------------------------
# Main Firewall Middleware
# ---------------------------------------------------------------------------
async def ai_firewall_check(request: Request, call_next):
    """
    Multi-layer firewall middleware.
    Blocks requests matching attack patterns + enforces request hygiene.
    """
    if os.getenv("ENABLE_AI_FIREWALL", "false").lower() != "true":
        return await call_next(request)

    if request.url.path in _EXEMPT_PATHS:
        return await call_next(request)

    client_ip = _get_client_ip(request)

    # Layer 0: Check if IP is temporarily banned
    if _is_ip_banned(client_ip):
        logger.critical("firewall.ip_banned", ip=client_ip, violations=len(_ip_violations[client_ip]))
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Your IP has been temporarily blocked due to repeated suspicious requests.",
        )

    # Layer 1: Content-Type validation for mutating methods
    if request.method in {"POST", "PUT", "PATCH"}:
        if not _validate_content_type(request):
            violation_count = _record_violation(client_ip)
            logger.warning(
                "firewall.invalid_content_type",
                ip=client_ip,
                content_type=request.headers.get("content-type", "missing"),
                violation=violation_count,
            )
            raise HTTPException(
                status_code=415,
                detail="Unsupported Media Type: Expected application/json",
            )

    # Layer 2: Check headers for injection
    if _check_headers(request):
        violation_count = _record_violation(client_ip)
        logger.critical("firewall.blocked_header_injection", ip=client_ip, violation=violation_count)
        raise HTTPException(status_code=403, detail="Forbidden: Suspicious headers detected")

    # Layer 3: Check URL + query params
    full_url = str(request.url)
    if _contains_attack(full_url):
        violation_count = _record_violation(client_ip)
        logger.critical("firewall.blocked_url", url=full_url[:200], ip=client_ip, violation=violation_count)
        raise HTTPException(status_code=403, detail="Forbidden: Suspicious request blocked by AI firewall")

    # Layer 4: Check request body for mutating methods
    if request.method in {"POST", "PUT", "PATCH"}:
        try:
            body = await request.body()

            # Body size check
            if len(body) > _MAX_BODY_BYTES:
                violation_count = _record_violation(client_ip)
                logger.warning(
                    "firewall.body_too_large",
                    ip=client_ip,
                    size_bytes=len(body),
                    max_bytes=_MAX_BODY_BYTES,
                    violation=violation_count,
                )
                raise HTTPException(
                    status_code=413,
                    detail=f"Request body too large ({len(body)} bytes). Maximum: {_MAX_BODY_BYTES} bytes.",
                )

            body_str = body.decode("utf-8", errors="ignore")
            if _contains_attack(body_str):
                violation_count = _record_violation(client_ip)
                logger.critical(
                    "firewall.blocked_body",
                    path=request.url.path,
                    method=request.method,
                    ip=client_ip,
                    violation=violation_count,
                )
                raise HTTPException(status_code=403, detail="Forbidden: Suspicious payload blocked by AI firewall")
        except HTTPException:
            raise
        except Exception:
            pass  # Don't block on body-read failures

    return await call_next(request)
