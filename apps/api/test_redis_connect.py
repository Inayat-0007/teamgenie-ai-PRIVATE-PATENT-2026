"""Quick Redis connectivity test."""
import os
from dotenv import load_dotenv
load_dotenv()

# Try Upstash REST API
try:
    from upstash_redis import Redis
    host = "alert-goblin-93077.upstash.io"
    rest_url = f"https://{host}"
    token = os.getenv("UPSTASH_REDIS_TOKEN", "")
    print(f"Trying REST: URL={rest_url}")
    print(f"Token prefix: {token[:20]}...")
    
    r = Redis(url=rest_url, token=token)
    r.set("harvester_test", "alive")
    val = r.get("harvester_test")
    print(f"REST SET/GET: {val}")
    print("Upstash REST OK!")
except Exception as e:
    print(f"Upstash REST FAIL: {type(e).__name__}: {e}")

# Try redis.asyncio with the URL
import asyncio
async def test_async():
    import redis.asyncio as aioredis
    url = os.getenv("UPSTASH_REDIS_URL", "")
    print(f"\nTrying redis.asyncio: {url[:50]}...")
    try:
        r = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=5)
        pong = await r.ping()
        print(f"PING: {pong}")
        await r.close()
    except Exception as e:
        print(f"redis.asyncio FAIL: {type(e).__name__}: {e}")

asyncio.run(test_async())
