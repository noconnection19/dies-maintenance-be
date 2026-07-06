"""Model database untuk Dies Task (Line Stop, Repair, Preventive)."""
import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class TaskType(str, enum.Enum):
    LINE_STOP  = "LINE_STOP"
    REPAIR     = "REPAIR"
    PREVENTIVE = "PREVENTIVE"


class TaskStatus(str, enum.Enum):
    OPEN        = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED      = "CLOSED"


class DiesTask(Base):
    __tablename__ = "dies_tasks"

    id          = Column(Integer, primary_key=True, index=True)
    task_type   = Column(SAEnum(TaskType), index=True, nullable=False)
    noreg       = Column(String(100), index=True, nullable=True)
    part_no     = Column(String(100), index=True, nullable=True)
    description = Column(String(500), nullable=True)
    status      = Column(SAEnum(TaskStatus), default=TaskStatus.OPEN, nullable=False)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    creator = relationship("User", foreign_keys=[created_by])
