# DepoSafe — Render Production Deployment Guide

This guide provides end-to-end instructions for deploying DepoSafe (Backend API + Frontend Web UI) on [Render](https://render.com).

---

## 1. Architectural Strategy & Resource Budget

| Dimension | Production Specification | Render Free Tier Allocation | Free Tier Headroom |
|---|---|---|---|
| **Backend Compute** | Python 3.11 Slim Docker (`uvicorn --workers 1`) | Free Tier Web Service (0.1 CPU, 512 MB RAM) | Fully fits (~130 MB buffer) |
| **Backend Memory** | **382.91 MB peak** (during extraction & PDF gen) | 512 MB RAM limit | **+129.09 MB headroom** |
| **Storage / DB** | Embedded SQLite + ephemeral container storage | Ephemeral disk (reset on cold restart) | Auto-reseeds in **1.57s** (< 30s target) |
| **Mock Bank** | Integrated in-process / internal router | Same backend container (0 extra services) | Saves 1 service & 150 MB RAM |
| **Frontend UI** | Next.js 14 Docker (`next start -p $PORT`) | Free Tier Web Service (0.1 CPU, 512 MB RAM) | Static routes + SSR client |
| **Cold-Start Budget** | Target: Reseed in < 30 seconds | **Actual measured: 1.57 seconds** | **5.2% of target limit** |

> [!NOTE]
> **Free Tier Ephemeral Disk & Auto-Reseeding**:
> Render free tier does not support persistent disks. DepoSafe addresses this with **automatic cold-start seeding**. When the container spins up from cold sleep with an empty database, `backend/app/main.py` detects 0 FDRs and populates all 80 institutions, 164 FDRs, and the Hero Case (`BNB-DEL-HERO-1000`) from the synthetic ground truth in **~1.5 seconds**.

---

## 2. Measured Memory Profile (Under 450 MB Target)

The backend memory was empirically profiled across all resource-intensive operations:

```
[1] Baseline process RSS:                     62.97 MB
[2] After App & TestClient initialization:    256.86 MB
[3] After Hero Case fetch (ID=156):           311.78 MB
[4] After Upload & Document AI Pipeline:      382.69 MB
[5] After Evidence Pack PDF Generation:       382.91 MB
=========================================================
PEAK BACKEND MEMORY CONSUMPTION:              382.91 MB (< 450 MB target)
```

### Instance Size Recommendation
- **Demo / Jury Evaluation / Prototype**: **Render Free Tier (512 MB RAM)** is fully sufficient. Single-worker mode (`--workers 1`) guarantees the process remains safely below 450 MB.
- **Enterprise / Bureau Production**: **Render Starter ($7/month, 512 MB - 1 GB RAM, 0.5 CPU)** or **Standard ($25/month, 2 GB RAM, 1 CPU)** with persistent disk mounted at `/data` (`DATA_DIR=/data`) to eliminate cold-start sleep delays and support concurrent officer uploads.

---

## 3. Step-by-Step Manual Actions Required in Render

Follow these exact steps in your Render web dashboard:

### Step 1: Connect GitHub Repository
1. Log in to [dashboard.render.com](https://dashboard.render.com/).
2. Navigate to **Account Settings** &rarr; **Connected Accounts** &rarr; Connect your GitHub account.
3. Ensure Render has read access to `sampada1912/deposafe`.

### Step 2: Deploy Blueprint (`render.yaml`)
1. In the Render Dashboard, click the **New +** button in the top right.
2. Select **Blueprint**.
3. Choose the `sampada1912/deposafe` repository and branch `main`.
4. Render will scan `render.yaml` and configure two services:
   - `deposafe-backend` (Docker Web Service)
   - `deposafe-frontend` (Docker Web Service)
5. Click **Apply**.

### Step 3: Configure Required Secrets (`sync: false`)
Because `SECRET_KEY` and `BANK_SIGNING_KEY` have `sync: false` in `render.yaml`, Render prompts you to provide them securely in the UI:
1. In the `deposafe-backend` service settings &rarr; **Environment** tab:
   - **`SECRET_KEY`**: Enter a strong random 32+ character string. (Generate via `openssl rand -hex 32`).
   - **`BANK_SIGNING_KEY`**: Enter a strong random 16+ character string. (Generate via `openssl rand -hex 16`).
   > [!IMPORTANT]
   > In `ENVIRONMENT=production`, the DepoSafe backend **strictly refuses to start** if the default developer keys are used. You must set custom random strings.

### Step 4: Synchronize Service URLs (Mutual Linking)
Once Render provisions the services, it assigns public HTTPS hostnames:
- Backend: `https://deposafe-backend-xxxx.onrender.com`
- Frontend: `https://deposafe-frontend-xxxx.onrender.com`

Perform the two cross-links:
1. **Frontend `NEXT_PUBLIC_API_URL`**:
   - Go to `deposafe-frontend` &rarr; **Environment**.
   - Set `NEXT_PUBLIC_API_URL` = `https://<YOUR-BACKEND-SLUG>.onrender.com/api/v1`.
   - Save changes.
2. **Backend `CORS_ORIGINS`**:
   - Go to `deposafe-backend` &rarr; **Environment**.
   - Set `CORS_ORIGINS` = `https://<YOUR-FRONTEND-SLUG>.onrender.com,http://localhost:3000`.
   - Save changes.

### Step 5: Trigger Final Build & Redeploy
1. In `deposafe-frontend`, click **Manual Deploy** &rarr; **Clear build cache & deploy** (this bakes the backend URL into client-side JS bundles).
2. In `deposafe-backend`, click **Manual Deploy** &rarr; **Deploy latest commit**.

---

## 4. Post-Deployment Verification

### 1. Automated Smoke Test
From your local terminal, run the automated smoke test suite directly against your Render production URL:
```bash
./scripts/smoke_test.sh https://<YOUR-BACKEND-SLUG>.onrender.com
```
Expected output:
```
[1/5] Checking service health endpoint (/health)...
  [PASS] Health check OK (Status: healthy, DB: connected, Seeded FDRs: 164)
[2/5] Testing JWT authentication across all 5 RBAC roles...
  [PASS] Role authenticated: SYSTEM_ADMIN (admin@deposafe.aicte.gov.in)
  [PASS] Role authenticated: VERIFICATION_OFFICER (officer@deposafe.aicte.gov.in)
  [PASS] Role authenticated: REGIONAL_OFFICER (ro.north@deposafe.aicte.gov.in)
  [PASS] Role authenticated: COMPETENT_AUTHORITY (director.approval@aicte-india.org)
  [PASS] Role authenticated: INSTITUTION_USER (institution1@vidya.edu.in)
  [PASS] Role authenticated: AUDITOR (auditor@deposafe.aicte.gov.in)
[3/5] Verifying Hero Case (BNB-DEL-HERO-1000)...
  [PASS] Hero Case loaded: ID #156, Review Priority Score: 60.0/100, Flags: 2
[4/5] Testing document upload and AI extraction pipeline...
  [PASS] Upload and AI pipeline execution succeeded
[5/5] Verifying cryptographic SHA-256 hash-chained audit ledger...
  [PASS] Cryptographic audit chain verified mathematically (Blocks: 22)
==========================================================
 ALL SMOKE TESTS PASSED SUCCESSFULLY!
```

### 2. Live Browser Verification
1. Navigate to `https://<YOUR-FRONTEND-SLUG>.onrender.com`.
2. Log in using any demo role:
   - **Verification Officer**: `officer@deposafe.aicte.gov.in` / `Password@123`
   - **Competent Authority**: `director.approval@aicte-india.org` / `Password@123`
3. Click on the Hero Case `BNB-DEL-HERO-1000` to verify the 4-source provenance comparison, metadata anomaly badge, ELA forensic view, and release gate.

---

## 5. Local Docker Compose Verification

To run the exact same containerized production images locally:

```bash
# 1. Build and start containers in background
docker compose up -d --build

# 2. Verify health of both services
docker compose ps

# 3. Run demo verification check against the local stack
./scripts/demo_check.sh

# 4. Run production smoke tests
./scripts/smoke_test.sh http://localhost:8000
```
