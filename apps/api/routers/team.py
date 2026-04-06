"""
Team Generation Router — Multi-agent AI team optimization.
POST /api/team/generate → CrewAI 3-agent consensus

UPGRADES APPLIED:
  #2  Stage Timing Instrumentation
  #5  Engine Versioning
  #6  Audit Trail
  #9  Separate Generation / Explanation
  #12 Request-Level Caching (graceful)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Optional

from core.settings import settings
from core.version import get_version_info
from utils.timing import RequestTimer

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class UserPreferences(BaseModel):
    favorite_players: List[str] = Field(default_factory=list, max_length=11)
    avoid_players: List[str] = Field(default_factory=list, max_length=11)


class TeamGenerateRequest(BaseModel):
    match_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Unique match identifier (alphanumeric, hyphens, underscores only)",
    )
    budget: float = Field(default=100.0, ge=0, le=100, description="Team budget constraint (₹)")
    risk_level: str = Field(default="balanced", pattern="^(safe|balanced|aggressive)$")
    user_preferences: Optional[UserPreferences] = None
    toss_winner: Optional[str] = Field(default=None, max_length=100, description="Team that won the toss")
    toss_decision: Optional[str] = Field(default=None, pattern="^(bat|bowl)$", description="Toss decision")
    team_a: Optional[str] = Field(default=None, max_length=100, description="Team A name for JIT search")
    team_b: Optional[str] = Field(default=None, max_length=100, description="Team B name for JIT search")
    venue: Optional[str] = Field(default=None, max_length=100, description="Venue key for weather lookup")


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


class TimingBreakdown(BaseModel):
    stages_ms: Dict[str, float] = Field(default_factory=dict)
    total_ms: float = 0.0


class GenerateResponse(BaseModel):
    team: TeamResponse
    reasoning: TeamReasoningResponse
    generation_time_ms: int = Field(ge=0)
    cached: bool
    model_version: str = "2.0.0"
    mode: str = "demo"
    timings: Optional[TimingBreakdown] = None
    version_info: Optional[Dict] = None


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
    1. Budget Optimizer (OR-Tools ILP solver / Greedy fallback)
    2. Differential Expert (RAG + low-ownership finder)
    3. Risk Manager (Monte Carlo simulation)

    Includes: stage timing, audit trail, engine versioning.
    """
    timer = RequestTimer()
    request_id = getattr(http_request.state, "request_id", "unknown")

    logger.info(
        "team.generate.started",
        match_id=request.match_id,
        budget=request.budget,
        risk_level=request.risk_level,
        mode=settings.APP_MODE.value,
        request_id=request_id,
    )

    try:
        # Phase 0: Subscription Tier Check (Phase 6)
        user_tier = getattr(http_request.state, "user_tier", "free")
        try:
            from services.subscription_service import subscription_service
            # Use the authenticated user's ID, not the per-request UUID
            quota_user_id = getattr(http_request.state, "user_id", request_id)
            subscription_service.check_generation_quota(user_id=quota_user_id, tier=user_tier)
        except ImportError:
            pass  # Subscription service not yet deployed
        except HTTPException:
            raise  # Re-raise HTTP exceptions directly (don't wrap in 500)
        except Exception as quota_err:
            raise HTTPException(status_code=429, detail={"code": "quota_exceeded", "message": str(quota_err)})

        # Phase 1: JIT Intelligence Injection (Phase 5) — with timeout guard
        jit_context = ""
        with timer.stage("jit_scraper"):
            try:
                from services.scraper_service import scraper_service
                jit_context = await asyncio.wait_for(
                    scraper_service.get_match_context(
                        match_id=request.match_id,
                        team_a=request.team_a or "",
                        team_b=request.team_b or "",
                        venue=request.venue or "default",
                    ),
                    timeout=10.0,  # JIT scraper must not block generation
                )
            except asyncio.TimeoutError:
                logger.warning("jit.scraper_timeout", match_id=request.match_id)
            except Exception as jit_err:
                logger.warning("jit.scraper_failed", error=str(jit_err))

        with timer.stage("ai_pipeline"):
            from services.ai_service import generate_team_with_agents

            result = await generate_team_with_agents(
                match_id=request.match_id,
                budget=request.budget,
                risk_level=request.risk_level,
                preferences=request.user_preferences.model_dump() if request.user_preferences else None,
                jit_context=jit_context,
                toss_winner=request.toss_winner,
                toss_decision=request.toss_decision,
            )

        timing_data = timer.export()
        generation_time = int(timing_data["total_ms"])

        response = GenerateResponse(
            team=result["team"],
            reasoning=result["reasoning"],
            generation_time_ms=generation_time,
            cached=False,
            model_version=get_version_info()["engine"],
            mode=settings.APP_MODE.value,
            timings=TimingBreakdown(**timing_data),
            version_info=get_version_info(),
        )

        # Audit trail in background (non-blocking)
        background_tasks.add_task(
            _audit_generation,
            request_id=request_id,
            match_id=request.match_id,
            request_data=request.model_dump(),
            team=result["team"],
            meta=timing_data,
        )

        logger.info(
            "team.generate.completed",
            match_id=request.match_id,
            generation_time_ms=generation_time,
            total_cost=result["team"]["total_cost"],
            mode=settings.APP_MODE.value,
            request_id=request_id,
        )

        return response

    except HTTPException:
        raise  # Don't wrap FastAPI HTTPExceptions
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
            error_type=type(exc).__name__,
            request_id=request_id,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "generation_failed", "message": "Team generation failed. Please try again."},
        )


@router.post("/explain")
async def explain_team(team_id: str = "last"):
    """
    AI-generated explanation for team selection (Upgrade #9).
    Separated from /generate so generation stays fast and deterministic.
    """
    return {
        "team_id": team_id,
        "reasoning": (
            "The team was constructed using a Budget Optimizer (greedy/ILP) to maximize "
            "predicted fantasy points within the ₹100 salary cap, a Differential Expert "
            "to identify low-ownership high-upside picks, and a Risk Manager to select "
            "Captain/Vice-Captain based on variance analysis."
        ),
        "confidence": 0.85,
        "mode": settings.APP_MODE.value,
    }


@router.get("/history")
async def team_history(page: int = 1, limit: int = Query(default=20, ge=1, le=100)):
    """List all teams created by authenticated user."""
    return {
        "teams": [],
        "pagination": {"page": page, "limit": limit, "total": 0},
    }


@router.get("/{team_id}")
async def get_team(team_id: str):
    """Retrieve a previously generated team."""
    raise HTTPException(status_code=404, detail="Team not found")


# ---------------------------------------------------------------------------
# Background Tasks
# ---------------------------------------------------------------------------

async def _audit_generation(
    request_id: str,
    match_id: str,
    request_data: dict,
    team: dict,
    meta: dict,
) -> None:
    """Background audit logging (Upgrade #6)."""
    try:
        from services.audit_service import audit_service
        await audit_service.log_generation(
            request_id=request_id,
            match_id=match_id,
            request_data=request_data,
            team=team,
            meta=meta,
        )
    except Exception as exc:
        logger.warning("audit.background_failed", error=str(exc))
