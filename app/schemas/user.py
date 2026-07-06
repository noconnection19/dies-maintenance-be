"""Pydantic schemas untuk User / autentikasi."""
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from datetime import datetime


# ── Request ──────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreateRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "Member"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"Admin", "Supervisor", "Member"}
        if v not in allowed:
            raise ValueError(f"Role harus salah satu dari: {', '.join(allowed)}")
        return v


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ── Response ─────────────────────────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
