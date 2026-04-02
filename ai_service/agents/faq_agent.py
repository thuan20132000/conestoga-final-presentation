"""FAQ agent for business information and service inquiries."""

from agents.realtime import RealtimeAgent

from ai_service.tools.context import CallContext
from ai_service.tools.faq_tools import FAQ_TOOLS


faq_agent = RealtimeAgent[CallContext](
    name="FAQ Agent",
    instructions=(
        "You are a knowledgeable FAQ assistant for a salon business. "
        "Answer questions about business hours, location, contact details, "
        "and available services. Be friendly, concise, and accurate. "
        "Use the provided tools to look up real business data — never guess. "
        "If the caller wants to book, cancel, or look up an appointment, "
        "hand off to the appropriate agent."
    ),
    tools=list(FAQ_TOOLS),
)
