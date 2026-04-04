"""
Database Connection — Turso, Supabase, Pinecone, Redis.
With retry logic and connection pooling.
"""

import os
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def get_turso_client():
    """Get Turso (LibSQL) database client with retry."""
    from libsql_client import create_client
    return create_client(
        url=os.getenv("TURSO_DATABASE_URL", ""),
        auth_token=os.getenv("TURSO_AUTH_TOKEN", ""),
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def get_supabase_client():
    """Get Supabase client with retry."""
    from supabase import create_client
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def get_pinecone_index(index_name: str = "player-embeddings"):
    """Get Pinecone index with retry."""
    import pinecone
    pinecone.init(
        api_key=os.getenv("PINECONE_API_KEY", ""),
        environment=os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp"),
    )
    return pinecone.Index(index_name)


async def get_redis_client():
    """Get Redis client."""
    import redis.asyncio as aioredis
    url = os.getenv("UPSTASH_REDIS_URL", "redis://localhost:6379")
    return aioredis.from_url(url, decode_responses=True)


async def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a Turso SQL query with parameterized inputs."""
    client = await get_turso_client()
    result = await client.execute(query, params)
    return result.rows
