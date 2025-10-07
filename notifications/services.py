import logging
from dataclasses import dataclass
from typing import Optional, Dict

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    ok: bool
    error: Optional[str] = None


class EmailService:
    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        try:
            send_mail(subject=subject or "", message=body, from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None), recipient_list=[to_email])
            return SendResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Email send failed")
            return SendResult(ok=False, error=str(exc))


class SMSService:
    def send(self, to_phone: str, body: str) -> SendResult:
        try:
            logger.info("SMS to %s: %s", to_phone, body)
            return SendResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("SMS send failed")
            return SendResult(ok=False, error=str(exc))


class PushService:
    def send(self, device_token: str, title: str, body: str, data: Optional[Dict] = None) -> SendResult:
        try:
            logger.info("Push to %s: %s - %s | data=%s", device_token, title, body, data)
            return SendResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Push send failed")
            return SendResult(ok=False, error=str(exc))


class NotificationDispatcher:
    def __init__(self) -> None:
        self.email = EmailService()
        self.sms = SMSService()
        self.push = PushService()

    def dispatch(self, channel: str, to: str, title: str, body: str, data: Optional[Dict] = None) -> SendResult:
        if channel == "email":
            return self.email.send(to, title, body)
        if channel == "sms":
            return self.sms.send(to, body)
        if channel == "push":
            return self.push.send(to, title, body, data)
        return SendResult(ok=False, error=f"Unsupported channel: {channel}")
