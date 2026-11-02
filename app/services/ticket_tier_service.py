from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import TicketTier
from app.models.event import Event
from app.schemas.ticket_tier import TierCreate
from app.services.event_service import EVENT_STATUS_TRANSITION


async def create_tier(
    db: AsyncSession, event_id: UUID, payload: TierCreate
) -> TicketTier:
    event = await db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event not found")

    if not EVENT_STATUS_TRANSITION[event.status]:
        raise ConflictError(f"Cannot add tiers to an event that is {event.status}")

    tier = TicketTier(
        event_id=event_id,
        name=payload.name,
        price=payload.price,
        quota=payload.quota,
    )
    db.add(tier)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError(
            "A tier with this name already exists for the event"
        ) from None
    await db.refresh(tier)
    return tier
