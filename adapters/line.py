import httpx
import hashlib, hmac, base64
from core.config import get_settings

settings = get_settings()
LINE_API = "https://api.line.me/v2/bot"

HEADERS = {
    "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

async def send_message(user_id: str, text: str) -> bool:
    """Push a text message to a LINE user."""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN is not set")

    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": text}],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{LINE_API}/message/push", json=payload, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return True

async def send_flex(user_id: str, alt_text: str, contents: dict) -> bool:
    """Push a Flex Message (rich card) to a LINE user."""
    payload = {
        "to": user_id,
        "messages": [{"type": "flex", "altText": alt_text, "contents": contents}],
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{LINE_API}/message/push", json=payload, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return True

def verify_signature(body: bytes, signature: str) -> bool:
    """Verify LINE webhook X-Line-Signature header."""
    secret = settings.LINE_CHANNEL_SECRET.encode()
    digest = hmac.new(secret, body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)
