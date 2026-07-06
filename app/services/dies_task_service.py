"""
Business logic CRUD untuk semua jenis Dies Task.

Setiap router (dies_line_stop, dies_repair, dies_preventive) memanggil
fungsi-fungsi ini dengan `task_type` yang sudah ditentukan.
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
    status: str | None = None,
) -> tuple[list[DiesTask], int]:
    """Ambil semua task berdasarkan tipe dengan pagination. Kembalikan (items, total)."""
    query = db.query(DiesTask)
    
    if status == "ON_PROGRESS":
        query = query.filter(DiesTask.repaired_dt.is_(None))
    elif status == "COMPLETED":
        query = query.filter(DiesTask.repaired_dt.isnot(None))
        
    query = query.order_by(DiesTask.repaired_dt.desc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def get_task_by_id(db: Session, task_id: str, task_type: TaskType) -> DiesTask:
    """Ambil satu task. Raises HTTP 404 jika tidak ditemukan."""
    task = (
        db.query(DiesTask)
        .filter(DiesTask.id == task_id)
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
    created_by: str | None = None,
) -> DiesTask:
    """Buat task baru dengan task_type yang sudah ditentukan."""
    from sqlalchemy import func, cast, Integer

    # Generate next DIES_LINE_STOP_ID
    max_id = db.query(func.max(cast(DiesTask.id, Integer))).scalar()
    next_id = str((max_id or 0) + 1)

    payload = data.model_dump()
    # Hapus mock fields yang tidak ada di kolom DB
    payload.pop("noreg", None)
    payload.pop("description", None)

    task = DiesTask(
        id=next_id,
        created_by=created_by,
        **payload
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(
    db: Session,
    task_id: str,
    data: TaskUpdateRequest,
    task_type: TaskType,
) -> DiesTask:
    """Update field task. Raises HTTP 404 jika tidak ditemukan."""
    task = get_task_by_id(db, task_id, task_type)
    
    payload = data.model_dump(exclude_unset=True)
    payload.pop("noreg", None)
    payload.pop("description", None)

    for key, value in payload.items():
        setattr(task, key, value)
        
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: str, task_type: TaskType) -> None:
    """Hapus task. Raises HTTP 404 jika tidak ditemukan."""
    task = get_task_by_id(db, task_id, task_type)
    db.delete(task)
    db.commit()
