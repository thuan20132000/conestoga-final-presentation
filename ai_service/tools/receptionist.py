from ai_service.tools.base import BaseTool
from typing import Dict, Any, Callable
import json
from ai_service.services.business_booking_service import BusinessBookingService
from ai_service.tools.receptionist_agent import RECEPTIONIST_AGENT_TOOLS
from ai_service.services.openai_api import OpenAIAPI
from receptionist.models import SystemLog, CallSession, AIConfiguration, AIConfigurationStatus
from asgiref.sync import sync_to_async
from django.utils import timezone
from logging import getLogger
logger = getLogger(__name__)

AGENT_TOOLS = RECEPTIONIST_AGENT_TOOLS

SYSTEM_MESSAGE = (
    "You are a professional AI receptionist for SnapsBooking Salon. "
    "Your role is to assist clients with appointments, provide business information, "
    "and answer questions about our services. Always be helpful, professional, and friendly. "
    "Use the available tools to provide accurate information from our knowledge base. "
    "If you need to book appointments, get customer information or access specific business data, use the appropriate tools."
    "Ask the client for their phone number and name to register them if they don't provide it before making any appointments."
)


class ReceptionistTools(BaseTool):
    """Tools for the receptionist."""
    _booking_service: BusinessBookingService = None
    _business_id: int = None

    def __init__(self, business_id: int = None):
        """
        Initialize the receptionist tools.
        
        Args:
            business_id: Optional business ID. If not provided, will be set via set_business_id()
        """
        print("Initializing receptionist tools...")
        self._business_id = business_id
        if business_id:
            self._booking_service = BusinessBookingService(business_id)
        self._openai_api = OpenAIAPI()
        super().__init__()
    
    def set_business_id(self, business_id: int):
        """
        Set the business ID and initialize the booking service.
        
        Args:
            business_id: The business ID to use for booking operations
        """
        self._business_id = business_id
        self._booking_service = BusinessBookingService(business_id)
    
    def _ensure_booking_service(self):
        """Ensure booking service is initialized."""
        if not self._booking_service:
            raise RuntimeError("Booking service not initialized. Call set_business_id() first.")
    
    async def create_system_log(self, level: str, call: None, message: str, metadata: Dict[str, Any]):
        """Create a system log."""
        await SystemLog.objects.acreate(
            level=level,
            call=call,
            message=message,
            metadata=metadata
        )
        
    async def update_call_session(self, call_sid: str, **kwargs):
        """Update call session."""
        ended_at = timezone.now()
        kwargs["ended_at"] = ended_at
        conversation_transcript = kwargs.get("conversation_transcript")
        if conversation_transcript:
            outcome = await self._openai_api.analyze_conversation(conversation_transcript)
            kwargs["outcome"] = outcome.get("outcome", "unknown")
            kwargs["sentiment"] = outcome.get("sentiment", "neutral")
            kwargs["transcript_summary"] = outcome.get("summary", "Unknown")
        await CallSession.objects.filter(call_sid=call_sid).aupdate(**kwargs)

    async def execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Execute function calls and return results."""
        print(f"Executing function call: {function_name}")
        print(f"Arguments: {arguments}")
        
        try:
            self._ensure_booking_service()
            data = None
            
            if function_name == "get_business_information":
                data = await self._booking_service.get_business_information(
                    arguments.get("info_type", "general")
                )
                
            elif function_name == "get_service_information":
                data = await self._booking_service.get_service_information()
                
            elif function_name == "check_availability":
                data = await self._booking_service.check_availability(
                    date=arguments.get("date"),
                    time=arguments.get("time", "any"),
                    service_type=arguments.get("service_type")
                )
                
            elif function_name == "get_customer_information":
                data = await self._booking_service.get_or_create_customer(
                    phone_number=arguments.get("customer_phone"),
                    customer_name=arguments.get("customer_name", "Unknown")
                )
                
            elif function_name == "book_appointment":
                data = await self._booking_service.book_appointment(
                    phone_number=arguments.get("phone_number"),
                    name=arguments.get("name"),
                    date=arguments.get("date"),
                    service_ids=arguments.get("service_ids"),
                    available_time_slot=arguments.get("available_time_slot"),
                    notes=arguments.get("notes", "")
                )
                
                logger.info(f"Booked appointment: {data}")
                
            elif function_name == "look_up_appointment":
                data = await self._booking_service.lookup_appointments(
                    phone_number=arguments.get("phone_number"),
                    date=arguments.get("date")
                )
                
            elif function_name == "cancel_appointment":
                data = await self._booking_service.cancel_appointment(
                    appointment_id=arguments.get("appointment_id"),
                    phone_number=arguments.get("phone_number"),
                    name=arguments.get("name"),
                    service_name=arguments.get("service_name"),
                    date=arguments.get("date"),
                    time=arguments.get("time")
                )
                
            else:
                return f"Unknown function: {function_name}"

            print(f"Function call data: {data}")
            return json.dumps(data)

        except Exception as e:
            print(f"Error executing {function_name}: {str(e)}")
            return f"Error executing {function_name}: {str(e)}"

    async def ai_configuration(self, call_to: str) -> AIConfiguration:
        """Get AI configuration."""
        ai_configuration = await AIConfiguration.objects.aget(
            business__twilio_phone_number=call_to,
            status=AIConfigurationStatus.ACTIVE.value
        )
        return ai_configuration