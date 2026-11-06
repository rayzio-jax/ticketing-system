from typing import Annotated

from fastapi import APIRouter, Header

from app.api.deps import CurrentUser, DbSession
from app.schemas.booking import BookingRequest, BookingResponse
from app.schemas.error import ErrorResponse
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingResponse,
    summary="Book an event ticket",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        404: {
            "model": ErrorResponse,
            "description": "Event or Ticket is not found",
        },
    },
)
async def create_booking(
    payload: BookingRequest,
    current_user: CurrentUser,
    db: DbSession,
    idem_key: Annotated[str, Header(min_length=8, max_length=255)],
):
    return await booking_service.create_booking(db, current_user, idem_key, payload)
