from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import relationship
import enum
from core.database import Base

class ChannelType(str, enum.Enum):
    line     = "line"
    telegram = "telegram"
    whatsapp = "whatsapp"

class Channel(Base):
    __tablename__ = "channels"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type        = Column(Enum(ChannelType), nullable=False)
    external_id = Column(String(100), nullable=False)   # line userId / tg chat_id / phone
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="channels")
