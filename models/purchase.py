from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from core.database import Base

class Purchase(Base):
    __tablename__ = "purchases"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    phone        = Column(String(20),  nullable=False)   # kept even if user deleted
    amount     = Column(Float, nullable=False)
    store_id     = Column(String(100), nullable=True)
    channel_sent = Column(String(50),  nullable=True)  # which channel was used
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="purchases")
