#!/bin/bash
# ============================================
# TeamGenie AI — Production Deploy
# Usage: ./scripts/deploy.sh [staging|production]
# ============================================

set -e

ENV=${1:-staging}
echo "🚀 Deploying TeamGenie AI to $ENV..."

# Run tests first
echo "🧪 Running tests..."
cd apps/api && python -m pytest tests/ -q && cd ../..
cd apps/web && npx next lint && cd ../..

# Deploy backend (Render auto-deploys via git push)
echo "📡 Backend: Render auto-deploys from main branch"

# Deploy frontend
echo "🌐 Deploying frontend to Vercel..."
if [ "$ENV" = "production" ]; then
    cd apps/web && npx vercel --prod && cd ../..
else
    cd apps/web && npx vercel && cd ../..
fi

# Deploy edge functions (if configured)
if command -v wrangler >/dev/null 2>&1; then
    echo "⚡ Deploying Cloudflare Workers..."
    cd infra && wrangler deploy && cd ..
fi

echo ""
echo "✅ Deployment to $ENV complete!"
echo "   Frontend: https://teamgenie.app"
echo "   Backend:  https://api.teamgenie.app"
echo "   Status:   https://status.teamgenie.app"
