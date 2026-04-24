"""
Webhooks from messengers → auto-bind channel on first message.
"""
from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from core.database import get_db
from core.config import get_settings
from services import user_service
from models.channel import ChannelType
from adapters import line as line_adapter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# ── Telegram ──────────────────────────────────────────────
@router.post("/telegram")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    message = data.get("message") or data.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = str(message["chat"]["id"])
    text = message.get("text", "")

    # /start <phone>  →  bind this chat_id to the phone
    if text.startswith("/start"):
        parts = text.split()
        phone = parts[1] if len(parts) > 1 else None
        if phone:
            user, _ = await user_service.get_or_create(db, phone)
            await user_service.bind_channel(db, user.id, ChannelType.telegram, chat_id)
            logger.info("Telegram bound: %s → %s", phone, chat_id)
        return {"ok": True}

    return {"ok": True}

# ── LINE ──────────────────────────────────────────────────
@router.post("/line")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    if not line_adapter.verify_signature(body, x_line_signature or ""):
        raise HTTPException(400, "Invalid LINE signature")

    data = await request.json()
    for event in data.get("events", []):
        if event.get("type") != "message":
            continue
        user_id = event["source"]["userId"]
        text = event.get("message", {}).get("text", "")

        # /bind <phone>
        if text.startswith("/bind"):
            parts = text.split()
            phone = parts[1] if len(parts) > 1 else None
            if phone:
                user, _ = await user_service.get_or_create(db, phone)
                await user_service.bind_channel(db, user.id, ChannelType.line, user_id)
                logger.info("LINE bound: %s → %s", phone, user_id)

    return {"ok": True}

# ── WhatsApp ──────────────────────────────────────────────
@router.get("/whatsapp")
async def whatsapp_verify(request: Request):
    """Meta webhook verification challenge."""
    params = request.query_params
    if params.get("hub.verify_token") == settings.WHATSAPP_VERIFY_TOKEN:
        return int(params.get("hub.challenge", 0))
    raise HTTPException(403, "Invalid verify token")

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()
    try:
        entry = data["entry"][0]
        change = entry["changes"][0]["value"]
        messages = change.get("messages", [])
        for msg in messages:
            phone = msg["from"]  # sender's phone in E.164
            text = msg.get("text", {}).get("body", "")
            # auto-bind the WhatsApp number
            user, _ = await user_service.get_or_create(db, f"+{phone}")
            await user_service.bind_channel(db, user.id, ChannelType.whatsapp, f"+{phone}")
            logger.info("WhatsApp bound/confirmed: +%s", phone)
    except (KeyError, IndexError):
        pass
    return {"status": "ok"}
