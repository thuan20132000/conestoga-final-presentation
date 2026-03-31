"""Service for managing call sessions and system logs."""

import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async
from django.utils import timezone

from ai_service.services.openai_api import OpenAIAPI
from receptionist.models import (
    AIConfiguration,
    AIConfigurationStatus,
    CallSession,
    ConversationMessage,
    SystemLog,
)

logger = logging.getLogger(__name__)


class CallSessionService:
    """Manages CallSession lifecycle and system logging."""

    def __init__(self, openai_api: Optional[OpenAIAPI] = None):
        self._openai_api = openai_api or OpenAIAPI()

    @staticmethod
    async def get_ai_configuration(call_to: str) -> AIConfiguration:
        """Fetch AIConfiguration for a business by its Twilio phone number."""
        return await AIConfiguration.objects.aget(
            business__twilio_phone_number=call_to,
            status=AIConfigurationStatus.ACTIVE.value,
        )

    async def finalize_call(
        self,
        call_sid: str,
        conversation_transcript: list[Dict[str, Any]],
    ) -> None:
        """Analyze conversation and update CallSession on call completion."""
        logger.info(f"Finalizing call session: {call_sid}")

        update_kwargs: Dict[str, Any] = {
            "status": "completed",
            "ended_at": timezone.now(),
            "conversation_transcript": conversation_transcript,
        }

        if conversation_transcript:
            try:
                outcome = await self._openai_api.analyze_conversation(
                    conversation_transcript
                )
                update_kwargs["outcome"] = outcome.get("outcome", "unknown")
                update_kwargs["sentiment"] = outcome.get("sentiment", "neutral")
                update_kwargs["transcript_summary"] = outcome.get("summary", "Unknown")
            except Exception as e:
                logger.error(f"Failed to analyze conversation for {call_sid}: {e}")

        await CallSession.objects.filter(call_sid=call_sid).aupdate(**update_kwargs)

    @staticmethod
    async def save_message(
        call_sid: str,
        role: str,
        content: str,
    ) -> None:
        """Save a conversation message to the database.

        Args:
            call_sid: The call session ID.
            role: Message role — 'user' or 'assistant'.
            content: The message text.
        """
        try:
            call = await CallSession.objects.aget(call_sid=call_sid)
            await ConversationMessage.objects.acreate(
                call=call,
                role=role,
                content=content,
            )
        except CallSession.DoesNotExist:
            logger.warning(f"Cannot save message: CallSession {call_sid} not found")
        except Exception as e:
            logger.error(f"Failed to save conversation message for {call_sid}: {e}")

    @staticmethod
    async def create_system_log(
        level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        call: Optional[CallSession] = None,
    ) -> None:
        """Create a system log entry."""
        await SystemLog.objects.acreate(
            level=level,
            call=call,
            message=message,
            metadata=metadata or {},
        )
