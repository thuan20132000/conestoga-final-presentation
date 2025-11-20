from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Business, BusinessSettings, BusinessRoles, OperatingHours
from service.models import ServiceCategory, Service
from staff.models import Staff
from datetime import time
from payment.models import PaymentMethod


@receiver(post_save, sender=Business)
def create_business_defaults(sender, instance, created, **kwargs):
    """
    Create default settings, roles, services, and staff when a business is created.
    """
    if not created:
        return

    # create business settings
    BusinessSettings.objects.create(
        business=instance,
        advance_booking_days=30,
        min_advance_booking_hours=2,
        max_advance_booking_days=90,
        time_slot_interval=15,
        buffer_time_minutes=0,
        send_reminder_emails=True,
        send_reminder_sms=False,
        reminder_hours_before=24,
        send_confirmation_sms=False,
        currency='CAD',
        tax_rate=0.13,
        require_payment_advance=False,
        allow_online_booking=True,
        require_client_phone=True,
        require_client_email=False,
        auto_confirm_appointments=False,
    )

    # create business roles
    defaults_roles = [
        {
            'name': 'Owner',
            'description': 'Owner of the business',
        },
        {
            'name': 'Manager',
            'description': 'Manager of the business',
        },
        {
            'name': 'Receptionist',
            'description': 'Receptionist of the business',
        },
        {
            'name': 'Stylist',
            'description': 'Stylist of the business',
        },
        {
            'name': 'Technician',
            'description': 'Technician of the business',
        },
    ]
    for role in defaults_roles:
        BusinessRoles.objects.create(business=instance, **role)

    # create business categories
    defaults_categories = [
        {
            'name': 'Hair Cuts',
            'description': 'Hair Cuts',
        },
        {
            'name': 'Hair Coloring',
            'description': 'Hair Coloring',
        },
        {
            'name': 'Hair Treatments',
            'description': 'Hair Treatments',
        },
        {
            'name': 'Nail Services',
            'description': 'Nail Services',
        },
        {
            'name': 'Spa Services',
            'description': 'Spa Services',
        },
        {
            'name': 'Dental Services',
            'description': 'Dental Services',
        },
    ]
    for category in defaults_categories:
        ServiceCategory.objects.create(business=instance, **category)

    # create business services
    defaults_services = [
        {
            'name': 'Women\'s Cut & Style',
            'description': 'Women\'s Cut & Style',
            'category': ServiceCategory.objects.first(),
            'duration_minutes': 60,
            'price': 85.00,
            'is_active': True,
            'requires_staff': True,
            'max_capacity': 1,
            'is_online_booking': True,
            'color_code': '#000000',
            'icon': 'fas fa-cut',
            'image': 'services/women_cut_style.jpg',
        },
        {
            'name': 'Men\'s Cut',
            'description': 'Men\'s Cut',
            'category': ServiceCategory.objects.first(),
            'duration_minutes': 30,
            'price': 45.00,
            'is_active': True,
            'requires_staff': True,
            'max_capacity': 1,
            'is_online_booking': True,
            'color_code': '#000000',
            'icon': 'fas fa-cut',
            'image': 'services/men_cut.jpg',
        },
        {
            'name': 'Full Color',
            'description': 'Full Color',
            'category': ServiceCategory.objects.first(),
            'duration_minutes': 120,
            'price': 150.00,
            'is_active': True,
            'requires_staff': True,
            'max_capacity': 1,
            'is_online_booking': True,
            'color_code': '#000000',
            'icon': 'fas fa-cut',
            'image': 'services/full_color.jpg',
        },
        {
            'name': 'Highlights',
            'description': 'Highlights',
            'category': ServiceCategory.objects.first(),
            'duration_minutes': 90,
            'price': 120.00,
            'is_active': True,
            'requires_staff': True,
            'max_capacity': 1,
            'is_online_booking': True,
            'color_code': '#000000',
            'icon': 'fas fa-cut',
            'image': 'services/highlights.jpg',
        },
        {
            'name': 'Deep Conditioning',
            'description': 'Deep Conditioning',
            'category': ServiceCategory.objects.first(),
            'duration_minutes': 45,
            'price': 65.00,
            'is_active': True,
            'requires_staff': True,
            'max_capacity': 1,
            'is_online_booking': True,
            'color_code': '#000000',
            'icon': 'fas fa-cut',
            'image': 'services/deep_conditioning.jpg',
        },
    ]

    for service in defaults_services:
        Service.objects.create(business=instance, **service)

    # create business staff
    defaults_staff = [
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'role': BusinessRoles.objects.first(),
        },
        {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jill.doe@example.com',
            'phone': '1234567890',
            'role': BusinessRoles.objects.first(),
        },
        {
            'first_name': 'Jack',
            'last_name': 'Doe',
            'email': 'jack.doe@example.com',
            'phone': '1234567890',
            'role': BusinessRoles.objects.first(),
        },
        {
            'first_name': 'Jill',
            'last_name': 'Doe',
            'email': 'jill.doe@example.com',
            'phone': '1234567890',
            'role': BusinessRoles.objects.first(),
        },
        {
            'first_name': 'Jill',
            'last_name': 'Doe',
            'email': 'jill.doe@example.com',
            'phone': '1234567890',
            'role': BusinessRoles.objects.first(),
        },
        {
            'first_name': 'Jill',
            'last_name': 'Doe',
            'email': 'jill.doe@example.com',
            'phone': '1234567890',
            'role': BusinessRoles.objects.first(),
        },
    ]
    for staff in defaults_staff:
        Staff.objects.create(business=instance, **staff)

    # create business operating hours
    for day in range(7):
        OperatingHours.objects.create(
            business=instance,
            day_of_week=day,
            is_open=True if day < 5 else False,
            open_time=time(9, 0) if day < 5 else None,
            close_time=time(17, 0) if day < 5 else None,
            break_start_time=time(12, 0) if day < 5 else None,
            break_end_time=time(13, 0) if day < 5 else None,
        )

    # create business payment methods
    defaults_payment_methods = [
        {
            'name': 'Cash',
            'payment_type': 'cash',
            'description': 'Cash payment',
            'is_active': True,
        },
        {
            'name': 'Credit Card',
            'payment_type': 'credit_card',
            'description': 'Credit Card payment',
            'is_active': True,
        },
        {
            'name': 'Debit Card',
            'payment_type': 'debit_card',
            'description': 'Debit Card payment',
            'is_active': True,
        },
        {
            'name': 'Online Payment',
            'payment_type': 'online',
            'description': 'Online payment',
            'is_active': True,
        },
        {
            'name': 'Gift Card',
            'payment_type': 'gift_card',
            'description': 'Gift Card payment',
            'is_active': True,
        },
        {
            'name': 'Bank Transfer',
            'payment_type': 'bank_transfer',
            'description': 'Bank Transfer payment',
            'is_active': True,
        },
    ]
    for payment_method in defaults_payment_methods:
        PaymentMethod.objects.create(business=instance, **payment_method)
