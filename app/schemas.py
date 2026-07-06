from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


# ─── Auth Schemas ──────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role: str

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class TaskStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"

class TaskBase(BaseModel):
    task_type: str
    noreg: Optional[str] = None
    part_no: Optional[str] = None
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.OPEN

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    noreg: Optional[str] = None
    part_no: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None

class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
