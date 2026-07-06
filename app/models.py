from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
import enum

from .database import Base


class User(Base):
    """Tabel user untuk autentikasi."""
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, index=True)
    username     = Column(String, unique=True, index=True, nullable=False)
    full_name    = Column(String, nullable=True)
    role         = Column(String, default="Member")
    hashed_password = Column(String, nullable=False)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

class TaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"

class DiesTask(Base):
    """
    Tabel generic untuk menyimpan semua task Dies Maintenance.
    Bisa dikembangkan lebih lanjut dengan memisahkan tabel per kategori jika diperlukan,
    tapi untuk awal kita satukan dengan flag `task_type`.
    """
    __tablename__ = "dies_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String, index=True) # "LINE_STOP", "REPAIR", "PREVENTIVE"
    noreg = Column(String, index=True, nullable=True)
    part_no = Column(String, index=True, nullable=True)
    description = Column(String, nullable=True)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.OPEN)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
