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

    async def sanitize_booking_services_data(self, raw_data: str, business_services_data: str) -> str:
        """Clean data."""
        print("Sanitizing data...")
        print("Raw data:: ", raw_data)
        # raw_data = "{'service_type': 'Pedicure', 'date': 'tomorrow', 'time': '1 PM'}"


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
