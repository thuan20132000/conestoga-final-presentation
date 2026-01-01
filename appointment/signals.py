import logging
from re import S
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from appointment.serializers import AppointmentServiceSerializer, AppointmentSerializer
from business.models import BusinessSettings
from .models import Appointment, AppointmentService, AppointmentStatusType
from notifications.models import Notification
from notifications.services import NotificationDispatcher
from datetime import datetime, timedelta
from appointment.services import AppointmentNotificationService
import time
from django.contrib.auth.models import User
from staff.models import Staff

logger = logging.getLogger(__name__)
dispatcher = NotificationDispatcher()


@receiver(post_save, sender=Appointment)
def handle_appointment_notifications(sender, instance, created, **kwargs):
    """Handle notifications for appointment creation and updates"""

    try:
        print("appointment instance:: ", instance)
        appointment_data = AppointmentSerializer(instance).data
        client_name = appointment_data.get('client_name', 'A client')
        client_phone = appointment_data.get('client_phone', None)
        business_phone = appointment_data.get(
            'business_phone_number', 'Unknown')
        business_name = appointment_data.get(
            'business_name', 'A business')

        appointment_id = appointment_data.get('id', None)
        business_id = appointment_data.get('business', None)

        # get business settings
        business_settings = BusinessSettings.objects.get(
            business_id=business_id
        )
        send_confirmation_sms = business_settings.send_confirmation_sms if business_settings else False
        reminder_hours_before = business_settings.reminder_hours_before if business_settings else 2
        business_timezone = business_settings.timezone

        timezone.activate(business_timezone)

        start_at = appointment_data.get('start_at')
        start_at_obj = datetime.fromisoformat(start_at)
        start_at_str = start_at_obj.strftime("%I:%M %p on %B %d, %Y")
        payment_status = appointment_data.get('payment_status', None)

        metadata = instance.metadata
        schedule_name = f"reminder-sms-{business_id}-{appointment_id}"
        schedule_time = start_at_obj - timedelta(
            hours=reminder_hours_before,
            minutes=0,
        )
        appointment_status = appointment_data.get('status', None)

        appointment_notification_service = AppointmentNotificationService(
            instance)

        with transaction.atomic():
            if created:
                # Client notifications
                if not client_phone:
                    return
                # send confirmation sms
                if metadata and metadata.get('is_send_confirmation_sms', False) == True:

                    if send_confirmation_sms == False:
                        return

                    # New appointment created
                    appointment_notification_service.send_client_confirmation_notification(
                        client_name=client_name,
                        client_phone=client_phone,
                        business_phone=business_phone,
                        business_name=business_name,
                        appointment_id=appointment_id,
                        start_at=start_at_str,
                        metadata=metadata,
                    )

                if metadata and metadata.get('is_send_reminder_sms', False) == True:
                    # New appointment created
                    if business_settings.send_reminder_sms == False:
                        return

                    if schedule_time <= timezone.now():
                        return

                    appointment_notification_service.send_client_reminder_notification(
                        client_name=client_name,
                        client_phone=client_phone,
                        business_phone=business_phone,
                        business_name=business_name,
                        appointment_id=appointment_id,
                        start_at=start_at_str,
                        metadata=metadata,
                        schedule_name=schedule_name,
                        schedule_time=schedule_time,
                    )
            else:
                if not client_phone:
                    return

                # Appointment rescheduled
                if metadata and metadata.get('is_send_sms_rescheduled_confirmation', False) == True:
                    appointment_notification_service.send_client_rescheduled_notification(
                        client_name=client_name,
                        client_phone=client_phone,
                        business_phone=business_phone,
                        business_name=business_name,
                        appointment_id=appointment_id,
                        business_id=business_id,
                        start_at_str=start_at_str,
                        metadata=metadata,
                    )
                # Appointment cancelled
                if metadata and metadata.get('is_send_sms_cancellation_confirmation', False) == True:
                    appointment_notification_service.send_client_cancellation_notification(
                        client_name=client_name,
                        client_phone=client_phone,
                        business_phone=business_phone,
                        business_name=business_name,
                        appointment_id=appointment_id,
                        business_id=business_id,
                        start_at_str=start_at_str,
                        metadata=metadata,
                        schedule_name=schedule_name,
                    )

                # Appointment completed
                if appointment_status == AppointmentStatusType.CHECKED_OUT:
                    if metadata.get('is_send_sms_checked_out_confirmation', False) == False:
                        return
                    appointment_notification_service.send_client_completed_notification(
                        client_name=client_name,
                        client_phone=client_phone,
                        business_phone=business_phone,
                        business_name=business_name,
                        appointment_id=appointment_id,
                        business_id=business_id,
                        metadata=metadata,
                    )

    except Exception as e:
        # logger.error(f"Error handling appointment notifications: {e}")
        return
    finally:
        timezone.deactivate()


@receiver(post_save, sender=AppointmentService)
def handle_appointment_service_added(sender, instance, created, **kwargs):
    """Handle notifications for appointment service changes"""

    # POS payment notifications
    if metadata and metadata.get('is_pos_payment', False) == True:
        return
      
    metadata = instance.metadata

    appointment = AppointmentSerializer(instance.appointment).data
    booking_source = appointment.get('booking_source', '')
    appointment_service = AppointmentServiceSerializer(instance).data
    client_name = appointment_service.get('client_name', 'A client')
    service_name = appointment_service.get(
        'service_name', 'Unknown Service')
    business_name = appointment.get('business_name', 'Unknown Business')
    business_id = appointment.get('business', None)
    staff_name = appointment_service.get('staff_name', 'Unknown Staff')

    staff_id = appointment_service.get('staff', None)
    start_time_obj = datetime.fromisoformat(
        appointment_service.get('start_at'))
    start_time_str = start_time_obj.strftime("%I:%M %p on %B %d, %Y")
    is_staff_request = appointment_service.get('is_staff_request')
    booking_source = f"from {booking_source}" if booking_source else ""
    staff_obj = Staff.objects.get(id=staff_id)

    appointment_notification_service = AppointmentNotificationService(instance)


    if created:

        staff_name = f"❤️ {staff_name}" if is_staff_request else "Anyone"

        # Staff appointment confirmation notifications
        appointment_notification_service.send_staff_appointment_confirmation_notification(
            staff=staff_obj,
            staff_name=staff_name,
            business_name=business_name,
            client_name=client_name,
            service_name=service_name,
            start_time_str=start_time_str,
            booking_source=booking_source,
            metadata=metadata,
        )
        appointment_notification_service.send_manager_appointment_confirmation_notification(
            staff=staff_obj,
            staff_name=staff_name,
            business_name=business_name,
            business_id=business_id,
            client_name=client_name,
            service_name=service_name,
            start_time_str=start_time_str,
            booking_source=booking_source,
            metadata=metadata,
        )
