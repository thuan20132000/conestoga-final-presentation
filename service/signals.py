from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='service.Service')
def add_service_to_all_staff(sender, instance, created, **kwargs):
    if not created:
        return

    from staff.models import StaffService
    staff_ids = instance.business.staff_set.filter(is_active=True).values_list('id', flat=True)
    StaffService.objects.bulk_create(
        [StaffService(staff_id=staff_id, service=instance) for staff_id in staff_ids],
        ignore_conflicts=True,
    )