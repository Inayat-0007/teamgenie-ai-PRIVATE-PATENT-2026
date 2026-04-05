#!/bin/bash
# ============================================
# TeamGenie AI — Production Deploy
# Usage: ./scripts/deploy.sh [staging|production]
# ============================================

set -euo pipefail

ENV=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# Validate environment
if [[ "$ENV" != "staging" && "$ENV" != "production" ]]; then
    error "Invalid environment: $ENV. Use 'staging' or 'production'."
    exit 1
fi

log "🚀 Deploying TeamGenie AI to ${ENV} (${TIMESTAMP})..."

# ------
# Step 1: Pre-flight checks
# ------
log "🔍 Running pre-flight checks..."

# Ensure clean git state for production
if [[ "$ENV" == "production" ]]; then
    if [[ -n "$(git -C "$ROOT_DIR" status --porcelain)" ]]; then
        error "Working directory has uncommitted changes. Commit or stash before production deploy."
        exit 1
    fi

    CURRENT_BRANCH=$(git -C "$ROOT_DIR" rev-parse --abbrev-ref HEAD)
    if [[ "$CURRENT_BRANCH" != "main" ]]; then
        error "Production deploys must be from 'main' branch. Current: ${CURRENT_BRANCH}"
        exit 1
    fi
fi

# ------
# Step 2: Run tests
# ------
log "🧪 Running backend tests..."
(cd "$ROOT_DIR/apps/api" && python -m pytest tests/ -q --tb=short) || {
    error "Backend tests failed. Aborting deploy."
    exit 1
}

log "🔍 Running frontend lint..."
(cd "$ROOT_DIR/apps/web" && npx next lint --quiet) || {
    warn "Frontend lint warnings detected (non-blocking)."
}

# ------
# Step 3: Deploy backend (Render auto-deploys via git push)
# ------
if [[ "$ENV" == "production" ]]; then
    log "📡 Backend: Render auto-deploys from main branch"
else
    log "📡 Backend: Render auto-deploys from develop branch"
fi

# ------
# Step 4: Deploy frontend
# ------
log "🌐 Deploying frontend to Vercel..."
if [[ "$ENV" == "production" ]]; then
    (cd "$ROOT_DIR/apps/web" && npx vercel --prod --yes)
else
    (cd "$ROOT_DIR/apps/web" && npx vercel --yes)
fi

# ------
# Step 5: Deploy edge functions (if configured)
# ------
if command -v wrangler >/dev/null 2>&1; then
    log "⚡ Deploying Cloudflare Workers..."
    (cd "$ROOT_DIR/infra" && wrangler deploy)
else
    warn "Wrangler not installed. Skipping edge function deploy."
fi

# ------
# Step 6: Post-deploy verification
# ------
log "🏥 Running post-deploy health check..."
sleep 5

HEALTH_URL="https://api.teamgenie.app/health"
if [[ "$ENV" == "staging" ]]; then
    HEALTH_URL="https://staging-api.teamgenie.app/health"
fi

if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    log "✅ Health check passed!"
else
    warn "⚠️  Health check failed. The API may still be starting up."
fi

echo ""
log "✅ Deployment to ${ENV} complete! (${TIMESTAMP})"
echo "   Frontend: https://teamgenie.app"
echo "   Backend:  https://api.teamgenie.app"
echo "   Status:   https://status.teamgenie.app"
echo "   Docs:     https://api.teamgenie.app/docs"
