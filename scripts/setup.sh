#!/bin/bash
# ============================================
# TeamGenie AI — One-Command Setup
# Usage: ./scripts/setup.sh
# ============================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}✅${NC} $*"; }
warn() { echo -e "${YELLOW}⚠️${NC} $*"; }
error() { echo -e "${RED}❌${NC} $*" >&2; }

echo ""
echo "🏏 TeamGenie AI — Setup Starting..."
echo "===================================="
echo ""

# ------
# Step 1: Check prerequisites
# ------
MISSING=0
command -v node >/dev/null 2>&1 || { error "Node.js required (v18+). Install: https://nodejs.org"; MISSING=1; }
command -v python3 >/dev/null 2>&1 || { error "Python 3.11+ required."; MISSING=1; }
command -v git >/dev/null 2>&1 || { error "Git required."; MISSING=1; }

if [[ $MISSING -eq 1 ]]; then
    echo ""
    error "Missing prerequisites. Install them and re-run."
    exit 1
fi

NODE_VER=$(node -v | sed 's/v//' | cut -d. -f1)
PYTHON_VER=$(python3 --version | sed 's/Python //' | cut -d. -f1-2)
log "Prerequisites OK — Node v${NODE_VER}, Python ${PYTHON_VER}"

# ------
# Step 2: Install Node.js dependencies (Turborepo + frontend)
# ------
echo ""
echo "📦 Installing Node.js dependencies..."
cd "$ROOT_DIR"

if command -v bun >/dev/null 2>&1; then
    bun install
elif [[ -f package-lock.json ]]; then
    npm ci
else
    npm install
fi
log "Node.js dependencies installed"

# ------
# Step 3: Install Python dependencies
# ------
echo ""
echo "🐍 Installing Python dependencies..."
cd "$ROOT_DIR/apps/api"

# Create venv if it doesn't exist
if [[ ! -d venv ]]; then
    python3 -m venv venv
    log "Virtual environment created"
fi

source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
log "Python dependencies installed"

cd "$ROOT_DIR"

# ------
# Step 4: Setup environment files
# ------
echo ""
echo "🔐 Setting up environment files..."

if [[ -f .env.example ]]; then
    [[ ! -f .env ]] && cp .env.example .env && log "Created .env (edit with your API keys)" || log ".env already exists"
    [[ ! -f apps/api/.env ]] && cp .env.example apps/api/.env && log "Created apps/api/.env" || log "apps/api/.env already exists"
fi

if [[ ! -f apps/web/.env.local ]]; then
    cat > apps/web/.env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
    log "Created apps/web/.env.local"
else
    log "apps/web/.env.local already exists"
fi

# ------
# Step 5: Create data directories
# ------
echo ""
echo "📁 Creating data directories..."
mkdir -p data/{raw,processed,models,embeddings}
log "Data directories ready"

# ------
# Step 6: Playwright browsers (optional)
# ------
echo ""
if command -v playwright >/dev/null 2>&1 || python3 -c "import playwright" 2>/dev/null; then
    echo "🎭 Installing Playwright browsers..."
    playwright install chromium 2>/dev/null || python3 -m playwright install chromium 2>/dev/null || warn "Playwright install skipped"
else
    warn "Playwright not installed — scraper features will be unavailable"
fi

# ------
# Step 7: Database migrations (if Turso is configured)
# ------
if [[ -n "${TURSO_DATABASE_URL:-}" ]]; then
    echo ""
    echo "🗄️ Running database migrations..."
    cd "$ROOT_DIR/apps/api"
    python3 -c "
from db.connection import execute_query
import asyncio
with open('../../db/migrations/001_initial_schema.sql') as f:
    asyncio.run(execute_query(f.read()))
print('Migration applied')
" 2>/dev/null || warn "Turso migration skipped (check TURSO_DATABASE_URL)"
    cd "$ROOT_DIR"
fi

# ------
# Done!
# ------
echo ""
echo "===================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo ""
echo "🚀 Quick Start:"
echo "  Terminal 1: cd apps/api && source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "  Terminal 2: cd apps/web && npm run dev"
echo ""
echo "  Or with Docker:  docker compose up -d"
echo ""
echo "  API Docs:  http://localhost:8000/docs"
echo "  Frontend:  http://localhost:3000"
echo "  Adminer:   http://localhost:8080  (docker compose --profile debug up)"
echo ""
echo "📝 Don't forget to edit .env with your API keys!"
echo "===================================="
