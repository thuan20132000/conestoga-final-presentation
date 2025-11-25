from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import uuid
from main.models import SoftDeleteModel


class Staff(AbstractUser, SoftDeleteModel):
    """Staff members working at the business"""
    
    
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE, null=True, blank=True, related_name='staff')
    phone = models.CharField(max_length=50, blank=True, null=True)
    role = models.ForeignKey(
        'business.BusinessRoles', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='staff',
        help_text="The role of the staff member in the business"
    )
    is_active = models.BooleanField(default=True)
    is_online_booking_allowed = models.BooleanField(default=True)
    is_payment_processing_allowed = models.BooleanField(default=True)
    hire_date = models.DateField(null=True, blank=True, default=timezone.now().date())
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.business})"
    
    def create_default_working_hours(self):
        from datetime import time
        for day in range(7):
            StaffWorkingHours.objects.create(staff=self, day_of_week=day, start_time=time(9, 30), end_time=time(17, 30))
        return self
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = str(uuid.uuid4())
            
        super().save(*args, **kwargs)
        
        if not self.working_hours.all():
            self.create_default_working_hours()

class StaffSalarySettings(SoftDeleteModel):
    """Staff salary settings"""
    BONUS_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ]
    staff = models.OneToOneField('staff.Staff', on_delete=models.CASCADE, related_name='staff_salary_settings')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    commission_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bonus_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bonus_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bonus_type = models.CharField(max_length=100, choices=BONUS_TYPE_CHOICES, default='percentage')
    
    class Meta:
        unique_together = ['staff']

class StaffService(SoftDeleteModel):
    """Many-to-many relationship between staff and services they can provide"""
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='staff_services')
    service = models.ForeignKey('service.Service', on_delete=models.CASCADE, related_name='staff_services')
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_duration = models.IntegerField(help_text="Duration in minutes", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_online_booking = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, help_text="Primary service for this staff member")
    
    class Meta:
        unique_together = ['staff', 'service']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - Service {self.service.name}"
    
class StaffWorkingHours(SoftDeleteModel):
    """Staff working hours"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    staff = models.ForeignKey('staff.Staff', on_delete=models.CASCADE, related_name='working_hours')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_working = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['staff', 'day_of_week']
    
    def __str__(self):
        return f"{self.staff} - {self.day_of_week}"

class StaffOffDay(SoftDeleteModel):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='staff_off_days')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.staff} - {self.start_date} to {self.end_date} - {self.reason}"
    
    class Meta:
        unique_together = ['staff', 'start_date', 'end_date']
