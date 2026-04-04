#!/bin/bash
# ============================================
# TeamGenie AI — One-Command Setup
# Usage: ./scripts/setup.sh
# ============================================

set -e

echo "🏏 TeamGenie AI — Setup Starting..."
echo "===================================="

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "❌ Node.js required. Install: https://nodejs.org"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ required."; exit 1; }

echo "✅ Prerequisites checked"

# Install root dependencies (Turborepo)
echo "📦 Installing Node.js dependencies..."
if command -v bun >/dev/null 2>&1; then
    bun install
else
    npm install
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd apps/api
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate 2>/dev/null || true
pip install -r requirements.txt --quiet
cd ../..

# Copy environment files
echo "🔐 Setting up environment files..."
[ ! -f .env ] && cp .env.example .env && echo "  Created .env (edit with your API keys)"
[ ! -f apps/api/.env ] && cp .env.example apps/api/.env
[ ! -f apps/web/.env.local ] && echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > apps/web/.env.local

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/raw data/processed data/models data/embeddings

# Run database migrations (if Turso is configured)
if [ -n "$TURSO_DATABASE_URL" ]; then
    echo "🗄️ Running database migrations..."
    cd apps/api
    python3 -c "
import subprocess
subprocess.run(['turso', 'db', 'shell', 'teamgenie', '<', '../../db/migrations/001_initial_schema.sql'], check=True)
" 2>/dev/null || echo "  ⚠️ Turso migration skipped (configure TURSO_DATABASE_URL)"
    cd ../..
fi

echo ""
echo "===================================="
echo "✅ Setup Complete!"
echo ""
echo "🚀 Quick Start:"
echo "  Terminal 1: cd apps/api && uvicorn main:app --reload --port 8000"
echo "  Terminal 2: cd apps/web && bun dev"
echo ""
echo "  API:  http://localhost:8000/docs"
echo "  Web:  http://localhost:3000"
echo ""
echo "📝 Don't forget to edit .env with your API keys!"
echo "===================================="
