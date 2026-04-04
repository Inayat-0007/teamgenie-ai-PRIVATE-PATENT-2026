"""
Team Generation Router — Multi-agent AI team optimization.
POST /api/team/generate → CrewAI 3-agent consensus
"""

from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional

logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class UserPreferences(BaseModel):
    favorite_players: List[str] = Field(default_factory=list, max_length=11)
    avoid_players: List[str] = Field(default_factory=list, max_length=11)


class TeamGenerateRequest(BaseModel):
    match_id: str = Field(..., min_length=1, max_length=100, description="Unique match identifier")
    budget: float = Field(default=100.0, ge=0, le=100, description="Team budget constraint (₹)")
    risk_level: str = Field(default="balanced", pattern="^(safe|balanced|aggressive)$")
    user_preferences: Optional[UserPreferences] = None


class PlayerResponse(BaseModel):
    id: str
    name: str
    role: str
    price: float
    predicted_points: float
    confidence: float = Field(ge=0, le=1)
    ownership_pct: float = Field(default=0.0, ge=0, le=100)
    form_trend: str = "stable"


class TeamReasoningResponse(BaseModel):
    budget_agent: str
    differential_agent: str
    risk_agent: str


class TeamResponse(BaseModel):
    players: List[PlayerResponse]
    captain: str
    vice_captain: str
    total_cost: float
    predicted_total: float
    risk_score: float = Field(ge=0, le=1)


class GenerateResponse(BaseModel):
    team: TeamResponse
    reasoning: TeamReasoningResponse
    generation_time_ms: int = Field(ge=0)
    cached: bool
    model_version: str = "1.0.0"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=GenerateResponse)
async def generate_team(
    request: TeamGenerateRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Generate optimal fantasy team using multi-agent AI.

    Three agents collaborate:
    1. Budget Optimizer (OR-Tools ILP solver)
    2. Differential Expert (RAG + low-ownership finder)
    3. Risk Manager (Monte Carlo simulation)
    """
    start_time = time.perf_counter()
    request_id = getattr(http_request.state, "request_id", "unknown")

    logger.info(
        "team.generate.started",
        match_id=request.match_id,
        budget=request.budget,
        risk_level=request.risk_level,
        request_id=request_id,
    )

    try:
        from services.ai_service import generate_team_with_agents

        result = await generate_team_with_agents(
            match_id=request.match_id,
            budget=request.budget,
            risk_level=request.risk_level,
            preferences=request.user_preferences.model_dump() if request.user_preferences else None,
        )

        generation_time = int((time.perf_counter() - start_time) * 1000)

        response = GenerateResponse(
            team=result["team"],
            reasoning=result["reasoning"],
            generation_time_ms=generation_time,
            cached=False,
        )

        logger.info(
            "team.generate.completed",
            match_id=request.match_id,
            generation_time_ms=generation_time,
            total_cost=result["team"]["total_cost"],
            request_id=request_id,
        )

        return response

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        )
    except Exception as exc:
        logger.error(
            "team.generate.failed",
            match_id=request.match_id,
            error=str(exc),
            request_id=request_id,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "generation_failed", "message": f"Team generation failed: {exc}"},
        )


@router.get("/history")
async def team_history(page: int = 1, limit: int = Field(default=20, ge=1, le=100)):
    """List all teams created by authenticated user."""
    # TODO: Query Turso with pagination
    return {
        "teams": [],
        "pagination": {"page": page, "limit": limit, "total": 0},
    }


@router.get("/{team_id}")
async def get_team(team_id: str):
    """Retrieve a previously generated team."""
    # TODO: Query Turso for team by ID
    raise HTTPException(status_code=404, detail="Team not found")
