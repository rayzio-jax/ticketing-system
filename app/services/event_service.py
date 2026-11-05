import base64
import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models import Event
from app.models.event import EVENT_STATUS_TRANSITION, EventStatus
from app.schemas.event import EventCreate, EventListParams, EventUpdate


def _encode_cursor(event: Event) -> str:
    raw = json.dumps({"start_at": event.start_at.isoformat(), "id": str(event.id)})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return datetime.fromisoformat(data["start_at"]), UUID(data["id"])
    except (ValueError, KeyError, TypeError):
        raise ValidationError("Invalid cursor") from None


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
    desc = params.order == "desc"

    stmt = select(Event).where(Event.status.in_([EventStatus.PUBLISHED]))

    if params.cursor is not None:
        pos = tuple_(*_decode_cursor(params.cursor))
        cols = tuple_(Event.start_at, Event.id)
        stmt = stmt.where(cols < pos if desc else cols > pos)

    if desc:
        stmt = stmt.order_by(Event.start_at.desc(), Event.id.desc())
    else:
        stmt = stmt.order_by(Event.start_at, Event.id)

    stmt = stmt.limit(params.limit + 1)

    events = list((await db.execute(stmt)).scalars().all())

    next_cursor = None
    if len(events) > params.limit:
        events = events[: params.limit]
        next_cursor = _encode_cursor(events[-1])

    return events, next_cursor


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
