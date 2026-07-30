"""
Entry point aplikasi FastAPI.

Menjalankan server:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.database import engine, Base, SessionLocal

import os
os.makedirs("uploads", exist_ok=True)

# Import semua models agar terdaftar ke metadata Base sebelum create_all
from app.models.user import User        # noqa: F401
from app.models.dies_task import (  # noqa: F401
    DiesTask, Line, Machine, Die, Attachment, PartOrderHeader, PartOrderDetail, DiesOperation,
    MstrPlant, MstrPartLocation, MstrSparepart, MstrApprovalH, MstrApprovalD,
    DetDiesPic, DetApproval, MstrPreventiveFormH, MstrPreventiveFormD,
    DetDiesPreventiveScheduleH, DetDiesPreventiveScheduleD, DetPreventiveForm, DetDiesRepair
)

# Routers
from app.routers.auth import router as auth_router
from app.routers.dies_line_stop import router as line_stop_router
from app.routers.dies_repair import router as repair_router
from app.routers.dies_preventive import router as preventive_router
from app.routers.dashboard import router as dashboard_router
from app.routers.attachments import router as attachments_router

from app.internal.admin import seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────

    # Base.metadata.create_all(bind=engine)
    print(f"[OK] Database ready: {settings.DATABASE_URL}")
    # db = SessionLocal()
    # try:
    #     seed_admin(db)
    # finally:
    #     db.close()
    yield
    # ── Shutdown ─────────────────────────────────────────────────────
    print("[INFO] App shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Exception handlers ───────────────────────────────────────────────
register_exception_handlers(app)

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    # ponytail: O(1) checks for MAINTENANCE_MODE before forwarding request
    if settings.MAINTENANCE_MODE and request.method != "OPTIONS" and request.url.path not in ["/", "/health", "/api/v1/health"]:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Server sedang dalam pemeliharaan terjadwal. Silakan coba beberapa saat lagi."
            }
        )
    return await call_next(request)

from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ── Routers ──────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router,       prefix=f"{API_PREFIX}/auth",       tags=["Auth"])
app.include_router(line_stop_router,  prefix=f"{API_PREFIX}/line-stop",  tags=["Dies Line Stop"])
app.include_router(repair_router,     prefix=f"{API_PREFIX}/repair",     tags=["Dies Repair"])
app.include_router(preventive_router, prefix=f"{API_PREFIX}/preventive", tags=["Dies Preventive"])
app.include_router(dashboard_router,  prefix=f"{API_PREFIX}/dashboard",  tags=["Dashboard"])
app.include_router(attachments_router, prefix=f"{API_PREFIX}/attachments", tags=["Attachments"])


# ── Health check ─────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

