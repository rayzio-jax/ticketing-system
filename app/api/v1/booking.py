from typing import Annotated

from fastapi import APIRouter, Header

from app.api.deps import CurrentUser, DbSession
from app.schemas.booking import BookingListParams, BookingRequest, BookingResponse
from app.schemas.error import ErrorResponse
from app.schemas.pagination import Page
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
            "description": "Tier not found, or event is not open",
        },
        409: {
            "model": ErrorResponse,
            "description": "Not enough tickets, or key reused with another request",
        },
        422: {
            "model": ErrorResponse,
            "description": "Invalid body or missing Idempotency-Key header",
        },
    },
)
async def create_booking(
    payload: BookingRequest,
    current_user: CurrentUser,
    db: DbSession,
    idem_key: Annotated[str, Header(min_length=8, max_length=255)],
):
    """Reserve tickets from a tier. Requires a logged-in user.

    The booking starts as `pending` and holds the tickets until `expires_at`.
    Unpaid bookings expire and the tickets are released. The total amount is
    calculated by the server.

    Send a unique `Idempotency-Key` header for each booking attempt. Retrying
    with the same key and the same body returns the original booking instead
    of creating a new one. Reusing the key with a different body returns `409`.
    """
    return await booking_service.create_booking(db, current_user, idem_key, payload)


@router.get(
    "",
    response_model=Page[BookingResponse],
    summary="Get all bookings owned by user",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        422: {
            "model": ErrorResponse,
            "description": "Invalid parameters or cursor",
        },
    },
)
async def list_user_bookings(
    user: CurrentUser, db: DbSession, params: BookingListParams
):
    """List the bookings of the logged-in user, newest first.

    Bookings of every status (`pending`, `paid`, `expired`, `cancelled`) are
    returned, even if the event is no longer public. Use `status` to filter by
    a single status.

    Results are cursor-paginated. Pass `next_cursor` from the response as
    `cursor` to get the next page; `null` means there are no more pages. Keep
    the same `order` and `status` across pages.
    """
    return await booking_service.list_user_bookings(db, user, params)
