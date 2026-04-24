from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.schemas import PurchaseEvent, PurchaseRead
from models.purchase import Purchase
from services import user_service, odoo
from services.router import route_message
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

POINTS_PER_UNIT = 1  # 1 point per 1 currency unit

@router.post("/", response_model=PurchaseRead, status_code=201)
async def handle_purchase(event: PurchaseEvent, db: AsyncSession = Depends(get_db)):
    """
    Main POS → API flow:
    1. Get or create user
    2. Upsert Odoo contact + add loyalty points
    3. Route notification to best channel
    4. Save purchase record
    """
    # 1. User
    user, _ = await user_service.get_or_create(db, event.phone)

    # 2. Odoo CRM
    try:
        odoo_id = await odoo.upsert_contact(event.phone, user.name or "")
        if user.odoo_id != odoo_id:
            user.odoo_id = odoo_id
            await db.commit()

        points = int(event.amount * POINTS_PER_UNIT)
        await odoo.add_loyalty_points(odoo_id, points)
        balance = await odoo.get_loyalty_balance(odoo_id)
    except Exception as exc:
        logger.warning("Odoo unavailable: %s", exc)
        points = int(event.amount * POINTS_PER_UNIT)
        balance = points  # fallback

    # 3. Reload user with channels
    user = await user_service.get_by_phone(db, event.phone)
    message = (
        f"🛍 Спасибо за покупку на {event.amount:.0f}!\n"
        f"✨ Начислено {points} баллов.\n"
        f"💎 Ваш баланс: {balance:.0f} баллов."
    )
    channel_used = await route_message(user.channels, message) if user.channels else None

    # 4. Save
    purchase = Purchase(
        user_id=user.id,
        phone=event.phone,
        amount=event.amount,
        store_id=event.store_id,
        channel_sent=channel_used,
    )
    db.add(purchase)
    await db.commit()
    await db.refresh(purchase)
    return purchase
