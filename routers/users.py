from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from services import user_service
from models.schemas import UserCreate, UserRead, ChannelRead

router = APIRouter()

@router.post("/", response_model=UserRead, status_code=201)
async def register_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    user, created = await user_service.get_or_create(db, body.phone, body.name or "")
    if not created:
        raise HTTPException(409, "User with this phone already exists")
    return user

@router.get("/{phone}", response_model=UserRead)
async def get_user(phone: str, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_by_phone(db, phone)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.get("/{phone}/channels", response_model=list[ChannelRead])
async def get_channels(phone: str, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_by_phone(db, phone)
    if not user:
        raise HTTPException(404, "User not found")
    return user.channels
