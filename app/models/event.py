import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_values

if TYPE_CHECKING:
    from app.models.ticket_tier import TicketTier


class EventStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ENDED = "ended"
    CANCELLED = "cancelled"


EVENT_STATUS_TRANSITION: dict[EventStatus, set[EventStatus]] = {
    EventStatus.DRAFT: {EventStatus.PUBLISHED, EventStatus.CANCELLED},
    EventStatus.PUBLISHED: {EventStatus.ENDED, EventStatus.CANCELLED},
    EventStatus.ENDED: set(),
    EventStatus.CANCELLED: set(),
}


class Event(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("name", "venue", "start_at", name="event_identity"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    venue: Mapped[str] = mapped_column(String(255))
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status", values_callable=enum_values),
        default=EventStatus.DRAFT,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    tiers: Mapped[list["TicketTier"]] = relationship(back_populates="event")
