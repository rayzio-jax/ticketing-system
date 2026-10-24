from fastapi import APIRouter

import app.services.auth_service as auth_service
from app.api.deps import DbSession
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.error import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user",
    responses={
        409: {"model": ErrorResponse, "description": "Email already registered"},
    },
)
async def register(payload: RegisterRequest, db: DbSession):
    """Create a customer account with an email and password.
    The role is always `customer`. Emails that are already registered are rejected.
    """
    return await auth_service.register(db, payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in a user",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid email or password"}
    },
)
async def login(payload: LoginRequest, db: DbSession):
    """Exchange an email and password for an `access_token` and a `refresh_token`.
    Use the access token on protected endpoints. Use the refresh token only to get a new
    access token.
    """
    return await auth_service.login(db, payload)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Get a new access token",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"}
    },
)
async def refresh(payload: RefreshRequest, db: DbSession):
    """Exchange a valid `refresh_token` for a new `access_token`.
    Access tokens are rejected here. If the refresh token has expired, user must log in
    again.
    """
    return await auth_service.refresh_session(db, payload)
