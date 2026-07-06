"""
Utilitas keamanan: hashing password & JWT token.

Menggunakan:
  - passlib[bcrypt]  — hashing password yang aman
  - python-jose[cryptography]  — JWT
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# ── Password hashing ─────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash plain-text password menggunakan bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifikasi plain-text password terhadap hash yang tersimpan."""
    return pwd_context.verify(plain, hashed)


# ── JWT ──────────────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Buat JWT access token.

    Args:
        data: Payload yang akan di-encode (biasanya {"sub": username, "role": role}).
        expires_delta: Durasi token berlaku. Default dari settings.

    Returns:
        JWT string yang bisa dikirim ke client.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode dan validasi JWT token.

    Returns:
        Payload dict jika valid.

    Raises:
        JWTError: Jika token tidak valid atau sudah expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
