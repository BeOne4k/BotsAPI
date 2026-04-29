from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import require_api_key
from services import user_service
from models.schemas import ChannelBind, ChannelRead, SendMessageRequest
from services.router import route_message

router = APIRouter()

@router.post("/bind", response_model=ChannelRead, status_code=201,
             dependencies=[Depends(require_api_key)])
async def bind_channel(body: ChannelBind, db: AsyncSession = Depends(get_db)):
    """Bind a messenger channel to a user identified by phone."""
    user = await user_service.get_by_phone(db, body.phone)
    if not user:
        raise HTTPException(404, "User not found – register first")
    ch = await user_service.bind_channel(db, user.id, body.channel_type, body.external_id)
    return ch

@router.post("/send", dependencies=[Depends(require_api_key)])
async def send_direct(body: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    """Send a message to a user via their best available channel."""
    user = await user_service.get_by_phone(db, body.phone)
    if not user:
        raise HTTPException(404, "User not found")
    channel_used = await route_message(user.channels, body.text)
    if not channel_used:
        raise HTTPException(502, "Could not deliver message via any channel")
    return {"status": "sent", "channel": channel_used}
