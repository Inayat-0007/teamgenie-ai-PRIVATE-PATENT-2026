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
# Clickbait / Spam / Prompt-Injection Filter (Security Fix 1.8)
# ---------------------------------------------------------------------------

_SPAM_PATTERNS = re.compile(
    r"(click here|subscribe|sign up|download now|you won't believe"
    r"|shocking|exclusive offer|\?!|\?\?|buy now|limited time)",
    re.IGNORECASE,
)

# Prompt injection patterns — blocks attempts to hijack LLM via scraped web content
_PROMPT_INJECTION_PATTERNS = re.compile(
    r"(ignore previous instructions|ignore all instructions|you are now"
    r"|system\s*:|assistant\s*:|forget everything|disregard|override"
    r"|act as|pretend you are|new instructions|do not follow)",
    re.IGNORECASE,
)

# HTML tag stripper
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_snippets(raw_text: str) -> str:
    """Remove HTML, clickbait, prompt injections, and normalize whitespace.
    
    Security: Scraped web content is sanitized before injection into LLM context
    to prevent prompt injection attacks via malicious web pages.
    """
    # Step 1: Strip all HTML tags
    raw_text = _HTML_TAG_RE.sub(" ", raw_text)
    
    lines = raw_text.split(".")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line or len(line) < 15:
            continue
        if _SPAM_PATTERNS.search(line):
            continue
        if _PROMPT_INJECTION_PATTERNS.search(line):
            continue
        if line.endswith("?"):
            continue
        # Truncate individual snippets to 500 chars max (prevents payload bombs)
        cleaned.append(line[:500])
    return ". ".join(cleaned[:8]) + "." if cleaned else ""


# ---------------------------------------------------------------------------
# DuckDuckGo JIT Search (Zero API Keys)
# ---------------------------------------------------------------------------

async def _ddg_search(query: str, max_results: int = 3) -> str:
    """Execute a DuckDuckGo text search and return cleaned snippets."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
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

    async def scrape_playing_xi(self, match_id: str, team_a: str = "", team_b: str = "") -> List[Dict[str, Any]]:
        """
        Master-Level JIT Roster Scraper.
        Domain-restricted search + Structural entity filtering.
        Cross-references scraped names against known player pool for real stats.
        """
        match_label = f"{team_a} vs {team_b}".strip() or match_id
        # Restricted to trusted cricket domains to avoid noise
        q = f'(site:espncricinfo.com OR site:cricbuzz.com OR site:sportskeeda.com) "{match_label}" probable playing XI today'
        
        logger.info("jit.roster_search", match_id=match_id, query=q)
        raw_intel = await _ddg_search(q, max_results=10)
        
        if not raw_intel:
            return []

        import re
        # Human Name Pattern: 2-3 capitalized words, no numbers, no dots (except initials)
        potential_names = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2}\b", raw_intel)
        
        KNOWN_TEAMS = {
            "Chennai", "Mumbai", "Bangalore", "Bengaluru", "Kolkata", "Delhi", "Rajasthan",
            "Punjab", "Hyderabad", "Gujarat", "Lucknow", "Super", "Kings", "Indians",
            "Royals", "Giants", "Titans", "Capitals", "Riders", "Knight", "Sunrisers"
        }
        
        NON_PLAYER_WORDS = {
            "Match", "Stadium", "India", "Live", "Daily", "Today", "Latest", "News", 
            "Probable", "Toss", "Report", "Pitch", "Team", "Fantasy", "Prediction", 
            "Versus", "Vs", "Result", "Venues", "IPL", "Cricketers", "Cricket", 
            "Ukraine", "Russia", "Peace", "Deal", "Breaking", "Analysis", "Players",
            "Politics", "Billion", "Deal", "Crisis", "Conflict", "World", "Ranking"
        }
        
        unique_names = []
        seen = set()
        for n in potential_names:
            words = set(re.findall(r"\w+", n))
            
            # 1. Reject if any word is a team name or stopword
            if words.intersection(KNOWN_TEAMS) or words.intersection(NON_PLAYER_WORDS):
                continue
            
            # 2. Reject if too long or looks like a title
            if len(n) > 25 or len(n.split()) > 3:
                continue
                
            # 3. Structural validation: Player names don't usually start with "The" or "A"
            if n.startswith(("The ", "A ", "In ", "At ")):
                continue

            if n.lower() not in seen:
                unique_names.append(n)
                seen.add(n.lower())

        # Defect #7 fix: Filter backup_stars by team membership
        if len(unique_names) < 11:
            logger.info("jit.padding_roster", found=len(unique_names))
            # Map team abbreviations to franchise players
            _TEAM_BACKUP_STARS: Dict[str, List[str]] = {
                "CSK": ["Ruturaj Gaikwad", "Ravindra Jadeja", "Devon Conway", "Matheesha Pathirana", "Moeen Ali"],
                "MI": ["Rohit Sharma", "Jasprit Bumrah", "Suryakumar Yadav", "Hardik Pandya", "Tim David"],
                "RCB": ["Virat Kohli", "Mohammed Siraj", "Glenn Maxwell", "Faf Du Plessis", "Dinesh Karthik"],
                "KKR": ["Rinku Singh", "Andre Russell", "Sunil Narine", "Phil Salt", "Mitchell Starc"],
                "DC": ["Rishabh Pant", "Kuldeep Yadav", "Axar Patel", "Tristan Stubbs", "Jake Fraser Mcgurk"],
                "RR": ["Sanju Samson", "Jos Buttler", "Yashasvi Jaiswal", "Yuzvendra Chahal", "Trent Boult"],
                "GT": ["Shubman Gill", "Rashid Khan", "David Miller", "Mohammed Shami", "Wriddhiman Saha"],
                "PBKS": ["Sam Curran", "Shikhar Dhawan", "Liam Livingstone", "Kagiso Rabada", "Jonny Bairstow"],
                "SRH": ["Pat Cummins", "Heinrich Klaasen", "Travis Head", "Abhishek Sharma", "Bhuvneshwar Kumar"],
                "LSG": ["Nicholas Pooran", "Quinton De Kock", "Marcus Stoinis", "Ravi Bishnoi", "Krunal Pandya"],
            }
            # Only pad with players from the two competing teams
            for team_code in [team_a.upper(), team_b.upper()]:
                stars = _TEAM_BACKUP_STARS.get(team_code, [])
                for s in stars:
                    if len(unique_names) >= 22:
                        break
                    if s.lower() not in seen:
                        unique_names.append(s)
                        seen.add(s.lower())

        names = unique_names[:22]
        
        if not names:
            return []

        # Cross-reference against known player pool for REAL stats
        from workers.harvester import _get_player_pool
        known_pool = {p["name"].lower(): p for p in _get_player_pool()}

        players = []
        teams = [team_a or "TEAM_A", team_b or "TEAM_B"]

        for i, name in enumerate(names):
            p_team = teams[0] if i < len(names) / 2 else teams[1]
            known = known_pool.get(name.lower())
            
            if known:
                # Use REAL stats from curated pool
                players.append({
                    "id": known["id"],
                    "name": known["name"],
                    "role": known["role"],
                    "price": known["price"],
                    "predicted_points": known["predicted_points"],
                    "ownership_pct": known["ownership_pct"],
                    "team": known.get("team", p_team),
                    "form_score": known.get("form_score", 50),
                    "status": "active",
                    "data_source": "curated_pool",
                })
            else:
                # Unknown player: conservative defaults, clearly tagged
                players.append({
                    "id": name.lower().replace(" ", "_"),
                    "name": name,
                    "role": "batsman",  # Default, not round-robin
                    "price": 7.0,       # Conservative base price
                    "predicted_points": 35.0,  # Below-average baseline
                    "ownership_pct": 5.0,      # Low ownership assumed
                    "team": p_team,
                    "form_score": 40,
                    "status": "active",
                    "data_source": "jit_estimated",
                })
            
        return players

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

        # Fast Speed Increase: Try reading from harvester's DB cache
        try:
            from db.connection import execute_query
            rows = await execute_query(
                "SELECT intel_type, content, fetched_at FROM match_intelligence WHERE match_id = ?",
                (match_id,)
            )
            if rows:
                intel_dict = {row[0]: row[1] for row in rows}
                # Check if we have the critical parts
                if "pitch_report" in intel_dict and "weather" in intel_dict:
                    logger.info("jit.db_cache_hit", match_id=match_id)
                    context_block = (
                        f"=== REAL-TIME INTELLIGENCE (Harvester Cache) ===\n"
                        f"[PITCH & CONDITIONS]: {intel_dict.get('pitch_report', '')}\n"
                        f"[WEATHER]: {intel_dict.get('weather', '')}\n"
                        f"[INJURIES & SQUAD NEWS]: {intel_dict.get('injuries', '')}\n"
                        f"[HEAD-TO-HEAD MATCHUPS]: {intel_dict.get('head_to_head', '')}\n"
                        f"=== END INTELLIGENCE ==="
                    )
                    _match_cache[_cache_key(match_id, "full_context")] = {
                        "data": context_block,
                        "ts": time.time(),
                    }
                    _CACHE_TTL["full_context"] = 1800
                    return context_block
        except Exception as exc:
            logger.warning("jit.db_cache_error", error=str(exc))

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
