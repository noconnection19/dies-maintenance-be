"""
Manajemen koneksi database menggunakan SQLAlchemy.

Cara pakai:
  - Inject `get_db` sebagai Depends di router untuk mendapatkan Session.
  - `Base` dipakai oleh semua model untuk mendaftarkan tabelnya.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator

from app.core.config import settings


# ── Engine ───────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # reconnect otomatis jika koneksi terputus
    pool_size=10,            # jumlah koneksi persistent dalam pool
    max_overflow=20,         # koneksi tambahan saat pool penuh
    pool_recycle=1800,       # recycle koneksi setiap 30 menit (hindari MariaDB wait_timeout)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base model ───────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class untuk semua SQLAlchemy ORM models."""
    pass


# ── Dependency ───────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Dependency FastAPI yang menyediakan database session per request.

    Contoh penggunaan di router:
        @router.get("/")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
