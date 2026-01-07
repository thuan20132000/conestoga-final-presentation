from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Business, BusinessSettings, BusinessRoles, OperatingHours, BusinessOnlineBooking
from service.models import ServiceCategory, Service
from staff.models import Staff
from datetime import time
from payment.models import PaymentMethod
from webpush.models import Group, PushInformation

from main.utils import get_business_managers_group_name 
from .services import BellebizBusinessInitializerService

@receiver(post_save, sender=Business)
def create_business_defaults(sender, instance, created, **kwargs):
    """
    Create default settings, roles, services, and staff when a business is created.
    """
    if not created:
        return
    
    business = instance
    BellebizBusinessInitializerService(business).initialize()
