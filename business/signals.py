# from django.db.models.signals import post_save
# from django.dispatch import receiver
# import os

# from .models import Business, BusinessSettings, BusinessRoles, OperatingHours, BusinessOnlineBooking
# from service.models import ServiceCategory, Service
# from staff.models import Staff
# from datetime import time
# from payment.models import PaymentMethod
# from webpush.models import Group, PushInformation

# from main.utils import get_business_managers_group_name
# from .services import BusinessInitializerService, BusinessDefaultsService


# @receiver(post_save, sender=Business)
# def create_business_defaults(sender, instance, created, **kwargs):
#     """
#     Create default settings/roles/etc when a business is created.
#     In development, optional sample data (services + staff) can be seeded
#     by setting AUTO_SEED_SAMPLE_BUSINESS_DATA=true in the environment.
#     """
#     if not created:
#         return

#     business = instance
#     auto_seed_sample = os.getenv("AUTO_SEED_SAMPLE_BUSINESS_DATA", "").lower() in (
#         "1",
#         "true",
#         "yes",
#     )

#     if auto_seed_sample:
#         service_csv_path = "dummy/services_by_salon_2026-01-26.csv"
#         category_csv_path = "dummy/service_categories_by_salon_2026-01-26.csv"
#         BusinessInitializerService(business, service_csv_path, category_csv_path).initialize()
#     else:
#         BusinessDefaultsService(business).initialize()
