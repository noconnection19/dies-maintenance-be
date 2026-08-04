"""Pydantic schemas untuk Dies Task."""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Union, List
from datetime import datetime

from app.models.dies_task import TaskType


class PartOrderDetailSchema(BaseModel):
    part_cd:   str
    part_name: str
    location:  Optional[str] = None
    qty:       int = 1

    model_config = ConfigDict(from_attributes=True)


class PartOrderHeaderSchema(BaseModel):
    id:           str
    dies_reff_id: str
    status:       str
    details:      List[PartOrderDetailSchema]

    model_config = ConfigDict(from_attributes=True)


class PartOrderCreateRequest(BaseModel):
    details: List[PartOrderDetailSchema]



# ── Master Schemas ───────────────────────────────────────────────────
class CompanyResponse(BaseModel):
    company_cd:   str
    plant_cd:     str
    company_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ModelResponse(BaseModel):
    model:      str
    model_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class RoleResponse(BaseModel):
    role_cd:   str
    role_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LineResponse(BaseModel):
    line_cd:    str
    line_name:  str
    company_cd: Optional[str] = None
    plant_cd:   Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MachineResponse(BaseModel):
    machine_cd:   str
    line_cd:      str
    machine_name: str
    company_cd:   Optional[str] = None
    plant_cd:     Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DieResponse(BaseModel):
    part_no:    str
    part_name:  Optional[str] = None
    model:      Optional[str] = None
    company_cd: Optional[str] = None
    plant_cd:   Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AttachmentResponse(BaseModel):
    id:              int
    attachment_name: str
    mimetype:        Optional[str] = None
    size:            Optional[int] = None
    file_path:       str

    model_config = ConfigDict(from_attributes=True)


# ── Request ──────────────────────────────────────────────────────────
class TaskCreateRequest(BaseModel):
    part_no:                 Optional[str] = None
    line_cd:                 Optional[str] = None
    machine_cd:              Optional[str] = None
    company_cd:              Optional[str] = None
    plant_cd:                Optional[str] = None
    approval_id:             Optional[str] = None
    operation_seq:           Optional[str] = None
    shift:                   Optional[str] = None
    model:                   Optional[str] = None
    status:                  Optional[str] = None
    duration_ls:             Optional[int] = None
    duration_mh:             Optional[int] = None
    classification:          Optional[str] = None
    problem_cd:              Optional[str] = None
    problem:                 Optional[str] = None
    rootcause:               Optional[str] = None
    countermeasure:          Optional[str] = None
    remark:                  Optional[str] = None
    sub_problem:             Optional[str] = None
    repaired_by:             Optional[str] = None
    repaired_dt:             Optional[datetime] = None
    noreg:                   Optional[str] = None
    description:             Optional[str] = None
    documentation_before_id: Optional[int] = None
    documentation_after_id:  Optional[int] = None
    pic_usernames:           Optional[List[str]] = None


class TaskUpdateRequest(BaseModel):
    part_no:                 Optional[str] = None
    line_cd:                 Optional[str] = None
    machine_cd:              Optional[str] = None
    company_cd:              Optional[str] = None
    plant_cd:                Optional[str] = None
    approval_id:             Optional[str] = None
    operation_seq:           Optional[str] = None
    shift:                   Optional[str] = None
    model:                   Optional[str] = None
    status:                  Optional[str] = None
    duration_ls:             Optional[int] = None
    duration_mh:             Optional[int] = None
    classification:          Optional[str] = None
    problem_cd:              Optional[str] = None
    problem:                 Optional[str] = None
    rootcause:               Optional[str] = None
    countermeasure:          Optional[str] = None
    remark:                  Optional[str] = None
    sub_problem:             Optional[str] = None
    repaired_by:             Optional[str] = None
    repaired_dt:             Optional[datetime] = None
    noreg:                   Optional[str] = None
    description:             Optional[str] = None
    documentation_before_id: Optional[int] = None
    documentation_after_id:  Optional[int] = None


# ── Response ─────────────────────────────────────────────────────────
class TaskResponse(BaseModel):
    id:                      str
    task_type:               TaskType = TaskType.LINE_STOP
    part_no:                 Optional[str] = None
    line_cd:                 Optional[str] = None
    machine_cd:              Optional[str] = None
    company_cd:              Optional[str] = None
    plant_cd:                Optional[str] = None
    approval_id:             Optional[str] = None
    operation_seq:           Optional[str] = None
    shift:                   Optional[str] = None
    model:                   Optional[str] = None
    status:                  Optional[str] = None
    duration_ls:             Optional[int] = None
    duration_mh:             Optional[int] = None
    classification:          Optional[str] = None
    problem_cd:              Optional[str] = None
    problem:                 Optional[str] = None
    rootcause:               Optional[str] = None
    countermeasure:          Optional[str] = None
    remark:                  Optional[str] = None
    sub_problem:             Optional[str] = None
    repaired_by:             Optional[str] = None
    repaired_dt:             Optional[datetime] = None
    noreg:                   Optional[str] = None
    description:             Optional[str] = None
    created_by:              Optional[str] = None
    created_dt:              Optional[datetime] = None
    changed_by:              Optional[str] = None
    changed_dt:              Optional[datetime] = None
    documentation_before_id: Optional[int] = None
    documentation_after_id:  Optional[int] = None
    documentation_before:    Optional[AttachmentResponse] = None
    documentation_after:     Optional[AttachmentResponse] = None
    part_orders:             Optional[List[PartOrderHeaderSchema]] = None
    pic_usernames:           Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)
