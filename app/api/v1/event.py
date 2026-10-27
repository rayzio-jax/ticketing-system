from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.error import ErrorResponse
from app.schemas.event import EventCreate, EventResponse
from app.services import event_service

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EventResponse,
    status_code=201,
    summary="Create a new event",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        422: {"model": ErrorResponse, "description": "Start time is not in the future"},
        409: {"model": ErrorResponse, "description": "Event already exists"},
    },
)
async def create_event(db: DbSession, payload: EventCreate, _admin: AdminUser):
    """Create an event. Only admins can access this endpoint.

    The event is always created with the `draft` status. `start_at` must be in
    the future and include a timezone offset.
    """
    return await event_service.create_event(db, payload)
