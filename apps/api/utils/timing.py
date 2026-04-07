"""
Stage Timing Instrumentation — Upgrade #2 from Master Doctrine v2.0.
Provides per-stage millisecond tracking for any pipeline execution.
"""

from __future__ import annotations

import time
from contextlib import contextmanager


class RequestTimer:
    """Track execution time per-stage for any pipeline."""

    def __init__(self):
        self.stages: dict[str, float] = {}
        self._start_time = time.perf_counter()

    @contextmanager
    def stage(self, name: str):
        """Context manager that records wall-clock time for a named stage."""
        stage_start = time.perf_counter()
        yield
        elapsed = (time.perf_counter() - stage_start) * 1000
        self.stages[name] = round(elapsed, 2)

    def total_ms(self) -> float:
        """Total elapsed time since timer creation."""
        return round((time.perf_counter() - self._start_time) * 1000, 2)

    def export(self) -> dict:
        """Export timing breakdown for API response."""
        return {
            "stages_ms": dict(self.stages),
            "total_ms": self.total_ms(),
        }
