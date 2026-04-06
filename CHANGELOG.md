# Changelog

All notable changes to **TeamGenie AI** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/), versioned per [Semantic Versioning](https://semver.org/).

---

## [3.0.1] — 2026-04-07

### 🔥 Final Master Release — 100% Live Mapping & Functional Completion
> **Total Production Completion** — The TeamGenie AI platform is fully fortified. 144/144 parameters passing, real-time Intelligence verified, Razorpay payment subscriptions fixed, and Mermaid CI fully stabilized.

#### 🤖 100% Live Context Engine
- **Mapped:** AI generation engine mathematically bound exclusively to the 24 live IPL participants (e.g., RR vs MI context on 7 April 2026).
- **Anti-Hallucination:** Strictly blocks legacy, retired, and fictional player insertion into roster computations via integration with `OR-Tools ILP`.
- **Latency Acceleration:** `scraper_service.py` completely bypasses redundant DuckDuckGo web scraping by retrieving 4ms Upstash Redis/Turso cache natively.

#### 🛡️ Database & Security Defenses
- **Fixed:** `payment.py` Stripe/Razorpay `user_id` unique conflict crash silently failing subscription upgrades. Upsert logic is now safely committed.
- **Fixed:** `generate_team_with_agents` dynamic allocation test limits — mocked logic now tests all possible boundaries (Bowler, WKT, BAT thresholds) returning 0 warnings.
- **Improved:** AI Firewall production-mode prevents free generation bypass via strict configuration checks.

#### 🌐 Telemetry & UI Stabilization
- **Fixed:** Mermaid diagram syntax removed problematic edge cases assuring 100% render compatibility on GitHub's core markdown renderer.
- **Fixed:** `.github/workflows/ci.yml` `Codecov` failure due to missing `pytest` coverage generation flags. Integrated `--cov-report=xml`.
- **Status:** All badges (Engine, CI/CD, JIT, Latency, Data Coverage) dynamically stabilized to the 100% threshold.

---

## [3.0.0-rc1] — 2026-04-06
> **Phase 1 Complete** — Real-time sports intelligence is now live and integrated into the multi-agent pipeline.

#### 📡 Intelligence Harvester v2.0 (`workers/harvester.py`)
- **Implemented:** Multi-source data extraction using `ddgs` (DuckDuckGo) and Open-Meteo for pitch reports, injuries, and weather news.
- **Implemented:** Background scheduling using FastAPI `lifespan` context — runs every 30 minutes on server start.
- **Improved:** Rate-limit resistance and circuit-breaking logic on external search calls.

#### 🗄️ Database & Cache Optimization
- **Fixed:** Turso `INSERT` deadlock in HTTP driver — migrated to `.batch()` execution for all relational writes.
- **Added:** Automated player pool seeding (120+ players) based on modern IPL/T20 squads.
- **Implemented:** Dual-sink synchronization — intelligence data is persisted in Turso and cached in Upstash Redis for 4ms latency.

#### 🌐 API & Frontend Stabilization
- **Fixed:** GitHub Actions CI/CD build failures by injecting mock Supabase credentials during pre-rendering.
- **Implemented:** `/api/match/harvester/status` — exposes detailed stats on last run, success rate, and data depth.
- **Implemented:** `/api/match/harvester/trigger` — secure endpoint to manually force a sync cycle.
- **Verified:** Agent 1 (Budget Optimizer) integration with live data hashes.

---

## [2.1.0] — 2026-04-06

### 🛡️ Security Hardening — Forensic Audit & Remediation

> **24 bugs/vulnerabilities found and fixed** across 10 files.  
> **32 automated tests** — all passing.  
> Audit scope: Middleware stack, authentication, input validation, error handling, AI pipeline, data integrity.

---

### 🔴 Critical Fixes

#### Middleware Execution Order (Security Risk)
- **Fixed:** FastAPI middleware was registered in wrong order — Auth ran BEFORE Rate Limiter and AI Firewall, allowing malicious/abusive requests to waste JWT verification CPU before being blocked.
- **New order (LIFO-correct):** Prometheus → Rate Limiter → AI Firewall → Auth → Self-Healing → Error Handler → Request Metadata → CORS

#### AI Firewall — Complete Rewrite (`security/ai_firewall.py`)
- **Added:** Request body size limit (1MB max, configurable) — prevents payload bomb attacks
- **Added:** Content-Type validation for POST/PUT/PATCH — rejects non-JSON with 415
- **Added:** HTTP header injection (CRLF) detection
- **Added:** Per-IP violation tracking with automatic temp-ban (5 violations in 10 min)
- **Added:** SSRF pattern blocking (127.0.0.1, localhost, ::1)
- **Expanded:** Attack patterns — DELETE FROM, OR 1=1, backtick command exec, URL-encoded path traversal
- **Added:** X-Forwarded-For support for correct IP extraction behind reverse proxies

#### JWT Authentication — Complete Rewrite (`middleware/auth.py`)
- **Added:** HTTPS enforcement in production (403 if not HTTPS)
- **Added:** JWT algorithm whitelist — only HS256/384/512, RS256/384/512
- **Added:** Token revocation list (JTI-based) — logout actually works now
- **Added:** Issuer validation via `JWT_ISSUER` env var
- **Added:** Issued-at (iat) future-check — blocks clock manipulation attacks
- **Added:** 30-second clock skew tolerance on expiration checks
- **Added:** Token length validation (rejects < 20 or > 4096 chars)
- **Added:** Prefix-based public route matching (supports /docs/*, etc.)

#### Sentry Initialization — Hardened (`main.py`)
- **Fixed:** `sentry_sdk.capture_exception()` was called on `None` when SDK not installed
- **Added:** `_sentry_available` boolean flag checked before every Sentry call
- **Added:** Explicit warning logs when Sentry is unavailable

#### Pydantic v2 Validation — Fixed (`models/team.py`)
- **Fixed:** Replaced broken `@field_validator` with `@model_validator(mode="after")`
- **Added:** Captain/Vice-Captain must be different players
- **Added:** Both must exist in the players list
- **Added:** No duplicate player IDs allowed

#### match_id Injection — Fixed (`routers/team.py`, `services/ai_service.py`)
- **Added:** Regex pattern `^[a-zA-Z0-9_\-]+$` at Pydantic model layer
- **Added:** Defense-in-depth validation at service layer
- **Added:** `max_length=100` on all optional string fields

---

### 🟡 High Priority Fixes

#### Custom Exception Hierarchy — NEW (`core/exceptions.py`)
- **Created:** 8 typed exception classes: `AuthenticationError` (401), `AuthorizationError` (403), `ValidationError` (422), `NotFoundError` (404), `QuotaExceededError` (429), `ExternalServiceError` (502), `GenerationError` (500), `FirewallBlockedError` (403)
- **All inherit** from `TeamGenieError` base class with `status_code` and `error_code`
- **Error handler** and FastAPI exception handlers both map these automatically

#### Auth Service — Hardened (`services/auth_service.py`)
- **Added:** Email regex validation BEFORE calling Supabase
- **Added:** Password strength validation in service layer
- **Fixed:** Error messages sanitized — never expose Supabase internals to client
- **Fixed:** Email partially masked in logs for privacy (`use***@...`)
- **Added:** Defensive session null-checks
- **Replaced:** Raw `ValueError` with typed `AuthenticationError`, `ValidationError`, `ExternalServiceError`

#### Auth Router — Consistent Errors + Real Logout (`routers/auth.py`)
- **Fixed:** All endpoints now catch `TeamGenieError` → proper `{code, message}` format
- **Fixed:** Logout actually calls `revoke_token(jti)` instead of being a no-op
- **Fixed:** Forgot-password returns `"If an account exists..."` — no email existence leak

#### AI Service — Anti-Hallucination Pipeline (`services/ai_service.py`)
- **Added:** `_validate_player_data()` — checks required fields, types, ranges, duplicates, roles
- **Added:** `_validate_team_output()` — 7 post-generation constraint checks
- **Added:** `_auto_heal_team()` — last-resort safety net for captain/VC reassignment
- **Added:** Production-aware `_fetch_players()` (PRODUCTION → DB, HYBRID → DB+fallback, DEMO → sample)
- **Added:** Enrichment consistency verification
- **Added:** `asyncio.wait_for(timeout=30s)` on all agent calls
- **Added:** `return_exceptions=True` with per-agent failure recovery
- **Fixed:** Division-by-zero guard on player price

#### Error Handler — Traceback Safety (`middleware/error_handler.py`)
- **Added:** Traceback truncation (4000 char max)
- **Added:** Sensitive data redaction (API_KEY, SECRET, TOKEN, PASSWORD, DSN patterns)
- **Added:** `TeamGenieError` → proper status code mapping
- **Added:** Environment-aware client messages (error type in dev, generic in production)

---

### 🟢 Medium/Low Priority Fixes

#### Production Endpoint Lockdown (`main.py`)
- `/docs` and `/redoc` disabled in production
- `/diagnostics` returns 403 unless `IS_DEV`
- `/ready` returns minimal info in production (no infrastructure details)

#### Security Headers (`main.py`)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security: max-age=31536000` (production only)
- `Content-Security-Policy: default-src 'self'` (production only)

#### CORS Tightened (`main.py`)
- `allow_methods` restricted to `GET, POST, PUT, DELETE, OPTIONS` (was `*`)
- `allow_headers` restricted to `Authorization, Content-Type, X-Request-ID` (was `*`)
- `expose_headers` added for rate-limit headers

#### Router Error Handling (`routers/team.py`)
- HTTPException from quota check no longer swallowed by generic handler
- JIT scraper wrapped in `asyncio.wait_for(timeout=10s)`
- Error messages no longer leak raw Python exception details
- `error_type` added to logs for faster debugging

---

### 📋 Testing

| Category | Count |
|----------|-------|
| Health / Readiness / Diagnostics | 3 |
| Team generation + validation | 9 |
| match_id format validation | 4 |
| Security headers | 2 |
| Data validation (anti-hallucination) | 6 |
| Custom exception types | 2 |
| Firewall (attack detection, IP tracking) | 3 |
| Auth (public routes, token revocation) | 2 |
| Auth service (email, password) | 2 |
| Information leakage prevention | 1 |
| **Total** | **32** |

---

### 📁 Files Changed

| File | Action |
|------|--------|
| `apps/api/core/exceptions.py` | ✨ **NEW** — Custom exception hierarchy |
| `apps/api/main.py` | 🔧 Middleware order, Sentry, security headers, CORS, endpoint lockdown |
| `apps/api/middleware/auth.py` | 🔧 HTTPS, revocation, issuer, algorithm whitelist |
| `apps/api/middleware/error_handler.py` | 🔧 Traceback safety, TeamGenieError support |
| `apps/api/models/team.py` | 🔧 Pydantic v2 model_validator fix |
| `apps/api/routers/auth.py` | 🔧 Custom exceptions, real logout, anti-leak |
| `apps/api/routers/team.py` | 🔧 match_id regex, JIT timeout, HTTPException passthrough |
| `apps/api/security/ai_firewall.py` | 🔧 6 security layers, IP tracking, SSRF |
| `apps/api/services/ai_service.py` | 🔧 Data validation, constraint checks, auto-heal |
| `apps/api/services/auth_service.py` | 🔧 Custom exceptions, input validation |
| `apps/api/tests/test_team.py` | 🧪 32 tests (was ~9) |

---

*Audited and remediated by Mohammed Inayat Hussain Qureshi — April 6, 2026*
