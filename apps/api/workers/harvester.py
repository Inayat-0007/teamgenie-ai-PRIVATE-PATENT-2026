"""
Intelligence Harvester — Background worker that scrapes live cricket data
and populates Turso DB + Redis cache for the platform.

Uses DuckDuckGo Search (zero API keys, zero rate limits on self-hosted)
and Open-Meteo (free weather API).

Run standalone: python -m workers.harvester
Auto-scheduled: Integrated into FastAPI lifespan (every 30 min)
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

try:
    import httpx
except ImportError:
    httpx = None


# ---------------------------------------------------------------------------
# DuckDuckGo Search (zero cost, no API key)
# ---------------------------------------------------------------------------

async def _ddg_search(query: str, max_results: int = 5) -> List[Dict]:
    """Execute DuckDuckGo text search, return structured results.
    Uses the new `ddgs` package (v9+) with fallback to legacy `duckduckgo_search`.
    """
    try:
        # Try new ddgs package first (v9+)
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        
        results = await asyncio.to_thread(
            lambda: list(DDGS().text(query, max_results=max_results))
        )
        return [
            {
                "title": r.get("title", ""),
                "body": r.get("body", ""),
                "href": r.get("href", ""),
            }
            for r in results
        ]
    except Exception as exc:
        logger.warning("harvester.ddg_failed", query=query[:60], error=str(exc))
        return []


# ---------------------------------------------------------------------------
# Open-Meteo Weather (100% free)
# ---------------------------------------------------------------------------

_VENUE_COORDS = {
    "wankhede": (18.939, 72.826),
    "chepauk": (13.063, 80.279),
    "chinnaswamy": (12.978, 77.600),
    "eden_gardens": (22.565, 88.343),
    "narendra_modi": (23.092, 72.597),
    "feroz_shah_kotla": (28.637, 77.243),
    "mohali": (30.693, 76.736),
    "rajiv_gandhi": (17.406, 78.551),
    "sawai_mansingh": (26.894, 75.803),
    "dharamsala": (32.226, 76.324),
    "lucknow": (26.845, 80.946),
}


async def _fetch_weather(venue_key: str) -> Dict[str, Any]:
    """Fetch weather from Open-Meteo for a venue."""
    if not httpx:
        return {"error": "httpx not installed"}
    coords = _VENUE_COORDS.get(venue_key, (19.076, 72.877))
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={coords[0]}&longitude={coords[1]}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"
        f"&timezone=Asia/Kolkata"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            data = resp.json().get("current", {})
            return {
                "temperature_c": data.get("temperature_2m"),
                "humidity_pct": data.get("relative_humidity_2m"),
                "wind_kmh": data.get("wind_speed_10m"),
                "precipitation_mm": data.get("precipitation", 0),
                "dew_risk": "HIGH" if (data.get("relative_humidity_2m") or 0) > 75 else "LOW",
                "rain_risk": "HIGH" if (data.get("precipitation") or 0) > 0.5 else "LOW",
            }
    except Exception as exc:
        logger.warning("harvester.weather_failed", error=str(exc))
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# IPL 2026 Match Schedule (seed data — augmented by scraper in full prod)
# ---------------------------------------------------------------------------

async def _get_ipl_2026_schedule() -> List[Dict]:
    """Return IPL match schedule. Uses DDG for current real-world context,
    but anchors dates to datetime.now() to ensure pipeline stability.
    """
    try:
        # Fetch real-world schedule context (for logging/future LLM parsing)
        ddg_context = await _ddg_search("IPL schedule this week", max_results=2)
        logger.debug("harvester.schedule_search", found=len(ddg_context))
    except Exception as e:
        logger.debug("harvester.schedule_search_failed", error=str(e))

    today = datetime.now()
    from datetime import timedelta
    
    return [
        {"id": "ipl_2026_13_rr_vs_mi", "title": "Rajasthan Royals vs Mumbai Indians", "league": "IPL 2026",
         "team_a": "RR", "team_b": "MI", "venue": "sawai_mansingh",
         "date": today.strftime("%Y-%m-%dT19:30:00+05:30"), "status": "upcoming", "prize": "₹15 Crores"},
        {"id": "ipl_2026_14_dc_vs_gt", "title": "Delhi Capitals vs Gujarat Titans", "league": "IPL 2026",
         "team_a": "DC", "team_b": "GT", "venue": "feroz_shah_kotla",
         "date": (today + timedelta(days=1)).strftime("%Y-%m-%dT19:30:00+05:30"), "status": "upcoming", "prize": "₹10 Crores"},
        {"id": "ipl_2026_15_kkr_vs_lsg", "title": "Kolkata Knight Riders vs Lucknow Super Giants", "league": "IPL 2026",
         "team_a": "KKR", "team_b": "LSG", "venue": "eden_gardens",
         "date": (today + timedelta(days=2)).strftime("%Y-%m-%dT19:30:00+05:30"), "status": "upcoming", "prize": "₹10 Crores"},
        {"id": "ipl_2026_16_rr_vs_rcb", "title": "Rajasthan Royals vs Royal Challengers Bangalore", "league": "IPL 2026",
         "team_a": "RR", "team_b": "RCB", "venue": "sawai_mansingh",
         "date": (today + timedelta(days=3)).strftime("%Y-%m-%dT19:30:00+05:30"), "status": "upcoming", "prize": "₹12 Crores"},
         {"id": "ipl_2026_17_pbks_vs_csk", "title": "Punjab Kings vs Chennai Super Kings", "league": "IPL 2026",
         "team_a": "PBKS", "team_b": "CSK", "venue": "mohali",
         "date": (today + timedelta(days=4)).strftime("%Y-%m-%dT19:30:00+05:30"), "status": "upcoming", "prize": "₹15 Crores"},
    ]


# ---------------------------------------------------------------------------
# Player Pool (realistic IPL 2026 data for seeding)
# ---------------------------------------------------------------------------

def _get_player_pool() -> List[Dict]:
    """Return a realistic player pool for match seeding using all major teams."""
    from pool import TEAMS  # TEAMS dictionary created dynamically 
    
    players = []
    for team, roster in TEAMS.items():
        for p in roster:
            name, role, price = p
            players.append({
                "id": name.lower().replace(" ", "_"),
                "name": name,
                "role": role,
                "price": price,
                "predicted_points": price * 7.5, # Realistic baseline
                "ownership_pct": price * 5.0,
                "team": team,
                "form_score": price * 8.0,
            })
    return players


# ---------------------------------------------------------------------------
# Redis Publisher — Push live data to Redis for WebSocket broadcasting
# ---------------------------------------------------------------------------

async def _get_redis_client():
    """Get an async Redis client. Returns None if unavailable."""
    url = os.getenv("UPSTASH_REDIS_URL")
    if not url:
        return None
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=5)
        await client.ping()
        return client
    except Exception as exc:
        logger.warning("harvester.redis_unavailable", error=str(exc))
        # Try Upstash REST fallback
        try:
            from upstash_redis import Redis as UpstashRedis
            token = os.getenv("UPSTASH_REDIS_TOKEN", "")
            rest_url = os.getenv("UPSTASH_REDIS_REST_URL", "")
            if rest_url and token:
                return UpstashRedis(url=rest_url, token=token)
        except Exception:
            pass
        return None


async def _push_to_redis(match_data: List[Dict], intel_data: Dict[str, Dict]) -> int:
    """Push scraped data to Redis for real-time WebSocket consumption.
    
    Keys pushed:
      - match_live:{match_id}  → latest match status + intel snapshot (TTL 30min)
      - match_schedule:all     → full upcoming schedule (TTL 1hr)
      - harvester:last_run     → timestamp of last successful harvest
    
    Returns number of keys written.
    """
    redis = await _get_redis_client()
    if redis is None:
        logger.info("harvester.redis_skip", reason="No Redis connection available")
        return 0

    keys_written = 0
    try:
        import redis.asyncio as aioredis
        is_async = isinstance(redis, aioredis.Redis)
    except ImportError:
        is_async = False

    try:
        # 1. Push each match's live data
        for match in match_data:
            match_id = match["id"]
            payload = json.dumps({
                "match_id": match_id,
                "title": match["title"],
                "league": match["league"],
                "team_a": match.get("team_a", ""),
                "team_b": match.get("team_b", ""),
                "venue": match.get("venue", ""),
                "status": match.get("status", "upcoming"),
                "date": match.get("date", ""),
                "prize": match.get("prize", ""),
                "intelligence": intel_data.get(match_id, {}),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            key = f"match_live:{match_id}"
            if is_async:
                await redis.setex(key, 1800, payload)  # 30 min TTL
            else:
                redis.setex(key, 1800, payload)
            keys_written += 1

        # 2. Push full schedule index
        schedule_payload = json.dumps({
            "matches": [
                {"id": m["id"], "title": m["title"], "league": m["league"],
                 "date": m.get("date", ""), "status": m.get("status", "upcoming")}
                for m in match_data
            ],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        if is_async:
            await redis.setex("match_schedule:all", 3600, schedule_payload)
        else:
            redis.setex("match_schedule:all", 3600, schedule_payload)
        keys_written += 1

        # 3. Set last run timestamp
        if is_async:
            await redis.set("harvester:last_run", datetime.now(timezone.utc).isoformat())
        else:
            redis.set("harvester:last_run", datetime.now(timezone.utc).isoformat())
        keys_written += 1

        logger.info("harvester.redis_pushed", keys_written=keys_written)
    except Exception as exc:
        logger.warning("harvester.redis_push_failed", error=str(exc))
    finally:
        if is_async:
            try:
                await redis.close()
            except Exception:
                pass

    return keys_written


# ---------------------------------------------------------------------------
# Turso DB Writer
# ---------------------------------------------------------------------------

async def _seed_matches_to_turso(matches: List[Dict]) -> int:
    """Insert/update match schedule into Turso."""
    from db.connection import execute_query
    count = 0
    for m in matches:
        try:
            await execute_query(
                """INSERT OR REPLACE INTO matches (id, title, league, team_a, team_b, venue, match_date, status, prize_pool)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (m["id"], m["title"], m["league"], m.get("team_a", ""), m.get("team_b", ""),
                 m.get("venue", ""), m.get("date", ""), m.get("status", "upcoming"), m.get("prize", ""))
            )
            count += 1
        except Exception as exc:
            logger.warning("harvester.match_insert_failed", match_id=m["id"], error=str(exc))
    return count


async def _seed_intelligence_to_turso(match_id: str, intel_type: str, content: str, source: str) -> None:
    """Insert intelligence data into match_intelligence table."""
    from db.connection import execute_query
    try:
        intel_id = f"{match_id}_{intel_type}_{int(time.time())}"
        await execute_query(
            """INSERT OR REPLACE INTO match_intelligence (id, match_id, intel_type, content, source, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (intel_id, match_id, intel_type, content, source,
             datetime.now(timezone.utc).isoformat())
        )
    except Exception as exc:
        logger.warning("harvester.intel_insert_failed", match_id=match_id, error=str(exc))


# ---------------------------------------------------------------------------
# Main Harvester Loop
# ---------------------------------------------------------------------------

async def run_harvest() -> Dict[str, Any]:
    """Execute a full harvest cycle.
    
    Pipeline:
    1. Ensure DB tables exist in Turso
    2. Seed match schedule → Turso
    3. Seed player pool → Turso
    4. Scrape live intelligence (DDG + Open-Meteo) → Turso
    5. Push all data → Redis for WebSocket broadcasting
    """
    logger.info("harvester.cycle_start")
    start = time.perf_counter()

    # Step 1: Ensure DB tables exist
    from db.connection import execute_query
    try:
        await execute_query("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                league TEXT DEFAULT '',
                team_a TEXT DEFAULT '',
                team_b TEXT DEFAULT '',
                venue TEXT DEFAULT '',
                match_date TEXT DEFAULT '',
                status TEXT DEFAULT 'upcoming',
                prize_pool TEXT DEFAULT ''
            )
        """)
        await execute_query("""
            CREATE TABLE IF NOT EXISTS match_intelligence (
                id TEXT PRIMARY KEY,
                match_id TEXT NOT NULL,
                intel_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'duckduckgo',
                fetched_at TEXT DEFAULT ''
            )
        """)
        await execute_query("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                price REAL DEFAULT 0,
                predicted_points REAL DEFAULT 0,
                ownership_pct REAL DEFAULT 0,
                team TEXT DEFAULT '',
                form_score REAL DEFAULT 50,
                match_id TEXT DEFAULT '',
                status TEXT DEFAULT 'active'
            )
        """)
        logger.info("harvester.tables_ensured")
    except Exception as exc:
        logger.error("harvester.table_creation_failed", error=str(exc))
        return {"error": str(exc)}

    # Step 2: Seed match schedule
    schedule = await _get_ipl_2026_schedule()
    match_count = await _seed_matches_to_turso(schedule)
    logger.info("harvester.matches_seeded", count=match_count)

    # Step 3: Seed player pool for each match
    player_pool = _get_player_pool()
    player_count = 0
    for match in schedule:
        allowed_teams = {match.get("team_a", ""), match.get("team_b", "")}
        for player in player_pool:
            if player["team"] not in allowed_teams:
                continue
            try:
                pid = f"{player['id']}_{match['id']}"
                await execute_query(
                    """INSERT OR REPLACE INTO players
                       (id, name, role, price, predicted_points, ownership_pct, team, form_score, match_id, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')""",
                    (pid, player["name"], player["role"], player["price"],
                     player["predicted_points"], player["ownership_pct"],
                     player["team"], player.get("form_score", 50), match["id"])
                )
                player_count += 1
            except Exception as exc:
                logger.warning("harvester.player_insert_failed", player=player["id"], error=str(exc))
    logger.info("harvester.players_seeded", count=player_count)

    # Step 4: Scrape live intelligence for each match
    intel_count = 0
    intel_data: Dict[str, Dict] = {}  # Collected for Redis push
    
    for match in schedule:
        label = f"{match['team_a']} vs {match['team_b']}"
        match_intel: Dict[str, Any] = {}

        # 4a: Pitch & conditions
        pitch_results = await _ddg_search(f"{label} pitch report today cricket 2026", max_results=3)
        if pitch_results:
            content = " ".join(r["body"] for r in pitch_results)
            await _seed_intelligence_to_turso(match["id"], "pitch_report", content, "duckduckgo")
            match_intel["pitch_report"] = content[:500]
            intel_count += 1

        # 4b: Injuries & playing XI
        injury_results = await _ddg_search(f"{label} IPL injuries playing XI latest", max_results=3)
        if injury_results:
            content = " ".join(r["body"] for r in injury_results)
            await _seed_intelligence_to_turso(match["id"], "injuries", content, "duckduckgo")
            match_intel["injuries"] = content[:500]
            intel_count += 1

        # 4c: Weather
        weather = await _fetch_weather(match.get("venue", "default"))
        if "error" not in weather:
            weather_json = json.dumps(weather)
            await _seed_intelligence_to_turso(
                match["id"], "weather", weather_json, "open-meteo"
            )
            match_intel["weather"] = weather
            intel_count += 1

        # 4d: Head-to-head
        h2h_results = await _ddg_search(f"{label} head to head cricket stats recent form", max_results=3)
        if h2h_results:
            content = " ".join(r["body"] for r in h2h_results)
            await _seed_intelligence_to_turso(match["id"], "head_to_head", content, "duckduckgo")
            match_intel["head_to_head"] = content[:500]
            intel_count += 1

        intel_data[match["id"]] = match_intel

        # Small delay between matches to be respectful to DuckDuckGo
        await asyncio.sleep(1.0)

    # Step 5: Push everything to Redis for WebSocket broadcasting
    redis_keys = await _push_to_redis(schedule, intel_data)

    elapsed = time.perf_counter() - start
    result = {
        "matches": match_count,
        "players": player_count,
        "intel": intel_count,
        "redis_keys": redis_keys,
        "elapsed_s": round(elapsed, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info("harvester.cycle_complete", **result)
    return result


# ---------------------------------------------------------------------------
# Background Scheduler — runs inside FastAPI lifespan
# ---------------------------------------------------------------------------

_harvester_task: Optional[asyncio.Task] = None

async def start_background_harvester(interval_minutes: int = 30):
    """Start the harvester as a background task that runs every `interval_minutes`.
    
    Called from FastAPI lifespan. Runs the first harvest immediately,
    then repeats on the given interval.
    """
    global _harvester_task

    async def _loop():
        while True:
            try:
                logger.info("harvester.scheduled_run_start")
                result = await run_harvest()
                logger.info("harvester.scheduled_run_complete", result=result)
            except asyncio.CancelledError:
                logger.info("harvester.background_cancelled")
                break
            except Exception as exc:
                logger.error("harvester.scheduled_run_error", error=str(exc))
            
            # Wait for next interval
            await asyncio.sleep(interval_minutes * 60)

    _harvester_task = asyncio.create_task(_loop())
    logger.info("harvester.background_started", interval_min=interval_minutes)


async def stop_background_harvester():
    """Cancel the background harvester task."""
    global _harvester_task
    if _harvester_task and not _harvester_task.done():
        _harvester_task.cancel()
        try:
            await _harvester_task
        except asyncio.CancelledError:
            pass
        logger.info("harvester.background_stopped")
    _harvester_task = None


# ---------------------------------------------------------------------------
# Entry point (standalone)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from dotenv import load_dotenv
    import sys

    # Add the api directory to path so imports work
    api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, api_dir)

    load_dotenv(os.path.join(api_dir, ".env"))

    print("=" * 60)
    print("TeamGenie AI — Intelligence Harvester v2.0")
    print("=" * 60)
    print(f"Turso URL: {os.getenv('TURSO_DATABASE_URL', 'NOT SET')[:40]}...")
    print(f"Redis URL: {os.getenv('UPSTASH_REDIS_URL', 'NOT SET')[:40]}...")
    print()

    result = asyncio.run(run_harvest())
    print(f"\nHarvest complete: {json.dumps(result, indent=2)}")
