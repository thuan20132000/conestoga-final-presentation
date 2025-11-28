import logging
from re import S
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from appointment.serializers import AppointmentServiceSerializer, AppointmentSerializer
from business.models import BusinessSettings
from .models import Appointment, AppointmentService
from notifications.models import Notification
from notifications.services import NotificationDispatcher
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
dispatcher = NotificationDispatcher()


@receiver(post_save, sender=Appointment)
def handle_appointment_notifications(sender, instance, created, **kwargs):
    """Handle notifications for appointment creation and updates"""

    try:
        appointment_data = AppointmentSerializer(instance).data
        client_name = appointment_data.get('client_name', 'Unknown Client')
        client_phone = appointment_data.get('client_phone', None)
        business_phone = appointment_data.get(
            'business_phone_number', 'Unknown Phone')
        business_name = appointment_data.get(
            'business_name', 'Unknown Business')

        appointment_id = appointment_data.get('id', None)
        business_id = appointment_data.get('business', None)

        # get business settings
        business_settings = BusinessSettings.objects.get(
            business_id=business_id)
        send_reminder_sms = business_settings.send_reminder_sms if business_settings else False
        send_confirmation_sms = business_settings.send_confirmation_sms if business_settings else False
        reminder_hours_before = business_settings.reminder_hours_before if business_settings else 2

        start_at = appointment_data.get('start_at')
        start_at_obj = datetime.fromisoformat(start_at)
        start_at_str = start_at_obj.strftime("%I:%M %p on %B %d, %Y")
        metadata = instance.metadata
        schedule_name = f"reminder-sms-{business_id}-{appointment_id}"
        schedule_time = start_at_obj - timedelta(
            hours=reminder_hours_before,
            minutes=0,
        )

        with transaction.atomic():
            if created:

                if not client_phone:
                    return
                # send confirmation sms
                if metadata and metadata.get('is_send_confirmation_sms', False) == True:
                    
                    if send_confirmation_sms == False:
                        return

                    # New appointment created
                    title = f"Appointment Confirmed - {business_name}"
                    body_message = f"Hello {client_name}, your appointment #{appointment_id} has been confirmed at {start_at_str} at {business_name}. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
                    print("================= Dispatching SMS to {to} - {body} - {business_id}", client_phone, body_message, business_id)
                    dispatcher.dispatch(
                        title=title,
                        body=body_message,
                        data=metadata,
                        channel=Notification.Channel.SMS,
                        to=client_phone,
                        business_id=business_id,
                    )

                if metadata and metadata.get('is_send_reminder_sms', False) == True:
                    # New appointment created
                    if send_reminder_sms == False:
                        return

                    if schedule_time <= timezone.now():
                        return

                    title = f"Appointment Reminder - {business_name}"
                    body_message = f"Hello {client_name}, your appointment #{appointment_id} at {start_at_str} at {business_name} is coming up soon. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
                    dispatcher.dispatch_scheduled(
                        title=title,
                        body=body_message,
                        data=metadata,
                        channel=Notification.Channel.SMS,
                        to=client_phone,
                        business_id=business_id,
                        schedule_name=schedule_name,
                        schedule_time=schedule_time,
                    )
            else:
                print("appointment updated")
                if not client_phone:
                    return

                # Appointment rescheduled
                if metadata and metadata.get('is_rescheduled') == True:
                    body_message = f"Hello {client_name}, your appointment #{appointment_id} has been rescheduled to {start_at_str} at {business_name}. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
                    title = f"Appointment Rescheduled - {business_name}"
                    dispatcher.dispatch(
                        title=title,
                        body=body_message,
                        data=metadata,
                        channel=Notification.Channel.SMS,
                        to=client_phone,
                        business_id=business_id,
                    )
                # Appointment cancelled
                if metadata and metadata.get('is_cancelled') == True:
                    body_message = f"Hello {client_name}, your appointment #{appointment_id} at {start_at_str} at {business_name} has been cancelled. Please contact us at {business_phone} if you have any questions."
                    title = f"Appointment Cancelled - {business_name}"
                    dispatcher.dispatch(
                        title=title,
                        body=body_message,
                        data=metadata,
                        channel=Notification.Channel.SMS,
                        to=client_phone,
                        business_id=business_id,
                    )

                    dispatcher.dispatch_destroy_scheduled(
                        channel=Notification.Channel.SMS,
                        schedule_name=schedule_name,
                    )
    except Exception as e:
        logger.error(f"Error handling appointment notifications: {e}")
        return


@receiver(post_save, sender=AppointmentService)
def handle_appointment_service_added(sender, instance, created, **kwargs):
    """Handle notifications for appointment service changes"""

    appointment = AppointmentSerializer(instance.appointment).data
    booking_source = appointment.get('booking_source', '')
    appointment_service = AppointmentServiceSerializer(instance).data
    client_name = appointment_service.get('client_name', 'Unknown Client')
    service_name = appointment_service.get(
        'service_name', 'Unknown Service')
    business_name = appointment.get('business_name', 'Unknown Business')
    staff_name = appointment_service.get('staff_name', 'Unknown Staff')
    start_time_obj = datetime.fromisoformat(
        appointment_service.get('start_at'))
    start_time_str = start_time_obj.strftime("%I:%M %p on %B %d, %Y")
    is_staff_request = appointment_service.get('is_staff_request')
    metadata = instance.metadata
    if is_staff_request:
        staff_name = f"❤️ {staff_name}"
        
    print("metadata", metadata)    
        
    if created:

        body_message = f"{client_name} has booked a new appointment for {service_name} at {start_time_str} with {staff_name} from {booking_source}."
        title = f"Appointment Service Added - {business_name}"
        dispatcher.dispatch(
            title=title,
            body=body_message,
            data=appointment_service,
            channel=Notification.Channel.PUSH,
            to=staff_name,
        )

    else:
        if metadata and metadata.get('is_rescheduled') == True:
            print("appointment service rescheduled")
            body_message = f"Hello {client_name}, your appointment #{appointment.get('id', None)} for {service_name} has been rescheduled to {start_time_str}."
            title = f"Appointment Service Rescheduled - {business_name}"
            print("body_message", body_message)
            dispatcher.dispatch(
                title=title,
                body=body_message,
                data=appointment_service,
                channel=Notification.Channel.PUSH,
                to=staff_name,
            )
