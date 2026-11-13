import logging
from contextlib import asynccontextmanager

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_MISSED,
    JobExecutionEvent,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import DbSession
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.db.session import engine
from app.tasks.expiry import run_expiry

logger = logging.getLogger(__name__)


def log_scheduler_event(e: JobExecutionEvent) -> None:
    if e.code == EVENT_JOB_EXECUTED:
        logger.info(
            "Job %s done; scheduled_at=%s",
            e.job_id,
            e.scheduled_run_time,
        )
    elif e.code == EVENT_JOB_ERROR:
        logger.error(
            "Job %s failed; scheduled_at=%s; exception=%r",
            e.job_id,
            e.scheduled_run_time,
            e.exception,
        )
    elif e.code == EVENT_JOB_MISSED:
        logger.warning(
            "Job %s skipped; scheduled_at=%s",
            e.job_id,
            e.scheduled_run_time,
        )


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_expiry,
        IntervalTrigger(minutes=1),
        id="expire_bookings",
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_listener(
        log_scheduler_event,
        EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED,
    )

    logger.info("Starting app and scheduler")
    scheduler.start()
    app.state.scheduler = scheduler

    try:
        yield
    finally:
        logger.info("Stopping app and scheduler")
        scheduler.shutdown()
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
