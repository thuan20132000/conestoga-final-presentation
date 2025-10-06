import openai
from ai_service.config import settings
from typing import List, Dict, Any
import json

class OpenAIAPI:
    """OpenAI API for the receptionist."""
    _client: openai.OpenAI
    _model: str
    _temperature: float

    def __init__(self):
        """Initialize the openai api."""
        self._client = openai.OpenAI(api_key=settings.openai_api_key)
        self._model = "gpt-5-mini"
        self._temperature = settings.openai_temperature
        
    async def generate_response(self, messages: List[Dict[str, Any]]):
        """Generate a response using the openai api."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        print("Response:: ", response.choices[0].message.content)
        
        return response.choices[0].message.content
    
    async def sanitize_booking_services_data(self, raw_data: str) -> str:
        """Clean data."""
        print("Sanitizing data...")
        print("Raw data:: ", raw_data)
        # raw_data = "{'service_type': 'Pedicure', 'date': 'tomorrow', 'time': '1 PM'}"

        business_services_data = [
            {
                "id": 2,
                "name": "Fill",
                "description": None,
                "price": "52.00",
                "duration": 50,
                "created_at": "2025-08-21T12:48:15.184012Z",
                "updated_at": "2025-08-21T12:48:15.184033Z",
                "salon": 1,
                "category": 2
            },
            {
                "id": 3,
                "name": "Shellac Manicure",
                "description": None,
                "price": "52.00",
                "duration": 45,
                "created_at": "2025-08-21T12:48:39.435517Z",
                "updated_at": "2025-08-22T03:31:39.390118Z",
                "salon": 1,
                "category": 1
            },
            {
                "id": 1,
                "name": "Fullset",
                "description": None,
                "price": "60.00",
                "duration": 60,
                "created_at": "2025-08-21T12:48:05.572800Z",
                "updated_at": "2025-08-22T03:06:22.157975Z",
                "salon": 1,
                "category": 2
            },
            {
                "id": 5,
                "name": "Pedicure",
                "description": None,
                "price": "40.00",
                "duration": 40,
                "created_at": "2025-08-22T03:32:04.947134Z",
                "updated_at": "2025-08-22T03:32:04.947175Z",
                "salon": 1,
                "category": 1
            },
            {
                "id": 4,
                "name": "Manicure",
                "description": None,
                "price": "40.00",
                "duration": 40,
                "created_at": "2025-08-21T12:48:52.460952Z",
                "updated_at": "2025-08-22T03:31:00.424502Z",
                "salon": 1,
                "category": 1
            }
        ]

        openai_api = OpenAIAPI()
        prompt = f"""
            You have the following services:
            {business_services_data}
            Convert this request: {raw_data} 
            Into a JSON object containing:
            - service_ids (match the service_type, if multiple services are provided, return multiple array of service_ids)
            - date (yyyy-mm-dd) or today if no date is provided
            - duration (match the duration, if multiple services are provided, return the total duration)
            Return only JSON.
            
            Example:
                service_ids: [5, 4],
                date: 2025-10-01,
                duration: 80
        """
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = await openai_api.generate_response(messages)
        response = json.loads(response)
        print("Sanitized data response:: ", response)
        return response
    
    async def sanitize_cancel_appointment_data(
        self, 
        customer_appointments: str, 
        service_name: str, 
        date: str, 
        time: str
    ) -> str:
        """Clean data."""
        print("Sanitizing data...")
        print("Raw data:: ", customer_appointments)
        print("Service name:: ", service_name)
        print("Date:: ", date)
        print("Time:: ", time)
        # raw_data = "{'service_type': 'Pedicure', 'date': 'tomorrow', 'time': '1 PM'}"
        
        openai_api = OpenAIAPI()
        prompt = f"""
            You have  a list of a customer's appointments:
            {customer_appointments}
            You have the following service:
            {service_name}
            You have the following date:
            {date}
            You have the following time:
            {time}
            
            Return the appointment_id of the appointment that matches the service_name, date, and time.
            Return appointment_id as a JSON object containing:
            - appointment_id (match the id)
            Return only JSON.
            
            Example:
                appointment_id: 1
        """
        messages = [
            {"role": "user", "content": prompt}
        ]
        response = await openai_api.generate_response(messages)
        response = json.loads(response)
        print("Sanitized data response:: ", response)
        return response
        