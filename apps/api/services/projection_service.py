"""
Projection Service — Upgrade #8 from Master Doctrine v2.0.
Statistical enrichment for each player before optimization.
Computes expected points, floor, ceiling, variance, form score.

DEFECT #3 FIX: Was using random.Random(seed) for ALL projections.
Now uses the player's own data (predicted_points, form_score) as baseline,
and queries Turso for historical form when available.
"""

from __future__ import annotations

import random
import statistics
from typing import Any, Dict, List

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from core.settings import settings, AppMode


class ProjectionService:
    """
    Enrich raw player data with statistical projections.
    This is the quantitative foundation before AI reasoning.
    """

    async def compute_projections(
        self,
        players: List[Dict[str, Any]],
        match_context: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        For each player, compute:
        - expected_points (based on actual predicted_points + form adjustment)
        - floor (10th percentile — worst likely outcome)
        - ceiling (90th percentile — best likely outcome)
        - variance (consistency metric)
        - form_score (from DB or player data, NOT random)
        """
        # Try to load real form scores from Turso
        db_form_scores = await self._load_db_form_scores()

        enriched = []

        for player in players:
            pid = player.get("id", "")
            base_points = float(player.get("predicted_points", 50))
            
            # Use DB form score if available, else use player's own form_score field
            form = float(
                db_form_scores.get(pid, player.get("form_score", 50))
            )
            
            # Form adjustment: form_score > 70 = trending up, < 40 = trending down
            form_multiplier = 0.85 + (form / 100) * 0.30  # Range: 0.85 to 1.15
            expected = base_points * form_multiplier
            
            # Variance based on role (bowlers are more volatile than batsmen)
            role = player.get("role", "batsman").lower()
            role_variance = {
                "batsman": 12.0,
                "bowler": 18.0,
                "all_rounder": 15.0,
                "wicket_keeper": 14.0,
            }
            stdev = role_variance.get(role, 15.0)
            
            # Floor/ceiling from expected ± standard deviation
            floor_val = max(0, expected - stdev)
            ceiling_val = expected + stdev

            projection = {
                **player,
                "expected_points": round(expected, 2),
                "floor": round(floor_val, 2),
                "ceiling": round(ceiling_val, 2),
                "variance": round(stdev, 2),
                "form_score": round(form, 2),
                "projection_source": "db" if pid in db_form_scores else "player_data",
            }
            enriched.append(projection)

        logger.info("projections.computed", player_count=len(enriched))
        return enriched

    async def _load_db_form_scores(self) -> Dict[str, float]:
        """Load real form_score values from Turso players table.
        Returns {player_id: form_score} dict. Empty dict on failure.
        """
        if settings.APP_MODE == AppMode.DEMO:
            return {}
        try:
            from db.connection import execute_query
            rows = await execute_query(
                "SELECT id, form_score FROM players WHERE form_score IS NOT NULL LIMIT 500"
            )
            scores = {}
            for row in rows:
                # Row is a tuple: (id, form_score)
                scores[str(row[0])] = float(row[1])
            logger.info("projections.db_form_loaded", count=len(scores))
            return scores
        except Exception as exc:
            logger.debug("projections.db_form_unavailable", error=str(exc))
            return {}

    def _compute_form(self, scores: List[float]) -> float:
        """Exponentially-weighted average: recent matches count more."""
        if not scores:
            return 50.0
        weights = [2 ** i for i in range(len(scores))]
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return weighted_sum / sum(weights)


projection_service = ProjectionService()
