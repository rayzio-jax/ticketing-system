from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.event import Event


class TicketTier(TimestampMixin, Base):
    __tablename__ = "ticket_tiers"
    __table_args__ = (
        CheckConstraint("sold >= 0 AND sold <= quota", name="sold_within_quota"),
        CheckConstraint("quota > 0", name="quota_positive"),
        CheckConstraint("price >= 0", name="price_non_negative"),
        UniqueConstraint("event_id", "name", name="event_tier_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[int]
    quota: Mapped[int]
    sold: Mapped[int] = mapped_column(server_default="0")

    event: Mapped["Event"] = relationship(back_populates="tiers")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="tier")
