from django.db import transaction
from django.utils import timezone
from .models import TimeEntry


class TimeEntryService:

    @staticmethod
    @transaction.atomic
    def clock_in(staff):
        if not staff.is_active:
            raise ValueError("Staff inactive")

        if TimeEntry.objects.filter(staff=staff, clock_out__isnull=True).exists():
            raise ValueError("Already clocked in")

        return TimeEntry.objects.create(
            staff=staff,
            clock_in=timezone.now(),
            status='IN_PROGRESS'
        )

    @staticmethod
    @transaction.atomic
    def clock_out(staff, break_minutes=0):
        try:
            entry = TimeEntry.objects.select_for_update().get(
                staff=staff,
                clock_out__isnull=True
            )
        except TimeEntry.DoesNotExist:
            raise ValueError("No active shift")

        entry.clock_out = timezone.now()
        entry.break_minutes = break_minutes
        entry.calculate_totals()
        entry.status = 'COMPLETED'
        entry.save()
        return entry
    
    @staticmethod
    @transaction.atomic
    def get_time_entry(staff):
        return TimeEntry.objects.get(staff=staff, clock_out__isnull=True)