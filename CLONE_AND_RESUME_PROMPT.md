# 🧞‍♂️ TeamGenie AI — AI Brain Transfer Prompt

**HOW TO USE THIS FILE:**
If you ever wipe this project, move to a new computer, open a new ChatGPT/Claude session, or spawn a new Antigravity workspace, **copy and paste the entire prompt below** as your very first message to the AI. 

It will instantly synchronize the AI with 100% of the project's history, architecture, built features, and immediate next steps without you having to type a single word of explanation.

---
---
**COPY EVERYTHING BELOW THIS LINE:**
---
---

**SYSTEM DIRECTIVE: CORE ARCHITECTURE SYNCHRONIZATION — v2.0**

You are assuming the role of **Principal AI Engineer & Architect (30-Year Veteran)** for **"TeamGenie AI"**, an enterprise-grade, multi-agent fantasy sports prediction platform for Indian cricket (IPL). I have just cloned/restored this repository into my workspace.

Before we write any new code or answer any questions, you must perform a mandatory **Context Download**.

**Execute the following steps using your local file-reading capabilities instantly:**

1. **READ `CONTEXT.md` (Crucial):** This is the master database of our project's reality (400+ lines). Pay special attention to:
   - Section 7: Chronological Change Log — understand what was built and when
   - Section 11: Deep Code Audit — critical engineering decisions documented forensically
   - Section 12: Prioritized next actions
   
2. **READ `ARCHITECTURE.md`:** The Turborepo monorepo structure (FastAPI + Next.js + Expo), 3-Agent AI system (Budget Optimizer, Differential Expert, Risk Manager), and security stance.

3. **READ `30 YEAR SENIOR AI ENGINEER NAME - MOHAMMAD INAYAT HUSSAIN.md` (v2.0):** Contains line-by-line code audit with actual Python/TypeScript code blocks showing WHY every design decision was made.

4. **READ `apps/api/db/migrations/001_initial_schema.sql`:** Proves the edge database schema is fully designed with 5 tables and 14 composite indexes.

**TECHNICAL STATE — WHAT IS BUILT AND HOW IT WORKS:**

### The Core Product
- Fantasy cricket team generator using **3 AI agents in consensus**
- **Budget Optimizer (Gemini)**: OR-Tools ILP solver (knapsack problem, strict ₹100 budget)
- **Differential Expert (Gemini)**: RAG-powered low-ownership hidden gem finder (<25% ownership threshold)
- **Risk Manager (Claude)**: Monte Carlo-informed Captain/VC assignment based on `safe|balanced|aggressive` risk profile

### The Data Pipeline
```
JIT Scraper (DuckDuckGo + Open-Meteo) →
Context Block →
AI Agents (parallel: 1+2, then sequential: 3) →
11 Pydantic-validated PlayerModel →
Response (4ms in DEMO mode)
```

### Critical Non-Obvious Engineering Facts
1. **`load_dotenv()` must be first in `main.py`** — middleware imports os.getenv() at startup
2. **FastAPI middleware is LIFO** — last registered = first to execute (Rate Limit → Firewall → Auth)
3. **`asyncio.gather(return_exceptions=True)`** in RAG pipeline — one failing Pinecone index doesn't crash the team
4. **ILP solver fallback**: OR-Tools → greedy heuristic (≈93% optimal, always works)
5. **JIT cache is global per-process** — 10M concurrent users trigger only N_pods searches (not 10M)
6. **`autouse=True` fixture mocks scraper** in conftest.py — prevents CI hang on network calls
7. **AppMode tri-modal**: `DEMO` (no keys) → `HYBRID` (partial) → `PRODUCTION` (all real)
8. **Smart placeholder detection**: `v.startswith("AIzaSyXXXX")` returns None to avoid fake key calls

### Current Runtime Status
- **Team Generation**: 🟢 WORKS (4ms, heuristic/greedy mode, 11 players)
- **Auth**: 🟢 Dev-bypass active (`PYTHON_ENV=development` → `dev_user` auto-assigned)
- **Redis/Rate Limit**: 🟡 Gracefully bypassed (no Redis connection)
- **AI Firewall**: 🟡 Disabled (`ENABLE_AI_FIREWALL=false` in dev)
- **Real LLMs**: 🔴 Stubs (need `GEMINI_API_KEY` + `CLAUDE_API_KEY`)
- **Database**: 🔴 Stubs (need `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN`)
- **CI/CD**: 🟢 All green (linting + pytest + security scan passing)

### What Needs to Happen for Production (Ordered Priority)
1. **P0**: Inject `GEMINI_API_KEY`, `TURSO_DATABASE_URL`, `SUPABASE_URL` into `.env`
2. **P0**: Replace hardcoded `_fetch_players()` in `ai_service.py` with Turso query
3. **P1**: Implement `_query_player_stats()` in `rag_service.py` (Pinecone integration)
4. **P1**: Deploy backend to Render, frontend to Vercel
5. **P2**: Add ILP role constraints (min 3 BAT, min 3 BOWL, max 7 from one team)
6. **P3**: Deploy Cloudflare Worker for geo-blocking
7. **P3**: Connect Prometheus for production observability

**YOUR REQUIRED RESPONSE:**
Do not write out generic advice. Do not ask me basic questions.
Simply read the files above, and reply with:
1. **"🧠 SYNCHRONIZATION COMPLETE — v2.0."**
2. A very brief 3-bullet summary proving you understand the specific technical state (mention the LIFO middleware order, the ILP fallback chain, or the JIT global cache design).
3. Confirm the current P0 priority: `"Ready to implement Turso database connection in _fetch_players()."`

Let's get to work.
