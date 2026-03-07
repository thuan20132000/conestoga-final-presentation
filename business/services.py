from django.db import transaction
from datetime import time
from decimal import Decimal
import json
import os
from pathlib import Path
from .models import Business, BusinessSettings, BusinessRoles, OperatingHours, BusinessOnlineBooking
from service.models import ServiceCategory, Service
from staff.models import Staff
from payment.models import PaymentMethod
from webpush.models import Group, PushInformation
from main.utils import get_business_managers_group_name
import csv
from main.common_settings import ONLINE_BOOKING_URL
from staff.services import StaffCredentialService
from subscription.models import BusinessSubscription, SubscriptionStatus, SubscriptionPlan


class BusinessInitializerService:
    """Base class for business initializer services"""
    def __init__(self, business, service_csv_path, category_csv_path):
        self.business = business
        self.service_csv_path = service_csv_path
        self.category_csv_path = category_csv_path
        self.category_mapping = {}

    def initialize(self):
        with transaction.atomic():
            self._create_business_settings()
            self._create_business_roles()
            self._create_operating_hours()
            self._create_payment_methods()
            self._create_business_managers_group()
            self._create_online_booking()
            self._create_service_categories()
            self._create_services()
            self._create_staff()
            self._create_manager()

    def _create_business_settings(self):
        """Create default business settings"""
        BusinessSettings.objects.create(
            business=self.business,
            advance_booking_days=30,
            min_advance_booking_hours=2,
            max_advance_booking_days=90,
            time_slot_interval=15,
            buffer_time_minutes=0,
            send_reminder_emails=True,
            send_reminder_sms=False,
            reminder_hours_before=24,
            send_confirmation_sms=False,
            currency="CAD",
            tax_rate=0.13,
            require_payment_advance=False,
            allow_online_booking=True,
            require_client_phone=True,
            require_client_email=False,
            auto_confirm_appointments=False,
        )

    def _create_business_roles(self):
        """Create default business roles"""
        defaults_roles = [
            {
                "name": "Technician",
                "description": "Technician of the business",
            },
            {
                "name": "Manager",
                "description": "Manager of the business",
            },
            {
                "name": "Receptionist",
                "description": "Receptionist of the business",
            },
            {
                "name": "Owner",
                "description": "Owner of the business",
            },
        ]
        for role in defaults_roles:
            BusinessRoles.objects.create(business=self.business, **role)

    def _create_staff(self):
        """Create default staff members"""
        technician_role = BusinessRoles.objects.get(name='Technician', business=self.business)
        
        defaults_staff = [
            {
                'first_name': 'John',
                'last_name': 'Nguyen',
                'email': 'john.nguyen@example.com',
                'phone': '1234567890',
                'role': technician_role,
            },
            {
                'first_name': 'Jane',
                'last_name': 'Tran',
                'email': 'jane.tran@example.com',
                'phone': '1234567891',
                'role': technician_role,
            },
        ]
        for staff in defaults_staff:
            Staff.objects.create(business=self.business, **staff)

    def _create_manager(self,):
        """Create default managers"""
        manager_role = BusinessRoles.objects.get(name='Manager', business=self.business)
        defaults_managers = {   
                'first_name': 'Lisa',
                'last_name': 'Tran',
                'email': 'lisa.tran@example.com',
                'phone': '1234567892',
                'role': manager_role,
            }
        manager = Staff.objects.create(business=self.business, **defaults_managers)
        manager.set_password('!Matkhau@123')
        manager.save()

    def _create_operating_hours(self):
        """Create default operating hours for each day of the week"""
        for day in range(7):
            OperatingHours.objects.create(
                business=self.business,
                day_of_week=day,
                is_open=True if day < 5 else False,
                open_time=time(9, 0) if day < 5 else None,
                close_time=time(17, 0) if day < 5 else None,
                break_start_time=time(12, 0) if day < 5 else None,
                break_end_time=time(13, 0) if day < 5 else None,
            )

    def _create_payment_methods(self):
        """Create default payment methods"""
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
                'is_active': False,
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
                'is_active': False,
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
            PaymentMethod.objects.create(business=self.business, **payment_method)

    def _create_business_managers_group(self):
        """Create business managers group for webpush notifications"""
        Group.objects.create(name=get_business_managers_group_name(self.business.id))

    def _create_online_booking(self):
        """Create default online booking configuration"""
        business_description = self.business.description if self.business.description else 'Online Booking'
        business_policy = 'Booking policy/terms shown to clients'
        BusinessOnlineBooking.objects.create(
            business=self.business,
            name=self.business.name,
            description=business_description,
            policy=business_policy,
            interval_minutes=self.business.settings.time_slot_interval,
            buffer_time_minutes=self.business.settings.buffer_time_minutes,
            is_active=True,
            shareable_link=f'{ONLINE_BOOKING_URL}/booking?business_id={self.business.id}',
        )

    def _create_service_categories(self):
        """Create default service categories"""
        base_dir = Path(__file__).resolve().parent
        csv_path = base_dir / self.category_csv_path
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                category = ServiceCategory.objects.create(
                    business=self.business,
                    name=row[2],
                    color_code=row[3],
                    sort_order=row[0],
                    is_online_booking=True,
                    is_active=True,
                )
                self.category_mapping[category.name] = category

    def _create_services(self):
        """Create default services"""
        base_dir = Path(__file__).resolve().parent
        csv_path = base_dir / self.service_csv_path
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                category = self.category_mapping.get(row[5])
                if not category:
                    category = None
                Service.objects.create(
                    business=self.business,
                    category=category,
                    name=row[2],
                    duration_minutes=row[4],
                    price=row[3],
                    is_active=True,
                    sort_order=row[0],
                    is_online_booking=True,
                )

class BellebizBusinessInitializerService(BusinessInitializerService):
    def __init__(self, business):
        self.business = business
        self._category_mapping = {}  # Maps serviceTypeId to category name

    def initialize(self):
        with transaction.atomic():
            self._create_business_settings()
            self._create_business_roles()
            self._create_service_categories()
            self._create_services()
            self._create_staff()
            self._create_operating_hours()
            self._create_payment_methods()
            self._create_business_managers_group()
            self._create_online_booking()


    def _create_service_categories(self):
        """Create default service categories from JSON file"""
        # Get the path to the JSON file
        base_dir = Path(__file__).resolve().parent
        json_path = base_dir / 'dummy' / 'nailicious-categories.json'
        
        # Load categories from JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        # Store category mapping for services (serviceTypeId -> category object)
        self._category_mapping = {}
        
        # Create categories, filtering only active ones
        for cat_data in categories_data:
            if cat_data.get('isActive', True):  # Only create active categories
                category = ServiceCategory.objects.create(
                    business=self.business,
                    name=cat_data.get('name', ''),
                    description=cat_data.get('description') or '',
                    color_code=cat_data.get('colorCode') or '',
                    sort_order=cat_data.get('orderBy', 0),
                    is_online_booking=cat_data.get('isOnlineBooking', True),
                    is_active=cat_data.get('isActive', True),
                )
                # Map serviceTypeId to category object for service creation
                service_type_id = str(cat_data.get('id', ''))
                self._category_mapping[service_type_id] = category

    def _create_services(self):
        """Create default services from JSON file"""
        # Get the path to the JSON file
        base_dir = Path(__file__).resolve().parent
        json_path = base_dir / 'dummy' / 'nailicious-services.json'
        
        # Load services from JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            services_data = json.load(f)
        
        # Create services
        for service_data in services_data:
            # Skip if service is deleted or not active
            if service_data.get('isDeleted', False) or not service_data.get('isActive', True):
                continue
            
            # Get the category from serviceTypeId
            service_type_id = str(service_data.get('serviceTypeId', ''))
            category = self._category_mapping.get(service_type_id)
            
            if not category:
                # Skip if category not found
                continue
            
            # Convert price to Decimal
            price_str = service_data.get('price', '0')
            try:
                price = Decimal(str(price_str))
            except (ValueError, TypeError):
                price = Decimal('0')
            
            # Get duration
            duration = service_data.get('duration', 0)
            if not duration or duration <= 0:
                duration = 30  # Default duration
            
            # Create the service
            Service.objects.create(
                business=self.business,
                category=category,
                name=service_data.get('name', ''),
                description=service_data.get('description') or '',
                duration_minutes=duration,
                price=price,
                is_active=service_data.get('isActive', True),
                sort_order=service_data.get('orderBy', 0),
                is_online_booking=service_data.get('isOnlineBooking', True),
            )



class BusinessRegisterService(BusinessInitializerService):
    """Service for registering a new business"""
    service_csv_path = "dummy/services_by_salon_2026-01-26.csv"
    category_csv_path = "dummy/service_categories_by_salon_2026-01-26.csv"
    
    
    def __init__(self, business: dict, owner: dict):
        super().__init__(business, self.service_csv_path, self.category_csv_path)
        self.business_data = business
        self.owner_data = owner

    def initialize(self):
        with transaction.atomic():
            self.business = self._create_business()
            self._create_business_settings()
            self._create_business_roles()
            self._create_operating_hours()
            self._create_payment_methods()
            self._create_business_managers_group()
            self._create_online_booking()
            self._create_service_categories()
            self._create_services()
            self._subscribe_free_trial()
            self._create_staff()
            self._create_manager()
            owner = self._create_owner()
            self.owner = owner
            return owner
            
            
    def _create_business(self):
        """Create default business"""
        business = Business.objects.create(**self.business_data)
        return business
            
    def _create_owner(self):
        """Create default owner"""
        owner_role = BusinessRoles.objects.get(name='Owner', business=self.business)
        owner = Staff.objects.create(business=self.business, role=owner_role, **self.owner_data)
        
        StaffCredentialService.create_or_reset_credentials(owner, send_sms=True)
        return owner

    def _subscribe_free_trial(self):
        """Subscribe to free trial"""
        subscription = BusinessSubscription.objects.create(
            business=self.business,
            plan=SubscriptionPlan.objects.get(name='Free Trial', is_active=True),
            status=SubscriptionStatus.TRIALING,
        )
        return subscription