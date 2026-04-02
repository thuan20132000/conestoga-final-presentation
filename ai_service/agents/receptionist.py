"""AI Receptionist — triage agent that hands off to specialized sub-agents."""

from agents.realtime import RealtimeAgent, realtime_handoff

from ai_service.agents.booking_agent import booking_agent
from ai_service.agents.customer_agent import customer_agent
from ai_service.agents.faq_agent import faq_agent
from ai_service.tools.context import CallContext


def create_receptionist_agent(instructions: str) -> RealtimeAgent[CallContext]:
    """Create the triage receptionist agent with handoffs to sub-agents.

    The receptionist greets the caller, determines intent, and hands off to:
    - FAQ Agent: business hours, location, services info
    - Booking Agent: check availability, book/cancel/look up appointments
    - Customer Agent: customer lookup, registration

    Sub-agents can also hand off to each other as needed.

    Args:
        instructions: System prompt from AIConfiguration.prompt for this business.
    """
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
    ]

    customer_agent.handoffs = [
        realtime_handoff(
            booking_agent,
            tool_description_override="Transfer back to the Booking Agent to continue with the appointment.",
        ),
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
                tool_description_override="Transfer to the FAQ Agent for business information, hours, location, or service details.",
            ),
            realtime_handoff(
                booking_agent,
                tool_description_override="Transfer to the Booking Agent for booking, canceling, or looking up appointments.",
            ),
            realtime_handoff(
                customer_agent,
                tool_description_override="Transfer to the Customer Agent for customer lookup or registration.",
            ),
        ],
    )
