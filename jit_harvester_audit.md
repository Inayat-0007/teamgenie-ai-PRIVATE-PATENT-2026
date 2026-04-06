# 🔬 TeamGenie AI — JIT Harvester & Data Flow Deep Audit

**Date:** 2026-04-07 00:36 IST  
**Auditor:** 30-Year Senior AI Engineer Assessment  
**Scope:** `workers/harvester.py`, `services/scraper_service.py`, `services/ai_service.py`, `services/projection_service.py`, `services/rag_service.py`, `routers/match.py`, `middleware/rate_limit.py`, `services/cache_service.py`, `db/connection.py`  
**Mode:** READ-ONLY — No code changes, no git pushes

---

## Executive Summary

The JIT Harvester and Data Flow pipeline has **12 critical defects** across 3 severity bands. While the architectural skeleton is sound (async pipelines, proper caching layers, graceful degradation), the real-time intelligence layer is fundamentally **hallucinating data** at multiple injection points, the rate limiter has a **silent bypass**, and the harvester has a **Turso connection leak** that will crash production under load.

---

## 🔴 CRITICAL — Must Fix Before Any Production Traffic

### DEFECT 1: `harvester.py` — Turso Client Connection Leak (Memory/Socket Exhaustion)

**File:** [harvester.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/workers/harvester.py)  
**Lines:** 281-311, 332-398

Every call to `execute_query()` in `db/connection.py` creates a **new Turso HTTP client**, executes ONE batch statement, then closes it. The harvester calls `execute_query()` in a tight loop:

```
6 matches × 20 players = 120 player inserts
6 matches × 4 intel types = 24 intel inserts  
6 match inserts + 3 CREATE TABLE calls
= 153 sequential Turso client open/close cycles per harvest
```

Every 30 minutes, this fires 153 HTTP connection handshakes to Turso (TLS + auth). The `create_client()` call in `get_turso_client()` has `@retry` with 3 attempts, so worst case = **459 HTTP roundtrips** if retries trigger.

**Impact:** Under load or Turso latency spikes, this will exhaust file descriptors or trigger Turso's per-IP connection limits. The harvester will fail silently (all exceptions are caught + logged), and the platform falls back to hardcoded data.

**Fix:** Refactor `execute_query()` to use a **connection pool** (singleton client) or at minimum batch all 153 statements into a single `.batch()` call per harvest cycle.

---

### DEFECT 2: `scraper_service.py` — Player Stats Are 100% Fabricated via `hash()`

**File:** [scraper_service.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/services/scraper_service.py)  
**Lines:** 248-259

When JIT scraping returns player names, every stat is fabricated:

```python
"price": 8.0 + (hash(name) % 30) / 10.0,       # FAKE — hash-based
"predicted_points": 40 + (hash(name) % 50),      # FAKE — hash-based
"ownership_pct": 10 + (hash(name) % 60),          # FAKE — hash-based
"role": roles[i % len(roles)],                     # FAKE — round-robin
```

**Impact:** Users receive teams where "Virat Kohli" might be assigned **"wicket_keeper"** with a **price of 8.7** (his actual Dream11 price is typically 10.5+). The `predicted_points` and `ownership_pct` have zero relationship to reality. Every user decision made from this data is based on fabricated numbers.

**Severity:** This is the single most dangerous defect. The system confidently presents fiction as data.

**Fix:** Either:  
a) Strip fabricated stats and clearly label JIT-scraped rosters as "unverified names only"  
b) Cross-reference names against the seeded `_get_player_pool()` in `harvester.py` to inherit known stats  
c) Add a `data_source: "scraped_unverified"` tag so the frontend can display warnings

---

### DEFECT 3: `projection_service.py` — All Projections Are Random Numbers

**File:** [projection_service.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/services/projection_service.py)  
**Lines:** 73-78

```python
def _get_recent_scores(self, player_id: str) -> List[float]:
    seed = hash(player_id) % 10000
    rng = random.Random(seed)
    return [rng.uniform(20, 90) for _ in range(10)]  # FAKE
```

The `expected_points`, `floor`, `ceiling`, `variance`, and `form_score` enrichments are all computed from **random numbers seeded by player ID**. These are passed into the Budget Optimizer (Agent 1) as `expected_points`, which **directly controls team selection**.

**Impact:** The OR-Tools ILP solver and greedy heuristic both optimize against made-up projection numbers. The "optimal team" is optimal relative to fiction.

**Fix:** When `APP_MODE == hybrid`, query Turso for actual `form_score` from the players table (already seeded by harvester). When unavailable, fall through to the random stub but tag it with `projection_source: "stub"`.

---

### DEFECT 4: `ai_service.py` — Risk Manager Lies About Monte Carlo

**File:** [ai_service.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/services/ai_service.py)  
**Lines:** 658-662

```python
"reasoning": (
    f"Applied {risk_level} risk profile → Captain: {captain}, VC: {vice_captain}. "
    f"Monte Carlo simulation shows 72% top-3 probability."
)
```

There is **no Monte Carlo simulation**. The 72% is a hardcoded string literal. The Captain/VC selection is purely deterministic: sort by points, pick top 2.

**Impact:** This is a trust/credibility issue. Users and investors reading the API response see "Monte Carlo" and assume probabilistic modeling is running. A legal auditor would flag this as misrepresentation.

**Fix:** Either implement an actual Monte Carlo sim (simple: 1000 random samples from floor/ceiling → count how often this team ranks top-3) or change the wording to: `"Deterministic captain/VC assignment based on highest projected points."`

---

## 🟡 HIGH — Functional Defects Affecting Data Integrity

### DEFECT 5: `rate_limit.py` — Silent Bypass When Redis Is Down

**File:** [rate_limit.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/middleware/rate_limit.py)  
**Lines:** 74-79

```python
except HTTPException:
    raise
except Exception as exc:
    logger.debug("rate_limit.redis_unavailable", error=str(exc))
    return await call_next(request)  # ← PASSES THROUGH UNPROTECTED
```

When Redis is unavailable (network outage, Upstash maintenance), the rate limiter catches the exception at `debug` level and **passes every request through with zero rate limiting**. The log level is `debug`, so in production with INFO-level logging, operators won't even see warnings.

**Impact:** During Redis outages, there is literally no rate limiting. An attacker who notices this can send unlimited requests to `/api/team/generate`, burning through LLM quota and Turso connection limits.

**Fix:** Add an in-memory sliding window fallback (dict of `{ip: [timestamps]}`) when Redis is unavailable, and elevate the log to `warning`.

---

### DEFECT 6: `harvester.py` — Static Schedule, No Dynamic Match Discovery

**File:** [harvester.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/workers/harvester.py)  
**Lines:** 118-139

```python
def _get_ipl_2026_schedule() -> List[Dict]:
    return [
        {"id": "ipl_2026_01", "title": "CSK vs MI", ...},  # 6 hardcoded matches
    ]
```

The harvester only knows about **6 statically defined matches**. IPL 2026 has 74+ league-stage matches. The system will never discover new matches unless someone manually edits this function and redeploys.

**Impact:** After April 11, the system has zero upcoming matches to serve. The API returns the same 6 stale rows forever.

**Fix:** Add a DDG search query for `"IPL 2026 schedule upcoming matches this week"` at the top of `run_harvest()` and parse match titles/dates from the results. Use the static list as fallback only.

---

### DEFECT 7: `scraper_service.py` — Backup Stars Pool Contaminates JIT Data

**File:** [scraper_service.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/services/scraper_service.py)  
**Lines:** 225-236

When JIT scraping finds fewer than 11 player names, the code silently pads with `backup_stars`:

```python
backup_stars = [
    "Ruturaj Gaikwad", "Ravindra Jadeja", "Rashid Khan", ...
]
```

These stars may **not be playing in the actual match** (e.g., Rashid Khan is padded into a CSK vs MI game). The user gets a team containing players from the wrong franchise.

**Impact:** Users select players who aren't in the match 11, losing fantasy points.

**Fix:** Filter `backup_stars` by `team_a` and `team_b` parameters. Add a `"source": "jit_padded"` flag to distinguish real-scraped from fallback players.

---

### DEFECT 8: `rag_service.py` — All 4 Indexes Return Hardcoded Strings

**File:** [rag_service.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/services/rag_service.py)  
**Lines:** 100-118

```python
async def _query_player_stats(self, query, k):
    return [{"content": f"Player trending stats indicating string performance.", ...}]

async def _query_match_history(self, query, k):
    return [{"content": f"Match history indicates player excels against left-arm pace.", ...}]

async def _query_venue_data(self, query, k):
    return [{"content": f"Wankhede Stadium is historically a batting paradise.", ...}]

async def _query_news(self, query, k):
    return [{"content": f"Expected to return to the squad after recovering from a niggle.", ...}]
```

All 4 RAG indexes return **the same hardcoded string** regardless of the query. The Pinecone vector search is imported but never called (`pass` on line 105). The Tavily news API key is configured in `.env` but never used in this function.

**Impact:** The RAG pipeline claims 4-index parallel retrieval with <300ms latency, but produces zero real retrieval. The Gemini generation step synthesizes answers from static fiction.

**Fix:** Wire `_query_player_stats()` to actual Pinecone queries, `_query_news()` to Tavily API (key is available), and `_query_venue_data()` to the JIT DDG search results already fetched by the scraper.

---

## 🟢 MEDIUM — Operational Issues

### DEFECT 9: `match.py` — Live Score Endpoint Returns Hardcoded Mock

**File:** [routers/match.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/match.py)  
**Lines:** 277-288

```python
mock_score = {
    "batting_team": "CSK",
    "score": "184/4",
    "overs": "19.2",
    ...
}
return {"match": {"id": match_id, "status": "live"}, "live_score": mock_score, "source": "mock"}
```

When both Redis and Turso miss for live data, the API returns a **static CSK score of 184/4** for EVERY match ID. Any match requested shows CSK batting.

**Fix:** Return `{"status": "no_live_data", "source": "unavailable"}` instead of fake scores.

---

### DEFECT 10: `match.py` — Upcoming Matches Fallback Has Fake Dates

**File:** [routers/match.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/match.py)  
**Lines:** 187-196

```python
return {
    "matches": [
        {"id": "ipl_2026_01", "date": "Tonight, 7:30 PM IST", ...},
        ...
    ],
    "source": "fallback",
}
```

The dates are **relative strings** ("Tonight", "Tomorrow", "Friday") that were accurate on the day they were written but are permanently wrong after that day.

**Fix:** Use ISO 8601 dates from `_get_ipl_2026_schedule()` instead of natural language.

---

### DEFECT 11: `harvester.py` — Redis Dual-Client Detection Is Fragile

**File:** [harvester.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/workers/harvester.py)  
**Lines:** 216

```python
is_async = hasattr(redis, 'setex')  # redis.asyncio vs upstash_redis
```

The `hasattr(redis, 'setex')` check is unreliable because **both** `redis.asyncio` and `upstash_redis.Redis` have a `setex` method. The difference is that one is async and the other is sync. If the wrong branch executes, the code will either `await` a sync call (returns `None`) or fail to `await` an async coroutine (logs a RuntimeWarning and leaks).

**Fix:** Check `isinstance(redis, UpstashRedis)` directly, or use a wrapper class that normalizes the interface.

---

### DEFECT 12: `ai_service.py` — `_fetch_players()` DB Query Returns Raw Tuples

**File:** [ai_service.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/services/ai_service.py)  
**Lines:** 421-431

```python
db = await get_db_connection()
rows = await db.execute("SELECT * FROM players WHERE match_id = ? AND status = 'active'", [match_id])
if rows:
    players = [dict(row) for row in rows]
```

This calls `get_db_connection()` which **doesn't exist** in `db/connection.py`. The file provides `get_turso_client()` and `execute_query()`. This code path will always raise `ImportError`, causing the function to skip the DB and fall through to JIT scraping → sample data.

**Fix:** Replace with `execute_query("SELECT id, name, role, price, predicted_points, ownership_pct, team, form_score FROM players WHERE match_id = ? AND status = 'active'", (match_id,))` and map tuple rows to dicts.

---

## 📊 Data Flow Reality Map

```
USER REQUEST (/api/team/generate)
       │
       ▼
   ┌── Quota Check ──────────────────── subscription_service (stub, no-op)
   │
   ├── JIT Scraper ──────────────────── DDG search → REAL names
   │     └── Stats ──────────────────── hash() FABRICATION ❌
   │
   ├── _fetch_players()
   │     ├── DB Path ────────────────── get_db_connection() BROKEN ❌
   │     ├── JIT Web Path ───────────── scraper_service (hash stats) ❌
   │     └── Fallback ───────────────── _get_sample_players() HARDCODED ❌
   │
   ├── Projection Enrichment ────────── random.Random(seed) FABRICATION ❌
   │
   ├── Budget Optimizer ─────────────── OR-Tools/Greedy on FAKE data ⚠️
   ├── Differential Expert ──────────── Filter on FAKE ownership ⚠️
   ├── Risk Manager ─────────────────── Deterministic (claims Monte Carlo) ❌
   │
   └── Output ───────────────────────── Well-structured JSON ✅
                                         but based on fiction
```

### What IS Actually Working (Real Data):
| Component | Status | Real Data? |
|-----------|--------|-----------|
| DDG text search | ✅ Working | ✅ Real web results |
| Open-Meteo weather | ✅ Working | ✅ Real weather data |
| Turso DB write (harvester) | ✅ Working | ✅ Persists correctly |
| Redis cache push | ✅ Working | ✅ Cached correctly |
| Security middleware stack | ✅ Working | N/A |
| WebSocket connection mgr | ✅ Working | N/A |
| Match intelligence API | ✅ Working | ✅ Returns real DDG intel |

### What Is Fabricated:
| Component | Status | Source |
|-----------|--------|--------|
| Player prices | ❌ Fake | `hash(name) % 30` |
| Predicted points | ❌ Fake | `hash(name) % 50` |
| Ownership percentages | ❌ Fake | `hash(name) % 60` |
| Player roles (JIT) | ❌ Fake | `roles[i % 4]` round-robin |
| Recent scores (projections) | ❌ Fake | `random.uniform(20, 90)` |
| Monte Carlo probability | ❌ Fake | `"72%"` hardcoded string |
| RAG index results | ❌ Fake | Static strings |
| Live match scores | ❌ Fake | `"184/4"` hardcoded |

---

## Priority Fix Order

| Priority | Defect | Effort | Impact |
|----------|--------|--------|--------|
| P0 | #12 — `get_db_connection()` broken import | 15 min | Unlocks DB-sourced player data |
| P0 | #1 — Turso connection leak | 30 min | Prevents socket exhaustion |
| P0 | #2 — Hash-fabricated stats | 45 min | Stops serving fiction |
| P0 | #3 — Random projection service | 30 min | Makes optimizer meaningful |
| P1 | #5 — Rate limiter bypass | 30 min | Prevents abuse during Redis outage |
| P1 | #4 — Monte Carlo lie | 5 min | Credibility fix |
| P1 | #7 — Backup stars contamination | 15 min | Data accuracy |
| P2 | #6 — Static match schedule | 45 min | Dynamic match discovery |
| P2 | #8 — RAG stub indexes | 2 hrs | Real retrieval pipeline |
| P2 | #9 — Mock live scores | 10 min | Honest "no data" response |
| P2 | #10 — Fake fallback dates | 10 min | Correct timestamps |
| P3 | #11 — Redis client detection | 15 min | Edge case reliability |

---

> **Bottom line:** The harvester architecture is production-grade and the async patterns are excellent. But the data flowing through it is ~70% fabricated. Fix Defects #12, #1, #2, #3 in that order and you have a real system.

*Audited by Mohammed Inayat Hussain Qureshi — April 7, 2026*
