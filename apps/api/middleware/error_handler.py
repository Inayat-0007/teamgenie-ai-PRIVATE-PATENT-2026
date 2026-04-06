"""
Error Handler — Global exception handling with structured logging.
Limits traceback length and filters sensitive values from logs.
"""

from __future__ import annotations

import os
import traceback

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from fastapi import Request
from fastapi.responses import JSONResponse

# Max traceback characters to log (prevents log bloat from deep stacks)
_MAX_TRACEBACK_CHARS = 4000

# Patterns to redact from logged tracebacks (env secrets, tokens, etc.)
_SENSITIVE_PATTERNS = (
    "API_KEY", "SECRET", "TOKEN", "PASSWORD", "DSN",
    "SUPABASE", "PINECONE", "REDIS_URL", "AUTH_TOKEN",
)


def _sanitize_traceback(tb_str: str) -> str:
    """Truncate and redact sensitive values from traceback text."""
    # Truncate
    if len(tb_str) > _MAX_TRACEBACK_CHARS:
        tb_str = tb_str[:_MAX_TRACEBACK_CHARS] + "\n... [TRUNCATED — full traceback in Sentry]"

    # Redact lines that contain env variable names with secrets
    sanitized_lines = []
    for line in tb_str.split("\n"):
        for pattern in _SENSITIVE_PATTERNS:
            if pattern in line.upper():
                line = f"  [REDACTED: line contained {pattern}]"
                break
        sanitized_lines.append(line)

    return "\n".join(sanitized_lines)


async def error_handler_middleware(request: Request, call_next):
    """Catch unhandled exceptions and return clean, structured error responses."""
    try:
        return await call_next(request)
    except Exception as exc:
        request_id = getattr(request.state, "request_id", "unknown")

        # Check if this is a custom TeamGenie exception with its own status code
        from core.exceptions import TeamGenieError
        if isinstance(exc, TeamGenieError):
            logger.warning(
                "handled_error",
                error_code=exc.error_code,
                message=exc.message[:200],
                status_code=exc.status_code,
                request_id=request_id,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.error_code,
                        "message": exc.message,
                        "request_id": request_id,
                    }
                },
            )

        # Generic unhandled exception
        raw_tb = traceback.format_exc()
        safe_tb = _sanitize_traceback(raw_tb)

        logger.error(
            "unhandled_error",
            method=request.method,
            path=request.url.path,
            error=str(exc)[:500],
            error_type=type(exc).__name__,
            request_id=request_id,
            traceback=safe_tb,
        )

        # Forward to Sentry if available AND initialized
        try:
            import sentry_sdk
            if sentry_sdk.Hub.current.client is not None:
                sentry_sdk.capture_exception(exc)
        except (ImportError, AttributeError, Exception):
            pass  # Never let Sentry crash the error handler

        # In production: generic message. In dev: include error type for debugging.
        is_production = os.getenv("PYTHON_ENV", "development") == "production"
        user_message = (
            "An unexpected error occurred."
            if is_production
            else f"An unexpected error occurred ({type(exc).__name__})."
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": user_message,
                    "request_id": request_id,
                    "path": request.url.path,
                }
            },
        )
