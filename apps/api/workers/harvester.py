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

def _get_ipl_2026_schedule() -> List[Dict]:
    """Return IPL 2026 match schedule for seeding."""
    return [
        {"id": "ipl_2026_01", "title": "Chennai Super Kings vs Mumbai Indians", "league": "IPL 2026",
         "team_a": "CSK", "team_b": "MI", "venue": "chepauk",
         "date": "2026-04-07T19:30:00+05:30", "status": "upcoming", "prize": "₹10 Crores"},
        {"id": "ipl_2026_02", "title": "Royal Challengers Bangalore vs KKR", "league": "IPL 2026",
         "team_a": "RCB", "team_b": "KKR", "venue": "chinnaswamy",
         "date": "2026-04-08T19:30:00+05:30", "status": "upcoming", "prize": "₹5 Crores"},
        {"id": "ipl_2026_03", "title": "Delhi Capitals vs Rajasthan Royals", "league": "IPL 2026",
         "team_a": "DC", "team_b": "RR", "venue": "feroz_shah_kotla",
         "date": "2026-04-09T19:30:00+05:30", "status": "upcoming", "prize": "₹5 Crores"},
        {"id": "ipl_2026_04", "title": "Gujarat Titans vs Punjab Kings", "league": "IPL 2026",
         "team_a": "GT", "team_b": "PBKS", "venue": "narendra_modi",
         "date": "2026-04-10T19:30:00+05:30", "status": "upcoming", "prize": "₹5 Crores"},
        {"id": "ipl_2026_05", "title": "Lucknow Super Giants vs Sunrisers Hyderabad", "league": "IPL 2026",
         "team_a": "LSG", "team_b": "SRH", "venue": "lucknow",
         "date": "2026-04-11T15:30:00+05:30", "status": "upcoming", "prize": "₹5 Crores"},
        {"id": "wc_2027_10", "title": "India vs Australia", "league": "World Cup",
         "team_a": "IND", "team_b": "AUS", "venue": "wankhede",
         "date": "2026-04-12T14:00:00+05:30", "status": "upcoming", "prize": "₹20 Crores"},
    ]


# ---------------------------------------------------------------------------
# Player Pool (realistic IPL 2026 data for seeding)
# ---------------------------------------------------------------------------

def _get_player_pool() -> List[Dict]:
    """Return a realistic player pool for match seeding."""
    return [
        {"id": "virat_kohli", "name": "Virat Kohli", "role": "batsman", "price": 10.5, "predicted_points": 85.3, "ownership_pct": 67.3, "team": "RCB", "form_score": 88},
        {"id": "rohit_sharma", "name": "Rohit Sharma", "role": "batsman", "price": 10.0, "predicted_points": 72.1, "ownership_pct": 71.5, "team": "MI", "form_score": 72},
        {"id": "jasprit_bumrah", "name": "Jasprit Bumrah", "role": "bowler", "price": 9.5, "predicted_points": 68.4, "ownership_pct": 55.2, "team": "MI", "form_score": 91},
        {"id": "ravindra_jadeja", "name": "Ravindra Jadeja", "role": "all_rounder", "price": 9.0, "predicted_points": 65.0, "ownership_pct": 42.1, "team": "CSK", "form_score": 78},
        {"id": "rishabh_pant", "name": "Rishabh Pant", "role": "wicket_keeper", "price": 9.0, "predicted_points": 60.5, "ownership_pct": 38.7, "team": "DC", "form_score": 75},
        {"id": "hardik_pandya", "name": "Hardik Pandya", "role": "all_rounder", "price": 9.0, "predicted_points": 62.0, "ownership_pct": 45.3, "team": "MI", "form_score": 69},
        {"id": "suryakumar_yadav", "name": "Suryakumar Yadav", "role": "batsman", "price": 9.0, "predicted_points": 70.2, "ownership_pct": 50.1, "team": "MI", "form_score": 82},
        {"id": "kuldeep_yadav", "name": "Kuldeep Yadav", "role": "bowler", "price": 8.5, "predicted_points": 55.3, "ownership_pct": 28.5, "team": "DC", "form_score": 70},
        {"id": "mohammed_siraj", "name": "Mohammed Siraj", "role": "bowler", "price": 8.0, "predicted_points": 50.1, "ownership_pct": 22.3, "team": "RCB", "form_score": 65},
        {"id": "axar_patel", "name": "Axar Patel", "role": "all_rounder", "price": 8.0, "predicted_points": 48.5, "ownership_pct": 18.2, "team": "DC", "form_score": 60},
        {"id": "shubman_gill", "name": "Shubman Gill", "role": "batsman", "price": 9.5, "predicted_points": 58.0, "ownership_pct": 35.6, "team": "GT", "form_score": 76},
        {"id": "ms_dhoni", "name": "MS Dhoni", "role": "wicket_keeper", "price": 8.5, "predicted_points": 45.0, "ownership_pct": 52.0, "team": "CSK", "form_score": 55},
        {"id": "ruturaj_gaikwad", "name": "Ruturaj Gaikwad", "role": "batsman", "price": 9.0, "predicted_points": 63.5, "ownership_pct": 30.2, "team": "CSK", "form_score": 80},
        {"id": "pat_cummins", "name": "Pat Cummins", "role": "bowler", "price": 9.0, "predicted_points": 58.0, "ownership_pct": 32.0, "team": "SRH", "form_score": 85},
        {"id": "rashid_khan", "name": "Rashid Khan", "role": "bowler", "price": 9.5, "predicted_points": 62.0, "ownership_pct": 40.5, "team": "GT", "form_score": 88},
        {"id": "matheesha_pathirana", "name": "Matheesha Pathirana", "role": "bowler", "price": 7.5, "predicted_points": 52.0, "ownership_pct": 12.0, "team": "CSK", "form_score": 78},
        {"id": "tristan_stubbs", "name": "Tristan Stubbs", "role": "batsman", "price": 7.0, "predicted_points": 48.0, "ownership_pct": 8.5, "team": "DC", "form_score": 73},
        {"id": "devon_conway", "name": "Devon Conway", "role": "batsman", "price": 8.0, "predicted_points": 55.0, "ownership_pct": 15.0, "team": "CSK", "form_score": 71},
        {"id": "sam_curran", "name": "Sam Curran", "role": "all_rounder", "price": 8.5, "predicted_points": 54.0, "ownership_pct": 25.0, "team": "PBKS", "form_score": 68},
        {"id": "rinku_singh", "name": "Rinku Singh", "role": "batsman", "price": 7.5, "predicted_points": 50.0, "ownership_pct": 20.0, "team": "KKR", "form_score": 74},
    ]


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
    is_async = hasattr(redis, 'setex')  # redis.asyncio vs upstash_redis

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
        if is_async and hasattr(redis, 'close'):
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
    schedule = _get_ipl_2026_schedule()
    match_count = await _seed_matches_to_turso(schedule)
    logger.info("harvester.matches_seeded", count=match_count)

    # Step 3: Seed player pool for each match
    player_pool = _get_player_pool()
    player_count = 0
    for match in schedule:
        for player in player_pool:
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
