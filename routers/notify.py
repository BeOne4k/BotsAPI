"""
POST /notify/review
-------------------
Принимает идентификатор пользователя (phone, telegram chat_id или LINE userId)
и отправляет ему сообщение с просьбой оставить отзыв через тот мессенджер,
который у него привязан.

Требует заголовок:  X-API-Key: <API_SECRET_KEY>

Примеры запросов:
  {"phone": "+66812345678"}
  {"telegram_chat_id": "123456789"}
  {"line_user_id": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional

from core.database import get_db
from core.security import require_api_key
from models.user import User
from models.channel import Channel, ChannelType
from services.router import route_message
from adapters import telegram as tg_adapter
from adapters import line as line_adapter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Тексты отзыва (можно расширить локализацией) ─────────────────────────────
REVIEW_MESSAGES = {
    "ru": (
        "🙏 Благодарим за покупку!\n\n"
        "Пожалуйста, оставьте отзыв о товаре — это займёт меньше минуты "
        "и поможет нам стать лучше. Ваше мнение очень важно для нас! 💬"
    ),
    "en": (
        "🙏 Thank you for your purchase!\n\n"
        "We'd love to hear your feedback — it takes less than a minute "
        "and helps us improve. Your opinion matters! 💬"
    ),
    "th": (
        "🙏 ขอบคุณสำหรับการซื้อของคุณ!\n\n"
        "กรุณาฝากรีวิวสินค้า — ใช้เวลาไม่ถึงนาที "
        "และช่วยให้เราพัฒนาได้ดีขึ้น ความคิดเห็นของคุณสำคัญมาก! 💬"
    ),
}

DEFAULT_REVIEW_MESSAGE = REVIEW_MESSAGES["ru"]


def _review_text(lang: Optional[str]) -> str:
    return REVIEW_MESSAGES.get(lang or "ru", DEFAULT_REVIEW_MESSAGE)


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    """
    Укажите ОДИН из трёх идентификаторов:
    - phone            : номер телефона пользователя (E.164)
    - telegram_chat_id : chat_id в Telegram
    - line_user_id     : userId в LINE
    """
    phone:            Optional[str] = None
    telegram_chat_id: Optional[str] = None
    line_user_id:     Optional[str] = None
    # Опционально — текст сообщения на нужном языке (ru/en/th).
    # Если не указан — берётся язык из профиля пользователя (или ru).
    language:         Optional[str] = None


class ReviewResponse(BaseModel):
    status:  str          # "sent" | "no_channel"
    channel: Optional[str] = None
    detail:  Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _find_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(User.phone == phone).options(selectinload(User.channels))
    )
    return result.scalars().first()


async def _find_user_by_channel(
    db: AsyncSession, channel_type: ChannelType, external_id: str
) -> Optional[User]:
    result = await db.execute(
        select(User)
        .join(User.channels)
        .where(Channel.type == channel_type, Channel.external_id == external_id)
        .options(selectinload(User.channels))
    )
    return result.scalars().first()


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/review",
    response_model=ReviewResponse,
    status_code=200,
    summary="Отправить пользователю запрос на отзыв о товаре",
    dependencies=[Depends(require_api_key)],
)
async def send_review_request(
    body: ReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Находит пользователя по phone / telegram_chat_id / line_user_id
    и отправляет ему сообщение с просьбой оставить отзыв.

    Если указан telegram_chat_id или line_user_id — сообщение идёт напрямую
    в тот мессенджер (только если чат уже открыт / пользователь подписан).

    Если указан phone — ищем привязанные каналы и отправляем через лучший
    (LINE → Telegram → WhatsApp).
    """
    identifiers = [body.phone, body.telegram_chat_id, body.line_user_id]
    if sum(x is not None for x in identifiers) == 0:
        raise HTTPException(
            status_code=422,
            detail="Specify at least one of: phone, telegram_chat_id, line_user_id",
        )

    # ── 1. Прямая отправка по chat_id / line userId ───────────────────────────
    if body.telegram_chat_id and not body.phone:
        text = _review_text(body.language)
        try:
            ok = await tg_adapter.send_message(body.telegram_chat_id, text)
        except Exception as exc:
            logger.warning("Telegram direct send failed: %s", exc)
            raise HTTPException(502, f"Telegram delivery failed: {exc}")
        if ok:
            return ReviewResponse(status="sent", channel="telegram")
        return ReviewResponse(status="no_channel", detail="Telegram returned not-ok")

    if body.line_user_id and not body.phone:
        text = _review_text(body.language)
        try:
            ok = await line_adapter.send_message(body.line_user_id, text)
        except Exception as exc:
            logger.warning("LINE direct send failed: %s", exc)
            raise HTTPException(502, f"LINE delivery failed: {exc}")
        if ok:
            return ReviewResponse(status="sent", channel="line")
        return ReviewResponse(status="no_channel", detail="LINE returned not-ok")

    # ── 2. Поиск по phone ─────────────────────────────────────────────────────
    if body.phone:
        user = await _find_user_by_phone(db, body.phone)

        # Если phone не найден, но есть и telegram_chat_id — пробуем через него
        if not user and body.telegram_chat_id:
            text = _review_text(body.language)
            try:
                await tg_adapter.send_message(body.telegram_chat_id, text)
                return ReviewResponse(status="sent", channel="telegram")
            except Exception as exc:
                raise HTTPException(502, f"Telegram delivery failed: {exc}")

        if not user and body.line_user_id:
            text = _review_text(body.language)
            try:
                await line_adapter.send_message(body.line_user_id, text)
                return ReviewResponse(status="sent", channel="line")
            except Exception as exc:
                raise HTTPException(502, f"LINE delivery failed: {exc}")

        if not user:
            raise HTTPException(404, f"User with phone {body.phone!r} not found")

        if not user.channels:
            return ReviewResponse(
                status="no_channel",
                detail="User has no bound messenger channels",
            )

        lang = body.language or user.language or "ru"
        text = _review_text(lang)
        channel_used = await route_message(user.channels, text)

        if not channel_used:
            return ReviewResponse(
                status="no_channel",
                detail="All channels failed to deliver",
            )
        return ReviewResponse(status="sent", channel=channel_used)

    # Недостижимо
    raise HTTPException(422, "Unexpected state")
