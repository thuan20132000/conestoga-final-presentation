from ai_service.tools.base import BaseTool
from typing import Dict, Any, Callable
import json
from ai_service.services.booking_api import BookingAPI
from ai_service.tools.receptionist_agent import RECEPTIONIST_AGENT_TOOLS
from ai_service.services.openai_api import OpenAIAPI
from receptionist.models import SystemLog, CallSession, AIConfiguration, AIConfigurationStatus
from asgiref.sync import sync_to_async
from django.utils import timezone

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
    _booking_api: BookingAPI

    def __init__(self):
        """Initialize the receptionist tools."""
        print("Initializing receptionist tools...")
        self._booking_api = BookingAPI()
        self._openai_api = OpenAIAPI()
        super().__init__()
        
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
        await CallSession.objects.filter(call_sid=call_sid).aupdate(**kwargs)

    async def execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """Execute function calls and return results."""
        print("Executing function call:: ", function_name)
        print("Arguments:: ", arguments)
        data = None
        try:
            if function_name == "get_business_information":
                data = await self._booking_api.fetch_business_information(arguments.get("info_type", "general"))
            elif function_name == "get_service_information":
                data = await self._booking_api.fetch_business_services(arguments.get("service_type", "all_services"))
                # return await self.get_service_information(arguments.get("service_type", "all_services"))
            elif function_name == "check_availability":
                print("====================Checking availability...====================")
                print("Arguments:: ", arguments)
                data = await self.check_availability(
                    arguments.get("date"),
                    arguments.get("time", "any"),
                    arguments.get("service_type")
                )
                print("Check availability data:: ", data)
            elif function_name == "get_customer_information":
                phone_number = arguments.get("customer_phone")
                customer_name = arguments.get("customer_name", "Unknown")
                data = await self._booking_api.fetch_customer_information(phone_number)
                if not data:
                    data = await self._booking_api.create_customer(customer_name, phone_number)
                    
            elif function_name == "book_appointment":
                print("====================Booking appointment...====================")
                print("Arguments:: ", arguments)
                phone_number = arguments.get("phone_number")
                print("Phone number:: ", phone_number)
                full_name = arguments.get("name")
                customer = await self._booking_api.fetch_customer_information(arguments.get("phone_number"))
                if not customer:
                    customer = await self._booking_api.create_customer(full_name, phone_number)

                services_ids = arguments.get("service_ids")
                booking_services = list()
                for service_id in services_ids:
                    booking_services.append({
                        "service_id": service_id,
                        "employee_id": arguments.get("available_time_slot").get("employee_id"),
                        "start_at": arguments.get("available_time_slot").get("start_at"),
                        "end_at": arguments.get("available_time_slot").get("end_at")
                    })

                appointment_data = {
                    "selected_date": arguments.get("date"),
                    "notes": "test notes",
                    "salon": 1,
                    "customer": customer.get("id"),
                    "booking_source": "phone",
                    "services": booking_services
                }
                
                booking_data = await self._booking_api.book_appointment(appointment_data)
                print("Booking data:: ", booking_data)

                return json.dumps(booking_data)
            
            elif function_name == "look_up_appointment":
                print("====================Looking up appointment...====================")
                phone_number = arguments.get("phone_number")
                print("Phone number:: ", phone_number)
                date = arguments.get("date")
                print("Date:: ", date)
                data = await self._booking_api.find_my_appointments(phone_number, date)
                print("Look up appointment data:: ", data)
                return json.dumps(data)
            
            elif function_name == "cancel_appointment":
                phone_number = arguments.get("phone_number")
                name = arguments.get("name")
                service_name = arguments.get("service_name")
                date = arguments.get("date")
                time = arguments.get("time")
                appointment_id = arguments.get("appointment_id")
                print("====================Cancelling appointment...====================")
                print("Phone number:: ", phone_number)
                print("Name:: ", name)
                print("Service name:: ", service_name)
                print("Date:: ", date)
                print("Time:: ", time)
                print("Appointment id:: ", appointment_id)
            
                
                canceled_data = await self._booking_api.cancel_appointment(
                    appointment_id,
                    phone_number
                )
                print("Canceled data:: ", canceled_data)
                return json.dumps(canceled_data)
            
            else:
                return f"Unknown function: {function_name}"

            print("Function call data:: ", data)
            return json.dumps(data)

        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"

    async def check_availability(self, date: str, time: str, service_type: str) -> str:
        """Check availability."""
        print("Checking availability...")
        print("Date:: ", date)
        print("Time:: ", time)
        print("Service type:: ", service_type)

        raw_data = f"{{ 'service_type': '{service_type}', 'date': '{date}', 'time': '{time}' }}"

        print("Raw data:: ", raw_data)
        sanitized_data = await self._openai_api.sanitize_booking_services_data(raw_data)

        print("Sanitized data:: ", sanitized_data)

        data = await self._booking_api.check_availability(
            booking__selected_date=sanitized_data.get("date"),
            service_duration=sanitized_data.get("duration"),
            service_ids=sanitized_data.get("service_ids")
        )
        print("Check availability data:: ", json.dumps(data, indent=4))

        return json.dumps(data)


    async def  ai_configuration(self, call_to: str) -> AIConfiguration:
        """Get AI configuration."""
        ai_configuration = await AIConfiguration.objects.aget(business__phone_number=call_to, status=AIConfigurationStatus.ACTIVE.value)
        return ai_configuration