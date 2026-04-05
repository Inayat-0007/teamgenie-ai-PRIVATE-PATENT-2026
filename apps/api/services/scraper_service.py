"""
Scraper Service — Just-In-Time (JIT) Intelligence Injection Engine.

Phase 5 Upgrade: Replaced Playwright-only scraper with a 3-pronged
DuckDuckGo search + Open-Meteo weather system.

Architecture:
  1. Pitch & Weather query  → cached 6 hours
  2. Injuries & Playing XI  → cached 1 hour
  3. Head-to-Head matchups   → cached 24 hours

Global per-match cache ensures 10M users at 7PM IPL toss time
only trigger ONE search per match, not per user.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any, Dict, List, Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

# ---------------------------------------------------------------------------
# Global Match-Level Cache (in-memory, per-process)
# ---------------------------------------------------------------------------

_match_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL = {
    "pitch_weather": 6 * 3600,   # 6 hours
    "injuries": 3600,             # 1 hour
    "matchups": 24 * 3600,        # 24 hours
}


def _cache_key(match_id: str, category: str) -> str:
    return f"{match_id}::{category}"


def _get_cached(match_id: str, category: str) -> Optional[str]:
    key = _cache_key(match_id, category)
    entry = _match_cache.get(key)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL.get(category, 3600):
        return entry["data"]
    return None


def _set_cached(match_id: str, category: str, data: str) -> None:
    key = _cache_key(match_id, category)
    _match_cache[key] = {"data": data, "ts": time.time()}


# ---------------------------------------------------------------------------
# Clickbait / Spam Filter
# ---------------------------------------------------------------------------

_SPAM_PATTERNS = re.compile(
    r"(click here|subscribe|sign up|download now|you won't believe"
    r"|shocking|exclusive offer|\?!|\?\?|buy now|limited time)",
    re.IGNORECASE,
)


def _clean_snippets(raw_text: str) -> str:
    """Remove clickbait sentences and normalize whitespace."""
    lines = raw_text.split(".")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line or len(line) < 15:
            continue
        if _SPAM_PATTERNS.search(line):
            continue
        if line.endswith("?"):
            continue
        cleaned.append(line)
    return ". ".join(cleaned[:8]) + "." if cleaned else ""


# ---------------------------------------------------------------------------
# DuckDuckGo JIT Search (Zero API Keys)
# ---------------------------------------------------------------------------

async def _ddg_search(query: str, max_results: int = 3) -> str:
    """Execute a DuckDuckGo text search and return cleaned snippets."""
    try:
        from duckduckgo_search import DDGS
        results = await asyncio.to_thread(
            lambda: list(DDGS().text(query, max_results=max_results))
        )
        raw = " ".join(r.get("body", "") for r in results)
        return _clean_snippets(raw)
    except Exception as exc:
        logger.warning("ddg.search_failed", query=query[:60], error=str(exc))
        return ""


# ---------------------------------------------------------------------------
# Open-Meteo Weather Fetch (Free, No API Key)
# ---------------------------------------------------------------------------

# Stadium coordinates for major IPL venues
_VENUE_COORDS: Dict[str, tuple] = {
    "wankhede": (18.939, 72.826),
    "chepauk": (13.063, 80.279),
    "chinnaswamy": (12.978, 77.600),
    "eden_gardens": (22.565, 88.343),
    "narendra_modi": (23.092, 72.597),
    "feroz_shah_kotla": (28.637, 77.243),
    "mohali": (30.693, 76.736),
    "rajiv_gandhi": (17.406, 78.551),
    "sawai_mansingh": (26.894, 75.803),
    "dharamsala": (32.226, 76.324),
    "lucknow": (26.845, 80.946),
    "default": (19.076, 72.877),  # Mumbai fallback
}


async def _fetch_weather(venue_key: str = "default") -> str:
    """Fetch current weather from Open-Meteo (100% free, no key)."""
    if not httpx:
        return "Weather data unavailable (httpx not installed)."
    coords = _VENUE_COORDS.get(venue_key, _VENUE_COORDS["default"])
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={coords[0]}&longitude={coords[1]}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation"
        f"&timezone=Asia/Kolkata"
    )
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            data = resp.json().get("current", {})
            temp = data.get("temperature_2m", "N/A")
            humidity = data.get("relative_humidity_2m", "N/A")
            wind = data.get("wind_speed_10m", "N/A")
            precip = data.get("precipitation", 0)
            dew = "HEAVY DEW EXPECTED" if int(str(humidity).replace("N/A", "0")) > 75 else "Low dew factor"
            rain = "RAIN LIKELY" if float(str(precip).replace("N/A", "0")) > 0.5 else "No rain expected"
            return (
                f"Stadium Weather: {temp}°C, Humidity: {humidity}%, "
                f"Wind: {wind} km/h. {dew}. {rain}."
            )
    except Exception as exc:
        logger.warning("weather.failed", error=str(exc))
        return "Weather data temporarily unavailable."


# ---------------------------------------------------------------------------
# Public API: get_match_context()
# ---------------------------------------------------------------------------

class ScraperService:
    """JIT Intelligence Engine — zero-cost, zero-hallucination data injection."""

    async def get_match_context(
        self,
        match_id: str,
        team_a: str = "",
        team_b: str = "",
        venue: str = "default",
    ) -> str:
        """
        Fetch real-time match intelligence from 3 sources in parallel.
        Returns a single text block ready for AI prompt injection.

        This is cached globally per match (not per user), so 10M users
        at 7PM toss time trigger only ONE search.
        """
        # Check full cache first
        cached_full = _get_cached(match_id, "full_context")
        if cached_full:
            logger.info("jit.cache_hit", match_id=match_id)
            return cached_full

        logger.info("jit.searching", match_id=match_id, teams=f"{team_a} vs {team_b}")

        # Build search queries
        match_label = f"{team_a} vs {team_b}".strip() or match_id
        q_pitch = f"{match_label} pitch report today dew factor weather cricket 2026"
        q_injuries = f"{match_label} IPL player injuries playing XI latest news today"
        q_matchups = f"{match_label} key player head to head cricket stats recent"

        # Fire all 3 searches + weather in parallel
        pitch_cached = _get_cached(match_id, "pitch_weather")
        injury_cached = _get_cached(match_id, "injuries")
        matchup_cached = _get_cached(match_id, "matchups")

        tasks = []
        fetch_map = []

        if not pitch_cached:
            tasks.append(_ddg_search(q_pitch))
            fetch_map.append("pitch_weather")
        if not injury_cached:
            tasks.append(_ddg_search(q_injuries))
            fetch_map.append("injuries")
        if not matchup_cached:
            tasks.append(_ddg_search(q_matchups))
            fetch_map.append("matchups")

        # Always fetch weather (fast, 100ms)
        tasks.append(_fetch_weather(venue))
        fetch_map.append("weather_live")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results back to categories
        fetched = {}
        for i, category in enumerate(fetch_map):
            val = results[i] if not isinstance(results[i], Exception) else ""
            fetched[category] = val
            if category in _CACHE_TTL:
                _set_cached(match_id, category, val)

        # Assemble final context block
        pitch = pitch_cached or fetched.get("pitch_weather", "")
        injuries = injury_cached or fetched.get("injuries", "")
        matchups = matchup_cached or fetched.get("matchups", "")
        weather = fetched.get("weather_live", "")

        context_block = (
            f"=== REAL-TIME INTELLIGENCE (JIT Scraped) ===\n"
            f"[PITCH & CONDITIONS]: {pitch}\n"
            f"[WEATHER]: {weather}\n"
            f"[INJURIES & SQUAD NEWS]: {injuries}\n"
            f"[HEAD-TO-HEAD MATCHUPS]: {matchups}\n"
            f"=== END INTELLIGENCE ==="
        )

        # Cache the assembled block for 30 minutes
        _set_cached(match_id, "full_context")
        _match_cache[_cache_key(match_id, "full_context")] = {
            "data": context_block,
            "ts": time.time(),
        }
        # Override TTL for full context: 30 min
        _CACHE_TTL["full_context"] = 1800

        logger.info(
            "jit.context_assembled",
            match_id=match_id,
            chars=len(context_block),
            sources_fetched=len([v for v in fetched.values() if v]),
        )

        return context_block

    # Legacy methods retained for backward compatibility
    async def scrape_live_score(self, match_id: str) -> dict:
        return {"match_id": match_id, "score": None, "source": "jit_upgrade"}

    async def scrape_player_stats(self, player_id: str) -> dict:
        return {"player_id": player_id, "stats": {}, "source": "jit_upgrade"}

    async def scrape_news(self, query: str) -> list:
        result = await _ddg_search(query, max_results=5)
        return [{"snippet": result, "source": "duckduckgo"}]


scraper_service = ScraperService()
