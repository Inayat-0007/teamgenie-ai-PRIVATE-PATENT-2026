"""
Error Handler — Global exception handling with Sentry integration.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback
import os


async def error_handler_middleware(request: Request, call_next):
    """Catch unhandled exceptions and return clean error responses."""
    try:
        return await call_next(request)
    except Exception as exc:
        # Log error
        tb = traceback.format_exc()
        print(f"❌ Unhandled error on {request.method} {request.url.path}:\n{tb}")

        # Sentry capture
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exc)
        except ImportError:
            pass

        request_id = getattr(request.state, "request_id", "unknown")

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
