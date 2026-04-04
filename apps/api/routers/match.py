"""
Match Data Router — Live scores, upcoming matches, and WebSocket updates.
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

import structlog
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)

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

    @property
    def active_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


manager = ConnectionManager()


@router.get("/upcoming")
async def get_upcoming_matches(
    sport: str = "cricket",
    format: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
):
    """List upcoming matches with optional format filter."""
    # TODO: Query Turso for scheduled matches
    return {"matches": [], "total": 0}


@router.get("/{match_id}")
async def get_match(match_id: str):
    """Get detailed match information."""
    # TODO: Query Turso for match details
    return {"match": {"id": match_id, "status": "scheduled"}}


@router.get("/{match_id}/live")
async def get_live_score(match_id: str):
    """Get real-time match score (from Redis cache or scraper)."""
    # TODO: Return latest scraped data from Redis cache
    return {"match": {"id": match_id, "status": "live"}, "live_score": {}}


@router.websocket("/{match_id}/ws")
async def match_websocket(websocket: WebSocket, match_id: str):
    """WebSocket for real-time match updates with heartbeat."""
    await manager.connect(websocket, match_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(websocket, match_id)
