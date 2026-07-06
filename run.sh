#!/usr/bin/env bash
# ─────────────────────────────────────────────
# run.sh — Script untuk menjalankan server
# ─────────────────────────────────────────────
set -e

# Pastikan virtual environment aktif
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment tidak aktif."
    echo "   Jalankan: source venv/bin/activate  (Linux/macOS)"
    echo "            .\\venv\\Scripts\\activate   (Windows)"
    exit 1
fi

# Load .env jika ada
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting Dies Maintenance API..."
echo "   Docs: http://localhost:8000/docs"

uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
