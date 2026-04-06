from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database import Base, engine
from .routers import dies_line_stop, dies_repair, dies_preventive


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: buat semua tabel kalau belum ada
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database ready — {settings.DATABASE_URL}")
    yield
    # Shutdown
    print("👋 App shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — agar Flutter Web bisa akses
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(dies_line_stop.router, prefix="/api/v1/line-stop", tags=["Dies Line Stop"])
app.include_router(dies_repair.router, prefix="/api/v1/repair", tags=["Dies Repair"])
app.include_router(dies_preventive.router, prefix="/api/v1/preventive", tags=["Dies Preventive"])


@app.get("/", tags=["Health"])
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
