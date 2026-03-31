import pytest
import json
from ai_service.services.openai_api import OpenAIAPI


@pytest.mark.asyncio
async def test_sanitize_booking_services_data(monkeypatch):
    """Test that sanitize_booking_services_data parses service data correctly."""
    async def mock_generate_response(self, messages):
        return '{"service_ids": [5], "date": "2025-10-01", "duration": 40}'

    monkeypatch.setattr(OpenAIAPI, "generate_response", mock_generate_response)

    api = OpenAIAPI()
    raw_data = "{'service_type': 'Pedicure', 'date': 'tomorrow', 'time': '1 PM'}"
    business_services = [{"id": 5, "name": "Pedicure", "duration": 40}]

    result = await api.sanitize_booking_services_data(raw_data, business_services)
    assert isinstance(result, dict)
