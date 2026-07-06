"""Router untuk autentikasi dan manajemen user."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user, require_role
from app.core.responses import success_response, created_response
from app.models.user import User
from app.schemas.user import LoginRequest, LoginResponse, UserCreateRequest, UserResponse
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="Login dan dapatkan JWT token")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    return auth_service.authenticate_user(db, body)


@router.get("/me", response_model=UserResponse, summary="Informasi user yang sedang login")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    summary="Buat user baru (Admin only)",
)
def create_user(
    body: UserCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("Admin")),
):
    new_user = auth_service.create_user(db, body)
    return created_response(
        data=UserResponse.model_validate(new_user).model_dump(),
        message="User berhasil dibuat",
    )


@router.get(
    "/users",
    summary="Daftar semua user (Admin & Supervisor)",
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("Admin", "Supervisor")),
):
    users = auth_service.list_users(db)
    return success_response(
        data=[UserResponse.model_validate(u).model_dump() for u in users]
    )


@router.post("/logout", summary="Logout user (bersihkan token)")
def logout():
    return success_response(message="Berhasil logout")

