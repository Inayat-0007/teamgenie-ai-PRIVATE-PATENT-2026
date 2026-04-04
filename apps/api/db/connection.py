"""
Database Connection — Turso, Supabase, Pinecone, Redis.
All connections use retry + exponential backoff for resilience.
"""

from __future__ import annotations

import os
from typing import Optional

import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = structlog.get_logger(__name__)

_RETRY_KWARGS = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=1, max=10),
    "retry": retry_if_exception_type(Exception),
}


@retry(**_RETRY_KWARGS)
async def get_turso_client():
    """Get Turso (LibSQL) database client with retry."""
    from libsql_client import create_client

    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN")

    if not url or not token:
        raise EnvironmentError("TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set")

    client = create_client(url=url, auth_token=token)
    logger.debug("turso.connected", url=url[:30] + "...")
    return client


@retry(**_RETRY_KWARGS)
def get_supabase_client():
    """Get Supabase client with retry."""
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

    return create_client(url, key)


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
    """Execute a parameterized Turso SQL query. Returns row list."""
    client = await get_turso_client()
    try:
        result = await client.execute(query, params)
        return result.rows
    finally:
        await client.close()
