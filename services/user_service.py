from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.user import User
from models.channel import Channel, ChannelType

async def get_by_phone(db: AsyncSession, phone: str) -> User | None:
    result = await db.execute(
        select(User).where(User.phone == phone).options(selectinload(User.channels))
    )
    return result.scalars().first()

async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id).options(selectinload(User.channels))
    )
    return result.scalars().first()

async def create(db: AsyncSession, phone: str, name: str = "", language: str = "ru") -> User:
    user = User(phone=phone, name=name, language=language)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_or_create(db: AsyncSession, phone: str, name: str = "") -> tuple[User, bool]:
    user = await get_by_phone(db, phone)
    if user:
        return user, False
    user = await create(db, phone, name)
    return user, True

async def bind_channel(
    db: AsyncSession, user_id: int, channel_type: ChannelType, external_id: str
) -> Channel:
    # remove old binding of same type for this user
    existing = await db.execute(
        select(Channel).where(Channel.user_id == user_id, Channel.type == channel_type)
    )
    for old in existing.scalars().all():
        await db.delete(old)

    ch = Channel(user_id=user_id, type=channel_type, external_id=external_id)
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ch
