# Bookngon AI - Virtual Receptionist (Django DRF + Twilio + OpenAI)

## Environment variables
Set these in your shell or a .env loaded by your process manager:

- OPENAI_API_KEY
- OPENAI_MODEL (optional, default: gpt-4o-mini)
- OPENAI_TEMPERATURE (optional, default: 0.4)
- ALLOWED_HOSTS (comma-separated, e.g. "localhost,127.0.0.1,*.ngrok-free.app")
- TWILIO_AUTH_TOKEN (optional for signature verification)

## Install & run (dev)
```bash
python -m venv env && source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Endpoints
- Voice webhook: `POST /api/receptionist/twilio/voice/`
- SMS webhook: `POST /api/receptionist/twilio/sms/`

Both return TwiML (`text/xml`).

## Twilio configuration
1. Expose your local server (e.g. using ngrok):
   ```bash
   ngrok http http://localhost:8000
   ```
2. In Twilio Console, set webhook URLs:
   - Voice: `https://<your-domain>/api/receptionist/twilio/voice/`
   - Messaging: `https://<your-domain>/api/receptionist/twilio/sms/`
3. Set request method to POST.

## Optional: Verify Twilio signatures
The code includes a placeholder `verify_twilio_signature` in `receptionist/views.py`. To enable robust verification, compute and check the `X-Twilio-Signature` header using `TWILIO_AUTH_TOKEN`.

## Quick test (without Twilio)
```bash
# SMS simulate
curl -X POST http://localhost:8000/api/receptionist/twilio/sms/ \
  -d 'From=+15551234567' -d 'Body=Hi, I want to book a table'

# Voice simulate (Twilio normally sends many params)
curl -X POST http://localhost:8000/api/receptionist/twilio/voice/ \
  -d 'SpeechResult=I would like a reservation at 7pm'
```

## Notes
- Responses are generated via OpenAI Chat Completions; adjust `SYSTEM_PROMPT` in `receptionist/views.py` as needed.
- Voice flow uses TwiML `Gather` to collect speech/DTMF and loops back to continue the conversation.
