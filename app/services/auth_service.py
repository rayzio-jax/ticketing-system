from uuid import UUID

import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    InvalidCredentialsError,
    UnauthorizedError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def register(db: AsyncSession, payload: RegisterRequest) -> User:
    """Create a customer account. Role is set to `customer` by default."""
    email = _normalize_email(payload.email)

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        raise ConflictError("Email already registered")

    user = User(email=email, password_hash=get_password_hash(payload.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Email already registered") from None
    await db.refresh(user)
    return user


async def login(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
    """Verify user credentials and return a JWT token."""
    email = _normalize_email(payload.email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise InvalidCredentialsError()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


async def refresh_session(
    db: AsyncSession, payload: RefreshRequest
) -> AccessTokenResponse:
    """Generate new access token from a valid refresh token."""
    try:
        decoded = decode_jwt(payload.refresh_token)
        uid = UUID(decoded["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise UnauthorizedError("Invalid or expired token") from None

    if decoded.get("type") != "refresh":
        raise UnauthorizedError("Invalid token type")

    user = await db.get(User, uid)
    if user is None:
        raise UnauthorizedError("Invalid or expired token")

    return AccessTokenResponse(access_token=create_access_token(user.id))
