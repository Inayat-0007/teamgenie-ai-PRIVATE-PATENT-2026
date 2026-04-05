"""
Prometheus Metrics Endpoint — Phase 8 Production Hardening.

Exposes GET /metrics in Prometheus text format for monitoring:
  - teamgenie_requests_total (counter)
  - teamgenie_generation_duration_seconds (histogram)
  - teamgenie_active_users (gauge)
  - teamgenie_cache_hits_total (counter)
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict

from fastapi import APIRouter, Response

router = APIRouter()

# ---------------------------------------------------------------------------
# Simple In-Memory Metrics (replaced by prometheus_client in production)
# ---------------------------------------------------------------------------

_counters: Dict[str, int] = defaultdict(int)
_histograms: Dict[str, list] = defaultdict(list)
_gauges: Dict[str, float] = defaultdict(float)


def inc(name: str, labels: str = "", value: int = 1) -> None:
    """Increment a counter."""
    key = f"{name}{{{labels}}}" if labels else name
    _counters[key] += value


def observe(name: str, value: float, labels: str = "") -> None:
    """Record a histogram observation."""
    key = f"{name}{{{labels}}}" if labels else name
    _histograms[key].append(value)
    # Keep last 1000 observations only
    if len(_histograms[key]) > 1000:
        _histograms[key] = _histograms[key][-500:]


def set_gauge(name: str, value: float, labels: str = "") -> None:
    """Set a gauge value."""
    key = f"{name}{{{labels}}}" if labels else name
    _gauges[key] = value


# ---------------------------------------------------------------------------
# /metrics endpoint
# ---------------------------------------------------------------------------

@router.get("/metrics")
async def prometheus_metrics():
    """Expose metrics in Prometheus text exposition format."""
    lines = [
        "# HELP teamgenie_info TeamGenie AI platform metadata",
        '# TYPE teamgenie_info gauge',
        'teamgenie_info{version="2.0.0",phase="8"} 1',
        "",
    ]

    # Counters
    lines.append("# HELP teamgenie_requests_total Total HTTP requests")
    lines.append("# TYPE teamgenie_requests_total counter")
    for key, val in _counters.items():
        lines.append(f"teamgenie_{key} {val}")
    lines.append("")

    # Histograms (export as summary: count + sum)
    lines.append("# HELP teamgenie_generation_seconds Team generation duration")
    lines.append("# TYPE teamgenie_generation_seconds summary")
    for key, vals in _histograms.items():
        if vals:
            lines.append(f"teamgenie_{key}_count {len(vals)}")
            lines.append(f"teamgenie_{key}_sum {sum(vals):.4f}")
    lines.append("")

    # Gauges
    lines.append("# HELP teamgenie_active_connections Current active connections")
    lines.append("# TYPE teamgenie_active_connections gauge")
    for key, val in _gauges.items():
        lines.append(f"teamgenie_{key} {val}")

    body = "\n".join(lines) + "\n"
    return Response(content=body, media_type="text/plain; charset=utf-8")
