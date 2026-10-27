from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Event
from app.models.event import EventStatus
from app.schemas.event import EventCreate


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


async def get_event(db: AsyncSession, id: UUID) -> Event:
    event = await db.get(Event, id)
    if event is None or event.status == EventStatus.DRAFT:
        raise NotFoundError("Event not found")

    return event
