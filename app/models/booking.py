import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_values

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.ticket_tier import TicketTier
    from app.models.user import User


class BookingStatus(enum.StrEnum):
    PENDING = "pending"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


BOOKING_STATUS_TRANSITION: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {
        BookingStatus.PAID,
        BookingStatus.EXPIRED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.PAID: set(),
    BookingStatus.EXPIRED: set(),
    BookingStatus.CANCELLED: set(),
}


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("qty > 0", name="qty_positive"),
        CheckConstraint("total_amount >= 0", name="total_amount_non_negative"),
        UniqueConstraint("user_id", "idem_key", name="user_idem_key"),
        Index("ix_bookings_expires_at", "expires_at"),
        Index(
            "uq_bookings_pending_user_tier",
            "user_id",
            "tier_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    tier_id: Mapped[int] = mapped_column(ForeignKey("ticket_tiers.id"), index=True)
    qty: Mapped[int]
    total_amount: Mapped[int]
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status", values_callable=enum_values),
        default=BookingStatus.PENDING,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    idem_key: Mapped[str] = mapped_column(String(255))

    user: Mapped["User"] = relationship(back_populates="bookings")
    tier: Mapped["TicketTier"] = relationship(back_populates="bookings")
    payments: Mapped[list["Payment"]] = relationship(back_populates="booking")
