"""
Factory function untuk membuat router Dies Task per kategori.

Cara pakai di router masing-masing feature:
    from app.routers.dies_task import make_dies_router
    from app.models.dies_task import TaskType

    router = make_dies_router(TaskType.LINE_STOP)
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.core.responses import success_response, created_response, paginated_response
from app.models.user import User
from app.models.dies_task import TaskType
from app.schemas.dies_task import TaskCreateRequest, TaskUpdateRequest, TaskResponse
from app.services import dies_task_service


def make_dies_router(task_type: TaskType) -> APIRouter:
    """Kembalikan APIRouter CRUD lengkap yang terkunci pada `task_type` tertentu."""
    router = APIRouter()

    @router.get("/", summary=f"Daftar {task_type.value}")
    def list_tasks(
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        items, total = dies_task_service.get_tasks(db, task_type, page, size)
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
        task = dies_task_service.create_task(db, body, task_type, created_by=current_user.id)
        return created_response(
            data=TaskResponse.model_validate(task).model_dump(),
            message="Task berhasil dibuat",
        )

    @router.get("/{task_id}", response_model=TaskResponse, summary=f"Detail {task_type.value}")
    def get_task(
        task_id: int,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        return dies_task_service.get_task_by_id(db, task_id, task_type)

    @router.put("/{task_id}", response_model=TaskResponse, summary=f"Update {task_type.value}")
    def update_task(
        task_id: int,
        body: TaskUpdateRequest,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        return dies_task_service.update_task(db, task_id, body, task_type)

    @router.delete(
        "/{task_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Hapus {task_type.value}",
    )
    def delete_task(
        task_id: int,
        db: Session = Depends(get_db),
        _: User = Depends(get_current_user),
    ):
        dies_task_service.delete_task(db, task_id, task_type)

    return router
