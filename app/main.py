from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import engine, get_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Simple ticketing system API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to ticketing system"}


@app.get("/health", tags=["Health"])
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}
