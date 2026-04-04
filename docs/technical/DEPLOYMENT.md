# 🚀 TeamGenie Deployment Guide

**Target:** Production (https://teamgenie.app)  
**Last Updated:** January 2026

---

## Prerequisites

```bash
# Required tools
node >= 20.0.0
python >= 3.11
bun >= 1.0.0
git >= 2.40.0

# Accounts needed (all FREE)
# GitHub, Vercel, Render, Cloudflare, Supabase,
# Turso, Upstash, Pinecone, Doppler
```

---

## Step 1: Clone & Install

```bash
git clone https://github.com/Inayat-0007/teamgenie-ai.git
cd teamgenie-ai

# Install dependencies
bun install                                    # Root (Turborepo)
cd apps/api && pip install -r requirements.txt # Backend
cd apps/web && bun install                     # Frontend
cd apps/mobile && bun install                  # Mobile
```

---

## Step 2: Environment Variables

```bash
# Copy example files
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# For production, use Doppler:
curl -Ls https://cli.doppler.com/install.sh | sh
doppler login
doppler setup
doppler secrets download --no-file --format env > .env
```

---

## Step 3: Database Setup

### Turso (Primary Database)
```bash
curl -sSfL https://get.tur.so/install.sh | bash
turso auth login
turso db create teamgenie --location ams   # Amsterdam
turso db show teamgenie                    # Copy URL & token to .env
turso db shell teamgenie < db/migrations/001_initial_schema.sql
```

### Supabase (Auth Database)
```bash
# Create project at https://supabase.com
# Region: Singapore | Plan: Free tier
# Copy SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY to .env
npx supabase db push
```

### Pinecone (Vector Database)
```bash
# Create account at https://pinecone.io
# Create index: player-embeddings, 384 dimensions, cosine metric
# Copy PINECONE_API_KEY to .env
```

### Upstash Redis (Cache)
```bash
# Create at https://upstash.com
# Name: teamgenie-cache | Region: Global
# Copy UPSTASH_REDIS_URL to .env
```

---

## Step 4: Deploy Backend (Render)

```yaml
# GitHub Integration (recommended):
# 1. Push to GitHub
# 2. Go to render.com → New Web Service → Connect GitHub repo

Name: teamgenie-api
Region: Singapore
Branch: main
Root Directory: apps/api
Runtime: Python 3.11
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT

# Add environment variables from .env
# Deploy: $0/month (free tier) → $7/month for 24/7
```

---

## Step 5: Deploy Frontend (Vercel)

```yaml
# GitHub Integration (auto-deploy on push):
# 1. Go to vercel.com → Import Git Repository
# 2. Select: Inayat-0007/teamgenie-ai

Framework Preset: Next.js
Root Directory: apps/web
Build Command: bun run build
Install Command: bun install

# Environment Variables:
NEXT_PUBLIC_API_URL=https://teamgenie-api.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://XXXXX.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
```

**CLI Alternative:**
```bash
npm install -g vercel
vercel login
cd apps/web && vercel --prod
```

---

## Step 6: Deploy Mobile App

### Android (Google Play Store)
```bash
cd apps/mobile
eas build --platform android --profile production
# Upload APK to Google Play Console → Submit for review (7-14 days)
```

### iOS (App Store)
```bash
eas build --platform ios --profile production
# Upload IPA via Transporter → App Store Connect → Submit (2-7 days)
```

### OTA Updates (bypass app store review)
```bash
eas update --branch production --message "Bug fixes"
```

---

## Step 7: Cloudflare Setup

### DNS Configuration
```
Type: CNAME | Name: @   | Target: cname.vercel-dns.com      | Proxy: ✅
Type: CNAME | Name: api | Target: teamgenie-api.onrender.com | Proxy: ✅
Type: CNAME | Name: www | Target: teamgenie.app              | Proxy: ✅
```

### Security Rules (WAF)
```
Rule 1: Block bots → (cf.bot_management.score < 30) → Block
Rule 2: Rate limit login → (/api/auth/login) → 10 req/min → Challenge
Rule 3: Block SQLi → (query contains "UNION SELECT") → Block
```

---

## Step 8: Monitoring Setup

| Service | Purpose | Setup |
|---|---|---|
| **Axiom** | Logs (1TB/mo free) | Copy AXIOM_TOKEN to .env |
| **Sentry** | Errors (5K/mo free) | Copy SENTRY_DSN to .env |
| **PostHog** | Analytics (1M events free) | Copy POSTHOG_API_KEY to .env |
| **Better Stack** | Uptime monitoring | Add https://api.teamgenie.app/health |

---

## Step 9: Payment Gateway (Razorpay)

```bash
# 1. Create account at razorpay.com
# 2. Complete KYC → Activate live mode
# 3. Copy keys to .env:
RAZORPAY_KEY_ID=rzp_live_XXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXX

# 4. Configure webhook:
# URL: https://api.teamgenie.app/api/webhooks/razorpay
# Events: payment.captured, subscription.charged
```

---

## Step 10: CI/CD Pipeline

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: '3.11' }
      - run: pip install -r apps/api/requirements.txt
      - run: pytest apps/api/tests
      - run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
  
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: oven-sh/setup-bun@v1
      - run: bun install
      - run: cd apps/web && bun run build
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## Step 11: Final Health Checks

```bash
# API health
curl https://api.teamgenie.app/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Frontend
curl -I https://teamgenie.app
# Expected: 200 OK

# Auth test
curl -X POST https://api.teamgenie.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass"}'

# Load test
k6 run scripts/load-test.js
```

---

## Rollback Procedure

```bash
# Frontend (Vercel)
vercel rollback

# Backend (Render)
# Dashboard → Deployments → Rollback to previous

# Database (Turso)
turso db restore teamgenie /backups/latest.db

# Mobile (OTA)
eas update --branch production --message "Rollback to v1.0.0"
```

---

## Scaling Guide

| Users | Action | Cost |
|---|---|---|
| **1K-10K** | Free tiers, upgrade Render to $7/mo | ~₹0-560/mo |
| **10K-50K** | Upgrade Turso Pro ($25), Upstash paid ($10) | ~₹3K/mo |
| **50K-100K** | Add load balancer, Pinecone paid ($70) | ~₹10K/mo |
| **100K+** | Move to Kubernetes (GKE), dedicated DB | ~₹50K/mo |

---

## Troubleshooting

| Issue | Solution |
|---|---|
| **502 Bad Gateway** | Check Render logs, ensure `$PORT` is used |
| **CORS Error** | Verify `ALLOWED_ORIGINS` matches frontend URL exactly |
| **Rate Limit Exceeded** | Check Cloudflare WAF rules, whitelist your IP |
| **DB Migration Failed** | Check syntax, rollback: `turso db restore` |
| **SSL Error** | Enable "Always Use HTTPS" in Cloudflare SSL/TLS |

---

**Support:** devops@teamgenie.app | **Emergency:** Telegram @teamgenie_oncall  
**Maintained By:** Mohammed Inayat Hussain Qureshi | **Last Updated:** January 2026
