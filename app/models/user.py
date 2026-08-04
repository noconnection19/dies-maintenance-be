"""Model database untuk User dan Role (autentikasi)."""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Role(Base):
    __tablename__ = "MSTR_ROLE"

    role_cd   = Column("ROLE_CD", String(20), primary_key=True)
    role_name = Column("ROLE_NAME", String(50), nullable=True)


class User(Base):
    __tablename__ = "MSTR_USER"

    username        = Column("USERNAME", String(50), primary_key=True)
    role            = Column("ROLE_CD", String(20), ForeignKey("MSTR_ROLE.ROLE_CD"), nullable=True, default="Member")
    full_name       = Column("NAME", String(200), nullable=True)
    hashed_password = Column("PASSWORD", String(512), nullable=False)
    created_at      = Column("CREATED_DT", DateTime(timezone=True), server_default=func.now())
    updated_at      = Column("CHANGED_DT", DateTime(timezone=True), onupdate=func.now())

    role_rel = relationship("Role", foreign_keys=[role])

    @property
    def id(self) -> int:
        return hash(self.username) % 1000000

    @property
    def is_active(self) -> bool:
        return True
