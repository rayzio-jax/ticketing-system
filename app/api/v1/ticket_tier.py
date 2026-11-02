from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.error import ErrorResponse
from app.schemas.ticket_tier import TierCreate, TierResponse
from app.services import ticket_tier_service

router = APIRouter(prefix="/evets/{event_id}/tiers", tags=["tiers"])


@router.post(
    "",
    response_model=TierResponse,
    status_code=201,
    summary="Create a ticket tier",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        403: {"model": ErrorResponse, "description": "Admin access required"},
        404: {"model": ErrorResponse, "description": "Event not found"},
        409: {
            "model": ErrorResponse,
            "description": "Tier name already exists for this event, or the event is locked",
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
