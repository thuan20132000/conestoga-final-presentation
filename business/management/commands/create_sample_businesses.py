from django.core.management.base import BaseCommand
from django.utils import timezone
from business.models import (
    BusinessType, Business, OperatingHours, BusinessSettings
)
from service.models import ServiceCategory, Service
from staff.models import Staff, StaffService


class Command(BaseCommand):
    help = 'Create sample businesses with services, staff, and settings'

    def handle(self, *args, **options):
        # Get business types
        hair_salon_type = BusinessType.objects.get(name='Hair Salon')
        nail_salon_type = BusinessType.objects.get(name='Nail Salon')
        spa_type = BusinessType.objects.get(name='Spa')
        dental_type = BusinessType.objects.get(name='Dental Clinic')

        # Create Hair Salon
        hair_salon = self.create_hair_salon(hair_salon_type)
        
        # Create Nail Salon
        nail_salon = self.create_nail_salon(nail_salon_type)
        
        # Create Spa
        spa = self.create_spa(spa_type)
        
        # Create Dental Clinic
        dental_clinic = self.create_dental_clinic(dental_type)

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample businesses with complete data')
        )

    def create_hair_salon(self, business_type):
        """Create a sample hair salon"""
        business, created = Business.objects.get_or_create(
            name='Style Studio Hair Salon',
            defaults={
                'business_type': business_type,
                'phone_number': '+1-555-0123',
                'email': 'info@stylestudio.com',
                'website': 'https://stylestudio.com',
                'address': '123 Main Street',
                'city': 'Toronto',
                'state_province': 'ON',
                'postal_code': 'M5V 3A8',
                'country': 'Canada',
                'description': 'Professional hair salon offering cutting-edge styles and treatments',
                'status': 'active'
            }
        )

        if created:
            self.create_operating_hours(business)
            self.create_business_settings(business)
            
            # Create service categories
            cut_category = ServiceCategory.objects.create(
                business=business,
                name='Hair Cuts',
                description='Professional haircuts for all hair types',
                sort_order=1
            )
            
            color_category = ServiceCategory.objects.create(
                business=business,
                name='Hair Coloring',
                description='Professional hair coloring and highlights',
                sort_order=2
            )
            
            treatment_category = ServiceCategory.objects.create(
                business=business,
                name='Hair Treatments',
                description='Deep conditioning and repair treatments',
                sort_order=3
            )

            # Create services
            services = [
                {'category': cut_category, 'name': 'Women\'s Cut & Style', 'duration': 60, 'price': 85.00},
                {'category': cut_category, 'name': 'Men\'s Cut', 'duration': 30, 'price': 45.00},
                {'category': cut_category, 'name': 'Children\'s Cut', 'duration': 30, 'price': 35.00},
                {'category': color_category, 'name': 'Full Color', 'duration': 120, 'price': 150.00},
                {'category': color_category, 'name': 'Highlights', 'duration': 90, 'price': 120.00},
                {'category': color_category, 'name': 'Balayage', 'duration': 150, 'price': 180.00},
                {'category': treatment_category, 'name': 'Deep Conditioning', 'duration': 45, 'price': 65.00},
                {'category': treatment_category, 'name': 'Keratin Treatment', 'duration': 180, 'price': 250.00},
            ]

            for service_data in services:
                Service.objects.create(
                    business=business,
                    category=service_data['category'],
                    name=service_data['name'],
                    duration_minutes=service_data['duration'],
                    price=service_data['price']
                )

            # Create staff
            staff_members = [
                {'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah@stylestudio.com'},
                {'first_name': 'Mike', 'last_name': 'Chen', 'email': 'mike@stylestudio.com'},
                {'first_name': 'Emma', 'last_name': 'Williams', 'email': 'emma@stylestudio.com'},
                {'first_name': 'Lisa', 'last_name': 'Brown', 'email': 'lisa@stylestudio.com'},
            ]

            for staff_data in staff_members:
                Staff.objects.create(
                    business=business,
                    first_name=staff_data['first_name'],
                    last_name=staff_data['last_name'],
                    email=staff_data['email'],
                    phone='+1-555-0123'
                )

            self.stdout.write(f'Created hair salon: {business.name}')

        return business

    def create_nail_salon(self, business_type):
        """Create a sample nail salon"""
        business, created = Business.objects.get_or_create(
            name='Luxe Nail Studio',
            defaults={
                'business_type': business_type,
                'phone_number': '+1-555-0456',
                'email': 'info@luxenails.com',
                'website': 'https://luxenails.com',
                'address': '456 Queen Street',
                'city': 'Toronto',
                'state_province': 'ON',
                'postal_code': 'M5H 2M9',
                'country': 'Canada',
                'description': 'Premium nail salon offering luxury manicures and pedicures',
                'status': 'active'
            }
        )

        if created:
            self.create_operating_hours(business)
            self.create_business_settings(business)
            
            # Create service categories
            manicure_category = ServiceCategory.objects.create(
                business=business,
                name='Manicures',
                description='Professional nail care and polish services',
                sort_order=1
            )
            
            pedicure_category = ServiceCategory.objects.create(
                business=business,
                name='Pedicures',
                description='Foot care and nail services',
                sort_order=2
            )
            
            nail_art_category = ServiceCategory.objects.create(
                business=business,
                name='Nail Art',
                description='Creative nail designs and decorations',
                sort_order=3
            )

            # Create services
            services = [
                {'category': manicure_category, 'name': 'Classic Manicure', 'duration': 45, 'price': 35.00},
                {'category': manicure_category, 'name': 'Gel Manicure', 'duration': 60, 'price': 50.00},
                {'category': manicure_category, 'name': 'French Manicure', 'duration': 50, 'price': 45.00},
                {'category': pedicure_category, 'name': 'Classic Pedicure', 'duration': 60, 'price': 45.00},
                {'category': pedicure_category, 'name': 'Spa Pedicure', 'duration': 90, 'price': 65.00},
                {'category': nail_art_category, 'name': 'Nail Art Design', 'duration': 30, 'price': 25.00},
                {'category': nail_art_category, 'name': 'Gel Extensions', 'duration': 120, 'price': 80.00},
            ]

            for service_data in services:
                Service.objects.create(
                    business=business,
                    category=service_data['category'],
                    name=service_data['name'],
                    duration_minutes=service_data['duration'],
                    price=service_data['price']
                )

            # Create staff
            staff_members = [
                {'first_name': 'Jessica', 'last_name': 'Lee', 'role': 'technician', 'email': 'jessica@luxenails.com'},
                {'first_name': 'Maria', 'last_name': 'Garcia', 'role': 'technician', 'email': 'maria@luxenails.com'},
                {'first_name': 'Amy', 'last_name': 'Taylor', 'role': 'technician', 'email': 'amy@luxenails.com'},
            ]

            for staff_data in staff_members:
                Staff.objects.create(
                    business=business,
                    first_name=staff_data['first_name'],
                    last_name=staff_data['last_name'],
                    role=staff_data['role'],
                    email=staff_data['email'],
                    phone='+1-555-0456'
                )

            self.stdout.write(f'Created nail salon: {business.name}')

        return business

    def create_spa(self, business_type):
        """Create a sample spa"""
        business, created = Business.objects.get_or_create(
            name='Serenity Wellness Spa',
            defaults={
                'business_type': business_type,
                'phone_number': '+1-555-0789',
                'email': 'info@serenityspa.com',
                'website': 'https://serenityspa.com',
                'address': '789 King Street',
                'city': 'Toronto',
                'state_province': 'ON',
                'postal_code': 'M5K 1A1',
                'country': 'Canada',
                'description': 'Luxury spa offering relaxation and wellness treatments',
                'status': 'active'
            }
        )

        if created:
            self.create_operating_hours(business)
            self.create_business_settings(business)
            
            # Create service categories
            massage_category = ServiceCategory.objects.create(
                business=business,
                name='Massage Therapy',
                description='Professional massage and body treatments',
                sort_order=1
            )
            
            facial_category = ServiceCategory.objects.create(
                business=business,
                name='Facial Treatments',
                description='Skincare and facial services',
                sort_order=2
            )
            
            wellness_category = ServiceCategory.objects.create(
                business=business,
                name='Wellness Services',
                description='Holistic wellness and relaxation treatments',
                sort_order=3
            )

            # Create services
            services = [
                {'category': massage_category, 'name': 'Swedish Massage', 'duration': 60, 'price': 120.00},
                {'category': massage_category, 'name': 'Deep Tissue Massage', 'duration': 60, 'price': 130.00},
                {'category': massage_category, 'name': 'Hot Stone Massage', 'duration': 90, 'price': 160.00},
                {'category': facial_category, 'name': 'Classic Facial', 'duration': 60, 'price': 100.00},
                {'category': facial_category, 'name': 'Anti-Aging Facial', 'duration': 90, 'price': 150.00},
                {'category': wellness_category, 'name': 'Aromatherapy Treatment', 'duration': 75, 'price': 110.00},
                {'category': wellness_category, 'name': 'Body Wrap', 'duration': 90, 'price': 140.00},
            ]

            for service_data in services:
                Service.objects.create(
                    business=business,
                    category=service_data['category'],
                    name=service_data['name'],
                    duration_minutes=service_data['duration'],
                    price=service_data['price']
                )

            # Create staff
            staff_members = [
                {'first_name': 'Rachel', 'last_name': 'Smith', 'role': 'technician', 'email': 'rachel@serenityspa.com'},
                {'first_name': 'David', 'last_name': 'Wilson', 'role': 'technician', 'email': 'david@serenityspa.com'},
                {'first_name': 'Sophie', 'last_name': 'Anderson', 'role': 'technician', 'email': 'sophie@serenityspa.com'},
            ]

            for staff_data in staff_members:
                Staff.objects.create(
                    business=business,
                    first_name=staff_data['first_name'],
                    last_name=staff_data['last_name'],
                    role=staff_data['role'],
                    email=staff_data['email'],
                    phone='+1-555-0789'
                )

            self.stdout.write(f'Created spa: {business.name}')

        return business

    def create_dental_clinic(self, business_type):
        """Create a sample dental clinic"""
        business, created = Business.objects.get_or_create(
            name='Bright Smile Dental',
            defaults={
                'business_type': business_type,
                'phone_number': '+1-555-0321',
                'email': 'info@brightsmile.com',
                'website': 'https://brightsmile.com',
                'address': '321 Bay Street',
                'city': 'Toronto',
                'state_province': 'ON',
                'postal_code': 'M5H 2Y2',
                'country': 'Canada',
                'description': 'Comprehensive dental care for the whole family',
                'status': 'active'
            }
        )

        if created:
            self.create_operating_hours(business)
            self.create_business_settings(business)
            
            # Create service categories
            general_category = ServiceCategory.objects.create(
                business=business,
                name='General Dentistry',
                description='Routine dental care and checkups',
                sort_order=1
            )
            
            cosmetic_category = ServiceCategory.objects.create(
                business=business,
                name='Cosmetic Dentistry',
                description='Aesthetic dental treatments',
                sort_order=2
            )
            
            specialty_category = ServiceCategory.objects.create(
                business=business,
                name='Specialty Services',
                description='Advanced dental procedures',
                sort_order=3
            )

            # Create services
            services = [
                {'category': general_category, 'name': 'Dental Cleaning', 'duration': 60, 'price': 120.00},
                {'category': general_category, 'name': 'Dental Exam', 'duration': 30, 'price': 80.00},
                {'category': general_category, 'name': 'Filling', 'duration': 45, 'price': 150.00},
                {'category': cosmetic_category, 'name': 'Teeth Whitening', 'duration': 90, 'price': 300.00},
                {'category': cosmetic_category, 'name': 'Veneers Consultation', 'duration': 60, 'price': 100.00},
                {'category': specialty_category, 'name': 'Root Canal', 'duration': 120, 'price': 800.00},
                {'category': specialty_category, 'name': 'Crown Placement', 'duration': 90, 'price': 600.00},
            ]

            for service_data in services:
                Service.objects.create(
                    business=business,
                    category=service_data['category'],
                    name=service_data['name'],
                    duration_minutes=service_data['duration'],
                    price=service_data['price']
                )

            # Create staff
            staff_members = [
                {'first_name': 'Dr. Michael', 'last_name': 'Roberts', 'role': 'owner', 'email': 'dr.roberts@brightsmile.com'},
                {'first_name': 'Dr. Sarah', 'last_name': 'Davis', 'role': 'technician', 'email': 'dr.davis@brightsmile.com'},
                {'first_name': 'Jennifer', 'last_name': 'Miller', 'role': 'receptionist', 'email': 'jennifer@brightsmile.com'},
            ]

            for staff_data in staff_members:
                Staff.objects.create(
                    business=business,
                    first_name=staff_data['first_name'],
                    last_name=staff_data['last_name'],
                    role=staff_data['role'],
                    email=staff_data['email'],
                    phone='+1-555-0321'
                )

            self.stdout.write(f'Created dental clinic: {business.name}')

        return business

    def create_operating_hours(self, business):
        """Create default operating hours for a business"""
        # Monday to Friday: 9 AM - 6 PM
        # Saturday: 9 AM - 4 PM
        # Sunday: Closed
        hours_data = [
            {'day': 0, 'open': True, 'open_time': '09:00', 'close_time': '18:00'},  # Monday
            {'day': 1, 'open': True, 'open_time': '09:00', 'close_time': '18:00'},  # Tuesday
            {'day': 2, 'open': True, 'open_time': '09:00', 'close_time': '18:00'},  # Wednesday
            {'day': 3, 'open': True, 'open_time': '09:00', 'close_time': '18:00'},  # Thursday
            {'day': 4, 'open': True, 'open_time': '09:00', 'close_time': '18:00'},  # Friday
            {'day': 5, 'open': True, 'open_time': '09:00', 'close_time': '16:00'},  # Saturday
            {'day': 6, 'open': False},  # Sunday
        ]

        for hour_data in hours_data:
            OperatingHours.objects.create(
                business=business,
                day_of_week=hour_data['day'],
                is_open=hour_data['open'],
                open_time=hour_data.get('open_time'),
                close_time=hour_data.get('close_time')
            )

    def create_business_settings(self, business):
        """Create default business settings"""
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
            currency='CAD',
            tax_rate=0.13,
            require_payment_advance=False,
            allow_online_booking=True,
            require_client_phone=True,
            require_client_email=False,
            auto_confirm_appointments=False
        )
