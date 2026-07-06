"""Model database untuk Dies Task (Line Stop, Repair, Preventive)."""
import enum
from sqlalchemy.ext.hybrid import hybrid_property
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


class Line(Base):
    __tablename__ = "MSTR_LINE"

    line_cd   = Column("LINE_CD", String(10), primary_key=True, index=True)
    line_name = Column("LINE_NAME", String(100), nullable=False)


class Machine(Base):
    __tablename__ = "MSTR_MACHINE"

    machine_cd   = Column("MACHINE_CD", String(10), primary_key=True, index=True)
    line_cd      = Column("LINE_CD", String(10), ForeignKey("MSTR_LINE.LINE_CD"), nullable=False)
    machine_name = Column("MACHINE_NAME", String(100), nullable=False)

    line = relationship("Line")


class Die(Base):
    __tablename__ = "MSTR_DIES"

    part_no = Column("PART_NO", String(50), primary_key=True, index=True)
    model   = Column("MODEL", String(100), nullable=True)


class DiesTask(Base):
    """
    Mapped directly to DET_DIES_LINE_STOP to fetch and save real Line Stop data.
    """
    __tablename__ = "DET_DIES_LINE_STOP"

    id          = Column("DIES_LINE_STOP_ID", String(100), primary_key=True, index=True)
    part_no     = Column("PART_NO", String(50), ForeignKey("MSTR_DIES.PART_NO"), nullable=True)
    line_cd     = Column("LINE_CD", String(10), ForeignKey("MSTR_LINE.LINE_CD"), nullable=True)
    machine_cd  = Column("MACHINE_CD", String(10), ForeignKey("MSTR_MACHINE.MACHINE_CD"), nullable=True)
    shift       = Column("SHIFT", String(1), nullable=True)
    model       = Column("MODEL", String(50), nullable=True)
    _status     = Column("STATUS", String(2), nullable=True)
    duration_ls = Column("DURATION_LS", Integer, nullable=True)

    @hybrid_property
    def status(self):
        if self._status == "0":
            return "OPEN"
        elif self._status == "1":
            return "IN_PROGRESS"
        elif self._status == "2":
            return "CLOSED"
        return self._status

    @status.setter
    def status(self, value):
        if value == "OPEN":
            self._status = "0"
        elif value == "IN_PROGRESS":
            self._status = "1"
        elif value == "CLOSED":
            self._status = "2"
        else:
            self._status = value

    @status.expression
    def status(cls):
        from sqlalchemy import case
        return case(
            (cls._status == "0", "OPEN"),
            (cls._status == "1", "IN_PROGRESS"),
            (cls._status == "2", "CLOSED"),
            else_=cls._status
        )
    duration_mh = Column("DURATION_MH", Integer, nullable=True)
    repaired_by = Column("REPAIRED_BY", String(100), nullable=True)
    repaired_dt = Column("REPAIRED_DT", DateTime, nullable=True)
    problem     = Column("PROBLEM", String(200), nullable=True)
    rootcause   = Column("ROOTCAUSE", String(200), nullable=True)
    countermeasure = Column("COUNTERMEASURE", String(200), nullable=True)
    created_by  = Column("CREATED_BY", String(100), nullable=True)
    created_dt  = Column("CREATED_DT", DateTime, server_default=func.now())
    changed_by  = Column("CHANGED_BY", String(100), nullable=True)
    changed_dt  = Column("CHANGED_DT", DateTime, onupdate=func.now())

    # Relationships
    line    = relationship("Line")
    machine = relationship("Machine")
    die     = relationship("Die")
