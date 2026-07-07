"""
Factory function untuk membuat router Dies Task per kategori.

Cara pakai di router masing-masing feature:
    from app.routers.dies_task import make_dies_router
    from app.models.dies_task import TaskType

    router = make_dies_router(TaskType.LINE_STOP)
"""
from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.core.responses import success_response, created_response, paginated_response
from app.models.user import User
from app.models.dies_task import TaskType
from app.schemas.dies_task import TaskCreateRequest, TaskUpdateRequest, TaskResponse, PartOrderDetailSchema, PartOrderHeaderSchema
from app.services import dies_task_service


def make_dies_router(task_type: TaskType) -> APIRouter:
    """Kembalikan APIRouter CRUD lengkap yang terkunci pada `task_type` tertentu."""
    router = APIRouter()

    @router.get("/", summary=f"Daftar {task_type.value}")
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

    @router.post("/", status_code=status.HTTP_201_CREATED, summary=f"Buat {task_type.value} baru")
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

    @router.get("/lines", summary="Daftar Line")
    def list_lines(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import Line
        items = db.query(Line).all()
        return success_response(data=[{"line_cd": i.line_cd, "line_name": i.line_name} for i in items])

    @router.get("/machines", summary="Daftar Machine")
    def list_machines(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import Machine
        items = db.query(Machine).all()
        return success_response(data=[{"machine_cd": i.machine_cd, "line_cd": i.line_cd, "machine_name": i.machine_name} for i in items])

    @router.get("/dies", summary="Daftar Dies")
    def list_dies(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
        from app.models.dies_task import Die
        items = db.query(Die).all()
        return success_response(data=[{"part_no": i.part_no, "model": i.model} for i in items])

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

    @router.post("/{task_id:path}/orders", response_model=PartOrderHeaderSchema, summary="Buat order part baru")
    def create_order(
        task_id: str,
        body: List[PartOrderDetailSchema],
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        details = [item.model_dump() for item in body]
        return dies_task_service.create_part_order(db, task_id, details)

    @router.put("/orders/{order_id}", response_model=PartOrderHeaderSchema, summary="Update order part")
    def update_order(
        order_id: str,
        body: List[PartOrderDetailSchema],
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        details = [item.model_dump() for item in body]
        return dies_task_service.update_part_order(db, order_id, details)

    return router
