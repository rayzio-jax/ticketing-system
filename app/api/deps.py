from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_jwt
from app.db.session import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]


async def get_current_user(credentials: BearerCredentials, db: DbSession) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing token")
    try:
        decoded = decode_jwt(credentials.credentials)
        uid = UUID(decoded["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise UnauthorizedError("Invalid or expired token") from None

    if decoded.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")

    user = await db.get(User, uid)
    if user is None:
        raise UnauthorizedError("Invalid or expired token")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
