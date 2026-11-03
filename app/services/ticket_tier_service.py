from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models import TicketTier
from app.models.event import EVENT_STATUS_TRANSITION, Event
from app.schemas.ticket_tier import TierCreate, TierUpdate


async def create_tier(
    db: AsyncSession, event_id: UUID, payload: TierCreate
) -> TicketTier:
    event = await db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event is not found")

    if not EVENT_STATUS_TRANSITION[event.status]:
        raise ConflictError(f"Cannot add tiers to an event that is {event.status}")

    tier = TicketTier(
        event_id=event_id,
        name=payload.name.capitalize(),
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


async def update_tier(
    db: AsyncSession, event_id: UUID, tier_id: int, payload: TierUpdate
) -> TicketTier:
    event = await db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event is not found")

    tier = await db.scalar(
        select(TicketTier).where(
            TicketTier.id == tier_id, TicketTier.event_id == event_id
        )
    )
    if tier is None:
        raise NotFoundError("Tier is not found")

    if not EVENT_STATUS_TRANSITION[event.status]:
        raise ConflictError(f"Cannot modify tiers of an event that is {event.status}")

    if payload.quota is not None and payload.quota < tier.sold:
        raise ConflictError(
            f"Quota cannot be lower than the {tier.sold} tickets already sold"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == tier.name:
            field = field.capitalize()
        setattr(tier, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError(
            "A tier with this name already exists for this event"
        ) from None
    await db.refresh(tier)
    return tier


async def read_tier(db: AsyncSession, event_id: UUID, tier_id: int) -> TicketTier:
    event = await db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event is not found")

    tier = await db.scalar(
        select(TicketTier).where(
            TicketTier.event_id == event_id, TicketTier.id == tier_id
        )
    )
    if tier is None:
        raise NotFoundError("Tier is not found")

    return tier
