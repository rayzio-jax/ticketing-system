from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import paginate
from app.models import Event
from app.models.event import EVENT_STATUS_TRANSITION, EventStatus
from app.schemas.event import EventCreate, EventListParams, EventUpdate


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


async def read_event_detail(
    db: AsyncSession, event_id: UUID, include_draft: bool = False
) -> Event:
    event = await db.get(Event, event_id, options=[selectinload(Event.tiers)])
    if event is None or (event.status != EventStatus.PUBLISHED and not include_draft):
        raise NotFoundError("Event is not found")
    return event


async def read_all_public_events(
    db: AsyncSession, params: EventListParams
) -> tuple[list[Event], str | None]:
    stmt = select(Event).where(Event.status.in_([EventStatus.PUBLISHED]))
    return await paginate(
        db,
        stmt,
        sort_col=Event.start_at,
        id_col=Event.id,
        limit=params.limit,
        cursor=params.cursor,
        desc=params.order == "desc",
    )


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
