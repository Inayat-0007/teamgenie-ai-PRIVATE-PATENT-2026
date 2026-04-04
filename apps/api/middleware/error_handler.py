"""
Error Handler — Global exception handling with structured logging.
"""

from __future__ import annotations

import traceback

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """Catch unhandled exceptions and return clean, structured error responses."""
    try:
        return await call_next(request)
    except Exception as exc:
        tb = traceback.format_exc()
        request_id = getattr(request.state, "request_id", "unknown")

        logger.error(
            "unhandled_error",
            method=request.method,
            path=request.url.path,
            error=str(exc),
            error_type=type(exc).__name__,
            request_id=request_id,
            traceback=tb,
        )

        # Forward to Sentry if available
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except ImportError:
            pass

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                    "request_id": request_id,
                }
            },
        )
