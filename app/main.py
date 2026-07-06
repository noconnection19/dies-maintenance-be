"""
Entry point aplikasi FastAPI.

Menjalankan server:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.database import engine, Base, SessionLocal

# Import semua models agar terdaftar ke metadata Base sebelum create_all
from app.models.user import User        # noqa: F401
from app.models.dies_task import DiesTask, Line, Machine, Die  # noqa: F401

# Routers
from app.routers.auth import router as auth_router
from app.routers.dies_line_stop import router as line_stop_router
from app.routers.dies_repair import router as repair_router
from app.routers.dies_preventive import router as preventive_router
from app.routers.dashboard import router as dashboard_router

from app.internal.admin import seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────

    Base.metadata.create_all(bind=engine)
    print(f"[OK] Database ready: {settings.DATABASE_URL}")
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()
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
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router,       prefix=f"{API_PREFIX}/auth",       tags=["Auth"])
app.include_router(line_stop_router,  prefix=f"{API_PREFIX}/line-stop",  tags=["Dies Line Stop"])
app.include_router(repair_router,     prefix=f"{API_PREFIX}/repair",     tags=["Dies Repair"])
app.include_router(preventive_router, prefix=f"{API_PREFIX}/preventive", tags=["Dies Preventive"])
app.include_router(dashboard_router,  prefix=f"{API_PREFIX}/dashboard",  tags=["Dashboard"])


# ── Health check ─────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

