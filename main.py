from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import users, purchases, channels, webhooks
from core.database import init_db

app = FastAPI(
    title="Messaging Router API",
    description="Purchase events → CRM → LINE / Telegram / WhatsApp routing",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router,     prefix="/users",     tags=["Users"])
app.include_router(purchases.router, prefix="/purchases", tags=["Purchases"])
app.include_router(channels.router,  prefix="/channels",  tags=["Channels"])
app.include_router(webhooks.router,  prefix="/webhooks",  tags=["Webhooks"])

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok"}
