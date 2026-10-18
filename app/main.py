from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings
from app.db.session import engine


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
async def health(db: DbSession):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}
