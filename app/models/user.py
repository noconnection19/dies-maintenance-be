"""Model database untuk User (autentikasi)."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class User(Base):
    __tablename__ = "MSTR_USER"

    username        = Column("USERNAME", String(50), primary_key=True)
    role            = Column("ROLE_CD", String(50), nullable=True, default="Member")
    full_name       = Column("NAME", String(100), nullable=True)
    hashed_password = Column("PASSWORD", String(500), nullable=False)
    created_at      = Column("CREATED_DT", DateTime(timezone=True), server_default=func.now())
    updated_at      = Column("CHANGED_DT", DateTime(timezone=True), onupdate=func.now())

    @property
    def id(self) -> int:
        return hash(self.username) % 1000000

    @property
    def is_active(self) -> bool:
        return True
