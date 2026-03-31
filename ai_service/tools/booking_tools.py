"""Booking tools for the AI receptionist agent, using @function_tool decorator."""

import json
import logging
from typing import Optional

from pydantic import BaseModel
from agents import function_tool
from agents.run_context import RunContextWrapper

from ai_service.tools.context import CallContext


class TimeSlot(BaseModel):
    """An available time slot for booking."""

    start_at: str
    end_at: str
    duration: int
    employee_id: int

logger = logging.getLogger(__name__)


@function_tool
async def get_business_information(
    ctx: RunContextWrapper[CallContext],
    info_type: str,
) -> str:
    """Get comprehensive business information including hours, contact details,
    location, and general information.

    Args:
        info_type: Type of information requested. One of: general, contact, location, all.
    """
    data = await ctx.context.booking_service.get_business_information(info_type)
    return json.dumps(data, default=str)


@function_tool
async def get_service_information(
    ctx: RunContextWrapper[CallContext],
) -> str:
    """Get detailed information about all available salon services and packages."""
    data = await ctx.context.booking_service.get_service_information()
    return json.dumps(data, default=str)


@function_tool
async def check_availability(
    ctx: RunContextWrapper[CallContext],
    date: str,
    time: str,
    service_type: str,
) -> str:
    """Check availability for a specific service on a given date and time.

    Args:
        date: Date to check availability for (e.g. 2025-01-15).
        time: Time to check availability for (e.g. 10:00 or any).
        service_type: Type of service to check availability for.
    """
    data = await ctx.context.booking_service.check_availability(
        date=date, time=time, service_type=service_type
    )
    return json.dumps(data, default=str)


@function_tool
async def get_customer_information(
    ctx: RunContextWrapper[CallContext],
    customer_phone: str,
    customer_name: Optional[str] = None,
) -> str:
    """Get information about a specific customer by phone number.
    Creates a new customer record if not found.

    Args:
        customer_phone: Phone number of the customer.
        customer_name: Name of the customer (used if creating new record).
    """
    data = await ctx.context.booking_service.get_or_create_customer(
        phone_number=customer_phone,
        customer_name=customer_name or "Unknown",
    )
    return json.dumps(data, default=str)


@function_tool
async def book_appointment(
    ctx: RunContextWrapper[CallContext],
    name: str,
    phone_number: str,
    service_ids: list[int],
    date: str,
    time: str,
    available_time_slot: TimeSlot,
    service_type: Optional[str] = None,
) -> str:
    """Book an appointment for a specific service.

    Args:
        name: Name of the client.
        phone_number: Phone number of the client (e.g. 0912345678).
        service_ids: List of service IDs to book appointment for.
        date: Date to book appointment for (e.g. 2025-01-15).
        time: Time to book appointment for (e.g. 10:00).
        available_time_slot: Time slot object with start_at, end_at, duration, and employee_id.
        service_type: Type of service to book (optional).
    """
    logger.info(f"Booking appointment: {name}, {phone_number}, {service_ids}, {date}")
    data = await ctx.context.booking_service.book_appointment(
        phone_number=phone_number,
        name=name,
        date=date,
        service_ids=service_ids,
        available_time_slot=available_time_slot.model_dump(),
        notes="",
    )
    return json.dumps(data, default=str)


@function_tool
async def look_up_appointment(
    ctx: RunContextWrapper[CallContext],
    phone_number: str,
    date: str,
) -> str:
    """Get next appointments for a specific client by phone number and date.

    Args:
        phone_number: Phone number of the client (e.g. 0912345678).
        date: Date of the appointment to look up (e.g. 2025-01-01).
    """
    data = await ctx.context.booking_service.lookup_appointments(
        phone_number=phone_number, date=date
    )
    return json.dumps(data, default=str)


@function_tool
async def cancel_appointment(
    ctx: RunContextWrapper[CallContext],
    phone_number: str,
    date: str,
    appointment_id: Optional[int] = None,
    service_name: Optional[str] = None,
    name: Optional[str] = None,
    time: Optional[str] = None,
) -> str:
    """Cancel an appointment for a specific service.

    Args:
        phone_number: Phone number of the client.
        date: Date of the appointment to cancel.
        appointment_id: ID of the appointment to cancel.
        service_name: Service name to cancel.
        name: Name of the client.
        time: Time of the appointment.
    """
    data = await ctx.context.booking_service.cancel_appointment(
        appointment_id=appointment_id,
        phone_number=phone_number,
        name=name,
        service_name=service_name,
        date=date,
        time=time,
    )
    return json.dumps(data, default=str)


ALL_BOOKING_TOOLS = [
    get_business_information,
    get_service_information,
    check_availability,
    get_customer_information,
    book_appointment,
    look_up_appointment,
    cancel_appointment,
]
