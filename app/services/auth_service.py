"""Business logic untuk autentikasi dan manajemen user."""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreateRequest, LoginRequest, LoginResponse, UserResponse


def authenticate_user(db: Session, body: LoginRequest) -> LoginResponse:
    """Validasi kredensial dan kembalikan JWT access token."""
    user = db.query(User).filter(User.username == body.username).first()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun tidak aktif",
        )

    token = create_access_token({"sub": user.username, "role": user.role})
    return LoginResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


def create_user(db: Session, data: UserCreateRequest) -> User:
    """Buat user baru. Raises HTTP 409 jika username sudah dipakai."""
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username sudah digunakan",
        )
    user = User(
        username=data.username,
        full_name=data.full_name,
        role=data.role,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).all()
