from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_jwt
from app.db.session import get_db
from app.models import User
from app.models.user import UserRole

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]


async def _user_from_token(token: str, db: AsyncSession) -> User:
    try:
        decoded = decode_jwt(token)
        uid = UUID(decoded["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise UnauthorizedError("Invalid or expired token") from None

    if decoded.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")

    user = await db.get(User, uid)
    if user is None:
        raise UnauthorizedError("Invalid or expired token")

    return user


async def get_current_user(credentials: BearerCredentials, db: DbSession) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing token")
    return await _user_from_token(credentials.credentials, db)


async def get_optional_user(
    credentials: BearerCredentials, db: DbSession
) -> User | None:
    if credentials is None:
        return None
    return await _user_from_token(credentials.credentials, db)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin access required")

    return user


AdminUser = Annotated[User, Depends(require_admin)]
