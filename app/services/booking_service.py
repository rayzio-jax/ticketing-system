from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Booking, Event, TicketTier, User
from app.models.booking import BookingStatus
from app.models.event import EventStatus
from app.schemas.booking import BookingRequest


async def _find_booking(db: AsyncSession, user_id: UUID, idem_key: str):
    return await db.scalar(
        select(Booking).where(Booking.user_id == user_id, Booking.idem_key == idem_key)
    )


async def _find_pending_booking(
    db: AsyncSession, user_id: UUID, tier_id: int
) -> Booking | None:
    return await db.scalar(
        select(Booking).where(
            Booking.user_id == user_id,
            Booking.tier_id == tier_id,
            Booking.status == BookingStatus.PENDING,
            Booking.expires_at > datetime.now(UTC),
        )
    )


async def _replay_or_existing(payload: BookingRequest, booking: Booking):
    if booking.tier_id != payload.tier_id or booking.qty != payload.qty:
        raise ConflictError("Idempotency key was already used with a different request")


async def create_booking(
    db: AsyncSession, user: User, idem_key: str, payload: BookingRequest
) -> Booking:
    existing = await _find_booking(db, user.id, idem_key)
    if existing is not None:
        await _replay_or_existing(payload, existing)

    pending = await _find_pending_booking(db, user.id, payload.tier_id)
    if pending is not None:
        raise ConflictError("There is an existing booking in pending")

    tier = await db.get(TicketTier, payload.tier_id)
    if tier is None:
        raise NotFoundError("Ticket is not found")

    event = await db.get(Event, tier.event_id)
    if event is None or event.status != EventStatus.PUBLISHED:
        raise NotFoundError("Event is not found")

    if tier.sold + payload.qty > tier.quota:
        raise ConflictError("Not enough quota available")

    tier.sold += payload.qty
    booking = Booking(
        user_id=user.id,
        tier_id=tier.id,
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
        existing = await _find_booking(db, user.id, idem_key)
        if existing is None:
            raise
        await _replay_or_existing(payload, existing)
        return existing
    await db.refresh(booking)
    return booking
