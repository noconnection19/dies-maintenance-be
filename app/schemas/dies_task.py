"""Pydantic schemas untuk Dies Task."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.dies_task import TaskStatus, TaskType


# ── Request ──────────────────────────────────────────────────────────
class TaskCreateRequest(BaseModel):
    noreg:       Optional[str] = None
    part_no:     Optional[str] = None
    description: Optional[str] = None
    status:      TaskStatus = TaskStatus.OPEN


class TaskUpdateRequest(BaseModel):
    noreg:       Optional[str] = None
    part_no:     Optional[str] = None
    description: Optional[str] = None
    status:      Optional[TaskStatus] = None


# ── Response ─────────────────────────────────────────────────────────
class TaskResponse(BaseModel):
    id:          int
    task_type:   TaskType
    noreg:       Optional[str] = None
    part_no:     Optional[str] = None
    description: Optional[str] = None
    status:      TaskStatus
    created_by:  Optional[int] = None
    created_at:  datetime
    updated_at:  Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
