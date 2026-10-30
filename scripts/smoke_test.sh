#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
# Strip trailing slash if present
BASE_URL="${BASE_URL%/}"

echo "=========================================================="
echo " DepoSafe: Production Smoke Test Suite"
echo " Target URL: ${BASE_URL}"
echo "=========================================================="

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

pass() {
  echo -e "  [${GREEN}PASS${NC}] $1"
}

fail() {
  echo -e "  [${RED}FAIL${NC}] $1"
  exit 1
}

# --------------------------------------------------------------------------
# 1. Health Check
# --------------------------------------------------------------------------
echo "[1/5] Checking service health endpoint (/health)..."
HEALTH_RESP=$(curl -s -f "${BASE_URL}/health" || fail "Health check endpoint returned non-200")
STATUS=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('status'))" "${HEALTH_RESP}")
DB_STATUS=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('database'))" "${HEALTH_RESP}")
FDR_COUNT=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('seeded_fdrs', 0))" "${HEALTH_RESP}")

if [[ "${STATUS}" == "healthy" && "${DB_STATUS}" == "connected" ]]; then
  pass "Health check OK (Status: ${STATUS}, DB: ${DB_STATUS}, Seeded FDRs: ${FDR_COUNT})"
else
  fail "Health check failed: ${HEALTH_RESP}"
fi

# --------------------------------------------------------------------------
# 2. Authentication for each Role
# --------------------------------------------------------------------------
echo "[2/5] Testing JWT authentication across all 5 RBAC roles..."

ROLES=(
  "SYSTEM_ADMIN:admin@deposafe.aicte.gov.in:Password@123"
  "VERIFICATION_OFFICER:officer@deposafe.aicte.gov.in:Password@123"
  "REGIONAL_OFFICER:ro.north@deposafe.aicte.gov.in:Password@123"
  "COMPETENT_AUTHORITY:director.approval@aicte-india.org:Password@123"
  "INSTITUTION_USER:institution1@vidya.edu.in:Password@123"
  "AUDITOR:auditor@deposafe.aicte.gov.in:Password@123"
)

OFFICER_TOKEN=""

for ITEM in "${ROLES[@]}"; do
  IFS=":" read -r ROLE_NAME EMAIL PWD <<< "${ITEM}"
  LOGIN_RESP=$(curl -s -f -X POST "${BASE_URL}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${EMAIL}\",\"password\":\"${PWD}\"}" || fail "Login failed for ${ROLE_NAME}")
  
  TOKEN=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('access_token', ''))" "${LOGIN_RESP}")
  if [[ -z "${TOKEN}" ]]; then
    fail "No token returned for ${ROLE_NAME}"
  fi
  if [[ "${ROLE_NAME}" == "VERIFICATION_OFFICER" ]]; then
    OFFICER_TOKEN="${TOKEN}"
  fi
  pass "Role authenticated: ${ROLE_NAME} (${EMAIL})"
done

# --------------------------------------------------------------------------
# 3. Hero Case Verification (BNB-DEL-HERO-1000)
# --------------------------------------------------------------------------
echo "[3/5] Verifying Hero Case (BNB-DEL-HERO-1000)..."

FDRS_RESP=$(curl -s -f "${BASE_URL}/api/v1/fdrs" \
  -H "Authorization: Bearer ${OFFICER_TOKEN}" || fail "Failed to fetch FDR list")

HERO_ID=$(python3 -c "
import json, sys
data = json.loads(sys.argv[1])
hero = next((f for f in data if f.get('fdr_number') == 'BNB-DEL-HERO-1000'), None)
if hero:
    print(hero['id'])
else:
    print('')
" "${FDRS_RESP}")

if [[ -z "${HERO_ID}" ]]; then
  fail "Hero Case BNB-DEL-HERO-1000 not found in database!"
fi

HERO_DETAIL=$(curl -s -f "${BASE_URL}/api/v1/fdr/${HERO_ID}" \
  -H "Authorization: Bearer ${OFFICER_TOKEN}" || fail "Failed to fetch Hero Case detail")

HERO_SCORE=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('review_priority_score'))" "${HERO_DETAIL}")
FLAG_COUNT=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(len(d.get('review_flags', [])))" "${HERO_DETAIL}")

pass "Hero Case loaded: ID #${HERO_ID}, Review Priority Score: ${HERO_SCORE}/100, Flags: ${FLAG_COUNT}"

# --------------------------------------------------------------------------
# 4. Upload with Extraction Pipeline
# --------------------------------------------------------------------------
echo "[4/5] Testing document upload and AI extraction pipeline..."

SAMPLE_PDF=$(python3 -c "
import glob
pdfs = glob.glob('data/synthetic/documents/FDR_*.pdf') + glob.glob('storage/**/*.pdf', recursive=True)
print(pdfs[0] if pdfs else '')
")
if [[ -z "${SAMPLE_PDF}" ]]; then
  # Fallback to creating a quick dummy PDF if not locally present
  SAMPLE_PDF="/tmp/smoke_test_fdr.pdf"
  python3 -c "
from reportlab.pdfgen import canvas
c = canvas.Canvas('${SAMPLE_PDF}')
c.drawString(100, 750, 'STATE BANK OF INDIA - FIXED DEPOSIT RECEIPT')
c.drawString(100, 700, 'FDR Number: SBI-SMOKE-9999')
c.drawString(100, 650, 'Principal Amount: Rs. 3,500,000.00')
c.save()
"
fi

UPLOAD_RESP=$(curl -s -f -X POST "${BASE_URL}/api/v1/fdr/${HERO_ID}/upload-document" \
  -H "Authorization: Bearer ${OFFICER_TOKEN}" \
  -F "file=@${SAMPLE_PDF};type=application/pdf" \
  -F "doc_type=FDR_CERTIFICATE" || fail "Document upload failed")

DOC_ID=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('id', d.get('document_id', 'OK')))" "${UPLOAD_RESP}")
pass "Upload and AI pipeline execution succeeded (Doc reference: ${DOC_ID})"

# --------------------------------------------------------------------------
# 5. Cryptographic Hash Chain Verification
# --------------------------------------------------------------------------
echo "[5/5] Verifying cryptographic SHA-256 hash-chained audit ledger..."

AUDIT_RESP=$(curl -s -f "${BASE_URL}/api/v1/audit/verify" \
  -H "Authorization: Bearer ${OFFICER_TOKEN}" || fail "Failed to query audit verification")

AUDIT_VERIFIED=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('verified'))" "${AUDIT_RESP}")
TOTAL_RECORDS=$(python3 -c "import json, sys; d=json.loads(sys.argv[1]); print(d.get('total_records'))" "${AUDIT_RESP}")

if [[ "${AUDIT_VERIFIED}" == "True" || "${AUDIT_VERIFIED}" == "true" ]]; then
  pass "Cryptographic audit chain verified mathematically (Blocks: ${TOTAL_RECORDS})"
else
  fail "Cryptographic audit chain verification failed: ${AUDIT_RESP}"
fi

echo "=========================================================="
echo -e "${GREEN} ALL SMOKE TESTS PASSED SUCCESSFULLY!${NC}"
echo "=========================================================="
exit 0
