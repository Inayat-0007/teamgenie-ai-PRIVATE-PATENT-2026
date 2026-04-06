# 🏗️ TeamGenie AI — Master Fixing Plan v3.0.2

> **Source:** GitHub Copilot Agents Audit (`VERY IMPORTANT.TXT`)  
> **Current Score:** Security 62/100 | Quality 75/100  
> **Target Score:** Security 90+ | Quality 90+  
> **Approach:** 6 Sprints, CRITICAL → LOW priority, no breaking changes

---

## User Review Required

> [!IMPORTANT]
> This plan touches **15+ files** across security, performance, testing, and infrastructure. Every sprint is independent — you can approve individual sprints or all at once. No sprint requires the previous one to be complete.

> [!WARNING]
> **Sprint 1 (Security)** should be done BEFORE any public launch. The in-memory token revocation (#1) and webhook replay (#2) are genuine production vulnerabilities. Sprint 2 (Performance) can wait until after launch.

---

## Sprint 1: 🔴 CRITICAL Security Fixes (Estimated: 45 min)

### Fix 1.1 — Token Revocation → Redis-backed (Copilot Finding #1)

**Problem:** `_revoked_tokens` is a Python `set()` in memory. On pod restart or deploy, all revoked tokens become valid again. In multi-pod K8s, each pod has a separate revocation list.

#### [MODIFY] [auth.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/middleware/auth.py)
- Replace `_revoked_tokens: Set[str]` with Redis-backed `SREM`/`SISMEMBER` calls
- Keep in-memory `set()` as fallback when Redis is down
- Add TTL matching JWT expiry so revoked tokens auto-cleanup

---

### Fix 1.2 — Webhook Idempotency Guard (Copilot Finding #2)

**Problem:** Replaying the same Razorpay `subscription.activated` event upgrades a user multiple times. No deduplication.

#### [MODIFY] [payment.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/payment.py)
- Store `event_id` from webhook payload in a `processed_webhooks` table
- Check for duplicate `event_id` before processing
- Return `200 OK` immediately on duplicate (Razorpay expects 200 for idempotent replays)

---

### Fix 1.3 — APP_MODE Production Guard (Copilot Finding #3)

**Problem:** `APP_MODE=DEMO` silently returns fake data with no code-level guard preventing it in production.

#### [MODIFY] [main.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/main.py)
- Add startup check: if `PYTHON_ENV=production` and `APP_MODE=DEMO`, log `CRITICAL` error and refuse to start
- Enforce: production env MUST have `APP_MODE=production`

---

### Fix 1.4 — IP Spoofing Prevention (Copilot Finding #5)

**Problem:** `X-Forwarded-For` is trivially spoofed. Anyone can send `X-Forwarded-For: 1.2.3.4` to bypass rate limits.

#### [MODIFY] [rate_limit.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/middleware/rate_limit.py)
- Use `request.client.host` as the primary IP source (already done ✅)
- Only trust `X-Forwarded-For` when `TRUSTED_PROXY_IPS` env var is set
- Add `TRUSTED_PROXY_DEPTH` for multi-proxy chains (default: 1)

---

### Fix 1.5 — Lock Down /docs in Production (Copilot Finding #8)

**Problem:** `/docs`, `/redoc`, `/openapi.json` expose the full API schema to the public internet without auth.

#### [MODIFY] [main.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/main.py)
- Already conditionally disabling docs in production (line ~70) — **verify** this is working correctly
- Remove `/docs`, `/redoc`, `/openapi.json` from `ai_firewall.py` EXEMPT_PATHS when in production

---

### Fix 1.6 — Clock Skew Reduction (Copilot Finding #10)

**Problem:** 30-second clock skew tolerance is generous. OWASP recommends ≤5s.

#### [MODIFY] [auth.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/middleware/auth.py)
- Change `_CLOCK_SKEW_TOLERANCE = 30` → `_CLOCK_SKEW_TOLERANCE = 5`

---

### Fix 1.7 — Account Deletion Re-auth (Copilot Finding #11)

**Problem:** `DELETE /api/user/me` can permanently delete an account with a single stolen JWT. No re-authentication.

#### [MODIFY] [user.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/user.py)
- Require `current_password` in the request body for account deletion
- Verify password against Supabase before proceeding

---

### Fix 1.8 — Scraper Content Sanitization (Copilot Finding #12)

**Problem:** DuckDuckGo search results are fed straight into LLM prompts without sanitization — prompt injection vector.

#### [MODIFY] [scraper_service.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/services/scraper_service.py)
- Strip all HTML tags from scraped content
- Truncate each snippet to 500 chars max
- Remove any text matching known prompt injection patterns (`ignore previous instructions`, `system:`, etc.)

---

### Fix 1.9 — Remove `playwright` from deps (Copilot Finding #15)

**Problem:** `playwright>=1.40` is still in requirements.txt but completely unused (replaced by DuckDuckGo). It adds ~150MB to the Docker image and has known CVE history.

#### [MODIFY] [requirements.txt](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/requirements.txt)
- Remove `playwright>=1.40` from line 45
- Verify `beautifulsoup4` is actually imported somewhere before keeping it

---

## Sprint 2: ⚡ Performance Quick Wins (Estimated: 30 min)

### Fix 2.1 — ILP Solver → ThreadPoolExecutor (Copilot Perf #5)

#### [MODIFY] [ai_service.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/services/ai_service.py)
- Wrap OR-Tools `Solve()` call in `asyncio.get_event_loop().run_in_executor(None, solve_fn)`
- Prevents CPU-bound ILP from blocking the async event loop

### Fix 2.2 — Middleware Short-Circuit for Health Endpoints (Copilot Perf #12)

#### [MODIFY] [main.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/main.py)
- Add early return check at the top of each middleware for `/health`, `/ready`, `/metrics`
- Eliminates 6 middleware hops for monitoring/probe calls

### Fix 2.3 — Harvester Parallel Match Processing (Copilot Perf #3)

#### [MODIFY] [harvester.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/workers/harvester.py)
- Wrap match processing loop in `asyncio.gather()` with `asyncio.Semaphore(3)`
- Expected: 60-70% reduction in full harvest cycle time

### Fix 2.4 — Database Indexes (Copilot Perf #9)

#### [NEW] [003_add_indexes.sql](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/db/migrations/003_add_indexes.sql)
- `CREATE INDEX idx_teams_match_id ON teams(match_id);`
- `CREATE INDEX idx_teams_user_id ON teams(user_id);`
- `CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);`
- `CREATE INDEX idx_payment_history_user_id ON payment_history(user_id);`

---

## Sprint 3: 🧪 Critical Test Coverage (Estimated: 60 min)

### Fix 3.1 — Payment Router Tests (ALL 4 ENDPOINTS — ZERO COVERAGE)

#### [NEW] [test_payment.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/tests/test_payment.py)

Tests to write:
- `test_create_order_valid_plan` — pro/elite plans return order_id
- `test_create_order_invalid_plan` — rejects bad plan_id
- `test_verify_payment_valid_signature` — signature verification works
- `test_verify_payment_invalid_signature` — rejects bad signature
- `test_verify_payment_production_no_razorpay` — blocks simulated in production
- `test_webhook_idempotency` — replayed event_id is rejected
- `test_webhook_invalid_signature` — bad HMAC returns 401
- `test_payment_status_free_user` — returns free tier
- `test_payment_status_paid_user` — returns correct plan

### Fix 3.2 — Auth Router Tests

#### [NEW] [test_auth.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/tests/test_auth.py)

Tests to write:
- `test_login_valid_credentials` (mocked Supabase)
- `test_login_invalid_credentials`
- `test_register_valid_user`
- `test_register_duplicate_email`
- `test_refresh_token_valid`
- `test_logout_revokes_token`

### Fix 3.3 — User Router Tests (GDPR Compliance)

#### [NEW] [test_user.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/tests/test_user.py)

Tests to write:
- `test_get_profile`
- `test_update_profile`
- `test_data_export_returns_json`
- `test_delete_account_requires_reauth`
- `test_withdraw_consent`

---

## Sprint 4: 📄 Error Consistency & API Docs (Estimated: 30 min)

### Fix 4.1 — Standardize Error Responses

Currently only `team.py` uses `TeamGenieError`. All other routers use raw `HTTPException(detail=str)`.

#### [MODIFY] [auth.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/auth.py), [payment.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/payment.py), [user.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/user.py), [player.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/player.py), [match.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/match.py)
- Replace all `HTTPException(detail=str)` with appropriate `TeamGenieError` subclasses
- Unified response format: `{error_code: str, message: str, request_id: str}`

### Fix 4.2 — WebSocket Auth Gate (Copilot Finding #16)

#### [MODIFY] [match.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/routers/match.py)
- Add JWT verification for WebSocket upgrade handshake (token via query param `?token=`)
- Reject unauthenticated WebSocket connections

---

## Sprint 5: 🛡️ Infrastructure & Deployment (Estimated: 20 min)

### Fix 5.1 — Add K8s Secrets to .gitignore

#### [MODIFY] [.gitignore](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/.gitignore)
- Add `infra/kubernetes/secrets.yaml` to `.gitignore`
- Replace with `infra/kubernetes/secrets.yaml.example` containing only placeholder values

### Fix 5.2 — Add Frontend to render.yaml

#### [MODIFY] [render.yaml](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/render.yaml)
- Add Next.js web service entry with proper build/start commands

### Fix 5.3 — CORS Production Guard (Copilot Finding #19)

#### [MODIFY] [main.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/main.py)
- If `PYTHON_ENV=production` and `CORS_ORIGINS=*`, refuse to start with a critical error log
- Force explicit origin list in production

---

## Sprint 6: 📦 Dependency Cleanup (Estimated: 10 min)

### Fix 6.1 — Remove Unused Dependencies

#### [MODIFY] [requirements.txt](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/requirements.txt)

| Package | Action | Reason |
|---------|--------|--------|
| `playwright>=1.40` | **REMOVE** | Replaced by DuckDuckGo, adds 150MB, CVE risk |
| `opentelemetry-*` (3 packages) | **VERIFY** then remove if unused | Not imported in main.py |
| `posthog>=3.3` | **VERIFY** then remove if unused | SDK present but no usage in backend |
| `passlib[bcrypt]>=1.7` | **VERIFY** | Supabase handles auth — may be unused |
| `cohere>=4.40` | **VERIFY** | Only Gemini + Claude are used by CrewAI |

---

## Summary Impact Table

| Sprint | Findings Fixed | Security Score Impact | Files Changed |
|--------|---------------|----------------------|---------------|
| Sprint 1 | #1, #2, #3, #5, #8, #10, #11, #12, #15 | 62 → 82 | 7 files |
| Sprint 2 | Perf #3, #5, #9, #12 | — | 4 files |
| Sprint 3 | 15+ test gaps | — | 3 new test files |
| Sprint 4 | #16, Error consistency | 82 → 87 | 6 files |
| Sprint 5 | #7, #19, Infra gaps | 87 → 90 | 3 files |
| Sprint 6 | #15, Dep audit | 90 → 92 | 1 file |

---

## Open Questions

> [!IMPORTANT]
> **Q1:** Do you want me to execute **all 6 sprints in one shot**, or do you prefer to approve and execute them one sprint at a time?

> [!IMPORTANT]
> **Q2:** For Fix 1.1 (Redis-backed token revocation) — should tokens revoked during a Redis outage be accepted (fail-open) or rejected (fail-closed)? Fail-closed is more secure but may block legitimate users during Redis downtime.

> [!IMPORTANT]
> **Q3:** For the dependency cleanup (Sprint 6) — should I first verify which packages are actually imported before removing, or do you trust the Copilot analysis and want me to remove them directly?

---

## Verification Plan

### Automated Tests
- `pytest apps/api/tests/ -v --tb=short --cov=. --cov-report=xml:coverage.xml` after each sprint
- Verify 0 failures before committing

### Manual Verification
- Restart FastAPI server after each sprint to verify no import errors
- Open `http://localhost:3000` and test 1-Click Generate to ensure no regressions
- Push to GitHub and verify CI pipeline passes (all 4 jobs: backend, frontend, docker, security)
