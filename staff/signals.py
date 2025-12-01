from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Staff, StaffService
from service.models import Service
import logging
from webpush.models import Group, PushInformation
from main.utils import get_business_managers_group_name
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Staff)
def handle_staff_post_save(sender, instance, created, **kwargs):
    """Create default working hours for a staff member"""
    if created:
        print(f"Created: {created}")

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
