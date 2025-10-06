"""WebSocket routes for real-time communication."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import base64
from typing import Dict, Any
import asyncio
import websockets
from fastapi.config import settings
import os
from dotenv import load_dotenv
from fastapi.tools.receptionist import ReceptionistTools
from fastapi.tools.receptionist_agent import RECEPTIONIST_AGENT_TOOLS

load_dotenv()


# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 5050))
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.8))
AGENT_TOOLS = RECEPTIONIST_AGENT_TOOLS

# Create router
router = APIRouter(prefix="/ws", tags=["websocket"])

# Enhanced system message for receptionist AI
SYSTEM_MESSAGE = (
    "You are a professional AI receptionist for SnapsBooking Salon. "
    "Your role is to assist clients with appointments, provide business information, "
    "and answer questions about our services. Always be helpful, professional, and friendly. "
    "Use the available tools to provide accurate information from our knowledge base. "
    "If you need to book appointments, get customer information or access specific business data, use the appropriate tools."
    "Ask the client for their phone number and name to register them if they don't provide it before making any appointments."
    
)

VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'error',
    'response.content.done',
    'rate_limits.updated',
    'response.done',
    'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started',
    'input_audio_buffer.speech_ended',
    'session.created',
    'session.updated',
    'response.function_call_arguments.done'
]
SHOW_TIMING_MATH = False


@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    receptionist_tools = ReceptionistTools()
    await websocket.accept()

    async with websockets.connect(
        f"wss://api.openai.com/v1/realtime?model=gpt-realtime&temperature={TEMPERATURE}",
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
    ) as openai_ws:
        print("OpenAI WebSocket connected")
        await send_session_update(openai_ws)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                        print(f"Incoming stream has started {stream_sid}")

                    elif data['event'] == 'media' and openai_ws.state.name == 'OPEN':
                        latest_media_timestamp = int(
                            data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload'],
                        }
                        await openai_ws.send(json.dumps(audio_append))

            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.state.name == 'OPEN':
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)

                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    if response['type'] == 'session.updated':
                        print(f"Session updated: {response}")

                    # receive audio from OpenAI and send it to Twilio
                    if response['type'] == 'response.output_audio.delta' and 'delta' in response:
                            # print(f"Received audio from OpenAI: {response}")

                            audio_payload = base64.b64encode(
                                base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }

                            await websocket.send_json(audio_delta)

                            if response.get("item_id") and response["item_id"] != last_assistant_item:
                                response_start_timestamp_twilio = latest_media_timestamp
                                last_assistant_item = response["item_id"]
                                if SHOW_TIMING_MATH:
                                    print(
                                        f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                            await send_mark(websocket, stream_sid)
                        
                    if response.get('type') == 'response.function_call_arguments.done':
                        name = response['name']
                        args = json.loads(response['arguments'])
                        call_id = response['call_id']
                        print(f"⚡ Function call requested: {name}({args})")
                        # Execute tool in Python
                        try:
                            result = await receptionist_tools.execute_function_call(name, args)
                        except Exception as e:
                            result = f"Error executing {name}: {str(e)}"

                        print(f"Result of function call: {result}")
                        
                        # Send result back into conversation
                        await openai_ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": result
                            }
                        }))

                        # Ask model to respond with this result
                        await openai_ws.send(json.dumps({"type": "response.create"}))
                        
                        
                        # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(
                                f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()

            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item
            print("Handling speech started event.")
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(
                        f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(
                            f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())


async def send_session_update(openai_ws):
    """Send session update to OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": "gpt-realtime",
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    "turn_detection": {"type": "server_vad"}
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": VOICE
                }
            },
            "instructions": SYSTEM_MESSAGE,
            "tools": AGENT_TOOLS
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))
