from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import UUID, AdminUser, DbSession, OptionalUser
from app.models.user import UserRole
from app.schemas.error import ErrorResponse
from app.schemas.event import (
    EventCreate,
    EventDetailResponse,
    EventListParams,
    EventListResponse,
    EventResponse,
    EventUpdate,
)
from app.schemas.pagination import Page
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


@router.get(
    "/{event_id}",
    response_model=EventDetailResponse,
    summary="Get an event",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        404: {
            "model": ErrorResponse,
            "description": "Invalid event id or event is drafted",
        },
        422: {"model": ErrorResponse, "description": "Invalid event id"},
    },
)
async def get_event(db: DbSession, event_id: UUID, user: OptionalUser):
    """Public endpoint.

    Anonymous users and customers can only see events
    that are not in draft. Admins can see any event.
    """
    include_draft = user is not None and user.role == UserRole.ADMIN
    return await event_service.read_event_detail(db, event_id, include_draft)


@router.get(
    "",
    response_model=Page[EventListResponse],
    summary="List public events",
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Invalid query parameters or cursor",
        }
    },
)
async def get_all_events(db: DbSession, params: Annotated[EventListParams, Query()]):
    """List events that are not in `draft`, `ended` or `cancelled`.
    Ordered by `start_at`.

    Use `next_cursor` from the response as `cursor` to get the next page. When
    `next_cursor` is `null`, there are no more pages. Keep the same `order`
    across pages.
    """
    events, next_cursor = await event_service.read_all_public_events(db, params)
    return Page[EventListResponse](
        items=[EventListResponse.model_validate(event) for event in events],
        next_cursor=next_cursor,
    )


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    summary="Update an event",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "Event is not found"},
        409: {"model": ErrorResponse, "description": "Event already exists"},
        422: {"model": ErrorResponse, "description": "Invalid input"},
    },
)
async def update_event(
    db: DbSession, event_id: UUID, payload: EventUpdate, _admin: AdminUser
):
    """Partially update an event. Only admins can access this endpoint.

    Only the fields sent in the request body are changed. Fields cannot be `null`.
    A `409` is returned if the new name, venue, and start time match
    another event.
    """
    return await event_service.update_event(db, event_id, payload)
