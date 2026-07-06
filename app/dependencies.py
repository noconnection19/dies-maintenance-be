"""
Shared FastAPI dependencies yang diinjeksi ke router via Depends().

Cara pakai:
    from app.dependencies import get_current_user, require_role

    @router.get("/protected")
    def protected(current_user: User = Depends(get_current_user)):
        ...

    @router.delete("/admin-only")
    def admin_only(current_user: User = Depends(require_role("Admin"))):
        ...
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# tokenUrl harus sesuai dengan prefix router auth di main.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency: Ekstrak dan validasi user dari JWT Bearer token.
    Raises HTTP 401 jika token tidak valid, HTTP 403 jika akun tidak aktif.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun tidak aktif",
        )
    return user


def require_role(*roles: str):
    """
    Dependency factory: Pastikan user memiliki salah satu role yang diizinkan.

    Contoh:
        Depends(require_role("Admin"))
        Depends(require_role("Admin", "Supervisor"))
    """
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Dibutuhkan role: {', '.join(roles)}",
            )
        return current_user
    return _check
