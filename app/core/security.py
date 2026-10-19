from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password=plain_password, hash=hashed_password)


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password=password)


def encode_jwt(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub"]},
    )


def _create_token(
    user_id: UUID, token_type: Literal["access", "refresh"], expires_delta: timedelta
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return encode_jwt(payload)


def create_access_token(user_id: UUID) -> str:
    return _create_token(
        user_id, "access", timedelta(minutes=settings.access_token_expiration_minutes)
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        user_id, "refresh", timedelta(days=settings.refresh_token_expiration_days)
    )
