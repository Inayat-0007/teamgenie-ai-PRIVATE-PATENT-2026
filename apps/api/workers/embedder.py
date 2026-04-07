"""
Pinecone Embedding Worker — Upserts harvested data to Pinecone indexes.
"""

import asyncio
import json
import os
import uuid

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

import google.generativeai as genai
from pinecone import Pinecone


# Try async Redis first, fallback to upstash REST
async def _get_redis_client():
    url = os.getenv("UPSTASH_REDIS_URL")
    if not url:
        return None
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(url, decode_responses=True)
        await client.ping()
        return client
    except Exception:
        try:
            from upstash_redis import Redis as UpstashRedis

            token = os.getenv("UPSTASH_REDIS_TOKEN", "")
            rest_url = os.getenv("UPSTASH_REDIS_REST_URL", "")
            if rest_url and token:
                return UpstashRedis(url=rest_url, token=token)
        except Exception:
            pass
        return None


async def _get_embedding(text: str) -> list[float]:
    """Generate embedding vector using Gemini."""
    import asyncio

    # Limit requests per minute for free tier
    await asyncio.sleep(1)
    result = await asyncio.to_thread(
        genai.embed_content,
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document",
    )
    return result.get("embedding", [])


async def run_embedder():
    """Extract data from cache, generate embeddings, push to Pinecone."""
    pc_key = os.getenv("PINECONE_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not pc_key or not gemini_key:
        logger.error("embedder.missing_keys")
        return

    genai.configure(api_key=gemini_key)
    pc = Pinecone(api_key=pc_key)
    index_name = os.getenv("PINECONE_INDEX_NAME", "teamgenie-rag")

    # Fast exit if index doesn't exist
    try:
        active_indexes = pc.list_indexes().names()
        if index_name not in active_indexes:
            logger.warning("embedder.index_not_found", index=index_name)
            return
    except Exception as e:
        logger.warning("embedder.pinecone_check_failed", error=str(e))
        return

    index = pc.Index(index_name)
    redis = await _get_redis_client()
    if not redis:
        logger.error("embedder.no_cache_found")
        return

    is_async = hasattr(redis, "keys") and asyncio.iscoroutinefunction(redis.keys)

    try:
        # 1. Embed Match Schedule & Venues
        schedule_keys = await redis.keys("match_live:*") if is_async else redis.keys("match_live:*")

        venue_vectors = []
        news_vectors = []

        for key in schedule_keys[:5]:  # limited for free tier
            data_str = await redis.get(key) if is_async else redis.get(key)
            if not data_str:
                continue
            data = json.loads(data_str)

            # Embed venue data
            if data.get("venue"):
                text = f"Venue: {data['venue']}. Details: Match {data['title']} at {data['date']}."
                intel = data.get("intelligence", {})

                # Check for weather/pitch data
                weather = intel.get("weather")
                if weather:
                    text += f" Weather: {weather.get('temperature_2m')}C, Wind: {weather.get('windspeed_10m')}km/h."

                vec = await _get_embedding(text)
                if vec:
                    venue_vectors.append(
                        {"id": f"venue_{data['id']}", "values": vec, "metadata": {"text": text, "type": "venue_data"}}
                    )

            # Embed DDG intelligence/news if available
            ddg_news = data.get("intelligence", {}).get("ddg_search", [])
            for res in ddg_news[:3]:
                news_text = f"{res.get('title', '')}: {res.get('body', '')}"
                vec = await _get_embedding(news_text)
                if vec:
                    news_vectors.append(
                        {
                            "id": f"news_{uuid.uuid4().hex[:8]}",
                            "values": vec,
                            "metadata": {"text": news_text, "type": "news"},
                        }
                    )

        if venue_vectors:
            await asyncio.to_thread(index.upsert, vectors=venue_vectors, namespace="venue_data")
            logger.info("embedder.venue_upserted", count=len(venue_vectors))

        if news_vectors:
            await asyncio.to_thread(index.upsert, vectors=news_vectors, namespace="news")
            logger.info("embedder.news_upserted", count=len(news_vectors))

    except Exception as e:
        logger.error("embedder.execution_failed", error=str(e))
    finally:
        if isinstance(redis, getattr(redis, "__class__", type)) and getattr(redis, "__module__", "").startswith(
            "redis.asyncio"
        ):
            await redis.close()


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))
    asyncio.run(run_embedder())
