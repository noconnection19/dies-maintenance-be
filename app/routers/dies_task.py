"""
Factory function untuk membuat router Dies Task per kategori.

Cara pakai di router masing-masing feature:
    from app.routers.dies_task import make_dies_router
    from app.models.dies_task import TaskType

    router = make_dies_router(TaskType.LINE_STOP)
"""
from typing import List, Union
from fastapi import APIRouter, Depends, status, Query, Body, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.core.responses import success_response, created_response, paginated_response
from app.models.user import User
from app.models.dies_task import TaskType
from app.schemas.dies_task import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    PartOrderDetailSchema,
    PartOrderHeaderSchema,
    PartOrderCreateRequest,
)

from app.services import dies_task_service


def make_dies_router(task_type: TaskType) -> APIRouter:
    """Kembalikan APIRouter CRUD lengkap yang terkunci pada `task_type` tertentu."""
    router = APIRouter()

    @router.get("", summary=f"Daftar {task_type.value}")
    def list_tasks(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        status: str = Query(None, description="Filter status (ON_PROGRESS / COMPLETED)"),
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        items, total = dies_task_service.get_tasks(db, task_type, page, size, status=status)
        return paginated_response(
            data=[TaskResponse.model_validate(i).model_dump() for i in items],
            total=total,
            page=page,
            size=size,
        )

    @router.post("", status_code=status.HTTP_201_CREATED, summary=f"Buat {task_type.value} baru")
    def create_task(
        body: TaskCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        task = dies_task_service.create_task(db, body, task_type, created_by=current_user.username)
        return created_response(
            data=TaskResponse.model_validate(task).model_dump(),
            message="Task berhasil dibuat",
        )

    @router.get("/companies", summary="Daftar Company / Plant")
    def list_companies(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import MstrCompany
        items = db.query(MstrCompany).all()
        return success_response(data=[{"company_cd": i.company_cd, "plant_cd": i.plant_cd, "company_name": i.company_name} for i in items])

    @router.get("/models", summary="Daftar Master Model")
    def list_models(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import MstrModel
        items = db.query(MstrModel).all()
        return success_response(data=[{"model": i.model, "model_name": i.model_name} for i in items])

    @router.get("/lines", summary="Daftar Line")
    def list_lines(company_cd: str = Query(None), plant_cd: str = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import Line
        query = db.query(Line)
        if company_cd:
            query = query.filter(Line.company_cd == company_cd)
        if plant_cd:
            query = query.filter(Line.plant_cd == plant_cd)
        items = query.all()
        return success_response(data=[{"line_cd": i.line_cd, "line_name": i.line_name, "company_cd": i.company_cd, "plant_cd": i.plant_cd} for i in items])

    @router.get("/machines", summary="Daftar Machine")
    def list_machines(company_cd: str = Query(None), plant_cd: str = Query(None), line_cd: str = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import Machine
        query = db.query(Machine)
        if company_cd:
            query = query.filter(Machine.company_cd == company_cd)
        if plant_cd:
            query = query.filter(Machine.plant_cd == plant_cd)
        if line_cd:
            query = query.filter(Machine.line_cd == line_cd)
        items = query.all()
        return success_response(data=[{"machine_cd": i.machine_cd, "line_cd": i.line_cd, "machine_name": i.machine_name, "company_cd": i.company_cd, "plant_cd": i.plant_cd} for i in items])

    @router.get("/dies", summary="Daftar Dies")
    def list_dies(company_cd: str = Query(None), plant_cd: str = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import Die
        query = db.query(Die)
        if company_cd:
            query = query.filter(Die.company_cd == company_cd)
        if plant_cd:
            query = query.filter(Die.plant_cd == plant_cd)
        items = query.all()
        return success_response(data=[{"part_no": i.part_no, "part_name": i.part_name or "", "model": i.model or i.part_no, "company_cd": i.company_cd, "plant_cd": i.plant_cd} for i in items])

    @router.get("/dies/{part_no}/operations", summary="Daftar Proses/Operation per Part No")
    def list_dies_operations(part_no: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import DiesOperation
        items = db.query(DiesOperation).filter(DiesOperation.part_no == part_no).all()
        return success_response(data=[{"op": i.op, "proses": i.proses} for i in items])

    @router.get("/dies/{part_no}/machines", summary="Daftar Machine per Part No")
    def list_dies_machines(part_no: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import DiesOperation, Machine
        items = (
            db.query(Machine)
            .join(DiesOperation, Machine.machine_cd == DiesOperation.machine_cd)
            .filter(DiesOperation.part_no == part_no)
            .distinct()
            .all()
        )
        return success_response(data=[{"machine_cd": i.machine_cd, "line_cd": i.line_cd, "machine_name": i.machine_name} for i in items])

    @router.get("/dies/{part_no}/machines/{machine_cd}/operations", summary="Daftar Proses/Operation per Part No dan Machine")
    def list_dies_machine_operations(part_no: str, machine_cd: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import DiesOperation
        items = db.query(DiesOperation).filter(
            DiesOperation.part_no == part_no,
            DiesOperation.machine_cd == machine_cd
        ).all()
        return success_response(data=[{"op": i.op, "proses": i.proses} for i in items])

    @router.get("/pics", summary="Daftar PIC (Users)")
    def list_pics(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        items = db.query(User).all()
        return success_response(data=[{"username": i.username, "full_name": i.full_name} for i in items])

    @router.get("/systems", summary="Daftar System Options")
    def list_systems(system_type: str = Query(..., description="System Type"), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import MstrSystem
        items = db.query(MstrSystem).filter(MstrSystem.system_type == system_type).all()
        return success_response(data=[{"system_cd": i.system_cd, "system_value": i.system_value} for i in items])

    @router.get("/spareparts", summary="Daftar Sparepart & Stok")
    def list_spareparts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import MstrSparepart
        items = db.query(MstrSparepart).all()
        return success_response(data=[{
            "part_cd": i.part_cd,
            "part_name": i.part_name or "",
            "location_cd": i.location_cd or "",
            "qty_stock": i.qty_stock or 0
        } for i in items])

    @router.post("/{task_id:path}/send-to-repair", summary="Kirim ke DET_FORM_DIES_REPAIR")
    def send_to_repair(
        task_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        form = dies_task_service.create_form_dies_repair(
            db, dies_line_stop_id=task_id, pic=current_user.full_name or current_user.username, created_by=current_user.username
        )
        return success_response(
            data={"form_dies_repair_id": form.form_dies_repair_id, "dies_line_stop_id": form.dies_line_stop_id, "status": form.status},
            message="Data berhasil masuk ke DET_FORM_DIES_REPAIR"
        )

    @router.post("/{task_id:path}/orders", response_model=PartOrderHeaderSchema, summary="Buat order part baru")
    async def create_order(
        task_id: str,
        request: Request,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        raw_body = await request.json()
        if isinstance(raw_body, list):
            details = raw_body
        elif isinstance(raw_body, dict):
            details = raw_body.get("details", raw_body.get("items", [raw_body]))
        else:
            details = []
        return dies_task_service.create_part_order(db, task_id, details)

    @router.put("/orders/{order_id}", response_model=PartOrderHeaderSchema, summary="Update order part")
    async def update_order(
        order_id: str,
        request: Request,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        raw_body = await request.json()
        if isinstance(raw_body, list):
            details = raw_body
        elif isinstance(raw_body, dict):
            details = raw_body.get("details", raw_body.get("items", [raw_body]))
        else:
            details = []
        return dies_task_service.update_part_order(db, order_id, details)

    @router.get("/{task_id:path}", response_model=TaskResponse, summary=f"Detail {task_type.value}")
    def get_task(
        task_id: str,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        return dies_task_service.get_task_by_id(db, task_id, task_type)

    @router.put("/{task_id:path}", response_model=TaskResponse, summary=f"Update {task_type.value}")
    def update_task(
        task_id: str,
        body: TaskUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        return dies_task_service.update_task(db, task_id, body, task_type, changed_by=current_user.username)

    @router.delete(
        "/{task_id:path}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Hapus {task_type.value}",
    )
    def delete_task(
        task_id: str,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        dies_task_service.delete_task(db, task_id, task_type)



    return router
