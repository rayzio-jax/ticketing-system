from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import DbSession
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
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


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    details: dict[str, list[str]] = {}
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"] if p != "body")
        key = loc or "body"
        msg = err["msg"].removeprefix("Value error, ")
        details.setdefault(key, []).append(msg)  # simpan error pertama per field

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": details,
            }
        },
    )


@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to ticketing system"}


@app.get("/health", tags=["health"])
async def health(db: DbSession):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "connected"}


app.include_router(api_router, prefix="/api/v1")
