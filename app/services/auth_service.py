from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, InvalidCredentials
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def register(db: AsyncSession, payload: RegisterRequest) -> User:
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
    email = _normalize_email(payload.email)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise InvalidCredentials()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )
