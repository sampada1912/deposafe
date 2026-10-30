#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================================="
echo " DepoSafe: Pre-Demo Health & Integrity Verification Check"
echo "=========================================================="

cd "${PROJECT_ROOT}"

# 1. Check Backend Health Endpoint
echo "[1/4] Checking backend health endpoint (http://localhost:8000/health)..."
if ! curl -sf http://127.0.0.1:8000/health >/dev/null && ! curl -sf http://localhost:8000/health >/dev/null; then
  echo "[-] ERROR: Backend API is not responding on http://localhost:8000/health"
  echo "    Ensure backend is running (e.g., make run-backend)"
  exit 1
fi
echo "  [OK] Backend health check passed."

# 2. Check Seeded Database Record Counts
echo "[2/4] Verifying seeded database record counts..."
PYTHONPATH=. backend/venv/bin/python3 -c "
import sys
from backend.app.core.database import SessionLocal
from backend.app.models.deposafe_models import Institution, FDR, User

db = SessionLocal()
inst_count = db.query(Institution).count()
fdr_count = db.query(FDR).count()
user_count = db.query(User).count()
db.close()

print(f'  -> Institutions: {inst_count} (expected >= 80)')
print(f'  -> FDRs:         {fdr_count} (expected >= 164)')
print(f'  -> Users:        {user_count} (expected >= 6)')

if inst_count < 80 or fdr_count < 164 or user_count < 6:
    print('[-] ERROR: Insufficient seeded data in database!')
    sys.exit(1)
"
echo "  [OK] Database record counts verified."

# 3. Verify Hero Demo Case Exists and Loads
echo "[3/4] Verifying Hero Demo Case (BNB-DEL-HERO-1000)..."
PYTHONPATH=. backend/venv/bin/python3 -c "
import sys
from backend.app.core.database import SessionLocal
from backend.app.models.deposafe_models import FDR

db = SessionLocal()
hero = db.query(FDR).filter(FDR.fdr_number == 'BNB-DEL-HERO-1000').first()
db.close()

if not hero:
    print('[-] ERROR: Hero Case FDR BNB-DEL-HERO-1000 not found in database!')
    sys.exit(1)

print(f'  -> Found Hero FDR #{hero.id}: {hero.fdr_number} (Amount: Rs {hero.amount:,.2f})')
print(f'  -> Bank: {hero.bank_name}, Branch: {hero.branch_name}')
"
echo "  [OK] Hero Case successfully verified."

# 4. Verify Cryptographic Hash Chain Audit Integrity
echo "[4/4] Verifying SHA-256 cryptographic audit chain mathematical integrity..."
PYTHONPATH=. backend/venv/bin/python3 -c "
import sys
from backend.app.core.database import SessionLocal
from backend.app.services.audit_service import verify_audit_chain

db = SessionLocal()
res = verify_audit_chain(db)
db.close()

print(f'  -> Verified:     {res.get(\"verified\")}')
print(f'  -> Total Blocks: {res.get(\"total_records\")}')
print(f'  -> Message:      {res.get(\"message\")}')

if not res.get('verified', False):
    print('[-] ERROR: Audit hash chain integrity check failed!')
    sys.exit(1)
"
echo "  [OK] Cryptographic hash chain verified."

echo "=========================================================="
echo " ALL CHECKS PASSED: Environment is 100% ready for demo!"
echo "=========================================================="
exit 0

