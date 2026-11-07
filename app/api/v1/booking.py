from typing import Annotated

from fastapi import APIRouter, Header

from app.api.deps import CurrentUser, DbSession
from app.schemas.booking import BookingRequest, BookingResponse
from app.schemas.error import ErrorResponse
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    status_code=201,
    response_model=BookingResponse,
    summary="Book an event ticket",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        404: {
            "model": ErrorResponse,
            "description": "Event or Ticket is not found",
        },
        409: {
            "model": ErrorResponse,
            "description": "Idempotency key used or no remaining quota left",
        },
    },
)
async def create_booking(
    payload: BookingRequest,
    current_user: CurrentUser,
    db: DbSession,
    idem_key: Annotated[str, Header(min_length=8, max_length=255)],
):
    """Public endpoint. Create a booking by the `tier_id` of the event.

    Only 1 booking is available per 1 user, a booking will expired if
    user has not proceed into payment within 15 minutes.
    Booking is handled with idempotency key to prevent multiple
    booking actions concurrently per user.
    """
    return await booking_service.create_booking(db, current_user, idem_key, payload)
