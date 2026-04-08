"""Data access service for handling incoming Twilio calls."""

from typing import Optional

from business.models import Business
from receptionist.models import (
    AIConfiguration,
    AIConfigurationStatus,
    CallSession,
)


async def get_business_by_twilio_number(twilio_number: str) -> Optional[Business]:
    """Return the business that owns the given Twilio phone number, if any."""
    return await Business.objects.filter(twilio_phone_number=twilio_number).afirst()


async def get_active_ai_configuration(business: Business) -> Optional[AIConfiguration]:
    """Return the active AI configuration for a business, if any."""
    return await AIConfiguration.objects.filter(
        business=business,
        status=AIConfigurationStatus.ACTIVE.value,
    ).afirst()


async def create_call_session(
    *,
    call_sid: str,
    caller_number: str,
    receiver_number: str,
    business_id: int,
    status: str,
    direction: str = "inbound",
) -> CallSession:
    """Persist a CallSession record for an incoming call."""
    return await CallSession.objects.acreate(
        call_sid=call_sid,
        caller_number=caller_number,
        receiver_number=receiver_number,
        direction=direction,
        status=status,
        business_id=business_id,
    )



def resolve_forward_number(business: Business) -> Optional[str]:
    """Pick the best phone number to forward an incoming call to.

    Returns None if there is no usable number (or the only candidate is the
    business's own Twilio number, which would create a loop).
    """
    forward_to = business.forward_phone_number or business.phone_number
    if forward_to and forward_to != business.twilio_phone_number:
        return forward_to
    return None
