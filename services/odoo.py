"""
Odoo CRM integration via XML-RPC.
Handles: contact upsert, loyalty points, purchase history.
"""
import xmlrpc.client
import asyncio
from functools import partial
from core.config import get_settings

settings = get_settings()

def _get_uid() -> int:
    common = xmlrpc.client.ServerProxy(f"{settings.ODOO_URL}/xmlrpc/2/common")
    return common.authenticate(settings.ODOO_DB, settings.ODOO_USERNAME, settings.ODOO_PASSWORD, {})

def _models():
    return xmlrpc.client.ServerProxy(f"{settings.ODOO_URL}/xmlrpc/2/object")

async def _run_sync(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args))

# ── Public API ────────────────────────────────────────────

async def upsert_contact(phone: str, name: str = "") -> int:
    """Create or update Odoo contact by phone. Returns odoo contact id."""
    uid = await _run_sync(_get_uid)
    models = _models()

    # search existing
    ids = await _run_sync(
        models.execute_kw,
        settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
        "res.partner", "search",
        [[["phone", "=", phone]]],
    )

    data = {"phone": phone, "name": name or phone}
    if ids:
        await _run_sync(
            models.execute_kw,
            settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
            "res.partner", "write",
            [ids, data],
        )
        return ids[0]
    else:
        new_id = await _run_sync(
            models.execute_kw,
            settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
            "res.partner", "create",
            [data],
        )
        return new_id

async def add_loyalty_points(odoo_id: int, points: int, reason: str = "purchase") -> None:
    """Add loyalty points to a contact (uses loyalty.card model if available)."""
    uid = await _run_sync(_get_uid)
    models = _models()
    # This requires Odoo loyalty module; adjust model name if needed
    try:
        await _run_sync(
            models.execute_kw,
            settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
            "loyalty.card", "create",
            [{"partner_id": odoo_id, "points": points, "source": reason}],
        )
    except Exception:
        pass  # loyalty module may not be installed

async def get_loyalty_balance(odoo_id: int) -> float:
    """Fetch total loyalty points for a contact."""
    uid = await _run_sync(_get_uid)
    models = _models()
    try:
        cards = await _run_sync(
            models.execute_kw,
            settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
            "loyalty.card", "search_read",
            [[["partner_id", "=", odoo_id]]],
            {"fields": ["points"]},
        )
        return sum(c["points"] for c in cards)
    except Exception:
        return 0.0
