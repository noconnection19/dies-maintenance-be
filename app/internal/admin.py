"""
Fungsi internal/admin yang dijalankan saat startup.

Tidak diekspos sebagai endpoint publik.
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def seed_admin(db: Session) -> None:
    """Buat akun admin default jika tabel users masih kosong."""
    if db.query(User).count() == 0:
        admin = User(
            username="admin",
            full_name="Administrator",
            role="Admin",
            hashed_password=hash_password("admin123"),
        )
        db.add(admin)
        db.commit()
        print("[SEED] Seeded default admin  (username: admin / password: admin123)")
        print("[WARNING] Segera ganti password default setelah login pertama!")
