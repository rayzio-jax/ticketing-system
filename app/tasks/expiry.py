import logging

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.models import Booking, TicketTier
from app.models.booking import BookingStatus

logger = logging.getLogger(__name__)


async def expire_bookings(db: AsyncSession) -> int:
    expired = (
        await db.execute(
            update(Booking)
            .where(
                Booking.status == BookingStatus.PENDING,
                Booking.expires_at < func.now(),
            )
            .values(status=BookingStatus.EXPIRED)
            .returning(Booking.tier_id, Booking.qty)
        )
    ).all()

    released: dict[int, int] = {}
    for tier_id, qty in expired:
        released[tier_id] = released.get(tier_id, 0) + qty

    for tier_id in sorted(released):
        await db.execute(
            update(TicketTier)
            .where(TicketTier.id == tier_id)
            .values(sold=TicketTier.sold - released[tier_id])
        )
    await db.commit()
    if len(expired) > 0:
        logger.info("Booking resolved: %d`", len(expired))
    else:
        logger.info("No expired booking has resolved")
    return len(expired)


async def run_expiry() -> None:
    async with SessionLocal() as db:
        await expire_bookings(db)
