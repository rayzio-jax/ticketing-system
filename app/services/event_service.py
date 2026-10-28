from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Event
from app.models.event import EventStatus
from app.schemas.event import EventCreate, EventUpdate

EVENT_STATUS_TRANSITION: dict[EventStatus, set[EventStatus]] = {
    EventStatus.DRAFT: {EventStatus.PUBLISHED, EventStatus.CANCELLED},
    EventStatus.PUBLISHED: {EventStatus.ENDED, EventStatus.CANCELLED},
    EventStatus.ENDED: set(),
    EventStatus.CANCELLED: set(),
}


async def create_event(db: AsyncSession, payload: EventCreate) -> Event:
    if payload.start_at <= datetime.now(UTC):
        raise ValidationError("Event start time must be ahead of now")

    event = Event(name=payload.name, venue=payload.venue, start_at=payload.start_at)
    db.add(event)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Event already exists") from None
    await db.refresh(event)
    return event


async def read_event(db: AsyncSession, event_id: UUID) -> Event:
    event = await db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event is not found")

    return event


async def read_public_event(db: AsyncSession, event_id: UUID) -> Event:
    event = await read_event(db, event_id)
    if (
        event.status == EventStatus.DRAFT
        or event.status == EventStatus.CANCELLED
        or event.status == EventStatus.ENDED
    ):
        raise NotFoundError("Event is not found")

    return event


async def update_event(db: AsyncSession, event_id: UUID, payload: EventUpdate) -> Event:
    event = await db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event is not found")

    if not EVENT_STATUS_TRANSITION[event.status]:
        raise ConflictError(f"Cannot modify an event that is {event.status}")

    if payload.start_at is not None and payload.start_at <= datetime.now(UTC):
        raise ValidationError("Event start time must be ahead of now")

    if payload.status is not None and payload.status != event.status:
        if payload.status not in EVENT_STATUS_TRANSITION[event.status]:
            raise ConflictError(
                f"Cannot change status from {event.status} to {payload.status}"
            )

    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in changes.items():
        setattr(event, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Event already exists") from None
    await db.refresh(event)
    return event
