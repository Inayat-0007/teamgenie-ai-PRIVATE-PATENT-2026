"""
Match Data Router — Live scores, upcoming matches, and WebSocket updates.

Data flow:
  1. Harvester writes to Turso DB + Redis
  2. REST endpoints read from Turso (persistent) with Redis fallback (fast)
  3. WebSocket endpoint reads from Redis and broadcasts to connected clients
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Thread-safe WebSocket connection manager grouped by match_id."""

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, match_id: str):
        await websocket.accept()
        async with self._lock:
            if match_id not in self._connections:
                self._connections[match_id] = []
            self._connections[match_id].append(websocket)
        logger.debug("ws.connected", match_id=match_id)

    async def disconnect(self, websocket: WebSocket, match_id: str):
        async with self._lock:
            if match_id in self._connections:
                self._connections[match_id] = [
                    ws for ws in self._connections[match_id] if ws is not websocket
                ]
                if not self._connections[match_id]:
                    del self._connections[match_id]
        logger.debug("ws.disconnected", match_id=match_id)

    async def broadcast(self, match_id: str, data: dict):
        async with self._lock:
            connections = list(self._connections.get(match_id, []))

        dead: list[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            await self.disconnect(ws, match_id)

    async def broadcast_all(self, data: dict):
        """Broadcast data to ALL connected clients across all matches."""
        async with self._lock:
            all_connections = [
                (mid, list(conns)) for mid, conns in self._connections.items()
            ]
        for match_id, connections in all_connections:
            for ws in connections:
                try:
                    await ws.send_json(data)
                except Exception:
                    await self.disconnect(ws, match_id)

    @property
    def active_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Redis helpers — read harvested data from Redis cache
# ---------------------------------------------------------------------------

async def _read_redis_key(key: str) -> Optional[str]:
    """Read a key from Redis. Returns None if unavailable."""
    import os
    url = os.getenv("UPSTASH_REDIS_URL")
    if not url:
        return None
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=3)
        val = await r.get(key)
        await r.close()
        return val
    except Exception:
        # Try Upstash REST fallback
        try:
            from upstash_redis import Redis as UpstashRedis
            rest_url = os.getenv("UPSTASH_REDIS_REST_URL", "")
            token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "") or os.getenv("UPSTASH_REDIS_TOKEN", "")
            if rest_url and token:
                r = UpstashRedis(url=rest_url, token=token)
                return r.get(key)
        except Exception:
            pass
        return None


# ---------------------------------------------------------------------------
# REST Endpoints — STATIC routes FIRST (before /{match_id} dynamic route)
# ---------------------------------------------------------------------------

@router.get("/harvester/status")
async def harvester_status():
    """Check the status of the intelligence harvester."""
    last_run = await _read_redis_key("harvester:last_run")
    return {
        "harvester": "active",
        "last_run": last_run or "never",
        "ws_connections": manager.active_count,
    }


@router.post("/harvester/trigger")
async def trigger_harvest():
    """Manually trigger a harvest cycle. Returns results when complete."""
    try:
        from workers.harvester import run_harvest
        result = await run_harvest()
        return {"status": "complete", "result": result}
    except Exception as e:
        logger.error("harvester.manual_trigger_failed", error=str(e))
        return {"status": "error", "error": str(e)}


@router.get("/upcoming")
async def get_upcoming_matches(
    sport: str = "cricket",
    format: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
):
    """List upcoming matches. Reads from Turso DB with Redis schedule cache fallback."""
    
    # Try Redis schedule cache first (fastest)
    try:
        cached_schedule = await _read_redis_key("match_schedule:all")
        if cached_schedule:
            data = json.loads(cached_schedule)
            matches = data.get("matches", [])[:limit]
            if matches:
                return {
                    "matches": matches,
                    "total": len(matches),
                    "source": "redis_cache",
                    "updated_at": data.get("updated_at"),
                }
    except Exception:
        pass

    # Try Turso DB (persistent store)
    from db.connection import execute_query
    try:
        query = "SELECT id, title, league, match_date, status, prize_pool FROM matches WHERE status='upcoming' LIMIT ?"
        rows = await execute_query(query, (limit,))
        matches = [
            {
                "id": r[0], "title": r[1], "league": r[2],
                "date": r[3], "status": r[4], "prize": r[5]
            } for r in rows
        ]
        if matches:
            return {"matches": matches, "total": len(matches), "source": "turso_db"}
    except Exception as e:
        logger.warning("match.query_failed", reason="Matches table missing or query failed", error=str(e))

    # Production fallback — dynamically dated seed data
    today = datetime.now()
    return {
        "matches": [
            {"id": "ipl_2026_01", "title": "Chennai Super Kings vs Mumbai Indians", "league": "IPL 2026", "date": today.strftime("%Y-%m-%dT19:30:00+05:30"), "status": "upcoming", "prize": "₹10 Crores"},
            {"id": "ipl_2026_02", "title": "Royal Challengers Bangalore vs KKR", "league": "IPL 2026", "date": (today + timedelta(days=1)).strftime("%Y-%m-%dT19:30:00+05:30"), "status": "upcoming", "prize": "₹5 Crores"},
            {"id": "wc_2027_10", "title": "India vs Australia", "league": "World Cup", "date": (today + timedelta(days=4)).strftime("%Y-%m-%dT14:00:00+05:30"), "status": "upcoming", "prize": "₹20 Crores"},
            {"id": "eng_aus_01", "title": "England vs Australia", "league": "The Ashes", "date": (today + timedelta(days=5)).strftime("%Y-%m-%dT10:00:00+05:30"), "status": "upcoming", "prize": "₹2 Crores"}
        ],
        "total": 4,
        "source": "fallback",
    }


@router.get("/{match_id}")
async def get_match(match_id: str):
    """Get detailed match information with intelligence data."""
    # Try Redis first (has intelligence attached by harvester)
    try:
        cached = await _read_redis_key(f"match_live:{match_id}")
        if cached:
            data = json.loads(cached)
            return {"match": data, "source": "redis_cache"}
    except Exception:
        pass

    # Try Turso DB
    from db.connection import execute_query
    try:
        query = "SELECT id, title, league, team_a, team_b, venue, match_date, status, prize_pool FROM matches WHERE id = ?"
        rows = await execute_query(query, (match_id,))
        if rows:
            r = rows[0]
            match_data = {
                "id": r[0], "title": r[1], "league": r[2],
                "team_a": r[3], "team_b": r[4], "venue": r[5],
                "date": r[6], "status": r[7], "prize": r[8],
            }
            # Fetch intelligence for this match
            try:
                intel_rows = await execute_query(
                    "SELECT intel_type, content, source, fetched_at FROM match_intelligence WHERE match_id = ?",
                    (match_id,)
                )
                intelligence = {
                    row[0]: {"content": row[1][:500], "source": row[2], "fetched_at": row[3]}
                    for row in intel_rows
                }
                match_data["intelligence"] = intelligence
            except Exception:
                match_data["intelligence"] = {}

            return {"match": match_data, "source": "turso_db"}
    except Exception:
        pass

    return {"match": {"id": match_id, "status": "scheduled"}, "source": "fallback"}


@router.get("/{match_id}/live")
async def get_live_score(match_id: str):
    """Get real-time match score from Redis (pushed by harvester)."""
    # Try Redis live data
    try:
        cached_data = await _read_redis_key(f"match_live:{match_id}")
        if cached_data:
            data = json.loads(cached_data)
            return {
                "match": {"id": match_id, "status": data.get("status", "live")},
                "live_data": data,
                "source": "redis",
            }
    except Exception as e:
        logger.warning("redis.read_failed", match_id=match_id, error=str(e))

    # Turso fallback — get latest intelligence
    from db.connection import execute_query
    try:
        rows = await execute_query(
            "SELECT intel_type, content FROM match_intelligence WHERE match_id = ? ORDER BY fetched_at DESC LIMIT 5",
            (match_id,)
        )
        if rows:
            intel = {row[0]: row[1][:300] for row in rows}
            return {
                "match": {"id": match_id, "status": "live"},
                "intelligence": intel,
                "source": "turso_db",
            }
    except Exception:
        pass

    # No live data available — return honest response instead of fake scores
    return {
        "match": {"id": match_id, "status": "no_live_data"},
        "message": "No live data available. The match may not have started yet, or live tracking is not available for this match.",
        "source": "unavailable",
    }


@router.get("/{match_id}/intelligence")
async def get_match_intelligence(match_id: str):
    """Get all harvested intelligence for a match."""
    from db.connection import execute_query
    try:
        rows = await execute_query(
            "SELECT id, intel_type, content, source, fetched_at FROM match_intelligence WHERE match_id = ? ORDER BY fetched_at DESC",
            (match_id,)
        )
        intel = [
            {
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "source": row[3],
                "fetched_at": row[4],
            }
            for row in rows
        ]
        return {"match_id": match_id, "intelligence": intel, "total": len(intel)}
    except Exception as e:
        logger.warning("match.intel_query_failed", error=str(e))
        return {"match_id": match_id, "intelligence": [], "total": 0}


@router.get("/{match_id}/players")
async def get_match_players(match_id: str):
    """Get all players for a specific match."""
    from db.connection import execute_query
    try:
        rows = await execute_query(
            "SELECT id, name, role, price, predicted_points, ownership_pct, team, form_score FROM players WHERE match_id = ? AND status = 'active' ORDER BY predicted_points DESC",
            (match_id,)
        )
        players = [
            {
                "id": row[0], "name": row[1], "role": row[2],
                "price": row[3], "predicted_points": row[4],
                "ownership_pct": row[5], "team": row[6], "form_score": row[7],
            }
            for row in rows
        ]
        return {"match_id": match_id, "players": players, "total": len(players)}
    except Exception as e:
        logger.warning("match.players_query_failed", error=str(e))
        return {"match_id": match_id, "players": [], "total": 0}


# ---------------------------------------------------------------------------
# WebSocket — Real-time match updates
# ---------------------------------------------------------------------------

@router.websocket("/{match_id}/ws")
async def match_websocket(websocket: WebSocket, match_id: str):
    """WebSocket for real-time match updates.
    
    Protocol:
      - Client sends "ping" → server replies "pong"
      - Server pushes live data from Redis every 15 seconds
      - Client can send "refresh" to force immediate data push
    """
    await manager.connect(websocket, match_id)
    
    # Background task to push Redis data periodically
    async def push_live_data():
        while True:
            try:
                cached = await _read_redis_key(f"match_live:{match_id}")
                if cached:
                    data = json.loads(cached)
                    await websocket.send_json({
                        "type": "live_update",
                        "data": data,
                    })
            except Exception:
                break
            await asyncio.sleep(15)  # Push every 15 seconds

    push_task = asyncio.create_task(push_live_data())

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "refresh":
                # Force immediate data push
                cached = await _read_redis_key(f"match_live:{match_id}")
                if cached:
                    await websocket.send_json({
                        "type": "live_update",
                        "data": json.loads(cached),
                    })
                else:
                    await websocket.send_json({
                        "type": "no_data",
                        "message": "No live data available yet",
                    })
    except WebSocketDisconnect:
        pass
    finally:
        push_task.cancel()
        await manager.disconnect(websocket, match_id)


