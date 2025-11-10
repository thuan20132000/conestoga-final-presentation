import logging
from re import S
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from appointment.serializers import AppointmentServiceSerializer, AppointmentSerializer

from .models import Appointment, AppointmentService
from notifications.models import Notification
from notifications.services import NotificationDispatcher
from datetime import datetime
logger = logging.getLogger(__name__)
dispatcher = NotificationDispatcher()


def get_client_contact_info(client, business):
    """Get client contact information based on preferred contact method"""
    logger.info(f"Client: {client.id}")
    if not client:
        return None, None
    preferred_method = client.preferred_contact_method
    logger.info(f"Preferred method: {preferred_method}")
    # If client prefers no contact, don't send notifications
    if preferred_method == 'none':
        return None, None

    # Determine channel and recipient based on preferred method
    if preferred_method in ['email', 'Email']:
        if client.email:
            return Notification.Channel.EMAIL, client.email
        # Fallback to SMS if email not available
        if client.phone:
            return Notification.Channel.SMS, client.phone
    elif preferred_method in ['sms', 'SMS', 'phone', 'Phone']:
        if client.phone:
            return Notification.Channel.SMS, client.phone
        # Fallback to email if phone not available
        if client.email:
            return Notification.Channel.EMAIL, client.email
    else:
        # Default: try email first, then SMS
        if client.email:
            return Notification.Channel.EMAIL, client.email
        elif client.phone:
            return Notification.Channel.SMS, client.phone

    return None, None


@receiver(post_save, sender=Appointment)
def handle_appointment_notifications(sender, instance, created, **kwargs):
    """Handle notifications for appointment creation and updates"""

    try:
        appointment_data = AppointmentSerializer(instance).data
        client_name = appointment_data.get('client_name', 'Unknown Client')
        client_phone = appointment_data.get('client_phone', 'Unknown Phone')
        business_phone = appointment_data.get(
            'business_phone_number', 'Unknown Phone')
        business_name = appointment_data.get(
            'business_name', 'Unknown Business')
        start_at = appointment_data.get('start_at')
        start_at_obj = datetime.fromisoformat(start_at)
        start_at_str = start_at_obj.strftime("%I:%M %p on %B %d, %Y")
        metadata = instance.metadata

        logger.warning(f"Appointment: {appointment_data}")

        with transaction.atomic():
            print(f"Created: {created}")
            if created:

                # New appointment created
                title = f"Appointment Confirmed - {business_name}"
                body_message = f"Hello {client_name}, your appointment has been confirmed on {start_at_str} at {business_name}. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
                logger.warning(
                    f"Created notification for appointment confirmed: {body_message}")
                dispatcher.dispatch(
                    title=title,
                    body=body_message,
                    data=metadata,
                    channel=Notification.Channel.SMS,
                    to=client_phone,
                )
                logger.warning(
                    f"Created notification for appointment confirmed")

            else:
                print(
                    f"================= Appointment updated metadata: {metadata}")

                # Appointment rescheduled
                if metadata and metadata.get('is_rescheduled') == True:
                    body_message = f"Hello {client_name}, your appointment has been rescheduled to {start_at_str} at {business_name}. If you need to cancel or reschedule your appointment, please contact us at {business_phone}."
                    title = f"Appointment Rescheduled - {business_name}"
                    dispatcher.dispatch(
                        title=title,
                        body=body_message,
                        data=metadata,
                        channel=Notification.Channel.SMS,
                        to=client_phone,
                    )
                # Appointment cancelled
                if metadata and metadata.get('is_cancelled') == True:
                    body_message = f"Hello {client_name}, your appointment has been cancelled on {start_at_str} at {business_name}. Please contact us at {business_phone} if you have any questions."
                    title = f"Appointment Cancelled - {business_name}"
                    dispatcher.dispatch(
                        title=title,
                        body=body_message,
                        data=metadata,
                        channel=Notification.Channel.SMS,
                        to=client_phone,
                    )
    except Exception as e:
        logger.error(f"Error handling appointment notifications: {e}")
        return


@receiver(post_save, sender=AppointmentService)
def handle_appointment_service_added(sender, instance, created, **kwargs):
    """Handle notifications for appointment service changes"""

    if created:
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
        if is_staff_request:
            staff_name = f"❤️ {staff_name}"

        body_message = f"{client_name} has booked a new appointment for {service_name} at {start_time_str} with {staff_name} from {booking_source}."
        title = f"Appointment Service Added - {business_name}"
        logger.warning(f"Created notification for appointment service added")
        dispatcher.dispatch(
            title=title,
            body=body_message,
            data=appointment_service,
            channel=Notification.Channel.PUSH,
            to=staff_name,
        )
