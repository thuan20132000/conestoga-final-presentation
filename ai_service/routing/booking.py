"""Health and test routes for the AI Receptionist application."""

from fastapi import APIRouter
from datetime import datetime
from ai_service.config import settings
from ai_service.services.booking_api import BookingAPI
from receptionist.models import SystemLog

# Create router
router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    print("Health check endpoint")
    system_log = SystemLog(
        message="Health check endpoint",
        level="info",
        created_at=datetime.now()
    )
    system_log.save()
    print("System log:: ", system_log)
    return {
        "status": "healthy",
        "service": "ai-receptionist",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# get business information
@router.get("/business-information")
async def get_business_information():
    """Get business information."""
    return await BookingAPI().fetch_business_information()
  
# get business services
@router.get("/business-services")
async def get_business_services():
    """Get business services."""
    return await BookingAPI().fetch_business_services()
  

# check availability
@router.get("/check-availability")
async def check_availability(booking__selected_date: str, service_duration: str, service_ids: str = ""):
    """Check availability."""
    print("Booking selected date:: ", booking__selected_date)
    return await BookingAPI().check_availability(booking__selected_date, service_duration, service_ids)


# get next appointments
@router.get("/next-appointments")
async def get_next_appointments(phone_number: str):
    """Get next appointments."""
    return await BookingAPI().get_next_appointments(phone_number)