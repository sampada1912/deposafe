import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.api import auth, fdrs, institutions, compliance, democlock, graph, workload, audit, evaluation, mock_bank, lifecycle, release

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="DepoSafe - AI-Assisted Security Deposit / FDR Intelligence & Management Portal for AICTE Regulation Bureau",
    version="1.0.0"
)

# Enforce configurable CORS origins (restricted to frontend in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount storage directory for document viewing
os.makedirs(settings.STORAGE_DIR, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

# Include Routers under standard API_V1_STR (/api/v1)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(institutions.router, prefix=settings.API_V1_STR)
app.include_router(fdrs.router, prefix=f"{settings.API_V1_STR}/fdrs")
app.include_router(fdrs.router, prefix=f"{settings.API_V1_STR}/fdr")
app.include_router(compliance.router, prefix=settings.API_V1_STR)
app.include_router(democlock.router, prefix=settings.API_V1_STR)
app.include_router(graph.router, prefix=settings.API_V1_STR)
app.include_router(workload.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(evaluation.router, prefix=settings.API_V1_STR)
app.include_router(mock_bank.router, prefix=settings.API_V1_STR)
app.include_router(lifecycle.router, prefix=settings.API_V1_STR)
app.include_router(lifecycle.router, prefix="")
app.include_router(release.router, prefix=settings.API_V1_STR)
app.include_router(release.router, prefix="")

# Direct root-level route aliases for SIH prompt specifications:
# POST /auth/login, /institutions, GET /institutions, POST /fdr/upload, GET /fdr/{id}, GET /fdr
app.include_router(auth.router, prefix="")
app.include_router(institutions.router, prefix="")
app.include_router(fdrs.router, prefix="/fdrs")
app.include_router(fdrs.router, prefix="/fdr")
app.include_router(mock_bank.router, prefix="")

@app.on_event("startup")
def startup_event():
    # 1. Enforce production security rules (refuse default keys in production)
    settings.validate_production_secrets()

    # 2. Reseed database automatically on cold start if empty or incomplete
    db = SessionLocal()
    try:
        from backend.app.models.deposafe_models import FDR
        fdr_count = db.query(FDR).count()
        if fdr_count < 164:
            t0 = time.time()
            from data.seed_loader import load_synthetic_data_into_db
            print(f"[STARTUP] Cold start detected ({fdr_count} FDRs). Reseeding synthetic dataset...")
            load_synthetic_data_into_db(db)
            duration = time.time() - t0
            print(f"[STARTUP] Auto-seeding completed in {duration:.2f} seconds.")
        else:
            print(f"[STARTUP] Database initialized with {fdr_count} FDRs. Ready.")
    except Exception as e:
        print(f"[STARTUP] Startup initialization error: {e}")
    finally:
        db.close()

@app.get("/health")
def health_check():
    db_status = "connected"
    fdr_count = 0
    try:
        from sqlalchemy import text
        from backend.app.models.deposafe_models import FDR
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            fdr_count = db.query(FDR).count()
        finally:
            db.close()
    except Exception as e:
        db_status = f"unhealthy: {e}"
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "database": db_status})

    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "database": db_status,
        "seeded_fdrs": fdr_count,
        "disclaimer": "AI is advisory. Versioned rules dictate compliance.",
        "storage": os.path.abspath(settings.STORAGE_DIR)
    }
