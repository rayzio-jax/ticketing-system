import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_values

if TYPE_CHECKING:
    from app.models.booking import Booking


class PaymentStatus(enum.StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount > 0", name="amount_non_negative"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    booking_id: Mapped[UUID] = mapped_column(ForeignKey("bookings.id"), index=True)
    amount: Mapped[int]
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", values_callable=enum_values),
        default=PaymentStatus.PENDING,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    booking: Mapped["Booking"] = relationship(back_populates="payments")
