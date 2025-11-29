from notifications.models import Notification
import logging
from dataclasses import dataclass
from typing import Optional, Dict
import datetime
from django.core.mail import send_mail
from main import common_settings
import boto3
import json
from pathlib import Path
# from pywebpush import webpush
from webpush import send_group_notification, send_user_notification

logger = logging.getLogger(__name__)


AWS_REGION = common_settings.AWS_REGION
LAMBDA_SEND_SMS_ARN = common_settings.AWS_LAMBDA_SEND_SMS_ARN
SCHEDULER_POLICY_ARN = common_settings.AWS_SCHEDULER_POLICY_ARN

lambda_client = boto3.client("lambda", region_name=AWS_REGION)
events_client = boto3.client("events", region_name=AWS_REGION)
schedule_client = boto3.client("scheduler", region_name=AWS_REGION)


@dataclass
class SendResult:
    ok: bool
    error: Optional[str] = None


class SMSService:
    group_name: str = "bookngon-calendar"

    def send(self, to_phone: str, body: str, business_id: Optional[int] = None) -> SendResult:
        try:
            message = f"{body} {common_settings.OPT_OUT_MESSAGE}"
            payload = {
                "phone_number": to_phone,
                "message": message,
                "from_phone_number": common_settings.SMS_DEFAULT_SENDER
            }
            response = lambda_client.invoke(
                FunctionName=LAMBDA_SEND_SMS_ARN,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload).encode('utf-8')
            )
            print(f"Response: {response}")
            # Body is a StreamingBody; decode to string then JSON
            body_bytes = response["Payload"].read()
            body_str = body_bytes.decode("utf-8")
            result = json.loads(body_str) if body_str else {}
            # Optionally look at FunctionError or LogResult
            print(f"Result: {result}")

            if result.get('statusCode', 0) != 200:
                print(f"Failed to send SMS: {result}")
                Notification.objects.create(
                    channel=Notification.Channel.SMS,
                    to=to_phone,
                    body=message,
                    status=Notification.Status.FAILED,
                    business_id=business_id,
                )

                return SendResult(ok=False, error=f"Failed to send SMS: {result}")

            logger.warning(f"========= SMS to {to_phone}: {message}")
            Notification.objects.create(
                channel=Notification.Channel.SMS,
                to=to_phone,
                body=message,
                status=Notification.Status.SENT,
                business_id=business_id,
            )

            return SendResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("SMS send failed")
            return SendResult(ok=False, error=str(exc))

    def send_scheduled(
        self,
        to_phone: str,
        body: str,
        business_id: Optional[int] = None,
        schedule_time: datetime.datetime = None,
        schedule_name: Optional[str] = None
    ) -> SendResult:
        try:

            message = f"{body} {common_settings.OPT_OUT_MESSAGE}"
            at_expression = f"at({schedule_time.strftime('%Y-%m-%dT%H:%M:%S')})"
            response = schedule_client.create_schedule(
                Name=schedule_name,
                ScheduleExpression=at_expression,
                State="ENABLED",
                FlexibleTimeWindow={
                    "Mode": "OFF",
                },
                Description=f"SMS to {to_phone} at {schedule_time}",
                Target={
                    "Arn": LAMBDA_SEND_SMS_ARN,
                    "RoleArn": SCHEDULER_POLICY_ARN,
                    "Input": json.dumps({
                        "phone_number": to_phone,
                        "message": message,
                        "from_phone_number": common_settings.SMS_DEFAULT_SENDER
                    })
                },
                ScheduleExpressionTimezone="America/Toronto",
                GroupName=self.group_name
            )
            Notification.objects.create(
                channel=Notification.Channel.SMS,
                to=to_phone,
                body=message,
                status=Notification.Status.PENDING,
                business_id=business_id,
                data={
                    "schedule_name": schedule_name,
                    "schedule_time": schedule_time.isoformat(),
                },
            )

            return SendResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("SMS schedule failed")
            return SendResult(ok=False, error=str(exc))

    def destroy_scheduled(self, schedule_name: str) -> SendResult:
        try:

            schedule_client.delete_schedule(
                Name=schedule_name,
                GroupName=self.group_name
            )
            return SendResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("SMS destroy scheduled failed")
            return SendResult(ok=False, error=str(exc))


class PushService:
    def send(self, user, title: str, body: str, data: Optional[Dict] = None) -> SendResult:
        try:
            logger.warning(
                f"================= Push to {user} - {title}")
            logger.warning(f"================= Body: {body}")
            logger.warning(f"================= Data: {data}")

            payload = {"head": "Welcome!", "body": "Hello World"}
            # response = send_user_notification(
            #     user=user, payload=payload, ttl=1000)
            
            response = send_group_notification(group_name="Test1", payload=payload, ttl=1000)
            print(f"================= Push Response: {response}")
            # print(f"================= Push Response: {response}")

            return SendResult(ok=True)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Push send failed")
            return SendResult(ok=False, error=str(exc))


class NotificationDispatcher:
    def __init__(self) -> None:
        self.sms = SMSService()
        self.push = PushService()

    def dispatch(
        self,
        channel: str,
        to: str,
        title: str,
        body: str,
        business_id: Optional[int] = None,
        data: Optional[Dict] = None,
    ) -> SendResult:
        if channel == Notification.Channel.SMS:
            print(
                f"================= Dispatching SMS to {to} - {body} - {business_id}")
            return self.sms.send(to, body, business_id)
        if channel == Notification.Channel.PUSH:
            return self.push.send(to, title, body, data)
        return SendResult(ok=False, error=f"Unsupported channel: {channel}")

    def dispatch_scheduled(
        self,
        channel: str,
        to: str,
        title: str,
        body: str,
        business_id: Optional[int] = None,
        data: Optional[Dict] = None,
        schedule_time: Optional[datetime.datetime] = None,
        schedule_name: Optional[str] = None,
    ) -> SendResult:
        if channel == Notification.Channel.SMS:
            return self.sms.send_scheduled(to, body, business_id, schedule_time, schedule_name)
        return SendResult(ok=False, error=f"Unsupported channel: {channel}")

    def dispatch_destroy_scheduled(self, channel: str, schedule_name: str) -> SendResult:
        if channel == Notification.Channel.SMS:
            return self.sms.destroy_scheduled(schedule_name)
        return SendResult(ok=False, error=f"Unsupported channel: {channel}")
