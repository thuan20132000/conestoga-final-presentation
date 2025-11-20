from django.core.management.base import BaseCommand
from django.utils import timezone
from business.models import (
    BusinessType, Business, OperatingHours, BusinessSettings, BusinessRoles
)
from service.models import ServiceCategory, Service
from staff.models import Staff, StaffService
from payment.models import PaymentMethod


class Command(BaseCommand):
    help = 'Create sample businesses with services, staff, and settings'

    def handle(self, *args, **options):
        # Get business types
        hair_salon_type = BusinessType.objects.get(name='Hair Salon')
        nail_salon_type = BusinessType.objects.get(name='Nail Salon')
        spa_type = BusinessType.objects.get(name='Spa')
        dental_type = BusinessType.objects.get(name='Dental Clinic')
        
        self.create_hair_salon(hair_salon_type)
        self.create_nail_salon(nail_salon_type)


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

        return business
