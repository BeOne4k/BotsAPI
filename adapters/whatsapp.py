import httpx
from core.config import get_settings

settings = get_settings()
WA_API = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

async def send_message(to: str, text: str) -> bool:
    """Send a free-form text message (only within 24-hour session window)."""
    if not settings.WHATSAPP_ACCESS_TOKEN:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN is not set")

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(WA_API, json=payload, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return True

async def send_template(to: str, template_name: str, language: str = "ru", components: list = None) -> bool:
    """Send an approved template message (works outside 24h window)."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            **({"components": components} if components else {}),
        },
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(WA_API, json=payload, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return True
