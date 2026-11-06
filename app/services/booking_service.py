from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Booking, Event, TicketTier, User
from app.models.event import EventStatus
from app.schemas.booking import BookingRequest


async def create_booking(
    db: AsyncSession, user: User, idem_key: str, payload: BookingRequest
) -> Booking:
    tier = await db.get(TicketTier, payload.tier_id)
    if tier is None:
        raise NotFoundError("Ticket is not found")

    event = await db.get(Event, tier.event_id)
    if event is None or event.status != EventStatus.PUBLISHED:
        raise NotFoundError("Event is not found")

    if tier.sold + payload.qty > tier.quota:
        raise ConflictError("Not enough tickets available")

    tier.sold += payload.qty
    booking = Booking(
        user_id=user.id,
        ticket_id=tier.id,
        qty=payload.qty,
        total_amount=payload.qty * tier.price,
        expires_at=datetime.now(UTC)
        + timedelta(minutes=settings.booking_expire_minutes),
        idem_key=idem_key,
    )
    db.add(booking)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Idempotency key already used") from None
    await db.refresh(booking)
    return booking
