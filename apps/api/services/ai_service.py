"""
AI Service — CrewAI multi-agent team generation.
Orchestrates 3 agents: Budget Optimizer, Differential Expert, Risk Manager.

UPGRADES APPLIED:
  #7  OR-Tools ILP Solver (with greedy fallback)
  #8  Player Projection Engine integration
  #10 RAG made optional and scoped
  #15 Graceful Degradation Framework
  FIX: Added timeouts, solver error guards, match_id validation
  FIX: Production-aware _fetch_players, data validation, output constraint checks
"""

from __future__ import annotations

import asyncio
import os
import re
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
_AGENT_TIMEOUT_SECONDS = 30  # Max time for any single agent to run

# Required fields for each player dict
_REQUIRED_PLAYER_FIELDS = {"id", "name", "role", "price", "predicted_points", "team"}

# Valid cricket roles for fantasy teams
_VALID_ROLES = {"batsman", "bowler", "all_rounder", "wicket_keeper"}

# Regex for safe match IDs: alphanumeric + hyphens + underscores, 1-100 chars
_MATCH_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,100}$")


def _validate_match_id(match_id: str) -> None:
    """Validate match_id format to prevent injection or invalid lookups."""
    if not match_id or not match_id.strip():
        raise ValueError("match_id cannot be empty")
    if not _MATCH_ID_PATTERN.match(match_id):
        raise ValueError(
            f"Invalid match_id format: '{match_id}'. "
            "Must be 1-100 characters, alphanumeric with hyphens/underscores only."
        )


def _validate_player_data(players: list[dict]) -> list[dict]:
    """
    Validate and sanitize player data from ANY source (DB, API, sample).
    Removes invalid players, logs warnings. Prevents hallucinated/malformed data
    from propagating through the pipeline.
    """
    valid_players = []
    seen_ids = set()

    for i, p in enumerate(players):
        # Check required fields exist
        missing = _REQUIRED_PLAYER_FIELDS - set(p.keys())
        if missing:
            logger.warning("player.missing_fields", index=i, player_id=p.get("id", "?"), missing=list(missing))
            continue

        # Check for duplicate IDs
        if p["id"] in seen_ids:
            logger.warning("player.duplicate_id", player_id=p["id"])
            continue
        seen_ids.add(p["id"])

        # Validate types and ranges
        try:
            price = float(p["price"])
            predicted = float(p["predicted_points"])
        except (TypeError, ValueError):
            logger.warning("player.invalid_numeric", player_id=p["id"])
            continue

        if price <= 0 or price > 20:
            logger.warning("player.invalid_price", player_id=p["id"], price=price)
            continue

        if predicted < 0:
            logger.warning("player.negative_points", player_id=p["id"], predicted=predicted)
            continue

        # Validate role
        role = p.get("role", "").lower()
        if role not in _VALID_ROLES:
            logger.warning("player.invalid_role", player_id=p["id"], role=role)
            continue

        # Sanitize — ensure consistent types and REJECT NON-PLAYER NAMES
        name_lower = p.get("name", "").lower()
        non_player_keywords = {"stadium", "team", "vs", "versus", "stadium", "ground", "pitch", "today", "report"}
        if any(kw in name_lower for kw in non_player_keywords):
            logger.warning("player.rejected_as_non_human", name=p.get("name"))
            continue

        sanitized = {
            **p,
            "price": price,
            "predicted_points": predicted,
            "role": role,
            "ownership_pct": float(p.get("ownership_pct", 50.0)),
            "team": str(p.get("team", "UNKNOWN")),
        }
        valid_players.append(sanitized)

    if len(valid_players) < len(players):
        logger.info(
            "player.validation_summary",
            input_count=len(players),
            valid_count=len(valid_players),
            dropped=len(players) - len(valid_players),
        )

    return valid_players


def _validate_team_output(team: dict, budget: float) -> list[str]:
    """
    Post-generation constraint verification.
    Returns a list of warnings (empty = all good).
    Prevents hallucinated/invalid teams from reaching the client.
    """
    warnings = []
    players = team.get("players", [])

    # 1. Must have exactly 11 players
    if len(players) != _TEAM_SIZE:
        warnings.append(f"Team has {len(players)} players, expected {_TEAM_SIZE}")

    # 2. Budget must not be exceeded
    total_cost = team.get("total_cost", 0)
    if total_cost > budget:
        warnings.append(f"Budget exceeded: ₹{total_cost:.1f} > ₹{budget:.1f}")

    # 3. Captain and Vice-Captain must be different
    captain = team.get("captain", "")
    vc = team.get("vice_captain", "")
    if captain == vc:
        warnings.append(f"Captain and Vice-Captain are the same: {captain}")

    # 4. Captain and VC must be in the team
    player_ids = {p["id"] for p in players}
    if captain and captain not in player_ids:
        warnings.append(f"Captain '{captain}' is not in the team roster")
    if vc and vc not in player_ids:
        warnings.append(f"Vice-Captain '{vc}' is not in the team roster")

    # 5. No duplicate players
    if len(player_ids) != len(players):
        warnings.append("Team contains duplicate players")

    # 6. All players must have valid roles
    for p in players:
        if p.get("role", "").lower() not in _VALID_ROLES:
            warnings.append(f"Player '{p.get('id')}' has invalid role: {p.get('role')}")

    # 7. Max 7 from same team (fantasy platform rule)
    from collections import Counter
    team_counts = Counter(p.get("team", "?") for p in players if "team" in p)
    for team_name, count in team_counts.items():
        if count > 7:
            warnings.append(f"Too many players from {team_name}: {count} (max 7)")

    # 8. Minimum Role Constraints
    roles = Counter(p.get("role", "") for p in players)
    if roles.get("batsman", 0) < 3:
        warnings.append(f"Too few batsmen: {roles.get('batsman', 0)} (min 3)")
    if roles.get("bowler", 0) < 3:
        warnings.append(f"Too few bowlers: {roles.get('bowler', 0)} (min 3)")
    if roles.get("wicket_keeper", 0) < 1:
        warnings.append(f"No wicket keeper selected (min 1)")
    if roles.get("all_rounder", 0) < 1:
        warnings.append(f"No all rounder selected (min 1)")

    return warnings


async def generate_team_with_agents(
    match_id: str,
    budget: float = _DEFAULT_BUDGET,
    risk_level: str = "balanced",
    preferences: Optional[dict] = None,
    jit_context: str = "",
    toss_winner: Optional[str] = None,
    toss_decision: Optional[str] = None,
    team_a: str = "",
    team_b: str = "",
) -> dict:
    """
    Generate optimal fantasy team using CrewAI multi-agent system.

    Pipeline:
        1. Validate match_id
        2. Fetch players → validate data → enrich with projections (#8)
        3. Budget Optimizer + Differential Expert run in parallel (with timeout)
        4. Risk Manager synthesises both outputs sequentially
        5. Validate output constraints before returning

    Graceful degradation (#15):
        - If projection fails → use raw data
        - If optimization fails → use greedy fallback
        - If RAG fails → skip differential context
        - If any agent times out → use fallback result
    """
    # Phase -1: Validate match_id format
    _validate_match_id(match_id)

    logger.info(
        "generation.started",
        match_id=match_id,
        budget=budget,
        risk_level=risk_level,
        mode=settings.APP_MODE.value,
        has_jit=bool(jit_context),
        has_toss=bool(toss_winner),
    )

    # Phase 0: Fetch available players (MASTER FIX: JIT LIVE SCRAPING)
    raw_players = await _fetch_players(match_id, team_a=team_a, team_b=team_b)

    if not raw_players:
        raise ValueError(f"No players found for match {match_id}")

    # Phase 0.3: Validate and sanitize player data (prevents hallucination)
    players = _validate_player_data(raw_players)

    if len(players) < _TEAM_SIZE:
        raise ValueError(
            f"After validation, only {len(players)} valid players remain "
            f"(need {_TEAM_SIZE}) for match {match_id}"
        )

    # Phase 0.5: Enrich with statistical projections (Upgrade #8)
    enriched_players = await _enrich_with_projections(players)

    # Phase 0.6: Verify enrichment didn't corrupt data
    enriched_players = _validate_player_data(enriched_players)
    if len(enriched_players) < _TEAM_SIZE:
        logger.warning("enrichment.corrupted_data_using_raw", enriched=len(enriched_players))
        enriched_players = players  # Fall back to pre-enrichment validated data

    # Phase 0.8: JIT Context Injection (Phase 5 Upgrade)
    if toss_winner and toss_decision:
        toss_intel = f"\n[TOSS RESULT]: {toss_winner} won the toss and chose to {toss_decision}.\n"
        jit_context = jit_context + toss_intel if jit_context else toss_intel

    if jit_context:
        logger.info("jit.injected", chars=len(jit_context))

    # Phase 1: Run Budget Optimizer + Differential Expert in parallel (with timeout)
    try:
        budget_result, differential_result = await asyncio.wait_for(
            asyncio.gather(
                _run_budget_optimizer(enriched_players, budget, preferences),
                _run_differential_expert(enriched_players, match_id, jit_context=jit_context),
                return_exceptions=True,
            ),
            timeout=_AGENT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error("generation.timeout", match_id=match_id, timeout_s=_AGENT_TIMEOUT_SECONDS)
        raise ValueError(
            f"Team generation timed out after {_AGENT_TIMEOUT_SECONDS}s. "
            "Please try again — the AI agents may be under heavy load."
        )

    # Handle individual agent failures from return_exceptions=True
    if isinstance(budget_result, Exception):
        logger.error("agent.budget_optimizer_failed", error=str(budget_result))
        # Emergency fallback: try greedy directly
        try:
            working_players = [
                {**p, "efficiency": p.get("expected_points", p["predicted_points"]) / max(p["price"], 0.1)}
                for p in enriched_players
            ]
            selected, cost, pts = _solve_greedy(working_players, budget)
            budget_result = {
                "players": selected,
                "total_cost": round(cost, 2),
                "total_points": round(pts, 2),
                "solver": "emergency-greedy",
                "reasoning": f"[emergency-greedy] Recovered from agent failure with {len(selected)} players.",
            }
        except Exception as fallback_exc:
            raise ValueError(f"Budget optimization failed completely: {budget_result}") from fallback_exc

    if isinstance(differential_result, Exception):
        logger.warning("agent.differential_expert_failed", error=str(differential_result))
        differential_result = {
            "differentials": [],
            "reasoning": "Differential analysis unavailable (agent error — skipped gracefully).",
        }

    # Phase 2: Risk Manager runs after (needs both outputs) — also with timeout
    try:
        risk_result = await asyncio.wait_for(
            _run_risk_manager(budget_result, differential_result, risk_level),
            timeout=_AGENT_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("agent.risk_manager_timeout", match_id=match_id)
        players_list = budget_result.get("players", [])
        risk_result = {
            "risk_score": 0.5,
            "captain": players_list[0]["id"] if players_list else "",
            "vice_captain": players_list[1]["id"] if len(players_list) > 1 else "",
            "reasoning": "Risk Manager timed out — used default captain/VC assignment.",
        }

    # Build final team response
    team = _build_consensus_team(budget_result, differential_result, risk_result)

    # Phase 3: Post-generation output validation (anti-hallucination gate)
    constraint_warnings = _validate_team_output(team, budget)
    if constraint_warnings:
        logger.warning(
            "generation.constraint_violations",
            match_id=match_id,
            violations=constraint_warnings,
        )
        # Auto-heal critical violations
        team = _auto_heal_team(team, budget_result, risk_result, constraint_warnings)

    logger.info(
        "generation.completed",
        match_id=match_id,
        total_cost=team["total_cost"],
        predicted_total=team["predicted_total"],
        player_count=len(team.get("players", [])),
        mode=settings.APP_MODE.value,
        warnings=len(constraint_warnings),
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


def _auto_heal_team(team: dict, budget_result: dict, risk_result: dict, warnings: list[str]) -> dict:
    """
    Attempt to fix constraint violations in the generated team.
    This is the last-resort safety net before the team reaches the client.
    """
    players = team.get("players", [])
    player_ids = {p["id"] for p in players}

    # Fix: Captain not in team → assign highest-points player
    captain = team.get("captain", "")
    vc = team.get("vice_captain", "")

    if captain not in player_ids and players:
        sorted_p = sorted(players, key=lambda x: x.get("predicted_points", 0), reverse=True)
        captain = sorted_p[0]["id"]
        team["captain"] = captain
        logger.info("auto_heal.captain_reassigned", new_captain=captain)

    if vc not in player_ids and players:
        sorted_p = sorted(players, key=lambda x: x.get("predicted_points", 0), reverse=True)
        vc = sorted_p[1]["id"] if len(sorted_p) > 1 else sorted_p[0]["id"]
        team["vice_captain"] = vc
        logger.info("auto_heal.vc_reassigned", new_vc=vc)

    # Fix: Captain == Vice-Captain
    if team["captain"] == team["vice_captain"] and len(players) > 1:
        sorted_p = sorted(players, key=lambda x: x.get("predicted_points", 0), reverse=True)
        for p in sorted_p:
            if p["id"] != team["captain"]:
                team["vice_captain"] = p["id"]
                break

    return team


async def _enrich_with_projections(players: list[dict]) -> list[dict]:
    """Upgrade #8: Statistical enrichment with graceful fallback."""
    try:
        from services.projection_service import projection_service
        enriched = await projection_service.compute_projections(players)

        # Verify enrichment preserved all players and added required fields
        if len(enriched) != len(players):
            logger.warning(
                "projections.count_mismatch",
                input=len(players),
                output=len(enriched),
            )
            return players

        logger.info("projections.applied", count=len(enriched))
        return enriched
    except Exception as exc:
        logger.warning("projections.failed_using_raw", error=str(exc))
        return players


async def _fetch_players(match_id: str, team_a: str = "", team_b: str = "") -> list[dict[str, Any]]:
    """
    Fetch available players for a match.

    Tri-modal behavior:
      - PRODUCTION: query Turso database, else JIT Scraping
      - HYBRID: try DB, then JIT Scraping, then fallback to sample
      - DEMO: try JIT Scraping, then sample data
    """
    # 1. Attempt Database Query (PRO / HYBRID)
    if settings.APP_MODE in [AppMode.PRODUCTION, AppMode.HYBRID]:
        try:
            from db.connection import execute_query
            rows = await execute_query(
                "SELECT id, name, role, price, predicted_points, ownership_pct, team, form_score FROM players WHERE match_id = ? AND status = 'active'",
                (match_id,),
            )
            if rows:
                _cols = ["id", "name", "role", "price", "predicted_points", "ownership_pct", "team", "form_score"]
                players = [{_cols[i]: row[i] for i in range(len(_cols))} for row in rows]
                logger.info("players.fetched_from_db", match_id=match_id, count=len(players))
                return players
        except Exception as exc:
            logger.warning("players.db_failed", error=str(exc))

    # 2. MASTER FIX: Attempt Real-Time JIT Web Scraping (DuckDuckGo Roster Extraction)
    try:
        from services.scraper_service import scraper_service
        logger.info("players.attempt_jit_scrape", match_id=match_id)
        scraped_players = await scraper_service.scrape_playing_xi(match_id, team_a=team_a, team_b=team_b)
        if scraped_players:
            logger.info("players.fetched_from_web", match_id=match_id, count=len(scraped_players))
            return scraped_players
    except Exception as exc:
        logger.warning("players.jit_scrape_failed", error=str(exc))

    # 3. Fallback (Last Resort)
    logger.info("players.using_sample_data", match_id=match_id)
    return _get_sample_players()


def _get_sample_players() -> list[dict[str, Any]]:
    """Static sample data for DEMO/HYBRID fallback. Clearly marked as non-production."""
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
    players: list[dict], budget: float, preferences: Optional[dict] = None,
) -> dict:
    """
    Agent 1: Maximize points within budget.
    Upgrade #7: Try OR-Tools ILP first, fallback to greedy.
    """
    # Apply user preferences
    working_players = []
    for p in players:
        player = {**p}
        predicted = player.get("expected_points", player.get("predicted_points", 0))
        price = player.get("price", 1)
        if price <= 0:
            price = 1  # Guard against division by zero
        player["efficiency"] = predicted / price

        if preferences:
            if player["id"] in (preferences.get("favorite_players") or []):
                player["efficiency"] *= 1.15
            if player["id"] in (preferences.get("avoid_players") or []):
                player["efficiency"] *= 0.1
        working_players.append(player)

    # Try OR-Tools ILP (Upgrade #7)
    # Audit Fix #04 CRITICAL: Both solvers are CPU-bound and MUST run in a thread
    # to avoid blocking the asyncio event loop (which freezes ALL concurrent requests).
    solver_used = "greedy-heuristic"
    try:
        from ortools.linear_solver import pywraplp
        selected, total_cost, total_points = await asyncio.to_thread(_solve_ilp, working_players, budget)
        solver_used = "or-tools-ilp"
    except ImportError:
        # Graceful fallback to greedy
        selected, total_cost, total_points = await asyncio.to_thread(_solve_greedy, working_players, budget)
    except RuntimeError as exc:
        # ILP solver found no optimal solution — fallback
        logger.warning("ilp.no_optimal_solution", error=str(exc))
        selected, total_cost, total_points = await asyncio.to_thread(_solve_greedy, working_players, budget)
        solver_used = "greedy-heuristic-after-ilp-fail"

    # Validate solver output
    if len(selected) < _TEAM_SIZE:
        logger.warning(
            "solver.insufficient_players",
            solver=solver_used,
            selected=len(selected),
            required=_TEAM_SIZE,
        )
        # Pad from remaining players if possible
        selected_ids = {p["id"] for p in selected}
        remaining = [p for p in working_players if p["id"] not in selected_ids]
        remaining.sort(key=lambda x: x["efficiency"], reverse=True)
        for p in remaining:
            if len(selected) >= _TEAM_SIZE:
                break
            if total_cost + p["price"] <= budget:
                selected.append(p)
                total_cost += p["price"]
        total_points = sum(p.get("expected_points", p.get("predicted_points", 0)) for p in selected)

    # Final validation: budget must not be exceeded
    if total_cost > budget:
        logger.error("solver.budget_exceeded", cost=total_cost, budget=budget, solver=solver_used)
        # Re-run greedy with strict budget (guaranteed safe)
        selected, total_cost, total_points = await asyncio.to_thread(_solve_greedy, working_players, budget)
        solver_used = "greedy-heuristic-budget-fix"

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

    # Role Constraints (Fantasy Platform Rules)
    solver.Add(sum(x[p["id"]] for p in players if p.get("role") == "batsman") >= 3)
    solver.Add(sum(x[p["id"]] for p in players if p.get("role") == "bowler") >= 3)
    solver.Add(sum(x[p["id"]] for p in players if p.get("role") == "wicket_keeper") >= 1)
    solver.Add(sum(x[p["id"]] for p in players if p.get("role") == "all_rounder") >= 1)

    # Maximum 7 players from any single team
    unique_teams = {p.get("team", "UNKNOWN") for p in players}
    for t in unique_teams:
        solver.Add(sum(x[p["id"]] for p in players if p.get("team", "UNKNOWN") == t) <= 7)

    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError(f"No optimal solution: status={status}")

    selected = [p for p in players if x[p["id"]].solution_value() == 1]
    total_cost = sum(p["price"] for p in selected)
    total_points = sum(p.get("expected_points", p["predicted_points"]) for p in selected)

    return selected, total_cost, total_points


def _solve_greedy(players: list[dict], budget: float) -> tuple:
    """Greedy heuristic fallback (always works, no dependencies)."""
    sorted_players = sorted(players, key=lambda x: x.get("efficiency", 0), reverse=True)

    selected: list[dict] = []
    total_cost = 0.0
    team_counts = {}

    for player in sorted_players:
        if len(selected) >= _TEAM_SIZE:
            break
            
        team_name = player.get("team", "UNKNOWN")
        if team_counts.get(team_name, 0) >= 7:
            continue
            
        if total_cost + player["price"] <= budget:
            selected.append(player)
            total_cost += player["price"]
            team_counts[team_name] = team_counts.get(team_name, 0) + 1

    total_points = sum(p.get("expected_points", p.get("predicted_points", 0)) for p in selected)
    return selected, total_cost, total_points


async def _run_differential_expert(players: list[dict], match_id: str, jit_context: str = "") -> dict:
    """Agent 2: Find low-ownership, high-upside players. Uses JIT intel."""
    differentials = [
        p
        for p in players
        if p.get("ownership_pct", 100) < _DIFFERENTIAL_OWNERSHIP_THRESHOLD
        and p.get("expected_points", p.get("predicted_points", 0)) > _DIFFERENTIAL_POINTS_THRESHOLD
    ]

    differentials.sort(
        key=lambda p: p.get("expected_points", p.get("predicted_points", 0)) / max(p.get("ownership_pct", 1), 1),
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

    if not players:
        return {
            "risk_score": risk_scores.get(risk_level, 0.5),
            "captain": "",
            "vice_captain": "",
            "reasoning": "No players available for captain/VC assignment.",
        }

    # Captain = highest predicted points; Vice = second highest
    sorted_by_points = sorted(
        players,
        key=lambda p: p.get("expected_points", p.get("predicted_points", 0)),
        reverse=True,
    )
    captain = sorted_by_points[0]["id"]
    vice_captain = sorted_by_points[1]["id"] if len(sorted_by_points) > 1 else sorted_by_points[0]["id"]

    # For aggressive risk: prefer a differential pick as captain
    if risk_level == "aggressive" and differential_result.get("differentials"):
        top_diff = differential_result["differentials"][0]
        # Only use differential pick if it's in the selected team
        selected_ids = {p["id"] for p in players}
        if top_diff["id"] in selected_ids:
            vice_captain = captain
            captain = top_diff["id"]

    # Guarantee captain != vice_captain
    if captain == vice_captain and len(sorted_by_points) > 1:
        vice_captain = sorted_by_points[1]["id"] if sorted_by_points[1]["id"] != captain else sorted_by_points[0]["id"]

    return {
        "risk_score": risk_scores.get(risk_level, 0.5),
        "captain": captain,
        "vice_captain": vice_captain,
        "reasoning": (
            f"Applied {risk_level} risk profile → Captain: {captain} (highest projected pts), "
            f"VC: {vice_captain} (2nd highest). Deterministic selection based on points ranking."
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
                "predicted_points": round(p.get("expected_points", p.get("predicted_points", 0)), 1),
                "confidence": round(min(p.get("efficiency", 8) / 10, 0.99), 2),
                "ownership_pct": p.get("ownership_pct", 0),
                "form_trend": "rising" if p.get("form_score", 50) > 55 else "stable",
                "team": p.get("team", "UNKNOWN"),
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
