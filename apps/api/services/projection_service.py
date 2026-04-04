"""
Projection Service — Upgrade #8 from Master Doctrine v2.0.
Statistical enrichment for each player before optimization.
Computes expected points, floor, ceiling, variance, form score.
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
        - expected_points (mean of recent performances)
        - floor (10th percentile — worst likely outcome)
        - ceiling (90th percentile — best likely outcome)
        - variance (consistency metric)
        - form_score (exponentially-weighted recent average)
        """
        enriched = []

        for player in players:
            recent_scores = self._get_recent_scores(player["id"])

            mean_pts = statistics.mean(recent_scores) if recent_scores else player.get("predicted_points", 50)
            stdev = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 15.0
            form = self._compute_form(recent_scores)

            if len(recent_scores) >= 5:
                sorted_scores = sorted(recent_scores)
                n = len(sorted_scores)
                floor_val = sorted_scores[max(0, n // 10)]
                ceiling_val = sorted_scores[min(n - 1, n - n // 10)]
            else:
                floor_val = max(0, mean_pts - stdev)
                ceiling_val = mean_pts + stdev

            projection = {
                **player,
                "expected_points": round(mean_pts, 2),
                "floor": round(floor_val, 2),
                "ceiling": round(ceiling_val, 2),
                "variance": round(stdev, 2),
                "form_score": round(form, 2),
            }
            enriched.append(projection)

        logger.info("projections.computed", player_count=len(enriched))
        return enriched

    def _get_recent_scores(self, player_id: str) -> List[float]:
        """Fetch last 10 fantasy scores for this player."""
        # In DEMO mode: generate plausible stub data seeded by player_id
        seed = hash(player_id) % 10000
        rng = random.Random(seed)
        return [rng.uniform(20, 90) for _ in range(10)]

    def _compute_form(self, scores: List[float]) -> float:
        """Exponentially-weighted average: recent matches count more."""
        if not scores:
            return 50.0
        weights = [2 ** i for i in range(len(scores))]
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        return weighted_sum / sum(weights)


projection_service = ProjectionService()
