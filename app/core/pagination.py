import base64
import json
from datetime import datetime
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import Select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute


def encode_cursor(sort_value: datetime, row_id: UUID) -> str:
    raw = json.dumps({"v": sort_value.isoformat(), "id": str(row_id)})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return datetime.fromisoformat(data["v"]), UUID(data["id"])
    except (ValueError, KeyError, TypeError):
        raise ValidationError("Invalid cursor") from None


async def paginate[T](
    db: AsyncSession,
    stmt: Select[T],
    *,
    sort_col: InstrumentedAttribute[datetime],
    id_col: InstrumentedAttribute[UUID],
    limit: int,
    cursor: str | None,
    desc: bool,
) -> tuple[list[T], str | None]:
    if cursor is not None:
        position = tuple_(*decode_cursor(cursor))
        columns = tuple_(sort_col, id_col)
        stmt = stmt.where(columns < position if desc else columns > position)

    if desc:
        stmt = stmt.order_by(sort_col.desc(), id_col.desc())
    else:
        stmt = stmt.order_by(sort_col, id_col)

    rows = list(await db.scalars(stmt.limit(limit + 1)))

    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        next_cursor = encode_cursor(
            getattr(last, sort_col.key), getattr(last, id_col.key)
        )
    return rows, next_cursor
