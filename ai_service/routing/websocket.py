"""WebSocket routes for real-time communication."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import base64
from typing import Dict, Any
import asyncio
import websockets
from ai_service.config import settings
import os
from dotenv import load_dotenv
from ai_service.tools.receptionist import ReceptionistTools
from ai_service.tools.receptionist_agent import RECEPTIONIST_AGENT_TOOLS
from datetime import datetime

load_dotenv()


# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 5050))
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.8))
AGENT_TOOLS = RECEPTIONIST_AGENT_TOOLS

# Create router
router = APIRouter(prefix="/ws", tags=["websocket"])

VOICE = 'verse'
MODEL = 'gpt-realtime-mini'
LOG_EVENT_TYPES = [
    'error',
    'response.content.done',
    'rate_limits.updated',
    'response.done',
    'input_audio_buffer.committed',
    'input_audio_buffer.transcript.done',
    'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started',
    'input_audio_buffer.speech_ended',
    'session.created',
    'session.updated',
    'response.function_call_arguments.done',
]
SHOW_TIMING_MATH = False


@router.websocket("/media-stream/{call_sid}/call_to/{call_to}")
async def handle_media_stream(websocket: WebSocket, call_sid: str, call_to: str):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    receptionist_tools = ReceptionistTools()
    ai_configuration = await receptionist_tools.ai_configuration(call_to)
    print("AI configuration:: ", ai_configuration)
    
    
    await websocket.accept()
    
    print("Call SID:: ", call_sid)
    print("Call to:: ", call_to)
    
    
    async def send_session_update(openai_ws):
        """Send session update to OpenAI."""
        session_update = {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "model": ai_configuration.model_name,
                "output_modalities": ["audio"],
                "audio": {
                    "input": {
                        "format": {"type": "audio/pcmu"},
                        "turn_detection": {"type": "server_vad"},
                        "transcription": {
                            "model": "whisper-1",
                            "language": "en",
                            "prompt": "Transcribe the audio into text."
                        }
                    },
                    "output": {
                        "format": {"type": "audio/pcmu"},
                        "voice": ai_configuration.voice_provider
                    }
                },
                "instructions": ai_configuration.prompt,
                "tools": AGENT_TOOLS,
            }
        }
        await openai_ws.send(json.dumps(session_update))


    async with websockets.connect(
        f"wss://api.openai.com/v1/realtime?model={ai_configuration.model_name}&temperature={ai_configuration.temperature}",
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
        conversation_transcript = []  # Store conversation transcript

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

                    if data['event'] == 'stop':
                        print("Incoming stream has stopped")
                        print(f"Conversation transcript: {conversation_transcript}")
                        
                        
                        await receptionist_tools.update_call_session(
                            call_sid=call_sid, 
                            status="completed", 
                            conversation_transcript=conversation_transcript
                        )
                
                        
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
                    print(f"Response: {response['type']}")
                    
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)

                    if response['type'] == 'response.done':
                        print(f"Response done: {response}")
                        # Remove the transcript extraction from here

                    # caller transcription completed
                    if response['type'] == 'conversation.item.input_audio_transcription.completed':
                        print(f"Caller audio transcription completed: {response}")
                        transcription = response['transcript']
                        print(f"Caller audio transcription: {transcription}")
                        conversation_transcript.append({
                            "speaker": "caller",
                            "content": transcription,
                            "timestamp": datetime.now().isoformat()
                        })
                        print(f"Conversation transcript: {conversation_transcript}")
                    
                    # assistant transcription completed
                    if response['type'] == 'response.output_audio_transcript.done':
                        print(f"Assistant audio transcription done: {response}")
                        transcription = response['transcript']
                        print(f"Assistant audio transcription: {transcription}")
                        
                        conversation_transcript.append({
                            "speaker": "assistant",
                            "content": transcription,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    
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

                    if response['type'] == 'input_audio_buffer.speech_stopped':
                        print(f"Input audio buffer speech stopped: {response}")
                        
                        # Check if audio was appended before committing
                        if latest_media_timestamp > 1000:
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.commit",
                            }))
                            print(f"Committing input audio buffer to openai")
                        else:

                            print(f"No audio was appended before committing")
                    
                    if response.get('type') == 'input_audio_buffer.transcript.done':
                        print(f"Input audio buffer transcript done: {response}")
                        transcript = response.get('transcript')
                        print(f"Input audio buffer transcript: {transcript}")
                        await openai_ws.send(json.dumps({
                            "type": "input_audio_buffer.commit",
                        }))
                        print(f"Input audio buffer transcript: {response['transcript']}")
                        # conversation_transcript.append({
                        #     "speaker": "caller",
                        #     "content": response['content']['transcript'],
                        #     "timestamp": datetime.now().isoformat()
                        # })
                        # print(f"Conversation transcript: {conversation_transcript}")
                        
                        
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


