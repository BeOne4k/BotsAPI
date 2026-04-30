from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from core.database import Base

class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    phone      = Column(String(20),  unique=True, nullable=False, index=True)
    name       = Column(String(100), nullable=True)
    language   = Column(String(10),  default="ru")
    odoo_id    = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    channels   = relationship("Channel", back_populates="user", lazy="select")