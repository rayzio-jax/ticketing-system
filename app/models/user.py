import enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_values

if TYPE_CHECKING:
    from app.models.booking import Booking


class UserRole(enum.StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=enum_values),
        default=UserRole.CUSTOMER,
    )

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
