# 🔍 Complete `.env` Credential & Setup Audit

I did a forensic cross-reference of **every single `os.getenv()` and `process.env` call** in your entire codebase against your `.env.example`. Here is the full truth.

---

## ❌ MISSING from `.env.example` — Code References Them, Template Doesn't List Them

These are environment variables your **actual code reads** but your `.env.example` **does not document**. A developer cloning your repo would never know to set these.

| Variable | Where Used | Impact |
|----------|-----------|--------|
| `APP_MODE` | [settings.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/core/settings.py#L27) — controls `demo`/`hybrid`/`production` mode | **CRITICAL** — determines if system uses real DB or sample data |
| `JWT_ISSUER` | [auth.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/middleware/auth.py#L176) — issuer validation in JWT verification | **HIGH** — production JWT tokens will be rejected without this |
| `ENABLE_RAG` | [settings.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/core/settings.py#L44) — toggles RAG pipeline | **MEDIUM** — RAG silently stays off even if Pinecone is configured |
| `FIREWALL_MAX_BODY_BYTES` | [ai_firewall.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/security/ai_firewall.py#L36) — max request body size | Low — defaults to 1MB |
| `FIREWALL_BAN_THRESHOLD` | [ai_firewall.py](file:///c:/Users/moham/Music/DEPLOY%20V1%20INAYAT/Gitlatestclone%204%20march/teamgenie-ai-PRIVATE-PATENT-2026/apps/api/security/ai_firewall.py#L91) — violations before IP ban | Low — defaults to 5 |

> [!IMPORTANT]
> **`APP_MODE`** is the single most important missing variable. Without it, your system silently defaults to `demo` mode — serving hardcoded sample data even if you have real Turso/Gemini keys configured. You probably want `APP_MODE=hybrid` or `APP_MODE=production`.

---

## ✅ Covered — These Are All Properly Documented

Your `.env.example` correctly lists every one of these (used in actual code):

| Category | Variables | Status |
|----------|----------|--------|
| **Runtime** | `PYTHON_ENV`, `ALLOWED_ORIGINS` | ✅ |
| **Database** | `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN` | ✅ |
| **Auth** | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` | ✅ |
| **Cache** | `UPSTASH_REDIS_URL` | ✅ |
| **Vector DB** | `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` | ✅ |
| **AI/LLM** | `GEMINI_API_KEY`, `CLAUDE_API_KEY`, `COHERE_API_KEY` | ✅ |
| **Scraping** | `TAVILY_API_KEY` | ✅ |
| **Security** | `JWT_ALGORITHM` | ✅ |
| **Monitoring** | `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_ENVIRONMENT` | ✅ |
| **Rate Limiting** | `RATE_LIMIT_FREE_TIER`, `RATE_LIMIT_PAID_TIER` | ✅ |
| **Feature Flags** | `ENABLE_AI_FIREWALL`, `ENABLE_SELF_HEALING` | ✅ |
| **Frontend** | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL` | ✅ |

---

## ⚠️ Listed in `.env.example` But NOT Actually Used in Code

These are "aspirational" variables — documented in the template but no code reads them yet. They're either planned features or stubs:

| Variable | Category | Analysis |
|----------|---------|----------|
| `OPENAI_API_KEY` | AI | Listed in `config.py` Pydantic model but no actual code calls OpenAI |
| `GROQ_API_KEY` | AI | No code usage found |
| `DEEPSEEK_API_KEY` | AI | No code usage found |
| `HUGGINGFACE_API_KEY` | AI | No code usage found |
| `JINA_API_KEY` | Scraping | No code usage found |
| `BROWSERBASE_API_KEY/PROJECT_ID` | Scraping | No code usage found |
| `RAZORPAY_*` (3 vars) | Payments | No payment router implemented |
| `STRIPE_*` (3 vars) | Payments | No payment router implemented |
| `JWT_SECRET` | Auth | Code uses `SUPABASE_JWT_SECRET` instead |
| `JWT_EXPIRY_MINUTES` | Auth | No code reads this (Supabase handles token expiry) |
| `REFRESH_TOKEN_EXPIRY_DAYS` | Auth | No code reads this |
| `ENCRYPTION_KEY` | Security | No code usage found |
| `BCRYPT_ROUNDS` | Security | No code usage found |
| `CSRF_SECRET` | Security | No code usage found |
| `AXIOM_*` | Monitoring | No code usage found |
| `POSTHOG_*` | Analytics | Backend doesn't use; frontend CSP references it |
| `BETTERSTACK_API_KEY` | Monitoring | No code usage found |
| `DOPPLER_TOKEN` | Secrets | Infrastructure-level, not in app code |
| `RESEND_*` | Email | No email service implemented |
| `ONESIGNAL_*` | Push | No push notification code |
| `TELEGRAM_*` | Alerts | No Telegram integration code |
| `CLOUDFLARE_*` | CDN | Infrastructure-level |
| `VERCEL_*` | Deploy | CI/infrastructure-level |
| `RENDER_*` | Deploy | CI/infrastructure-level |
| `GITHUB_TOKEN` | Deploy | CI-level |
| `EAS_PROJECT_ID` | Mobile | Expo not yet active |
| `TEST_*` (6 vars) | Testing | Tests use mocks, not real test databases |
| `DATA_RETENTION_DAYS` | Compliance | No code reads this |
| `COOKIE_CONSENT_REQUIRED` | Compliance | No code reads this |
| `FORCE_HTTPS` | Compliance | Auth middleware hardcodes HTTPS check |
| `ENABLE_HSTS`, `ENABLE_CSP` | Compliance | Headers are hardcoded in middleware |
| `ENABLE_ANALYTICS` | Feature Flag | No code reads this |
| `ENABLE_PUSH_NOTIFICATIONS` | Feature Flag | No code reads this |
| `ENABLE_EMAIL_NOTIFICATIONS` | Feature Flag | No code reads this |

> [!NOTE]
> These aren't "errors" — they're infrastructure vars and planned feature placeholders. Keep them in `.env.example` as documentation for future development. But be aware that filling them in today won't activate any functionality.

---

## 🚨 Human Work Checklist — What YOU Need to Do

### Priority 1: Critical (App Won't Work Properly Without These)

| # | Task | Where to Get It | Time |
|---|------|----------------|------|
| 1 | **Get a Gemini API Key** | [Google AI Studio](https://makersuite.google.com/app/apikey) | 2 min |
| 2 | **Set `APP_MODE=hybrid`** in `.env` | Just type it | 10 sec |
| 3 | **Create Supabase project** → get URL + anon key + JWT secret | [supabase.com/dashboard](https://supabase.com/dashboard) | 5 min |
| 4 | **Create Turso database** → get URL + auth token | [turso.tech/app](https://turso.tech/app) | 3 min |
| 5 | **Run DB migrations** against Turso | Execute `db/migrations/001_initial_schema.sql` | 2 min |
| 6 | **Set `JWT_ISSUER`** (usually `https://YOUR_PROJECT.supabase.co/auth/v1`) | Copy from Supabase dashboard | 30 sec |

### Priority 2: Important (For Full Feature Set)

| # | Task | Where to Get It | Time |
|---|------|----------------|------|
| 7 | **Upstash Redis** → get URL | [upstash.com](https://upstash.com) (free tier) | 3 min |
| 8 | **Pinecone** → create index `player-embeddings` (1536 dims, cosine) | [app.pinecone.io](https://app.pinecone.io) | 5 min |
| 9 | **Tavily API key** (for real-time web scraping) | [tavily.com](https://tavily.com) | 2 min |
| 10 | **Claude API key** (fallback LLM) | [console.anthropic.com](https://console.anthropic.com) | 3 min |

### Priority 3: Production Deployment (When Ready to Go Live)

| # | Task | Where to Get It |
|---|------|----------------|
| 11 | **Sentry DSN** | [sentry.io](https://sentry.io) |
| 12 | **Razorpay keys** (if Indian payments) | [dashboard.razorpay.com](https://dashboard.razorpay.com) |
| 13 | **Domain + Cloudflare** | [cloudflare.com](https://cloudflare.com) |
| 14 | **Vercel/Render deploy** | Platform dashboard |
| 15 | **Set `PYTHON_ENV=production`** | `.env` on production server |

---

## 📋 Updated `.env.example` Patch — Add the 5 Missing Variables

Here are the exact lines you should add to your `.env.example`:

```diff
 #==========================================
 # BACKEND (FastAPI)
 #==========================================
 NODE_ENV=development
 PYTHON_ENV=development
+APP_MODE=demo                    # demo | hybrid | production
 API_HOST=0.0.0.0
 API_PORT=8000

 #==========================================
 # AUTHENTICATION & SECURITY
 #==========================================
 JWT_SECRET=your-super-secret-jwt-key-min-32-chars
 JWT_ALGORITHM=HS256
+JWT_ISSUER=https://YOUR_PROJECT.supabase.co/auth/v1

 #==========================================
 # FEATURE FLAGS
 #==========================================
 ENABLE_AI_FIREWALL=true
 ENABLE_SELF_HEALING=true
+ENABLE_RAG=false                 # Requires Pinecone + Cohere keys
 ENABLE_ANALYTICS=true

+#==========================================
+# AI FIREWALL TUNING (optional)
+#==========================================
+FIREWALL_MAX_BODY_BYTES=1048576  # 1MB default
+FIREWALL_BAN_THRESHOLD=5         # violations before temp IP ban
```

---

## ✅ Things That Are Already Correct

- `.gitignore` properly excludes `.env`, `.env.local`, and `*.env` ✅
- `.env.example` is whitelisted in `.gitignore` with `!.env.example` ✅
- CI workflow (`ci.yml`) doesn't leak secrets — uses hardcoded test values ✅
- Docker compose uses `env_file` reference (not inline secrets) ✅
- Frontend only uses `NEXT_PUBLIC_*` vars (no server secrets exposed to browser) ✅
- `config.py` Pydantic model has `extra="ignore"` so unknown vars don't crash ✅

> [!TIP]
> **Bottom line**: Your `.env.example` is 95% complete. The 5 missing variables above are the only gap. Everything else is either already covered or is a future placeholder. The **minimum to get the full system working** is items 1–6 in the Human Work Checklist (roughly 15 minutes of setup).
