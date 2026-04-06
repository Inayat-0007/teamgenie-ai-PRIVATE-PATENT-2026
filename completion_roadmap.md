# TeamGenie AI 100% Production Roadmap (Open-Source Hardened)

This document outlines the complete step-by-step structure of the remaining work required to take TeamGenie AI from its current "stable backend" state to its **100% production-ready** final state. **Crucially, this phase relies exclusively on the discussed open-source, rate-limit-resistant scraping stack (Firecrawl & Lightpanda)** to bypass free-tier ceilings.

---

## Phase 1: The Live Data Pipeline (Agent 0 - Intelligence Harvester)
Right now, the platform is missing real-time sports intelligence. We will abandon traditional SaaS APIs in favor of the agreed open-source scraper stack to avoid rate limits.

* **Step 1: Deploy Open-Source Scrapers (Lightpanda & Firecrawl)** 
  * Spin up local/self-hosted instances of **Firecrawl** and **Lightpanda** to handle unmetered, high-level scraping of JS-heavy sports websites without hitting upstream API limits.
* **Step 2: Build the Harvester Script (`apps/api/workers/harvester.py`)** 
  * Create a background worker that fetches data on a cron schedule.
  * Connect the worker to Firecrawl/Lightpanda to extract live match schedules, playing XI details, weather, pitch conditions, and cricket news without restriction.
* **Step 3: Connect Harvester to Turso Database & Upstash Redis**
  * Update `matches` and `match_intelligence` tables in Turso with the freshly scraped live data.
  * Push live scores directly to Redis so the WebSockets in `apps/api/routers/match.py` can instantly broadcast them to users.

---

## Phase 2: Vector Memory Integration (Pinecone)
The AI currently uses Gemini for generation, but the "knowledge" fetching is disconnected.

* **Step 4: Generate Data Embeddings**
  * Write a utility to convert the harvested news and player stats into vector embeddings.
* **Step 5: Upsert Data to Pinecone**
  * Connect `pinecone-client` to push the generated embeddings into namespaces (`player_stats`, `match_history`, `venue_data`, `news`).
* **Step 6: Complete the RAG Service**
  * Inside `apps/api/services/rag_service.py`, replace the `TODO` stubs in `_query_player_stats`, `_query_match_history`, `_query_venue_data` and `_query_news` to execute real similarity searches against Pinecone.
* **Step 7: Implement Reranking**
  * Re-rank the vector search results based on the highest contextual relevance before passing the context to the AI model.

---

## Phase 3: Frontend Data Wiring
The backend handles real data now, but the frontend still relies on hardcoded data arrays in `/lib/api.ts`.

* **Step 8: Wire up Matches (`apps/web/app/matches/`)**
  * Update the UI to call `/api/match/upcoming` instead of the static `getMatches()` array.
* **Step 9: Wire up Player Analytics (`apps/web/app/players/`)**
  * Update the player search bar to hit the `/api/player/search` and `/api/player/{id}/stats` endpoints dynamically.
  * Connect the AI Insights button to `/api/player/{id}/insights`.
* **Step 10: State Management & UI Synchronization**
  * Ensure user active states, quotas, and preferences are synchronized correctly across the Navigation bar and Dashboard sections.

---

## Phase 4: Observability & Production Hardening
To prevent the application from failing blindly in production, telemetry must be enabled.

* **Step 11: Setup Sentry Error Tracking**
  * In `apps/api/main.py`, init the `sentry-sdk` to automatically catch and report unhandled backend exceptions.
* **Step 12: Route Protection Check**
  * Double-check that `apps/api/routers/team.py` and profile modification routes correctly validate the JWT standard and cannot be accessed easily by bots.
* **Step 13: Final Build & Deploy Strategy**
  * Clean up and minimize `package.json` and React bundles for the Web tier.
  * Ensure Python dependencies (`requirements.txt`) are isolated.
  * Finalize the Dockerfiles or deployment configs for Vercel (Frontend) and Render/Fly.io (Backend).
