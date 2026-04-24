from sqlalchemy import Column, Integer, String, DateTime, func
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    phone      = Column(String, unique=True, nullable=False, index=True)
    name       = Column(String, nullable=True)
    language   = Column(String, default="ru")
    odoo_id    = Column(Integer, nullable=True)        # Odoo contact ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
