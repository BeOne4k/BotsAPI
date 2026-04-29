"""
API-key authentication dependency.
Pass the key in the X-API-Key header.
"""
from fastapi import Header, HTTPException, status
from core.config import get_settings

settings = get_settings()


async def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """FastAPI dependency — raises 401 if key is missing or wrong."""
    if not settings.API_SECRET_KEY or x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
