import pytest
import asyncio
import json
from fastapi.tools.receptionist import ReceptionistTools

@pytest.mark.asyncio
async def test_sanitize_data(monkeypatch):
    # Patch OpenAIAPI.generate_response to return a deterministic JSON string
    async def mock_generate_response(self, prompt):
        # Simulate a response that matches the prompt's requirements
        return '{"service_id": 5, "date": "2024-06-01", "duration": 40}'

    # Patch the method in the OpenAIAPI class
    from fastapi.services import openai_api

    tools = ReceptionistTools()
    raw_data = "{'service_type': 'Pedicure, Manicure', 'date': 'tomorrow', 'time': '1 PM'}"
    result = await tools.sanitize_data(raw_data)
    print("Result:: ", result)
    result = json.loads(result)
    assert result["service_id"] == [5, 4]
    assert result["date"] == "2025-10-01"
    assert result["duration"] == 80

@pytest.mark.asyncio
async def test_sanitize_data_no_date(monkeypatch):
    # Patch OpenAIAPI.generate_response to return a deterministic JSON string
    async def mock_generate_response(self, prompt):
        # Simulate a response that matches the prompt's requirements
        return '{"service_id": 5, "date": "2025-09-30", "duration": 40}'

    # Patch the method in the OpenAIAPI class
    from fastapi.services import openai_api

    tools = ReceptionistTools()
    raw_data = "{'service_type': 'Pedicure', 'time': '1 PM'}"
    result = await tools.sanitize_data(raw_data)
    print("Result:: ", result)
    result = json.loads(result)
    assert result["service_id"] == [5]
    assert result["date"] == "2025-09-30"
    assert result["duration"] == 40

