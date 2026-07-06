"""Pydantic schemas untuk Dies Task."""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Union
from datetime import datetime

from app.models.dies_task import TaskStatus, TaskType


# ── Master Schemas ───────────────────────────────────────────────────
class LineResponse(BaseModel):
    line_cd:   str
    line_name: str

    model_config = ConfigDict(from_attributes=True)


class MachineResponse(BaseModel):
    machine_cd:   str
    line_cd:      str
    machine_name: str

    model_config = ConfigDict(from_attributes=True)


class DieResponse(BaseModel):
    part_no: str
    model:   Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Request ──────────────────────────────────────────────────────────
class TaskCreateRequest(BaseModel):
    part_no:        Optional[str] = None
    line_cd:        Optional[str] = None
    machine_cd:     Optional[str] = None
    shift:          Optional[str] = None
    model:          Optional[str] = None
    status:         Optional[str] = None
    duration_ls:    Optional[int] = None
    duration_mh:    Optional[int] = None
    problem:        Optional[str] = None
    rootcause:      Optional[str] = None
    countermeasure: Optional[str] = None
    repaired_by:    Optional[str] = None
    noreg:          Optional[str] = None
    description:    Optional[str] = None


class TaskUpdateRequest(BaseModel):
    part_no:        Optional[str] = None
    line_cd:        Optional[str] = None
    machine_cd:     Optional[str] = None
    shift:          Optional[str] = None
    model:          Optional[str] = None
    status:         Optional[str] = None
    duration_ls:    Optional[int] = None
    duration_mh:    Optional[int] = None
    problem:        Optional[str] = None
    rootcause:      Optional[str] = None
    countermeasure: Optional[str] = None
    repaired_by:    Optional[str] = None
    noreg:          Optional[str] = None
    description:    Optional[str] = None


# ── Response ─────────────────────────────────────────────────────────
class TaskResponse(BaseModel):
    id:             str
    task_type:      TaskType = TaskType.LINE_STOP
    part_no:        Optional[str] = None
    line_cd:        Optional[str] = None
    machine_cd:     Optional[str] = None
    shift:          Optional[str] = None
    model:          Optional[str] = None
    status:         Optional[str] = None
    duration_ls:    Optional[int] = None
    duration_mh:    Optional[int] = None
    problem:        Optional[str] = None
    rootcause:      Optional[str] = None
    countermeasure: Optional[str] = None
    repaired_by:    Optional[str] = None
    repaired_dt:    Optional[datetime] = None
    noreg:          Optional[str] = None
    description:    Optional[str] = None
    created_by:     Optional[str] = None
    created_dt:     Optional[datetime] = None
    changed_by:     Optional[str] = None
    changed_dt:     Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
