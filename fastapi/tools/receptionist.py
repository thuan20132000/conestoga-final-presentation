from fastapi.tools.base import BaseTool
from typing import Dict, Any
import json
from fastapi.services.booking_api import BookingAPI
from fastapi.tools.receptionist_agent import RECEPTIONIST_AGENT_TOOLS
from fastapi.services.openai_api import OpenAIAPI


AGENT_TOOLS = RECEPTIONIST_AGENT_TOOLS


class ReceptionistTools(BaseTool):
    """Tools for the receptionist."""
    _booking_api: BookingAPI

    def __init__(self):
        """Initialize the receptionist tools."""
        print("Initializing receptionist tools...")
        self._booking_api = BookingAPI()
        self._openai_api = OpenAIAPI()
        super().__init__()

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
                data = await self.check_availability(
                    arguments.get("date"),
                    arguments.get("time", "any"),
                    arguments.get("service_type")
                )
            elif function_name == "get_customer_information":
                phone_number = arguments.get("customer_phone")
                customer_name = arguments.get("customer_name", "Unknown")
                data = await self._booking_api.fetch_customer_information(phone_number)
                if not data:
                    data = await self._booking_api.create_customer(customer_name, phone_number)
            elif function_name == "book_appointment":

                phone_number = arguments.get("phone_number")
                full_name = arguments.get("name")
                customer = await self._booking_api.fetch_customer_information(arguments.get("phone_number"))
                if not customer:
                    customer = await self._booking_api.create_customer(full_name, phone_number)

                print("Customer:: ", customer)

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
            
            elif function_name == "cancel_appointment":
                phone_number = arguments.get("phone_number")
                name = arguments.get("name")
                service_name = arguments.get("service_name")
                date = arguments.get("date")
                time = arguments.get("time")
                
                customer_appointments = await self._booking_api.get_next_appointments(
                    date,
                    phone_number,
                )
                print("Customer appointments data:: ", customer_appointments)
                
                
                return json.dumps(data)
            
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

