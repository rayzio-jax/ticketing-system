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

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest, db: DbSession):
    return await auth_service.register(db, payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: DbSession):
    return await auth_service.login(db, payload)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(payload: RefreshRequest, db: DbSession):
    return await auth_service.refresh_session(db, payload)
