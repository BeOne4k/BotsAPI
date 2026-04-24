from pydantic import BaseModel, field_validator
from typing import Optional
from models.channel import ChannelType

# ── Users ────────────────────────────────────────────────
class UserCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    language: str = "ru"

class UserRead(BaseModel):
    id: int
    phone: str
    name: Optional[str]
    language: str
    odoo_id: Optional[int]

    model_config = {"from_attributes": True}

# ── Channels ─────────────────────────────────────────────
class ChannelBind(BaseModel):
    phone: str
    channel_type: ChannelType
    external_id: str

class ChannelRead(BaseModel):
    id: int
    type: ChannelType
    external_id: str

    model_config = {"from_attributes": True}

# ── Purchases ─────────────────────────────────────────────
class PurchaseEvent(BaseModel):
    phone: str
    amount: float
    store_id: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("amount must be positive")
        return v

class PurchaseRead(BaseModel):
    id: int
    phone: str
    amount: float
    store_id: Optional[str]
    channel_sent: Optional[str]

    model_config = {"from_attributes": True}

# ── Messaging ──────────────────────────────────────────────
class SendMessageRequest(BaseModel):
    phone: str
    text: str
