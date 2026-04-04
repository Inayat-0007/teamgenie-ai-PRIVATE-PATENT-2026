"""
Match Data Router — Live scores and match info.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from typing import Optional, List
import json

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, match_id: str):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)

    def disconnect(self, websocket: WebSocket, match_id: str):
        if match_id in self.active_connections:
            self.active_connections[match_id].remove(websocket)

    async def broadcast(self, match_id: str, data: dict):
        if match_id in self.active_connections:
            for connection in self.active_connections[match_id]:
                await connection.send_json(data)

manager = ConnectionManager()


@router.get("/upcoming")
async def get_upcoming_matches(
    sport: str = "cricket",
    format: Optional[str] = None,
    limit: int = Query(default=10, le=50),
):
    """List upcoming matches."""
    # TODO: Query Turso for scheduled matches
    return {"matches": [], "total": 0}


@router.get("/{match_id}")
async def get_match(match_id: str):
    """Get detailed match information."""
    # TODO: Query Turso for match details
    return {"match": {"id": match_id, "status": "scheduled"}}


@router.get("/{match_id}/live")
async def get_live_score(match_id: str):
    """Get real-time match updates."""
    # TODO: Return latest scraped data from Redis cache
    return {"match": {"id": match_id, "status": "live"}, "live_score": {}}


@router.websocket("/{match_id}/ws")
async def match_websocket(websocket: WebSocket, match_id: str):
    """WebSocket for real-time match updates."""
    await manager.connect(websocket, match_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Heartbeat
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
