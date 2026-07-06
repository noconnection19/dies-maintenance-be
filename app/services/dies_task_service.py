"""
Business logic CRUD untuk semua jenis Dies Task.

Setiap router (dies_line_stop, dies_repair, dies_preventive) memanggil
fungsi-fungsi ini dengan `task_type` yang sudah terkunci,
sehingga tidak ada duplikasi logika.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.dies_task import DiesTask, TaskType
from app.schemas.dies_task import TaskCreateRequest, TaskUpdateRequest


def get_tasks(
    db: Session,
    task_type: TaskType,
    page: int = 1,
    size: int = 20,
) -> tuple[list[DiesTask], int]:
    """Ambil semua task berdasarkan tipe dengan pagination. Kembalikan (items, total)."""
    query = db.query(DiesTask).filter(DiesTask.task_type == task_type)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def get_task_by_id(db: Session, task_id: int, task_type: TaskType) -> DiesTask:
    """Ambil satu task. Raises HTTP 404 jika tidak ditemukan."""
    task = (
        db.query(DiesTask)
        .filter(DiesTask.id == task_id, DiesTask.task_type == task_type)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task dengan id={task_id} tidak ditemukan",
        )
    return task


def create_task(
    db: Session,
    data: TaskCreateRequest,
    task_type: TaskType,
    created_by: int | None = None,
) -> DiesTask:
    """Buat task baru dengan task_type yang sudah ditentukan."""
    task = DiesTask(task_type=task_type, created_by=created_by, **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(
    db: Session,
    task_id: int,
    data: TaskUpdateRequest,
    task_type: TaskType,
) -> DiesTask:
    """Update field task. Raises HTTP 404 jika tidak ditemukan."""
    task = get_task_by_id(db, task_id, task_type)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int, task_type: TaskType) -> None:
    """Hapus task. Raises HTTP 404 jika tidak ditemukan."""
    task = get_task_by_id(db, task_id, task_type)
    db.delete(task)
    db.commit()
