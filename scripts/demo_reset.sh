#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================================="
echo " DepoSafe: Automated Demo Environment Reset"
echo "=========================================================="

cd "${PROJECT_ROOT}"

echo "[1/4] Clearing application and test caches..."
rm -rf backend/.pytest_cache frontend/.next/cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "[2/4] Resetting SQLite database to clean genesis state..."
rm -f deposafe.db

echo "[3/4] Reseeding database from synthetic ground-truth dataset..."
PYTHONPATH=. backend/venv/bin/python3 data/seed_loader.py

echo "[4/4] Verifying Demo Clock reset to base date..."
PYTHONPATH=. backend/venv/bin/python3 -c "
from backend.app.core.database import SessionLocal
from backend.app.services.demo_clock import get_simulated_today
db = SessionLocal()
print('  -> Demo Clock current date:', get_simulated_today(db))
db.close()
"

echo "=========================================================="
echo " Demo reset complete! Clean database and demo clock ready."
echo "=========================================================="
