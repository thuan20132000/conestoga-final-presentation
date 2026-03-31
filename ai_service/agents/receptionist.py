"""AI Receptionist agent definition using OpenAI Agents SDK."""

from agents.realtime import RealtimeAgent

from ai_service.tools.booking_tools import ALL_BOOKING_TOOLS
from ai_service.tools.context import CallContext


def create_receptionist_agent(instructions: str) -> RealtimeAgent[CallContext]:
    """Create a RealtimeAgent configured as an AI receptionist.

    Created per-call because instructions come from AIConfiguration.prompt
    which varies per business.

    Args:
        instructions: System prompt from AIConfiguration.prompt for this business.
    """
    return RealtimeAgent(
        name="AI Receptionist",
        instructions=instructions,
        tools=list(ALL_BOOKING_TOOLS),
    )
