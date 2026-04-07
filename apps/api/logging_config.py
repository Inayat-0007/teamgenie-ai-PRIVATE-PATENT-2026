"""
Structlog Configuration — JSON-structured logging for production.
"""

from __future__ import annotations

import os
import sys


def configure_logging():
    """Configure structlog for the application environment. No-op if structlog not installed."""
    try:
        import structlog
    except ImportError:
        return  # structlog not installed — skip configuration

    is_dev = os.getenv("PYTHON_ENV", "development") == "development"

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
    ]

    if is_dev:
        # Pretty console output for development
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        # JSON output for production (Axiom, Datadog, ELK)
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(structlog.get_config().get("min_level", 0)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
