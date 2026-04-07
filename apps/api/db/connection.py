"""
Database Connection — Turso, Supabase, Pinecone, Redis.
All connections use retry + exponential backoff for resilience.
"""

from __future__ import annotations

import os
from typing import Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
    )
    _RETRY_KWARGS = {
        "stop": stop_after_attempt(3),
        "wait": wait_exponential(multiplier=1, min=1, max=10),
        "retry": retry_if_exception_type(Exception),
    }
except ImportError:
    # Fallback: no-op retry decorator when tenacity not installed
    def retry(**kwargs):  # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator
    _RETRY_KWARGS = {}


# Module-level singleton to avoid per-query connection churn
_turso_client = None
_turso_client_failed = False
_supabase_client = None


@retry(**_RETRY_KWARGS)
async def get_turso_client():
    """Get Turso (LibSQL) database client — singleton, reused across queries.
    
    Previously this created a new client per query (153+ TLS handshakes per
    harvest cycle). Now caches a single client for the process lifetime.
    """
    global _turso_client, _turso_client_failed
    
    if _turso_client is not None and not _turso_client_failed:
        return _turso_client
    
    from libsql_client import create_client

    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")

    if not url or not token:
        raise EnvironmentError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set")

    _turso_client = create_client(url=url, auth_token=token)
    _turso_client_failed = False
    logger.debug("turso.connected", url=url[:30] + "...")
    return _turso_client


@retry(**_RETRY_KWARGS)
def get_supabase_client():
    """Get Supabase client with retry — singleton to prevent connection churn.

    Audit Fix #5: Previously created a new client on every call, wasting
    TCP/TLS connections on every auth operation. Now cached like Turso.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

    _supabase_client = create_client(url, key)
    logger.debug("supabase.connected", url=url[:30] + "...")
    return _supabase_client


@retry(**_RETRY_KWARGS)
def get_pinecone_index(index_name: Optional[str] = None):
    """Get Pinecone index with retry. Uses v3+ API."""
    from pinecone import Pinecone

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise EnvironmentError("PINECONE_API_KEY must be set")

    pc = Pinecone(api_key=api_key)
    target_index = index_name or os.getenv("PINECONE_INDEX_NAME", "player-embeddings")
    return pc.Index(target_index)


async def get_redis_client():
    """Get Redis async client."""
    import redis.asyncio as aioredis

    url = os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379")
    return aioredis.from_url(url, decode_responses=True)


async def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a parameterized Turso SQL query. Returns row list for SELECTs, empty list for writes.
    
    Uses batch() instead of execute() to work around a KeyError: 'result' bug
    in libsql_client 0.3.1's HTTP driver for INSERT/REPLACE statements.
    
    NOTE: Does NOT close the client — singleton is reused across queries.
    On connection failure, marks the client for recreation on the next call.
    """
    global _turso_client_failed
    from libsql_client import Statement
    client = await get_turso_client()
    try:
        stmt = Statement(query, list(params))
        results = await client.batch([stmt])
        if results and len(results) > 0:
            rs = results[0]
            if hasattr(rs, 'rows'):
                return rs.rows
        return []
    except Exception as exc:
        _turso_client_failed = True  # Force reconnect on next call
        raise
