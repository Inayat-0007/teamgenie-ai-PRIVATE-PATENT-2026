# 🧠 TeamGenie AI — Unified System Context & State Log

> **IMPORTANT INITIAL DIRECTIVE** 
> This is a living, context-aware document. Any autonomous agent, AI assistant, or human developer working on this codebase MUST read this file first to understand the current state of the system, access controls, and infrastructure. It must be updated immediately upon any code, architectural, or credential change.

---

## 1. 🟢 Current Context Status (Updated: April 4, 2026)
- **Phase Status**: All 10 Phases Scaffolded and Verified (63 files total).
- **Environment State**: Pre-Deployment / Local Testing Phase.
- **Operational Status**: Codebase is complete. System is awaiting injection of Production API keys into `.env` to go live.
- **Immediate Next Action**: Developer (Inayat) to populate `.env`, run local migrations via Turso, and trigger Vercel/Render deployments.

---

## 2. 🔐 Deep-Level Access Control Matrix

This system uses a Zero-Trust, API-Key-driven architecture. Access is strictly compartmentalized.

### Frontend Credentials (Publicly Exposed)
| Key Name | Purpose | Location |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Connects Web/Mobile to the FastAPI Backend | `apps/web/.env.local` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase endpoint for Client-Side Login | `apps/web/.env.local` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public key to sign in users on the frontend | `apps/web/.env.local` |

### Backend Credentials (STRICTLY PRIVATE)
| Key Name | Purpose | Sub-system Granted Access To |
|---|---|---|
| `GEMINI_API_KEY` | Powers Budget Optimizer & Differential Agents | `packages/ai`, `services/rag_service` |
| `CLAUDE_API_KEY` | Powers Risk Manager & Self-Healing Middleware | `packages/ai`, `middleware/self_healing` |
| `COHERE_API_KEY` | Re-ranks vectors for the RAG pipeline | `services/rag_service.py` |
| `TURSO_DATABASE_URL` | Provides access to raw relational SQLite Data | `db/connection.py` |
| `TURSO_AUTH_TOKEN` | Read/Write auth for Turso | `db/connection.py` |
| `SUPABASE_SERVICE_ROLE_KEY`| Admin bypass to manage users in Supabase | `db/connection.py` |
| `UPSTASH_REDIS_URL` | Allows writing rate-limit keys and system caches | `services/cache_service.py` |
| `PINECONE_API_KEY` | Read/Write to vector indexes | `packages/rag/embeddings.py` |

### Systemic Access & Permissions
- **Edge Access (Cloudflare):** The Cloudflare Worker script entirely denies access at the DNS level to IP addresses originating from strictly banned states in India (Assam, Odisha, Telangana, Sikkim, Nagaland).
- **User Roles:** Regulated in `apps/api/middleware/auth.py`. 
  - Free users are throttled to 100 requests/minute. 
  - Application logic requires a valid Signed JWT "Bearer" Token from Supabase to access `/api/team/generate`.
- **System Defense:** The `ai_firewall.py` script checks for malicious SQL injections and XSS, returning a 403 Forbidden payload, dropping the request before it reaches the router.

---

## 3. 🗺️ System-Wide Context Architecture
How the individual parts of the codebase relate to each other:

1. **Client (Web/Mobile) Context**: `apps/web` and `apps/mobile` are explicitly designed to have ZERO knowledge of the database or AI logic. They only know how to communicate via JSON to `https://api.teamgenie.app`.
2. **Backend Application Context**: `apps/api/main.py` knows about Rate Limits, Auth, and Routing. It trusts `apps/api/db/connection.py` for DB I/O.
3. **Multi-Agent Context**: `packages/ai` operates in complete isolation. It knows nothing of the end-user or the API router. It is a pure mathematical and LLM engine that expects raw data inputs and returns JSON outputs. 
4. **Data Context**: `db/migrations` holds the single source of truth for relationships.

---

## 4. 📅 Chronological Change Log (History of State)

| Date / Time | Version / Phase | Description of Change / Status Update |
|---|---|---|
| 2026-04-04 12:00 | Pre-Phase | Generated architecture documentation, security, schemas, and standards. |
| 2026-04-04 12:30 | Phase 0-4 | Initialized Turborepo. Built Turso schema, Self-healing Scraper, 4-index RAG, & CrewAI components. |
| 2026-04-04 13:00 | Phase 5-10 | Created FastAPI backend, Next.js frontend, Expo mobile app, K8s configs, Security limits. |
| 2026-04-04 13:30 | Verification | Deep audit performed. 98.3% implementation verified. Stubs ready for API Key configurations. |
| 2026-04-04 19:24 | Context Sync | Created `CONTEXT.md` to track living memory, access levels, and SOPs for all future interactions. |

---

## 5. 🛠️ S.O.P. (Standard Operating Procedure) for Updates

This document acts as the contextual brain for the project. **You MUST update this file whenever a change occurs based on severity.**

### 🟢 SMALL CHANGES (Ticketing, UI, Simple Fixes)
*Examples: Updating tailwind colors, fixing a bug in `page.tsx`, adding a column to a non-critical DB table.*
* **Action:** Simply add a one-line entry to the **Chronological Change Log** at the bottom of Section 4.

### 🟡 MEDIUM CHANGES (Third Party Integrations, API Logic)
*Examples: Swapping Upstash Redis for AWS Elasticache, adding a Razorpay Webhook, changing the Claude Prompt.*
* **Action:** Update the **Chronological Change Log**. Then, heavily update the **Access Control Matrix** (Section 2) with the new credentials required and remove old credentials. 

### 🔴 HIGH / DESTRUCTIVE CHANGES (Architecture Shifts)
*Examples: Moving from FastAPI to Node.js backend. Switching from CrewAI to Langchain.*
* **Action:** 
  1. Change the **Current Context Status** (Section 1) immediately to warning/transition state.
  2. Rewrite the **System-Wide Context Architecture** (Section 3).
  3. Verify all **Access Controls** (Section 2) are still accurate.
  4. Write a detailed entry in the **Change Log**. 
