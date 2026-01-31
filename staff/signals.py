from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Staff, StaffService, TimeEntry
from service.models import Service
import logging
from webpush.models import Group, PushInformation
from main.utils import get_business_managers_group_name
from notifications.models import Notification
from notifications.services import NotificationDispatcher
from django.utils import timezone
from business.models import BusinessSettings
from datetime import datetime
dispatcher = NotificationDispatcher()

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Staff)
def handle_staff_post_save(sender, instance, created, **kwargs):
    """Create default working hours for a staff member"""
    if created:
        # assign all business services to the staff
        services = Service.objects.filter(business=instance.business)
        for service in services:
            StaffService.objects.create(
                staff=instance,
                service=service,
                is_primary=False,
                is_online_booking=True,
                custom_price=None,
                custom_duration=None,
                is_active=True
            )

    else:
        # update the staff group
        try:
            business_managers_group_name = get_business_managers_group_name(
                instance.business.id)
            push_information = PushInformation.objects.filter(
                user=instance).first()
            if push_information:
                push_information.group = Group.objects.get(
                    name=business_managers_group_name)
                push_information.save()
        except Exception as e:
            print(f"Error updating staff group: {e}")


# signal to send push notification to managers when a staff is clocked in or clocked out
@receiver(post_save, sender=TimeEntry)
def handle_time_entry_post_save(sender, instance, created, **kwargs):
    """Send push notification to managers when a staff is clocked in or clocked out"""
    try:
        business_id = instance.staff.business.id
        business_name = instance.staff.business.name
        first_name = instance.staff.first_name
        
        business_settings = BusinessSettings.objects.get(business_id=business_id)
        if not business_settings:
            business_timezone = timezone.get_current_timezone()
        else:
            business_timezone = business_settings.timezone
        
        timezone.activate(business_timezone)
        if created:
            update_title = ""
        else:
            update_title = "(Updated)"
            
        if instance.status == 'IN_PROGRESS':
            title = f"🔔 Staff Clocked In - {business_name}"
            clock_in_time = timezone.localtime(instance.clock_in).strftime('%I:%M %p on %B %d, %Y')
            body = f"{update_title} {first_name} has clocked in at {clock_in_time}."
            
            dispatcher.dispatchAsync(
                title=title,
                body=body,
                channel=Notification.Channel.PUSH,
                to=None,
                group_name=get_business_managers_group_name(business_id),
            )
            
        if instance.status == 'COMPLETED':
            title = f"🔔 Staff Clocked Out - {business_name}"
            clock_out_time = timezone.localtime(instance.clock_out).strftime('%I:%M %p on %B %d, %Y')
            body = f"{update_title} {first_name} has clocked out at {clock_out_time}."
            
            dispatcher.dispatchAsync(
                title=title,
                body=body,
                channel=Notification.Channel.PUSH,
                to=None,
                group_name=get_business_managers_group_name(business_id),
            )
    except Exception as e:
        print(f"Error sending time entry notification: {e}")
        return
    finally:
        timezone.deactivate()