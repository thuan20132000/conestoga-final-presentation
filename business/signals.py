from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Business, BusinessSettings, BusinessRoles, OperatingHours, BusinessOnlineBooking
from service.models import ServiceCategory, Service
from staff.models import Staff
from datetime import time
from payment.models import PaymentMethod
from webpush.models import Group, PushInformation

from main.utils import get_business_managers_group_name 
from main.common_settings import ONLINE_BOOKING_URL

@receiver(post_save, sender=Business)
def create_business_defaults(sender, instance, created, **kwargs):
    """
    Create default settings, roles, services, and staff when a business is created.
    """
    if not created:
        return
    
    business = instance

    # create business settings
    BusinessSettings.objects.create(
        business=business,
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
            'name': 'Technician',
            'description': 'Technician of the business',
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

    ]
    for role in defaults_roles:
        BusinessRoles.objects.create(business=business, **role)

    # create business categories
    defaults_categories = [
        {
            'name': 'Pedicure & Manicure',
            'description': 'Pedicure & Manicure',
            'color_code': '#6cd5cb',
            'icon': 'fas fa-cut',
            'image': 'services/hair_cuts.jpg',
            'is_online_booking': True,
            'is_active': True,
            'sort_order': 1,
        },
        {
            'name': 'Nail Extensions',
            'description': 'Nail Extensions',
            'color_code': '#ffbf69',
            'icon': 'fas fa-cut',
            'image': 'services/hair_cuts.jpg',
            'is_online_booking': True,
            'is_active': True,
            'sort_order': 2,
        },
        {
            'name': 'Extra',
            'description': 'Hair Treatments',
            'color_code': '#ffbf69',
            'icon': 'fas fa-cut',
            'image': 'services/hair_cuts.jpg',
            'is_online_booking': True,
            'is_active': True,
            'sort_order': 3,
        },
        {
            'name': 'Waxing',
            'description': 'Waxing Services',
            'color_code': '#ff00ffb8',
            'icon': 'fas fa-cut',
            'image': 'services/hair_cuts.jpg',
            'is_online_booking': True,
            'is_active': True,
            'sort_order': 4,
        },
        {
            'name': 'Eyebrow Tinting',
            'description': 'Eyebrow Tinting Services',
            'color_code': '#ff00ffb8',
            'icon': 'fas fa-cut',
            'image': 'services/hair_cuts.jpg',
            'is_online_booking': True,
            'is_active': True,
            'sort_order': 5,
        },
        {
            'name': 'Kid Service',
            'description': 'Kid Service',
            'color_code': '#6cd5cb',
            'icon': 'fas fa-cut',
            'image': 'services/hair_cuts.jpg',
            'is_online_booking': True,
            'is_active': True,
            'sort_order': 6,
        },
        {
            'name': 'Blocks Time',
            'description': 'Blocks Time',
            'color_code': '#5f4a6e',
            'icon': 'fas fa-clock',
            'image': 'services/blocks_time.jpg',
            'is_online_booking': True,
            'is_active': True,
            'sort_order': 7,
        }
    ]
    for category in defaults_categories:
        ServiceCategory.objects.create(business=business, **category)

    pedicure_category = ServiceCategory.objects.get(name='Pedicure & Manicure', business=business)
    nail_extensions_category = ServiceCategory.objects.get(name='Nail Extensions', business=business)
    extra_category = ServiceCategory.objects.get(name='Extra', business=business)
    waxing_category = ServiceCategory.objects.get(name='Waxing', business=business)
    eyebrow_tinting_category = ServiceCategory.objects.get(name='Eyebrow Tinting', business=business)
    kid_service_category = ServiceCategory.objects.get(name='Kid Service', business=business)
    blocks_time_category = ServiceCategory.objects.get(name='Blocks Time', business=business)
    # create business services
    defaults_services = [
        {
            "name": "Pedicure",
            "description": "",
            "price": "40.00",
            "duration_minutes": 40,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Bio Gel Fill",
            "description": "",
            "price": "53.00",
            "duration_minutes": 50,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Acrylic Full Set",
            "description": "",
            "price": "57.00",
            "duration_minutes": 60,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Acrylic Fill",
            "description": "",
            "price": "50.00",
            "duration_minutes": 50,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Bio Gel Full Set",
            "description": "",
            "price": "63.00",
            "duration_minutes": 60,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Pedicure With Shellac",
            "description": "",
            "price": "52.00",
            "duration_minutes": 45,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Bio Gel Overlay",
            "description": "",
            "price": "57.00",
            "duration_minutes": 50,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Dip Powder Without Extension Lenght",
            "description": "",
            "price": "45.00",
            "duration_minutes": 50,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Manicure",
            "description": "",
            "price": "27.00",
            "duration_minutes": 25,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Dip Powder With Extension Length",
            "description": "",
            "price": "55.00",
            "duration_minutes": 60,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Acrylic Overlay",
            "description": "",
            "price": "52.00",
            "duration_minutes": 45,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Acrylic Full Set On Toe",
            "description": "",
            "price": "55.00",
            "duration_minutes": 55,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "GEL-X",
            "description": "",
            "price": "60.00",
            "duration_minutes": 60,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Acrylic Remove Without Service",
            "description": "",
            "price": "15.00",
            "duration_minutes": 20,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Manicure With Shellac",
            "description": "",
            "price": "37.00",
            "duration_minutes": 35,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Ombre White",
            "description": "",
            "price": "15.00",
            "duration_minutes": 10,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Acrylic Remove With Service",
            "description": "",
            "price": "10.00",
            "duration_minutes": 20,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Take Off Shellac Without Service",
            "description": "",
            "price": "10.00",
            "duration_minutes": 10,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Shellac Polish On Finger Nails",
            "description": "",
            "price": "25.00",
            "duration_minutes": 20,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Take Off Shellac With Service",
            "description": "",
            "price": "5.00",
            "duration_minutes": 10,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Shellac Polish On Toe Nails",
            "description": "",
            "price": "30.00",
            "duration_minutes": 25,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Regular Polish On Finger",
            "description": "",
            "price": "15.00",
            "duration_minutes": 15,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Regular Polish On Toe",
            "description": "",
            "price": "18.00",
            "duration_minutes": 15,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Fix",
            "description": "",
            "price": "0.00",
            "duration_minutes": 15,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Finger Nails Cut",
            "description": "",
            "price": "10.00",
            "duration_minutes": 10,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Toe Nail Cut",
            "description": "",
            "price": "12.00",
            "duration_minutes": 10,
            "category_id": pedicure_category.id,
        },
        {
            "name": "Extra Long Nail",
            "description": "",
            "price": "15.00",
            "duration_minutes": 15,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Block 3 Hours",
            "description": "",
            "price": "0.00",
            "duration_minutes": 180,
            "category_id": blocks_time_category.id,
        },
        {
            "name": "French Tip",
            "description": "",
            "price": "10.00",
            "duration_minutes": 10,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Kid Pedicure With Shellac",
            "description": "",
            "price": "40.00",
            "duration_minutes": 35,
            "category_id": kid_service_category.id,
        },
        {
            "name": "Kid Regular Polish (Toes or Fingers)",
            "description": "",
            "price": "10.00",
            "duration_minutes": 10,
            "category_id": kid_service_category.id,
        },
        {
            "name": "Kid Manicure",
            "description": "",
            "price": "18.00",
            "duration_minutes": 20,
            "category_id": kid_service_category.id,
        },
        {
            "name": "Long Nail",
            "description": "",
            "price": "10.00",
            "duration_minutes": 15,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Medium Nail",
            "description": "",
            "price": "5.00",
            "duration_minutes": 10,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Kid Shellac Polish (Toes Or Fingers)",
            "description": "",
            "price": "17.00",
            "duration_minutes": 15,
            "category_id": kid_service_category.id,
        },
        {
            "name": "Kid Manicure With Shellac",
            "description": "",
            "price": "26.00",
            "duration_minutes": 30,
            "category_id": kid_service_category.id,
        },
        {
            "name": "Chrome Nail",
            "description": "",
            "price": "10.00",
            "duration_minutes": 10,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Ombre Color",
            "description": "",
            "price": "10.00",
            "duration_minutes": 10,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Design Nail Star",
            "description": "",
            "price": "5.00",
            "duration_minutes": 10,
            "category_id": nail_extensions_category.id,
        },
        {
            "name": "Eye Brow Tinting",
            "description": "",
            "price": "20.00",
            "duration_minutes": 20,
            "category_id": eyebrow_tinting_category.id,
        },
        {
            "name": "Eye Brow Waxing and Tinting",
            "description": "",
            "price": "30.00",
            "duration_minutes": 30,
            "category_id": eyebrow_tinting_category.id,
        },
        {
            "name": "Chin",
            "description": "",
            "price": "8.00",
            "duration_minutes": 5,
            "category_id": eyebrow_tinting_category.id,
        },
        {
            "name": "Side",
            "description": "",
            "price": "15.00",
            "duration_minutes": 10,
            "category_id": eyebrow_tinting_category.id,
        },
        {
            "name": "Full Leg",
            "description": "",
            "price": "50.00",
            "duration_minutes": 50,
            "category_id": waxing_category.id,
        },
        {
            "name": "Half Arm",
            "description": "",
            "price": "30.00",
            "duration_minutes": 25,
            "category_id": waxing_category.id,
        },
        {
            "name": "Upper Lip",
            "description": "",
            "price": "6.00",
            "duration_minutes": 5,
            "category_id": waxing_category.id,
        },
        {
            "name": "Full Arm",
            "description": "",
            "price": "50.00",
            "duration_minutes": 40,
            "category_id": waxing_category.id,
        },
        {
            "name": "Eye Brow",
            "description": "",
            "price": "12.00",
            "duration_minutes": 10,
            "category_id": eyebrow_tinting_category.id,
        },
        {
            "name": "Kid Pedicure",
            "description": "",
            "price": "30.00",
            "duration_minutes": 30,
            "category_id": kid_service_category.id,
        },
        {
            "name": "Under Arm",
            "description": "",
            "price": "18.00",
            "duration_minutes": 15,
            "category_id": waxing_category.id,
        },
        {
            "name": "Full Face",
            "description": "",
            "price": "35.00",
            "duration_minutes": 30,
            "category_id": waxing_category.id,
        },
        {
            "name": "Block 1 Hour",
            "description": "",
            "price": "0.00",
            "duration_minutes": 60,
            "category_id": blocks_time_category.id,
        },
        {
            "name": "Block All Day",
            "description": "",
            "price": "0.00",
            "duration_minutes": 600,
            "category_id": blocks_time_category.id,
        },
        {
            "name": "Block 2 Hours",
            "description": "",
            "price": "0.00",
            "duration_minutes": 120,
            "category_id": blocks_time_category.id,
        },
        {
            "name": "Half Leg",
            "description": "",
            "price": "30.00",
            "duration_minutes": 30,
            "category_id": waxing_category.id,
        }
    ]
    for service in defaults_services:
        Service.objects.create(business=business, **service)

    technician_role = BusinessRoles.objects.get(name='Technician', business=business)
    
    # create business staff
    defaults_staff = [
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'role': technician_role,
        },
        {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jill.doe@example.com',
            'phone': '1234567890',
            'role': technician_role,
        },
        {
            'first_name': 'Jack',
            'last_name': 'Doe',
            'email': 'jack.doe@example.com',
            'phone': '1234567890',
            'role': technician_role,
        },
        {
            'first_name': 'Jill',
            'last_name': 'Doe',
            'email': 'jill.doe@example.com',
            'phone': '1234567890',
            'role': technician_role,
        },
        {
            'first_name': 'Jill',
            'last_name': 'Doe',
            'email': 'jill.doe@example.com',
            'phone': '1234567890',
            'role': technician_role,
        },
        {
            'first_name': 'Jill',
            'last_name': 'Doe',
            'email': 'jill.doe@example.com',
            'phone': '1234567890',
            'role': technician_role,
        },
    ]
    for staff in defaults_staff:
        Staff.objects.create(business=business, **staff)

    
    # create business operating hours
    for day in range(7):
        OperatingHours.objects.create(
            business=business,
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
        PaymentMethod.objects.create(business=business, **payment_method)

    
    # create business managers group
    business_managers_group = Group.objects.create(name=get_business_managers_group_name(business.id))


    # create business online booking
    business_description = business.description if business.description else 'Online Booking'
    business_policy = 'Booking policy/terms shown to clients'
    BusinessOnlineBooking.objects.create(
        business=business,
        name=business.name,
        description=business_description,
        policy=business_policy,
        interval_minutes=business.settings.time_slot_interval,
        buffer_time_minutes=business.settings.buffer_time_minutes,
        is_active=True,
        shareable_link=f'{ONLINE_BOOKING_URL}/booking?business_id={business.id}',
    )
