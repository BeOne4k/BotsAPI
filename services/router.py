"""
Messaging Router
Priority: LINE → Telegram → WhatsApp
"""
import logging
from models.channel import ChannelType
from adapters import telegram, line, whatsapp

logger = logging.getLogger(__name__)

async def route_message(channels: list, text: str) -> str | None:
    """
    Try channels in priority order.
    Returns the ChannelType that succeeded, or None if all failed.
    channels: list of Channel ORM objects (already loaded for this user)
    """
    channel_map = {c.type: c for c in channels}

    for channel_type in (ChannelType.line, ChannelType.telegram, ChannelType.whatsapp):
        ch = channel_map.get(channel_type)
        if not ch:
            continue
        try:
            if channel_type == ChannelType.line:
                await line.send_message(ch.external_id, text)
            elif channel_type == ChannelType.telegram:
                await telegram.send_message(ch.external_id, text)
            elif channel_type == ChannelType.whatsapp:
                await whatsapp.send_message(ch.external_id, text)

            logger.info("Message delivered via %s to %s", channel_type, ch.external_id)
            return channel_type.value

        except Exception as exc:
            logger.warning("Failed to send via %s: %s", channel_type, exc)
            continue

    logger.error("All channels failed for channels: %s", channels)
    return None
