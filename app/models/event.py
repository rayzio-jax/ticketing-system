import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, enum_values


class EventStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ENDED = "ended"
    CANCELLED = "cancelled"


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255))
    venue: Mapped[str] = mapped_column(String(255))
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status", values_callable=enum_values),
        default=EventStatus.DRAFT,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
