"""AI Receptionist — triage agent that hands off to specialized sub-agents."""

from agents.realtime import RealtimeAgent, realtime_handoff

from ai_service.agents.booking_agent import create_booking_agent
from ai_service.agents.customer_agent import customer_agent
from ai_service.agents.faq_agent import faq_agent
from ai_service.agents.reschedule_agent import create_reschedule_agent
from ai_service.tools.context import CallContext


def create_receptionist_agent(instructions: str, caller_number: str) -> RealtimeAgent[CallContext]:
    """Create the triage receptionist agent with handoffs to sub-agents.

    The receptionist greets the caller, determines intent, and hands off to:
    - FAQ Agent: business hours, location, services info
    - Booking Agent: check availability, look up appointments, collect booking details
    - Customer Agent: customer lookup, registration
    - Reschedule Agent: appointment rescheduling

    Sub-agents can also hand off to each other as needed.

    Args:
        instructions: System prompt from AIConfiguration.prompt for this business.
        caller_number: Phone number of the caller.
    """
    # Create reschedule agent with caller's phone number baked in
    reschedule_agent = create_reschedule_agent(caller_number)


    booking_agent = create_booking_agent(caller_number)

    # Wire cross-agent handoffs so sub-agents can transfer between each other
    faq_agent.handoffs = [
        realtime_handoff(
            booking_agent,
            tool_description_override="Transfer to the Booking Agent for appointment management.",
        ),
        realtime_handoff(
            customer_agent,
            tool_description_override="Transfer to the Customer Agent for customer lookup or registration.",
        ),
        realtime_handoff(
            reschedule_agent,
            tool_description_override="Transfer to the Reschedule Agent for appointment rescheduling.",
        ),
    ]

    booking_agent.handoffs = [
        realtime_handoff(
            faq_agent,
            tool_description_override="Transfer to the FAQ Agent for business or service questions.",
        ),
        realtime_handoff(
            customer_agent,
            tool_description_override="Transfer to the Customer Agent for customer lookup or registration.",
        ),
        realtime_handoff(
            reschedule_agent,
            tool_description_override="Transfer to the Reschedule Agent for appointment rescheduling.",
        ),
    ]

    customer_agent.handoffs = [
        realtime_handoff(
            faq_agent,
            tool_description_override="Transfer to the FAQ Agent for business or service questions.",
        ),
        realtime_handoff(
            reschedule_agent,
            tool_description_override="Transfer to the Reschedule Agent for appointment rescheduling.",
        ),
    ]

    reschedule_agent.handoffs = [
        realtime_handoff(
            faq_agent,
            tool_description_override="Transfer to the FAQ Agent for business or service questions.",
        ),
    ]

    return RealtimeAgent[CallContext](
        name="AI Receptionist",
        instructions=instructions,
        handoffs=[
            realtime_handoff(
                faq_agent,
                tool_description_override="Transfer to the FAQ Agent for business hours, location, or service details.",
            ),
            realtime_handoff(
                customer_agent,
                tool_description_override="Transfer to the Customer Agent for customer registration.",
            ),
            realtime_handoff(
                reschedule_agent,
                tool_description_override="Transfer to the Reschedule Agent for appointment rescheduling.",
            ),
            realtime_handoff(
                booking_agent,
                tool_description_override="Transfer to the Booking Agent for collecting booking details.",
            ),
        ],
    )
