"""
Business logic CRUD untuk semua jenis Dies Task.

Setiap router (dies_line_stop, dies_repair, dies_preventive) memanggil
fungsi-fungsi ini dengan `task_type` yang sudah ditentukan.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone, timedelta

def get_utc7_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)

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
        query = query.filter(DiesTask.status.in_(['1', '2']))
    elif status == "COMPLETED":
        query = query.filter(DiesTask.status.in_(['3', '4']))
        
    query = query.order_by(DiesTask.created_dt.desc())
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return items, total


def get_pic_usernames(db: Session, task_id: str) -> list[str]:
    """Query DET_DIES_PIC for all usernames assigned to a task."""
    from app.models.dies_task import DetDiesPic
    rows = db.query(DetDiesPic.username).filter(DetDiesPic.dies_reff_id == task_id).all()
    return [r.username for r in rows]


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
    from app.models.dies_task import DetDiesPic

    # Generate next DIES_LINE_STOP_ID as LS{YYYYMMDD}/XXX
    today_str = get_utc7_now().strftime("%Y%m%d")
    prefix = f"LS{today_str}/"
    max_today_id = (
        db.query(DiesTask.id)
        .filter(DiesTask.id.like(f"{prefix}%"))
        .order_by(DiesTask.id.desc())
        .first()
    )
    if max_today_id:
        try:
            last_increment = int(max_today_id[0].split("/")[-1])
            next_increment = last_increment + 1
        except Exception:
            next_increment = 1
    else:
        next_increment = 1
    next_id = f"{prefix}{next_increment:03d}"

    payload = data.model_dump()
    # Hapus mock fields yang tidak ada di kolom DB
    payload.pop("noreg", None)
    payload.pop("description", None)

    # Extract pic_usernames list
    pic_usernames = payload.pop("pic_usernames", None) or []

    print(f"[DEBUG] create_task payload received: {payload}")
    payload['status'] = '1'  # Always start as On Progress
    now_dt = get_utc7_now()
    task = DiesTask(
        id=next_id,
        created_by=created_by,
        created_dt=now_dt,
        changed_dt=now_dt,
        **payload
    )
    db.add(task)

    # 1. PIC utama (origin): user yang sedang login
    pics_to_add = []
    if created_by:
        pics_to_add.append((created_by, 1))

    # 2. PIC tambahan (dropdown)
    for username in pic_usernames:
        if username and username != created_by:
            pics_to_add.append((username, 0))

    # Save to DET_DIES_PIC
    max_pic_id = db.query(func.max(DetDiesPic.dies_pic_id)).scalar() or 0
    for idx, (username, is_origin) in enumerate(pics_to_add):
        next_pic_id = max_pic_id + 1 + idx

        pic_entry = DetDiesPic(
            dies_pic_id=next_pic_id,
            dies_reff_id=next_id,
            username=username,
            is_origin_pic=is_origin,
            created_by=created_by,
            created_dt=get_utc7_now()
        )
        db.add(pic_entry)

    db.commit()
    db.refresh(task)
    return task


def update_task(
    db: Session,
    task_id: str,
    data: TaskUpdateRequest,
    task_type: TaskType,
    changed_by: str | None = None,
) -> DiesTask:
    """Update field task. Raises HTTP 404 jika tidak ditemukan."""
    task = get_task_by_id(db, task_id, task_type)
    
    payload = data.model_dump(exclude_unset=True)
    payload.pop("noreg", None)
    payload.pop("description", None)

    for key, value in payload.items():
        setattr(task, key, value)
        
    if changed_by:
        task.changed_by = changed_by
    task.changed_dt = get_utc7_now()

    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: str, task_type: TaskType) -> None:
    """Hapus task. Raises HTTP 404 jika tidak ditemukan."""
    task = get_task_by_id(db, task_id, task_type)
    db.delete(task)
    db.commit()


def create_part_order(db: Session, task_id: str, details_data: list[dict]) -> "PartOrderHeader":
    import random
    from app.models.dies_task import PartOrderHeader, PartOrderDetail

    # Generate a unique order id
    while True:
        order_id = f"321A{random.randint(100, 999)}"
        existing = db.query(PartOrderHeader).filter_by(id=order_id).first()
        if not existing:
            break

    header = PartOrderHeader(
        id=order_id,
        dies_reff_id=task_id,
        status="Waiting Confirmation"
    )
    db.add(header)

    for i, detail in enumerate(details_data):
        item = PartOrderDetail(
            part_order_id=order_id,
            item_no=i + 1,
            part_cd=detail["part_cd"],
            part_name=detail["part_name"],
            location=detail.get("location"),
            qty=detail.get("qty", 1)
        )
        db.add(item)

    db.commit()
    db.refresh(header)
    return header


def update_part_order(db: Session, order_id: str, details_data: list[dict]) -> "PartOrderHeader":
    from app.models.dies_task import PartOrderHeader, PartOrderDetail

    header = db.query(PartOrderHeader).filter_by(id=order_id).first()
    if not header:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order dengan id={order_id} tidak ditemukan"
        )

    if header.status != "Waiting Confirmation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order hanya bisa diedit ketika berstatus Waiting Confirmation"
        )

    # Delete existing details
    db.query(PartOrderDetail).filter_by(part_order_id=order_id).delete()

    # Re-insert new details
    for i, detail in enumerate(details_data):
        item = PartOrderDetail(
            part_order_id=order_id,
            item_no=i + 1,
            part_cd=detail["part_cd"],
            part_name=detail["part_name"],
            location=detail.get("location"),
            qty=detail.get("qty", 1)
        )
        db.add(item)

    db.commit()
    db.refresh(header)
    return header
