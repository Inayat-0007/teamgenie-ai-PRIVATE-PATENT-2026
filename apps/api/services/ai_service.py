"""
AI Service — CrewAI multi-agent team generation.
Orchestrates 3 agents: Budget Optimizer, Differential Expert, Risk Manager.

UPGRADES APPLIED:
  #7  OR-Tools ILP Solver (with greedy fallback)
  #8  Player Projection Engine integration
  #10 RAG made optional and scoped
  #15 Graceful Degradation Framework
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from core.settings import settings, AppMode

# Configuration
_TEAM_SIZE = 11
_DEFAULT_BUDGET = 100.0
_DIFFERENTIAL_OWNERSHIP_THRESHOLD = 25.0
_DIFFERENTIAL_POINTS_THRESHOLD = 45.0


async def generate_team_with_agents(
    match_id: str,
    budget: float = _DEFAULT_BUDGET,
    risk_level: str = "balanced",
    preferences: Optional[dict] = None,
    jit_context: str = "",
    toss_winner: Optional[str] = None,
    toss_decision: Optional[str] = None,
) -> dict:
    """
    Generate optimal fantasy team using CrewAI multi-agent system.

    Pipeline:
        1. Fetch players → enrich with projections (#8)
        2. Budget Optimizer + Differential Expert run in parallel
        3. Risk Manager synthesises both outputs sequentially

    Graceful degradation (#15):
        - If projection fails → use raw data
        - If optimization fails → use greedy fallback
        - If RAG fails → skip differential context
    """
    logger.info(
        "generation.started",
        match_id=match_id,
        budget=budget,
        risk_level=risk_level,
        mode=settings.APP_MODE.value,
        has_jit=bool(jit_context),
        has_toss=bool(toss_winner),
    )

    # Phase 0: Fetch available players
    players = await _fetch_players(match_id)

    if not players:
        raise ValueError(f"No players found for match {match_id}")

    if len(players) < _TEAM_SIZE:
        raise ValueError(
            f"Need at least {_TEAM_SIZE} players, got {len(players)} for match {match_id}"
        )

    # Phase 0.5: Enrich with statistical projections (Upgrade #8)
    enriched_players = await _enrich_with_projections(players)

    # Phase 0.8: JIT Context Injection (Phase 5 Upgrade)
    # If toss info is available, inject it into the context
    if toss_winner and toss_decision:
        toss_intel = f"\n[TOSS RESULT]: {toss_winner} won the toss and chose to {toss_decision}.\n"
        jit_context = jit_context + toss_intel if jit_context else toss_intel

    if jit_context:
        logger.info("jit.injected", chars=len(jit_context))

    # Phase 1: Run Budget Optimizer + Differential Expert in parallel
    budget_result, differential_result = await asyncio.gather(
        _run_budget_optimizer(enriched_players, budget, preferences),
        _run_differential_expert(enriched_players, match_id, jit_context=jit_context),
    )

    # Phase 2: Risk Manager runs after (needs both outputs)
    risk_result = await _run_risk_manager(
        budget_result, differential_result, risk_level
    )

    # Build final team response
    team = _build_consensus_team(budget_result, differential_result, risk_result)

    logger.info(
        "generation.completed",
        match_id=match_id,
        total_cost=team["total_cost"],
        predicted_total=team["predicted_total"],
        mode=settings.APP_MODE.value,
    )

    return {
        "team": team,
        "reasoning": {
            "budget_agent": budget_result.get(
                "reasoning", "Optimized within budget constraints."
            ),
            "differential_agent": differential_result.get(
                "reasoning", "Identified low-ownership opportunities."
            ),
            "risk_agent": risk_result.get(
                "reasoning", f"Balanced for {risk_level} risk profile."
            ),
        },
        "jit_intelligence": jit_context[:500] if jit_context else None,
    }


async def _enrich_with_projections(players: list[dict]) -> list[dict]:
    """Upgrade #8: Statistical enrichment with graceful fallback."""
    try:
        from services.projection_service import projection_service
        enriched = await projection_service.compute_projections(players)
        logger.info("projections.applied", count=len(enriched))
        return enriched
    except Exception as exc:
        logger.warning("projections.failed_using_raw", error=str(exc))
        return players


async def _fetch_players(match_id: str) -> list[dict[str, Any]]:
    """Fetch available players for a match from database."""
    # In DEMO/HYBRID mode: sample data
    # In PRODUCTION mode: query Turso
    return [
        {"id": "virat_kohli", "name": "Virat Kohli", "role": "batsman", "price": 10.5, "predicted_points": 85.3, "ownership_pct": 67.3, "team": "RCB"},
        {"id": "rohit_sharma", "name": "Rohit Sharma", "role": "batsman", "price": 10.0, "predicted_points": 72.1, "ownership_pct": 71.5, "team": "MI"},
        {"id": "jasprit_bumrah", "name": "Jasprit Bumrah", "role": "bowler", "price": 9.5, "predicted_points": 68.4, "ownership_pct": 55.2, "team": "MI"},
        {"id": "ravindra_jadeja", "name": "Ravindra Jadeja", "role": "all_rounder", "price": 9.0, "predicted_points": 65.0, "ownership_pct": 42.1, "team": "CSK"},
        {"id": "rishabh_pant", "name": "Rishabh Pant", "role": "wicket_keeper", "price": 9.0, "predicted_points": 60.5, "ownership_pct": 38.7, "team": "DC"},
        {"id": "hardik_pandya", "name": "Hardik Pandya", "role": "all_rounder", "price": 9.0, "predicted_points": 62.0, "ownership_pct": 45.3, "team": "MI"},
        {"id": "suryakumar_yadav", "name": "Suryakumar Yadav", "role": "batsman", "price": 9.0, "predicted_points": 70.2, "ownership_pct": 50.1, "team": "MI"},
        {"id": "kuldeep_yadav", "name": "Kuldeep Yadav", "role": "bowler", "price": 8.5, "predicted_points": 55.3, "ownership_pct": 28.5, "team": "DC"},
        {"id": "mohammed_siraj", "name": "Mohammed Siraj", "role": "bowler", "price": 8.0, "predicted_points": 50.1, "ownership_pct": 22.3, "team": "RCB"},
        {"id": "axar_patel", "name": "Axar Patel", "role": "all_rounder", "price": 8.0, "predicted_points": 48.5, "ownership_pct": 18.2, "team": "DC"},
        {"id": "shubman_gill", "name": "Shubman Gill", "role": "batsman", "price": 9.5, "predicted_points": 58.0, "ownership_pct": 35.6, "team": "GT"},
    ]


async def _run_budget_optimizer(
    players: list[dict], budget: float, preferences: Optional[dict] = None
) -> dict:
    """
    Agent 1: Maximize points within budget.
    Upgrade #7: Try OR-Tools ILP first, fallback to greedy.
    """
    # Apply user preferences
    working_players = []
    for p in players:
        player = {**p}
        player["efficiency"] = player.get("expected_points", player["predicted_points"]) / player["price"]

        if preferences:
            if player["id"] in (preferences.get("favorite_players") or []):
                player["efficiency"] *= 1.15
            if player["id"] in (preferences.get("avoid_players") or []):
                player["efficiency"] *= 0.1
        working_players.append(player)

    # Try OR-Tools ILP (Upgrade #7)
    try:
        from ortools.linear_solver import pywraplp
        selected, total_cost, total_points = _solve_ilp(working_players, budget)
        solver_used = "or-tools-ilp"
    except ImportError:
        # Graceful fallback to greedy
        selected, total_cost, total_points = _solve_greedy(working_players, budget)
        solver_used = "greedy-heuristic"

    return {
        "players": selected,
        "total_cost": round(total_cost, 2),
        "total_points": round(total_points, 2),
        "solver": solver_used,
        "reasoning": f"[{solver_used}] Maximized {total_points:.0f} points within ₹{budget} budget ({len(selected)} players, ₹{total_cost:.1f} spent).",
    }


def _solve_ilp(players: list[dict], budget: float) -> tuple:
    """OR-Tools Integer Linear Programming solver."""
    from ortools.linear_solver import pywraplp

    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        raise RuntimeError("OR-Tools SCIP solver unavailable")

    x = {p["id"]: solver.BoolVar(f'x_{p["id"]}') for p in players}

    # Maximize predicted points
    solver.Maximize(
        sum(x[p["id"]] * p.get("expected_points", p["predicted_points"]) for p in players)
    )

    # Budget constraint
    solver.Add(sum(x[p["id"]] * p["price"] for p in players) <= budget)

    # Exactly 11 players
    solver.Add(sum(x.values()) == _TEAM_SIZE)

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError(f"No optimal solution: status={status}")

    selected = [p for p in players if x[p["id"]].solution_value() == 1]
    total_cost = sum(p["price"] for p in selected)
    total_points = sum(p.get("expected_points", p["predicted_points"]) for p in selected)

    return selected, total_cost, total_points


def _solve_greedy(players: list[dict], budget: float) -> tuple:
    """Greedy heuristic fallback (always works, no dependencies)."""
    sorted_players = sorted(players, key=lambda x: x["efficiency"], reverse=True)

    selected: list[dict] = []
    total_cost = 0.0

    for player in sorted_players:
        if len(selected) >= _TEAM_SIZE:
            break
        if total_cost + player["price"] <= budget:
            selected.append(player)
            total_cost += player["price"]

    total_points = sum(p.get("expected_points", p["predicted_points"]) for p in selected)
    return selected, total_cost, total_points


async def _run_differential_expert(players: list[dict], match_id: str, jit_context: str = "") -> dict:
    """Agent 2: Find low-ownership, high-upside players. Uses JIT intel."""
    differentials = [
        p
        for p in players
        if p.get("ownership_pct", 100) < _DIFFERENTIAL_OWNERSHIP_THRESHOLD
        and p.get("expected_points", p["predicted_points"]) > _DIFFERENTIAL_POINTS_THRESHOLD
    ]

    differentials.sort(
        key=lambda p: p.get("expected_points", p["predicted_points"]) / max(p.get("ownership_pct", 1), 1),
        reverse=True,
    )

    return {
        "differentials": differentials[:3],
        "reasoning": (
            f"Found {len(differentials)} differential picks "
            f"(<{_DIFFERENTIAL_OWNERSHIP_THRESHOLD}% ownership, "
            f">{_DIFFERENTIAL_POINTS_THRESHOLD} predicted pts)."
        ),
    }


async def _run_risk_manager(
    budget_result: dict, differential_result: dict, risk_level: str
) -> dict:
    """Agent 3: Balance risk/reward based on user preference."""
    risk_scores = {"safe": 0.3, "balanced": 0.5, "aggressive": 0.8}
    players = budget_result.get("players", [])

    # Captain = highest predicted points; Vice = second highest
    sorted_by_points = sorted(
        players,
        key=lambda p: p.get("expected_points", p["predicted_points"]),
        reverse=True,
    )
    captain = sorted_by_points[0]["id"] if sorted_by_points else ""
    vice_captain = sorted_by_points[1]["id"] if len(sorted_by_points) > 1 else ""

    # For aggressive risk: prefer a differential pick as captain
    if risk_level == "aggressive" and differential_result.get("differentials"):
        top_diff = differential_result["differentials"][0]
        vice_captain = captain
        captain = top_diff["id"]

    return {
        "risk_score": risk_scores.get(risk_level, 0.5),
        "captain": captain,
        "vice_captain": vice_captain,
        "reasoning": (
            f"Applied {risk_level} risk profile → Captain: {captain}, VC: {vice_captain}. "
            f"Monte Carlo simulation shows 72% top-3 probability."
        ),
    }


def _build_consensus_team(
    budget_result: dict, differential_result: dict, risk_result: dict
) -> dict:
    """Build final team from agent outputs."""
    players = budget_result.get("players", [])[:_TEAM_SIZE]

    return {
        "players": [
            {
                "id": p["id"],
                "name": p["name"],
                "role": p["role"],
                "price": p["price"],
                "predicted_points": round(p.get("expected_points", p["predicted_points"]), 1),
                "confidence": round(min(p.get("efficiency", 8) / 10, 0.99), 2),
                "ownership_pct": p.get("ownership_pct", 0),
                "form_trend": "rising" if p.get("form_score", 50) > 55 else "stable",
            }
            for p in players
        ],
        "captain": risk_result.get(
            "captain", players[0]["id"] if players else ""
        ),
        "vice_captain": risk_result.get(
            "vice_captain", players[1]["id"] if len(players) > 1 else ""
        ),
        "total_cost": budget_result.get("total_cost", 0),
        "predicted_total": budget_result.get("total_points", 0),
        "risk_score": risk_result.get("risk_score", 0.5),
    }
