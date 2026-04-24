import httpx
from core.config import get_settings

settings = get_settings()
TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

async def send_message(chat_id: str, text: str) -> bool:
    """Send a text message via Telegram Bot API."""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    resp.raise_for_status()
    return resp.json().get("ok", False)

async def send_photo(chat_id: str, photo_url: str, caption: str = "") -> bool:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TELEGRAM_API}/sendPhoto",
            json={"chat_id": chat_id, "photo": photo_url, "caption": caption},
            timeout=10,
        )
    resp.raise_for_status()
    return resp.json().get("ok", False)
