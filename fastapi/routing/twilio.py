"""Twilio integration routes for the AI Receptionist application."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from fastapi.config import settings

# Create router
router = APIRouter(tags=["twilio"])


@router.post("/voice")
async def twilio_voice_webhook(request: Request):
    """Handle incoming Twilio voice calls."""
    try:
        # Get form data from Twilio
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        
        print(f"📞 Incoming call from {from_number} to {to_number}, CallSid: {call_sid}")
        
        # Create TwiML response to connect to WebSocket
        response = VoiceResponse()
        connect = Connect()
        
        # Build WebSocket URL
        host = request.url.hostname
        ws_url = f"wss://{host}/ws/twilio-media"
        print(f"🔗 Connecting to WebSocket: {ws_url}")
        stream = Stream(url=ws_url)
        
        connect.append(stream)
        response.append(connect)
        
        print(f"🔗 Connecting to WebSocket: {ws_url}")
        
        return HTMLResponse(content=str(response), media_type="application/xml")
        
    except Exception as e:
        print(f"❌ Error in Twilio webhook: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "details": str(e)}
        )


@router.post("/status")
async def twilio_status_webhook(request: Request):
    """Handle Twilio call status updates."""
    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        call_duration = form_data.get("CallDuration")
        
        print(f"📊 Call status update - SID: {call_sid}, Status: {call_status}, Duration: {call_duration}")
        
        return JSONResponse(content={"status": "received"})
        
    except Exception as e:
        print(f"❌ Error in Twilio status webhook: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )


@router.get("/test")
async def twilio_test_endpoint():
    """Test endpoint for Twilio integration."""
    return {
        "message": "Twilio integration is active",
        "webhook_url": f"{settings.public_ws_url.replace('ws://', 'http://').replace('wss://', 'https://')}/twilio/voice",
        "websocket_url": f"{settings.public_ws_url}/ws/twilio-media",
        "configuration": {
            "auth_token_configured": bool(settings.twilio_media_ws_token),
            "public_ws_url": settings.public_ws_url
        }
    }


@router.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    response.say(
        "Hello! Thank you for calling SnapsBooking Salon.",
        voice="Google.en-US-Chirp3-HD-Aoede"
    )
    response.pause(length=1)
    response.say(
        "You can now start speaking!",
        voice="Google.en-US-Chirp3-HD-Aoede"
    )
    host = request.url.hostname
    wss_url = f"wss://{host}/ws/media-stream"
    print("WSS URL:: ", wss_url)
    connect = Connect()
    connect.stream(url=wss_url)
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")
