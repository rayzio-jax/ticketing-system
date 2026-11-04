from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.error import ErrorResponse
from app.schemas.ticket_tier import TierCreate, TierResponse, TierUpdate
from app.services import ticket_tier_service

router = APIRouter(prefix="/events/{event_id}/tiers", tags=["tiers"])


@router.post(
    "",
    response_model=TierResponse,
    status_code=201,
    summary="Create a ticket tier",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "Event is not found"},
        409: {
            "model": ErrorResponse,
            "description": "Tier already exists for this event, or event is locked",
        },
        422: {"model": ErrorResponse, "description": "Invalid input"},
    },
)
async def create_tier(
    event_id: UUID, payload: TierCreate, db: DbSession, _admin: AdminUser
):
    """Create a ticket tier under an event. Only admins can access this endpoint.

    `price` is in rupiah and `quota` is the number of tickets available. The
    `sold` counter always starts at 0 and cannot be set. Tier names must be
    unique within an event, and tiers cannot be added to events that are
    `ended` or `cancelled`.
    """
    return await ticket_tier_service.create_tier(db, event_id, payload)


@router.patch(
    "/{tier_id}",
    response_model=TierResponse,
    summary="Update a ticket tier",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "Event or tier not found"},
        409: {
            "model": ErrorResponse,
            "description": "Name already used, quota below sold tickets, or event is locked",
        },
        422: {"model": ErrorResponse, "description": "Invalid input"},
    },
)
async def update_tier(
    event_id: UUID, tier_id: int, payload: TierUpdate, db: DbSession, _admin: AdminUser
):
    """Partially update a ticket tier. Only admins can access this endpoint.

    Only the fields you send are changed. `quota` cannot be lowered below the number
    of tickets already sold, and tiers of `ended` or `cancelled` events cannot be
    modified. The `sold` counter is managed by bookings and cannot be set here.
    """
    return await ticket_tier_service.update_tier(db, event_id, tier_id, payload)


@router.get(
    "/{tier_id}",
    response_model=TierResponse,
    summary="Fetch a ticket tier",
    responses={
        404: {"model": ErrorResponse, "description": "Event or tier not found"},
    },
)
async def get_tier(event_id: UUID, tier_id: int, db: DbSession):
    """Public endpoint. Fetch a ticket tier of an event."""
    return await ticket_tier_service.read_tier(db, event_id, tier_id)
