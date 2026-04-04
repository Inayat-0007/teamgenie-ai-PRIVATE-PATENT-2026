# 🏗️ TeamGenie AI — System Architecture

**Last Updated:** January 2026  
**Version:** 1.0.0  
**Author:** Mohammed Inayat Hussain Qureshi

---

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [AI/ML Pipeline](#aiml-pipeline)
5. [Infrastructure](#infrastructure)
6. [Security Architecture](#security-architecture)
7. [Scalability](#scalability)
8. [Monitoring & Observability](#monitoring--observability)

---

## High-Level Overview

TeamGenie is a **multi-agent AI system** that generates optimal fantasy sports teams. The architecture follows a **serverless-first, edge-native** approach with **AI at every layer**.

### Design Principles

1. **Zero Manual Ops** — AI manages deployments, bug fixes, scaling
2. **Edge-First** — <50ms latency globally via Cloudflare
3. **Cost-Optimized** — 98% gross margin via free tiers + smart routing
4. **Self-Healing** — AI detects and fixes production issues
5. **Security by Default** — Every request analyzed by AI firewall

---

## Core Components

### 1. Frontend Layer

```
┌─────────────────────────────────────────────┐
│          USER INTERFACES                    │
├─────────────────────────────────────────────┤
│                                             │
│  WEB APP (Next.js 14)                       │
│  ├─ Server Components (RSC)                 │
│  ├─ Edge Runtime (Vercel)                   │
│  ├─ Optimistic UI (React Query)             │
│  └─ Framer Motion (Animations)              │
│                                             │
│  MOBILE APP (Expo 52 + React Native)        │
│  ├─ File-based routing (Expo Router)        │
│  ├─ NativeWind (Tailwind CSS)               │
│  ├─ React Native Reanimated                 │
│  └─ OTA Updates (CodePush alternative)      │
│                                             │
└─────────────────────────────────────────────┘
           ↓ HTTPS (TLS 1.3)
```

**Tech Choices:**
- **Next.js 14:** Server Components reduce client JS by 40%
- **Expo:** Cross-platform with single codebase (70% code reuse)
- **Edge Runtime:** Deploy API routes to 300+ Cloudflare locations

---

### 2. API Gateway & Edge Layer

```
┌─────────────────────────────────────────────┐
│       CLOUDFLARE GLOBAL NETWORK             │
├─────────────────────────────────────────────┤
│                                             │
│  [DDoS Protection] ← Unlimited, FREE        │
│  [WAF] ← AI-generated rules                 │
│  [Bot Management] ← Challenge bad actors    │
│  [SSL/TLS] ← Auto-renewing certs            │
│  [CDN] ← Static asset caching               │
│                                             │
│  CLOUDFLARE WORKERS (Edge Compute)          │
│  ├─ 100K requests/day FREE                  │
│  ├─ Hono framework (ultra-fast routing)     │
│  ├─ KV storage (100K reads/day)             │
│  └─ Durable Objects (stateful edge)         │
│                                             │
└─────────────────────────────────────────────┘
           ↓ Route to origin
```

**Why Cloudflare:**
- Zero cold starts (vs Lambda's 100-500ms)
- 300+ PoPs globally (vs AWS's 33 regions)
- Unlimited DDoS on free tier (vs AWS Shield's $3K/month)

---

### 3. Application Backend

```
┌─────────────────────────────────────────────┐
│           FASTAPI APPLICATION               │
│           (Python 3.11, Async)              │
├─────────────────────────────────────────────┤
│                                             │
│  ROUTERS (API Endpoints)                    │
│  ├─ /api/team/generate                      │
│  ├─ /api/player/{id}/insights               │
│  ├─ /api/match/{id}/live                    │
│  └─ /api/user/preferences                   │
│                                             │
│  MIDDLEWARE STACK                           │
│  ├─ AI Firewall (Claude monitors)           │
│  ├─ Rate Limiter (Upstash Redis)            │
│  ├─ Auth (Supabase JWT)                     │
│  ├─ CORS (Secure headers)                   │
│  ├─ Self-Healing (Auto-fix errors)          │
│  └─ Telemetry (OpenTelemetry)               │
│                                             │
│  SERVICES (Business Logic)                  │
│  ├─ AI Service (CrewAI orchestration)       │
│  ├─ RAG Service (LangChain pipeline)        │
│  ├─ Scraper Service (Playwright)            │
│  └─ Cache Service (Redis management)        │
│                                             │
└─────────────────────────────────────────────┘
           ↓ Database queries
```

**Deployment:** Render (FREE tier) → Upgrade to $7/mo for 24/7

**Why FastAPI:**
- Async by default (handles 10K concurrent requests)
- Pydantic validation (runtime type safety)
- Auto-generated OpenAPI docs
- Python AI ecosystem (LangChain, CrewAI, scikit-learn)

---

### 4. Data Layer

```
┌─────────────────────────────────────────────┐
│              MULTI-DATABASE                 │
├─────────────────────────────────────────────┤
│                                             │
│  TURSO (Primary Database — 9GB FREE)        │
│  ├─ LibSQL (SQLite fork, edge replicas)     │
│  ├─ Tables: users, teams, players, matches  │
│  ├─ Point-in-time recovery (5-min backups)  │
│  └─ Multi-region: AMS, SIN, IAD             │
│                                             │
│  SUPABASE (Auth & Realtime — 500MB FREE)    │
│  ├─ Postgres 15                             │
│  ├─ Built-in auth (JWT, OAuth)              │
│  ├─ Row-Level Security (RLS)                │
│  └─ Realtime subscriptions (WebSockets)     │
│                                             │
│  UPSTASH REDIS (Cache — 10K cmds/day FREE)  │
│  ├─ Player stats (TTL: 5 min)               │
│  ├─ Team predictions (TTL: 10 min)          │
│  ├─ Rate limit counters                     │
│  └─ Session storage                         │
│                                             │
│  PINECONE (Vector DB — 100K vectors FREE)   │
│  ├─ Player embeddings (384 dimensions)      │
│  ├─ Match context embeddings                │
│  ├─ Venue embeddings                        │
│  └─ Cosine similarity search (<50ms)        │
│                                             │
└─────────────────────────────────────────────┘
```

**Data Consistency Strategy:**
- **Turso:** Source of truth for transactional data
- **Supabase:** Real-time updates via Postgres triggers
- **Redis:** Cache invalidation on DB writes
- **Pinecone:** Async embeddings generation (background job)

---

### 5. AI/ML Pipeline

```
┌─────────────────────────────────────────────┐
│         MULTI-AGENT SYSTEM (CrewAI)         │
├─────────────────────────────────────────────┤
│                                             │
│  INPUT: {match_id, budget, risk_level}      │
│     ↓                                       │
│  ┌─────────────────────────────────────┐   │
│  │  AGENT 1: Budget Optimizer          │   │
│  │  LLM: Gemini 2.0 Flash (FREE)       │   │
│  │  Tool: Google OR-Tools (ILP solver) │   │
│  │  Task: Max points ≤ ₹100 budget     │   │
│  └────────────┬────────────────────────┘   │
│               ↓                             │
│  ┌─────────────────────────────────────┐   │
│  │  AGENT 2: Differential Expert       │   │
│  │  LLM: Gemini 2.0 Flash (FREE)       │   │
│  │  Tool: RAG (Pinecone + LangChain)   │   │
│  │  Task: Find low-ownership gems      │   │
│  └────────────┬────────────────────────┘   │
│               ↓                             │
│  ┌─────────────────────────────────────┐   │
│  │  AGENT 3: Risk Manager              │   │
│  │  LLM: Claude 3.7 Haiku ($0.25/1M)   │   │
│  │  Tool: Monte Carlo simulation       │   │
│  │  Task: Balance risk vs reward       │   │
│  └────────────┬────────────────────────┘   │
│               ↓                             │
│  [Consensus Algorithm] ← Weighted voting    │
│               ↓                             │
│  [Personalization Layer] ← User history     │
│               ↓                             │
│  OUTPUT: {team: [...], confidence: 0.87}    │
│                                             │
└─────────────────────────────────────────────┘
```

**LLM Routing Logic:**
```python
def route_llm(task_complexity: float):
    if task_complexity < 0.3:
        return "gemini-2.0-flash"  # FREE, fast
    elif task_complexity < 0.7:
        return "deepseek-v3"  # FREE, good reasoning
    else:
        return "claude-haiku-4"  # $0.25/1M, best reasoning
```

**Cost Optimization:**
- 90% requests → Gemini/DeepSeek (FREE)
- 10% complex → Claude (₹20/month at 10K users)

---

## 6. RAG (Retrieval-Augmented Generation) Pipeline

```
┌─────────────────────────────────────────────┐
│        ADVANCED RAG ARCHITECTURE            │
├─────────────────────────────────────────────┤
│                                             │
│  USER QUERY: "Virat Kohli analysis"         │
│     ↓                                       │
│  [Query Rewriter] ← Gemini expands query    │
│     ↓                                       │
│  ┌──────────────────────────────────────┐  │
│  │  PARALLEL INDEX RETRIEVAL (async)    │  │
│  │                                      │  │
│  │  INDEX 1: Player Stats (Pinecone)   │  │
│  │  ├─ Embedding: all-MiniLM-L6-v2     │  │
│  │  ├─ Top-K: 5 results                │  │
│  │  └─ Time: ~50ms                     │  │
│  │                                      │  │
│  │  INDEX 2: Match History (Pinecone)  │  │
│  │  ├─ Filters: last_5_matches         │  │
│  │  ├─ Top-K: 3 results                │  │
│  │  └─ Time: ~40ms                     │  │
│  │                                      │  │
│  │  INDEX 3: Venue Data (BM25)         │  │
│  │  ├─ Keyword matching                │  │
│  │  ├─ Top-K: 2 results                │  │
│  │  └─ Time: ~10ms                     │  │
│  │                                      │  │
│  │  INDEX 4: Real-time News (Tavily)   │  │
│  │  ├─ API call to news aggregator     │  │
│  │  ├─ Top-K: 2 results                │  │
│  │  └─ Time: ~200ms                    │  │
│  │                                      │  │
│  └───────────┬──────────────────────────┘  │
│              ↓                              │
│  [Re-Ranker] ← Cohere Rerank (FREE tier)   │
│              ↓                              │
│  [Context Builder] ← Top 5 most relevant    │
│              ↓                              │
│  [LLM Generation] ← Gemini/Claude           │
│              ↓                              │
│  OUTPUT: "Virat averages 58 at Wankhede..." │
│                                             │
│  TOTAL TIME: ~300ms (vs 2-5 sec sequential) │
│                                             │
└─────────────────────────────────────────────┘
```

**Performance Optimization:**
- **Parallel queries:** 4 indexes queried simultaneously (asyncio)
- **Edge caching:** Cloudflare KV caches results (5-min TTL)
- **Semantic caching:** Similar queries return cached embeddings

---

## 7. Data Ingestion & Scraping

```
┌─────────────────────────────────────────────┐
│         SELF-HEALING SCRAPER                │
├─────────────────────────────────────────────┤
│                                             │
│  [Render Cron Job] ← Every 30 sec (match)   │
│          ↓                                  │
│  ┌────────────────────────────────────┐    │
│  │  PLAYWRIGHT BROWSER                │    │
│  │  ├─ Chromium (headless)            │    │
│  │  ├─ Stealth mode (anti-detection)  │    │
│  │  └─ Proxy rotation (Bright Data)   │    │
│  └───────────┬────────────────────────┘    │
│              ↓                              │
│  [AI Extraction] ← DeepSeek sees page       │
│              ↓                              │
│  [Data Validation] ← Claude checks quality  │
│              ↓                              │
│  ┌────────────────────────────────────┐    │
│  │  IF SCRAPER BREAKS:                │    │
│  │  1. Claude analyzes HTML diff      │    │
│  │  2. Rewrites CSS selector          │    │
│  │  3. Auto-commits fix to GitHub     │    │
│  │  4. Deploys in 30 sec              │    │
│  └────────────────────────────────────┘    │
│              ↓                              │
│  [Store in Turso] ← ACID transactions       │
│              ↓                              │
│  [Trigger Webhooks] ← Supabase Realtime     │
│                                             │
└─────────────────────────────────────────────┘
```

**Self-Healing Example:**
```python
try:
    score = page.locator('.cb-scr-wll-chvrn').text_content()
except Exception as e:
    # AI fixes the selector
    new_selector = claude.fix_selector(
        error=str(e),
        html=page.content()
    )
    # Auto-deploy fix
    update_code(new_selector)
    deploy()
```

---

## Infrastructure

### Deployment Architecture

```
┌─────────────────────────────────────────────┐
│          MULTI-CLOUD STRATEGY               │
├─────────────────────────────────────────────┤
│                                             │
│  PRIMARY: Cloudflare Workers (Edge)         │
│  ├─ Deployment: wrangler deploy             │
│  ├─ Regions: 300+ globally                  │
│  ├─ Cost: ₹0 (100K req/day)                 │
│  └─ Fallback: Vercel Edge Functions         │
│                                             │
│  BACKEND: Render (US East)                  │
│  ├─ Deployment: git push → auto-deploy      │
│  ├─ Cost: ₹0 (FREE tier) → ₹560/mo (paid)   │
│  └─ Fallback: Railway (EU)                  │
│                                             │
│  FRONTEND: Vercel (Global CDN)              │
│  ├─ Deployment: git push → auto-deploy      │
│  ├─ Cost: ₹0 (GitHub Edu PRO)               │
│  └─ Fallback: Cloudflare Pages              │
│                                             │
│  MOBILE: EAS Build (Expo)                   │
│  ├─ Deployment: eas build --platform all    │
│  ├─ Cost: ₹0 (30 builds/month)              │
│  └─ OTA Updates: eas update                 │
│                                             │
└─────────────────────────────────────────────┘
```

### Auto-Scaling Strategy

```yaml
# Kubernetes HPA (if using GKE)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-autoscaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: teamgenie-api
  minReplicas: 1
  maxReplicas: 1000
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
```

**OR Serverless (Recommended for ₹0 cost):**
```typescript
// Cloudflare Workers auto-scales 0 → ∞
// Zero configuration needed
export default {
  async fetch(request: Request): Promise<Response> {
    // Your API logic
    // Cloudflare handles scaling
  }
}
```

---

## Security Architecture

### Defense-in-Depth Strategy

```
┌─────────────────────────────────────────────┐
│         SECURITY LAYERS                     │
├─────────────────────────────────────────────┤
│                                             │
│  LAYER 1: Network (Cloudflare)              │
│  ├─ DDoS mitigation (unlimited)             │
│  ├─ WAF (OWASP Top 10 protection)           │
│  ├─ Bot detection (AI-powered)              │
│  └─ Rate limiting (10K rules)               │
│                                             │
│  LAYER 2: Application (AI Firewall)         │
│  ├─ SQL injection detection (Claude)        │
│  ├─ XSS prevention (CSP headers)            │
│  ├─ CSRF tokens (SameSite cookies)          │
│  └─ Input sanitization (Pydantic)           │
│                                             │
│  LAYER 3: Authentication (Supabase)         │
│  ├─ JWT tokens (RS256 signing)              │
│  ├─ OAuth 2.0 (Google, Apple)               │
│  ├─ MFA (TOTP, SMS)                         │
│  └─ Session management (Redis)              │
│                                             │
│  LAYER 4: Authorization (RLS)               │
│  ├─ Row-Level Security (Postgres)           │
│  ├─ Attribute-based access (ABAC)           │
│  └─ Least privilege principle               │
│                                             │
│  LAYER 5: Data (Encryption)                 │
│  ├─ At-rest: AES-256 (Turso/Supabase)       │
│  ├─ In-transit: TLS 1.3 (Cloudflare)        │
│  ├─ Secrets: Doppler + Infisical            │
│  └─ PII tokenization (payment data)         │
│                                             │
│  LAYER 6: Monitoring (AI Auditor)           │
│  ├─ Anomaly detection (Axiom + Claude)      │
│  ├─ Threat intelligence (Cloudflare)        │
│  ├─ Audit logs (immutable, 90-day)          │
│  └─ Incident response (automated)           │
│                                             │
└─────────────────────────────────────────────┘
```

### Threat Model

| Threat | Mitigation | Residual Risk |
|---|---|---|
| **DDoS Attack** | Cloudflare (survived 26M req/sec) | Low |
| **SQL Injection** | Pydantic validation + parameterized queries | Very Low |
| **XSS** | CSP headers + input sanitization | Low |
| **CSRF** | SameSite cookies + origin validation | Very Low |
| **Account Takeover** | MFA + rate limiting + device fingerprinting | Low |
| **Data Breach** | Encryption at rest + RLS + audit logs | Low |
| **API Abuse** | Rate limiting + AI firewall | Medium |
| **Insider Threat** | Least privilege + audit logs | Medium |

---

## Monitoring & Observability

### Metrics Collection

```
┌─────────────────────────────────────────────┐
│       OBSERVABILITY STACK (FREE)            │
├─────────────────────────────────────────────┤
│                                             │
│  LOGS: Axiom (1TB/month FREE)               │
│  ├─ Structured JSON logs                    │
│  ├─ Real-time streaming                     │
│  ├─ 90-day retention                        │
│  └─ AI anomaly detection                    │
│                                             │
│  ERRORS: Sentry (5K errors/month FREE)      │
│  ├─ Full stack traces                       │
│  ├─ Session replay                          │
│  ├─ Performance monitoring                  │
│  └─ AI auto-grouping                        │
│                                             │
│  ANALYTICS: PostHog (1M events/month FREE)  │
│  ├─ Product analytics                       │
│  ├─ Feature flags                           │
│  ├─ A/B testing                             │
│  └─ Session recordings                      │
│                                             │
│  UPTIME: Better Stack (FREE)                │
│  ├─ HTTP checks (1-min interval)            │
│  ├─ SSL monitoring                          │
│  ├─ Status page (status.teamgenie.app)      │
│  └─ Incident management                     │
│                                             │
│  TRACING: OpenTelemetry → Axiom             │
│  ├─ Distributed tracing                     │
│  ├─ Request correlation                     │
│  ├─ Performance profiling                   │
│  └─ Dependency mapping                      │
│                                             │
└─────────────────────────────────────────────┘
```

### AI-Powered Alerts

```python
# Anomaly detection via Claude
async def detect_anomaly(metrics: dict):
    analysis = await claude.analyze(f"""
    Current metrics:
    - Request rate: {metrics['req_per_sec']} req/sec
    - Error rate: {metrics['error_rate']}%
    - Latency p95: {metrics['latency_p95']}ms
    
    Historical baseline:
    - Request rate: 150 req/sec (±20)
    - Error rate: 0.1% (±0.05)
    - Latency p95: 320ms (±50)
    
    Is this an anomaly? If yes, severity (low/medium/high)?
    """)
    
    if analysis.is_anomaly and analysis.severity == "high":
        await alert_telegram("🚨 Anomaly detected")
        await auto_rollback()  # Self-healing
```

---

## Data Flow Diagrams

### Team Generation Flow

```
┌──────────┐
│   USER   │
└────┬─────┘
     │ POST /api/team/generate
     ↓
┌─────────────────┐
│  CLOUDFLARE     │ ← DDoS check, rate limit
│  WAF + WORKERS  │
└────┬────────────┘
     │
     ↓
┌─────────────────┐
│  AI FIREWALL    │ ← Claude analyzes request
└────┬────────────┘
     │ ✅ Safe
     ↓
┌─────────────────┐
│  FASTAPI        │
│  /team/generate │
└────┬────────────┘
     │
     ├───→ Check Redis cache
     │     └─ Hit? Return cached
     │
     ├───→ Query Turso (player data)
     │
     ├───→ Query Pinecone (RAG context)
     │
     ↓
┌─────────────────┐
│  CREWAI         │ ← 3 agents collaborate
│  ORCHESTRATOR   │
└────┬────────────┘
     │
     ├───→ Agent 1: Budget optimizer
     ├───→ Agent 2: Differential expert
     └───→ Agent 3: Risk manager
     │
     ↓
┌─────────────────┐
│  CONSENSUS      │ ← Weighted voting
└────┬────────────┘
     │
     ├───→ Personalize to user
     ├───→ Cache in Redis (10 min)
     ├───→ Log to Axiom
     ├───→ Track in PostHog
     │
     ↓
┌─────────────────┐
│  RESPONSE       │
│  {team: [...]}  │
└─────────────────┘
```

---

## Technology Decision Records (ADRs)

### ADR-001: Why FastAPI over Node.js?

**Context:** Need async backend with AI integration.  
**Decision:** FastAPI (Python)  
**Rationale:**
- **AI Ecosystem:** LangChain, CrewAI, scikit-learn all Python-first
- **Async Support:** ASGI (same concurrency as Node.js)
- **Type Safety:** Pydantic (better than Zod/io-ts)
- **Performance:** Uvicorn competitive with Node.js (10K req/sec)
- **Developer Velocity:** Founder's expertise (2-day vs 2-week)

**Consequences:**
- ✅ Faster AI integration
- ✅ Type-safe by default
- ⚠️ Larger Docker images (500MB vs 200MB Node)
- ⚠️ Fewer frontend devs familiar with Python

**Status:** Accepted

---

### ADR-002: Multi-Agent Architecture

**Context:** Single LLM produces generic, non-personalized teams.  
**Decision:** CrewAI multi-agent system (3 agents)  
**Rationale:**
- **Specialization:** Each agent expert in one domain
- **Debate Mechanism:** Agents vote, reach consensus
- **Cost Efficiency:** Route easy tasks to free LLMs
- **Competitive Moat:** Rare expertise (5% of engineers)
- **Better Accuracy:** 72% vs 55% single-LLM

**Consequences:**
- ✅ Higher accuracy
- ✅ Personalization capability
- ⚠️ More complex (3 LLM calls vs 1)
- ⚠️ Higher latency (5 sec vs 2 sec)

**Status:** Accepted

---

### ADR-003: Turso over Supabase as Primary DB

**Context:** Need 9GB+ storage, Supabase free tier is 500MB.  
**Decision:** Turso (LibSQL) as primary, Supabase for auth only  
**Rationale:**
- **Storage:** 9GB free (18x more than Supabase)
- **Edge Replication:** Multi-region by default
- **Cost:** $0 until 9GB (vs Supabase $25/month for 8GB)
- **Performance:** SQLite is fast (10K writes/sec)
- **Compatibility:** SQL, works with existing ORMs

**Consequences:**
- ✅ 18x more free storage
- ✅ Lower latency (edge replicas)
- ⚠️ Less mature than Postgres
- ⚠️ No realtime (use Supabase for that)

**Status:** Accepted

---

## Disaster Recovery Plan

### RTO/RPO Targets

| Scenario | RTO (Recovery Time) | RPO (Data Loss) |
|---|---|---|
| **API Outage** | 5 minutes (auto-failover) | 0 (stateless) |
| **Database Corruption** | 10 minutes (PITR) | 5 minutes (backup frequency) |
| **Data Center Failure** | 30 seconds (multi-region) | 0 (replicated) |
| **Complete Deletion** | 24 hours (restore from S3) | 1 hour (backup lag) |

### Backup Strategy

```yaml
Databases:
  Turso:
    frequency: "Every 5 minutes (point-in-time recovery)"
    retention: "30 days"
    location: "AMS, SIN, IAD (multi-region)"
    
  Supabase:
    frequency: "Daily snapshots"
    retention: "7 days"
    location: "AWS S3 (encrypted)"
    
Code:
  GitHub:
    frequency: "Every commit"
    retention: "Forever"
    
Secrets:
  Doppler:
    frequency: "Real-time sync"
    retention: "90-day audit log"
```

---

## Performance Budget

| Metric | Target | Acceptable | Critical |
|---|---|---|---|
| **Page Load (Web)** | <1 sec | <2 sec | >3 sec |
| **API Response (p95)** | <300ms | <500ms | >1 sec |
| **Team Generation** | <5 sec | <8 sec | >10 sec |
| **Mobile App Launch** | <2 sec | <3 sec | >5 sec |
| **Time to Interactive** | <2 sec | <4 sec | >6 sec |
| **Lighthouse Score** | >90 | >75 | <60 |

**Monitoring:** PostHog Real User Monitoring (RUM)

---

## Scalability Projections

| Users | Requests/Day | DB Size | AI Calls/Day | Monthly Cost |
|---|---|---|---|---|
| **1,000** | 10,000 | 500MB | 1,000 | ₹0 (free tier) |
| **10,000** | 100,000 | 2GB | 10,000 | ₹500 |
| **50,000** | 500,000 | 8GB | 50,000 | ₹2,000 |
| **100,000** | 1,000,000 | 15GB | 100,000 | ₹10,000 |
| **500,000** | 5,000,000 | 50GB | 500,000 | ₹50,000 |

**Key Insight:** 98% gross margin maintained even at 500K users.

---

## Appendix: Tech Stack Versions

```json
{
  "frontend": {
    "next": "14.1.0",
    "react": "18.2.0",
    "typescript": "5.3.3",
    "tailwindcss": "3.4.1"
  },
  "backend": {
    "python": "3.11.7",
    "fastapi": "0.109.0",
    "uvicorn": "0.27.0",
    "pydantic": "2.5.3"
  },
  "ai": {
    "langchain": "0.1.4",
    "crewai": "0.1.20",
    "openai": "1.10.0",
    "anthropic": "0.8.1"
  },
  "databases": {
    "turso": "0.4.1",
    "supabase-py": "2.2.0",
    "redis": "5.0.1"
  },
  "deployment": {
    "docker": "24.0.7",
    "kubernetes": "1.28.4",
    "wrangler": "3.24.0"
  }
}
```

---

**Document Maintained By:** Mohammed Inayat Hussain Qureshi  
**Last Review:** January 2026  
**Next Review:** March 2026
