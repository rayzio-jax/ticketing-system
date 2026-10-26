from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.error import ErrorResponse
from app.schemas.event import EventCreate, EventResponse
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "/new",
    response_model=EventResponse,
    status_code=201,
    summary="Create a new event",
    responses={401: {"model": ErrorResponse, "description": "Unauthorize access"}},
)
async def new_event(db: DbSession, payload: EventCreate, _admin: AdminUser):
    """Create an event; only authenticated admins may access this endpoint"""
    return await event_service.create_event(db, payload)
