from django.core.management.base import BaseCommand

from business.models import Business
from staff.models import StaffRole


class Command(BaseCommand):
    help = 'Create sample staff roles for all businesses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--business-id', type=int, help='Target a single business id'
        )
        parser.add_argument(
            '--clear-existing', action='store_true',
            help='Remove existing StaffRole for targeted businesses before creating'
        )

    def handle(self, *args, **options):
        business_id = options.get('business_id')
        clear_existing = options.get('clear_existing')

        if business_id:
            businesses = Business.objects.filter(id=business_id)
        else:
            businesses = Business.objects.all()

        if not businesses.exists():
            self.stdout.write(self.style.WARNING('No businesses found'))
            return

        for business in businesses:
            if clear_existing:
                StaffRole.objects.filter(business=business).delete()
            created_count = 0
            for role_value, _ in StaffRole.ROLE_CHOICES:
                obj, created = StaffRole.objects.get_or_create(
                    business=business, name=role_value
                )
                if created:
                    created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Business '{business.name}': ensured {created_count} staff roles"
                )
            )
