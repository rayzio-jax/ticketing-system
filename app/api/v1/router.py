from fastapi import APIRouter

from app.api.v1 import auth, booking, event, ticket_tier

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(event.router)
api_router.include_router(ticket_tier.router)
api_router.include_router(booking.router)
