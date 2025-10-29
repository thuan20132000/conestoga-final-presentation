import openai
from ai_service.config import settings
from typing import List, Dict, Any
import json
import io
import base64


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
                "id": 10,
                "name": "Shellac Manicure",
                "description": "",
                "price": "40.00",
                "duration": 35,
                "created_at": "2025-06-03T01:27:08.814693Z",
                "updated_at": "2025-06-03T01:27:08.814705Z",
                "salon": 1,
                "category": 4
            },
            {
                "id": 63,
                "name": "Volume Full Set / Full Wispy Volume",
                "description": "",
                "price": "60.00",
                "duration": 60,
                "created_at": "2025-07-10T03:39:04.703056Z",
                "updated_at": "2025-07-10T03:39:04.703071Z",
                "salon": 1,
                "category": 4
            },
            {
                "id": 57,
                "name": "Fullset",
                "description": "",
                "price": "57.00",
                "duration": 60,
                "created_at": "2025-06-26T05:01:05.264745Z",
                "updated_at": "2025-06-26T05:01:05.264761Z",
                "salon": 1,
                "category": 5
            },
            {
                "id": 65,
                "name": "Pedicure With Shellac",
                "description": "",
                "price": "50.00",
                "duration": 50,
                "created_at": "2025-07-15T04:39:24.598273Z",
                "updated_at": "2025-07-15T04:39:24.598287Z",
                "salon": 1,
                "category": 4
            },
            {
                "id": 66,
                "name": "Take off Shellac",
                "description": "",
                "price": "10.00",
                "duration": 10,
                "created_at": "2025-07-15T04:39:42.919079Z",
                "updated_at": "2025-07-15T04:39:42.919093Z",
                "salon": 1,
                "category": 4
            },
            {
                "id": 9,
                "name": "Manicure 2",
                "description": "",
                "price": "37.00",
                "duration": 30,
                "created_at": "2025-06-03T01:26:44.778188Z",
                "updated_at": "2025-07-16T20:33:32.403595Z",
                "salon": 1,
                "category": 4
            },
            {
                "id": 64,
                "name": "Pedicure",
                "description": "",
                "price": "50.00",
                "duration": 50,
                "created_at": "2025-07-15T04:39:12.838167Z",
                "updated_at": "2025-07-15T04:39:12.838181Z",
                "salon": 1,
                "category": 4
            },
            {
                "id": 67,
                "name": "Take off Shellac with service",
                "description": "",
                "price": "10.00",
                "duration": 15,
                "created_at": "2025-07-15T04:39:58.409178Z",
                "updated_at": "2025-08-22T04:05:34.657732Z",
                "salon": 1,
                "category": 4
            },]

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

    async def analyze_conversation(self, conversation: List[Dict[str, Any]]) -> str:
        """Analyze a conversation."""
        # conversation = [
        #     {"role": "user", "content": "Hello, how are you?"},
        #     {"role": "assistant", "content": "I'm good, thank you!"},
        # ]
        openai_api = OpenAIAPI()
        prompt = f"""
            You have the following conversation:
            {conversation}
            
            Analyze the conversation and return the outcome, sentiment and summary. 
            If the conversation is not clear, return unknown. If the conversation is positive, return positive. If the conversation is negative, return negative. If the conversation is neutral, return neutral.
            If the conversation is not clear, return unknown. If the conversation is positive, return positive. If the conversation is negative, return negative. If the conversation is neutral, return neutral.
            
            Return outcome, sentiment and summary as a JSON object containing:
            - outcome (successful, unsuccessful, unknown)
            - sentiment (positive, negative, neutral)
            - summary (summary of the conversation)
            Return only JSON.
            
            Example:
                outcome: successful,
                sentiment: positive
        """
        messages = [
            {"role": "user", "content": prompt}
        ]

        response = await openai_api.generate_response(messages)
        response = json.loads(response)
        print("Analyzed conversation response:: ", response)
        return response
