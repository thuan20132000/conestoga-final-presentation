"""Main router that combines all route modules."""

from fastapi import APIRouter
from fastapi.routing import health, twilio, websocket, booking

# Create main router
main_router = APIRouter(tags=["main"])

# Include all sub-routers
main_router.include_router(health.router)
main_router.include_router(twilio.router)
main_router.include_router(websocket.router)
main_router.include_router(booking.router)
