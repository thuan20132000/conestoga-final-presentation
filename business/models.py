from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from staff.models import Staff


class BusinessType(models.Model):
    """Different types of businesses that can use the system."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # For UI icons
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Business(models.Model):
    """Represents a salon or company using the AI receptionist."""
    BUSINESS_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Approval'),
    ]
    
    name = models.CharField(max_length=255)
    business_type = models.ForeignKey(BusinessType, on_delete=models.PROTECT, related_name='businesses')
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default="Canada")
    timezone = models.CharField(max_length=100, default="America/Toronto")
    status = models.CharField(max_length=20, choices=BUSINESS_STATUS_CHOICES, default='active')
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Businesses'
    
    def __str__(self):
        return self.name




class OperatingHours(models.Model):
    """Operating hours for each day of the week"""
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='operating_hours')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(blank=True, null=True)
    close_time = models.TimeField(blank=True, null=True)
    is_break_time = models.BooleanField(default=False, help_text="Has break time during the day")
    break_start_time = models.TimeField(blank=True, null=True)
    break_end_time = models.TimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['business', 'day_of_week']
        ordering = ['day_of_week']
    
    def __str__(self):
        day_name = dict(self.DAY_CHOICES)[self.day_of_week]
        if not self.is_open:
            return f"{day_name}: Closed"
        return f"{day_name}: {self.open_time} - {self.close_time}"


class BusinessSettings(models.Model):
    """Additional settings and preferences for the business"""
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='settings')
    
    # Booking settings
    advance_booking_days = models.PositiveIntegerField(default=30, help_text="How many days in advance can clients book")
    min_advance_booking_hours = models.PositiveIntegerField(default=2, help_text="Minimum hours in advance for booking")
    max_advance_booking_days = models.PositiveIntegerField(default=90, help_text="Maximum days in advance for booking")
    
    # Time slot settings
    time_slot_interval = models.PositiveIntegerField(default=15, help_text="Time slot interval in minutes")
    buffer_time_minutes = models.PositiveIntegerField(default=0, help_text="Buffer time between appointments")
    
    # Notification settings
    send_reminder_emails = models.BooleanField(default=True)
    send_reminder_sms = models.BooleanField(default=False)
    reminder_hours_before = models.PositiveIntegerField(default=24, help_text="Hours before appointment to send reminder")
    
    # Payment settings
    currency = models.CharField(max_length=3, default="CAD")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.13, help_text="Tax rate as decimal (0.13 = 13%)")
    require_payment_advance = models.BooleanField(default=False)
    
    # General settings
    allow_online_booking = models.BooleanField(default=True)
    require_client_phone = models.BooleanField(default=True)
    require_client_email = models.BooleanField(default=False)
    auto_confirm_appointments = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Settings for {self.business.name}"
